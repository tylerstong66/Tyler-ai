"""Persistent iterative training sessions for Tyler AI Skill Lab v2.19.

A session never activates a skill. Each round creates/evaluates a candidate through
SkillPromotionLab, records the result, and either marks the candidate ready for the
existing human promotion gate or preserves the active skill and waits for another
round. Failed candidate history is exposed to the next candidate draft.
"""

import hashlib
import json
import re
from datetime import datetime, timezone

SKILL_TRAINING_SESSION_CATEGORY = "skill_training_session"
SKILL_TRAINING_ROUND_CATEGORY = "skill_training_round"
SKILL_ITERATION_CATEGORIES = {
    SKILL_TRAINING_SESSION_CATEGORY,
    SKILL_TRAINING_ROUND_CATEGORY,
}


def _norm(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _slug(value):
    return re.sub(r"[^a-z0-9]+", "-", _norm(value).lower()).strip("-")[:80]


def _hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def _parse_row(row):
    try:
        data = json.loads(str((row or {}).get("memories") or ""))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    out = dict(data)
    out["_row_id"] = (row or {}).get("id")
    out["_created_at"] = (row or {}).get("created_at")
    return out


class IterativeSkillTrainer:
    """One bounded candidate+benchmark round at a time, persisted across calls."""

    TERMINAL = {"quality_gate_passed", "exhausted", "stale", "cancelled"}

    def __init__(self, lab, get_rows, save_row, now_fn=None, max_rounds=6):
        self.lab = lab
        self.get_rows = get_rows
        self.save_row = save_row
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc).isoformat())
        self.max_rounds = max(1, min(int(max_rounds), 20))

    def _now(self):
        value = self.now_fn()
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    def _records(self, category, limit=300):
        out = []
        for row in self.get_rows(category, limit) or []:
            parsed = _parse_row(row)
            if parsed:
                out.append(parsed)
        return out

    def _save(self, category, payload, importance=8):
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        rows = self.save_row(text, category, importance) or []
        out = dict(payload)
        if rows and isinstance(rows[0], dict):
            out["_row_id"] = rows[0].get("id")
        return out

    def sessions(self, skill_name=None, limit=50):
        sid = _slug(skill_name) if skill_name else None
        rows = self._records(SKILL_TRAINING_SESSION_CATEGORY, max(100, limit * 6))
        if sid:
            rows = [x for x in rows if _slug(x.get("skill_id")) == sid]
        # Records are append-only snapshots. Return only the newest snapshot per id.
        seen, out = set(), []
        for item in rows:
            session_id = str(item.get("session_id") or "")
            if not session_id or session_id in seen:
                continue
            seen.add(session_id)
            out.append(item)
            if len(out) >= limit:
                break
        return out

    def latest_session(self, skill_name):
        return next(iter(self.sessions(skill_name, 20)), None)

    def rounds(self, session_id, limit=30):
        target = str(session_id or "").upper()
        return [
            x for x in self._records(SKILL_TRAINING_ROUND_CATEGORY, max(100, limit * 5))
            if str(x.get("session_id") or "").upper() == target
        ][:limit]

    def feedback_bundle(self, skill_name, max_attempts=6):
        """Collect active weaknesses plus failed candidate evidence for redrafting."""
        active = self.lab.engine.get_skill(skill_name)
        if not active:
            raise ValueError(f"Skill {skill_name!r} was not found.")
        suite_hash = self.lab._suite_hash(active["skill_id"])
        active_run = self.lab._valid_eval(active, "active")
        active_weaknesses = []
        if active_run:
            for case in active_run.get("case_results") or []:
                active_weaknesses.extend(case.get("weaknesses") or [])

        candidates = {
            item.get("candidate_id"): item
            for item in self.lab.candidates(active["skill_id"], 100)
            if int(item.get("base_version") or -1) == int(active.get("version") or 0)
        }
        attempts = []
        for run in self.lab.evaluations(active["skill_id"], "candidate", 100):
            cid = run.get("candidate_id")
            candidate = candidates.get(cid)
            if not candidate or run.get("suite_hash") != suite_hash:
                continue
            weaknesses = []
            for case in run.get("case_results") or []:
                weaknesses.extend(case.get("weaknesses") or [])
            attempts.append({
                "candidate_id": cid,
                "average_score": float(run.get("average_score") or 0),
                "pass_rate": float(run.get("pass_rate") or 0),
                "weakness_count": int(run.get("weakness_count") or 0),
                "weaknesses": [_norm(x) for x in weaknesses if _norm(x)][:12],
                "instructions": list(candidate.get("instructions") or [])[:10],
                "success_criteria": list(candidate.get("success_criteria") or [])[:10],
                "rationale": _norm(candidate.get("rationale"))[:600],
            })
            if len(attempts) >= max(1, min(int(max_attempts), 12)):
                break

        # Stable de-duplication while preserving newest-first evidence order.
        seen, deduped = set(), []
        for item in active_weaknesses:
            key = _norm(item).lower()
            if key and key not in seen:
                seen.add(key)
                deduped.append(_norm(item))
        return {
            "active_version": int(active.get("version") or 1),
            "active_evaluation_id": (active_run or {}).get("run_id"),
            "active_average_score": float((active_run or {}).get("average_score") or 0),
            "active_pass_rate": float((active_run or {}).get("pass_rate") or 0),
            "active_weaknesses": deduped[:20],
            "failed_attempts": attempts,
            "suite_hash": suite_hash,
        }

    def start(self, skill_name, restart=False):
        active = self.lab.engine.get_skill(skill_name)
        if not active:
            raise ValueError(f"Skill {skill_name!r} was not found.")
        active_run = self.lab._valid_eval(active, "active")
        if not active_run:
            raise ValueError("A fresh active benchmark is required before iterative training.")

        current = self.latest_session(active["skill_id"])
        if current and current.get("status") not in self.TERMINAL and not restart:
            return current

        now = self._now().isoformat()
        sid = "TRN-" + _hash([
            active["skill_id"], active.get("version"), active_run.get("run_id"), now
        ])[:10].upper()
        feedback = self.feedback_bundle(active["skill_id"])
        payload = {
            "kind": "skill_training_session",
            "session_id": sid,
            "skill_id": active["skill_id"],
            "skill_name": active.get("name"),
            "active_version": int(active.get("version") or 1),
            "suite_hash": feedback["suite_hash"],
            "baseline_evaluation_id": active_run.get("run_id"),
            "baseline_average_score": float(active_run.get("average_score") or 0),
            "baseline_pass_rate": float(active_run.get("pass_rate") or 0),
            "baseline_weakness_count": int(active_run.get("weakness_count") or 0),
            "prior_failed_attempts": len(feedback["failed_attempts"]),
            "rounds_completed": 0,
            "max_rounds": self.max_rounds,
            "best_candidate_score": None,
            "best_candidate_id": None,
            "status": "ready_for_round",
            "automatic_activation": False,
            "human_promotion_required": True,
            "created_at": now,
            "updated_at": now,
        }
        return self._save(SKILL_TRAINING_SESSION_CATEGORY, payload, 8)

    def _validate_session(self, session):
        active = self.lab.engine.get_skill(session.get("skill_id"))
        if not active:
            return False, "active_skill_missing"
        if int(active.get("version") or 0) != int(session.get("active_version") or -1):
            return False, "active_skill_version_changed"
        if self.lab._suite_hash(active["skill_id"]) != session.get("suite_hash"):
            return False, "benchmark_suite_changed"
        if not self.lab._valid_eval(active, "active"):
            return False, "active_benchmark_stale"
        return True, None

    def advance(self, skill_name):
        session = self.latest_session(skill_name)
        if not session:
            raise ValueError("No iterative training session exists. Start one first.")
        if session.get("status") == "quality_gate_passed":
            raise ValueError("Training already has a candidate that passed the quality gate.")
        if session.get("status") in {"exhausted", "cancelled", "stale"}:
            raise ValueError("Training session is not eligible for another round.")

        ok, reason = self._validate_session(session)
        if not ok:
            stale = dict(session)
            stale.update({"status": "stale", "stale_reason": reason, "updated_at": self._now().isoformat()})
            self._save(SKILL_TRAINING_SESSION_CATEGORY, stale, 9)
            raise ValueError("Training session became stale: " + reason)

        active = self.lab.engine.get_skill(session["skill_id"])
        active_run = self.lab._valid_eval(active, "active")
        candidate = self.lab.propose_candidate(active["skill_id"])
        candidate_run = self.lab.evaluate(active["skill_id"], "candidate")
        metrics = self.lab._metrics(active_run, candidate_run)

        round_number = int(session.get("rounds_completed") or 0) + 1
        weaknesses = []
        for case in candidate_run.get("case_results") or []:
            weaknesses.extend(case.get("weaknesses") or [])
        round_payload = {
            "kind": "skill_training_round",
            "session_id": session["session_id"],
            "round_number": round_number,
            "skill_id": active["skill_id"],
            "active_version": int(active.get("version") or 1),
            "candidate_id": candidate.get("candidate_id"),
            "candidate_version": int(candidate.get("candidate_version") or 1),
            "candidate_evaluation_id": candidate_run.get("run_id"),
            "candidate_average_score": float(candidate_run.get("average_score") or 0),
            "candidate_pass_rate": float(candidate_run.get("pass_rate") or 0),
            "candidate_weakness_count": int(candidate_run.get("weakness_count") or 0),
            "weaknesses": [_norm(x) for x in weaknesses if _norm(x)][:20],
            "metrics": metrics,
            "gate_passed": bool(metrics.get("gate_passed")),
            "created_at": self._now().isoformat(),
        }
        saved_round = self._save(SKILL_TRAINING_ROUND_CATEGORY, round_payload, 8)

        score = float(candidate_run.get("average_score") or 0)
        best_score = session.get("best_candidate_score")
        is_best = best_score is None or score > float(best_score)
        if metrics.get("gate_passed"):
            status = "quality_gate_passed"
        elif round_number >= int(session.get("max_rounds") or self.max_rounds):
            status = "exhausted"
        else:
            status = "needs_next_round"

        updated = dict(session)
        updated.update({
            "rounds_completed": round_number,
            "status": status,
            "last_candidate_id": candidate.get("candidate_id"),
            "last_candidate_evaluation_id": candidate_run.get("run_id"),
            "last_candidate_score": score,
            "last_candidate_pass_rate": float(candidate_run.get("pass_rate") or 0),
            "last_gate_passed": bool(metrics.get("gate_passed")),
            "updated_at": self._now().isoformat(),
        })
        if is_best:
            updated["best_candidate_score"] = score
            updated["best_candidate_id"] = candidate.get("candidate_id")
        saved_session = self._save(SKILL_TRAINING_SESSION_CATEGORY, updated, 9 if metrics.get("gate_passed") else 8)
        return {
            "session": saved_session,
            "round": saved_round,
            "candidate": candidate,
            "evaluation": candidate_run,
            "metrics": metrics,
        }

    def cancel(self, skill_name):
        session = self.latest_session(skill_name)
        if not session:
            raise ValueError("No iterative training session exists.")
        if session.get("status") == "quality_gate_passed":
            raise ValueError("A quality-passing candidate exists; leave it for promotion or start a fresh session later.")
        updated = dict(session)
        updated.update({"status": "cancelled", "updated_at": self._now().isoformat()})
        return self._save(SKILL_TRAINING_SESSION_CATEGORY, updated, 7)

    def status(self, skill_name=None):
        sessions = self.sessions(skill_name, 20)
        return {
            "enabled": True,
            "one_bounded_round_per_command": True,
            "automatic_activation": False,
            "human_promotion_required": True,
            "max_rounds": self.max_rounds,
            "sessions": sessions,
        }
