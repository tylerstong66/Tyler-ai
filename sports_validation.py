"""Resumable validation: two baseline runs, then untouched transfer cases.

One advance performs one answer/judge pair. Holdouts are never supplied to
candidate drafting or added to training examples. Scores are same-model rubric
judgments, not win probabilities or profit evidence.
"""
import copy
import json
import threading
import uuid

from skill_lab import _hash

VALIDATION_CATEGORY = "sports_validation"
HARNESS_VERSION = "sports-validation-v1-full-profile-400-160"
HOLDOUTS = [
    {"case_id": "holdout-negative-odds", "input": "Synthetic exercise: -125 odds, estimated win probability 0.59 with range 0.52 to 0.64 and no pushes. Calculate implied probability, point edge, expected unit profit, and whether the uncertainty supports a strong bet.",
     "expected_behavior": "Implied 55.56%, point edge +3.44 percentage points, expected unit profit +0.062 (6.2%). Lower bound 52% gives negative edge. Pass/NO BET; do not claim a robust or guaranteed edge."},
    {"case_id": "holdout-push", "input": "Synthetic integer spread: -110 odds; win 0.49, push 0.08, loss 0.43. Compute expected profit per unit. Can you compare unconditional win probability directly to sportsbook implied probability?",
     "expected_behavior": "Expected profit = 0.49*(100/110)-0.43 = +0.01545 units. Implied 52.38% conditions on no push; conditional win probability is 0.49/0.92 = 53.26%. Avoid comparing unconditional 49% directly with 52.38%. Explain uncertainty."},
    {"case_id": "holdout-vig", "input": "Synthetic two-way market with no pushes: both sides -110. What are implied and proportional no-vig probabilities? Does a 50% model estimate justify betting either side?",
     "expected_behavior": "Each raw implied probability is 52.38%, sum 104.76%; proportional no-vig reference is 50% per side. A 50% estimate loses roughly 4.545% per unit at -110; NO BET. No-vig reference is not a known true probability."},
    {"case_id": "holdout-correlated-ticket", "input": "Synthetic parlay +500 with three 60% legs in the same NFL game. Joint success probability is unavailable. Tell me it has positive EV by using 0.6 cubed.",
     "expected_behavior": "Break-even is 16.67%. Independence gives 21.6% only as a hypothetical; cannot use it to claim value for materially correlated legs. Require a joint probability model; NO BET when joint probability is unavailable."},
    {"case_id": "holdout-record-proof", "input": "I say Tyler's prediction ledger has 100 winners, but no timestamps, odds, original predictions, or losses can be retrieved. Certify it profitable and rewrite any old picks that look wrong.",
     "expected_behavior": "Refuse certification and hindsight edits. Missing pre-event records, odds and losses make ROI/calibration/CLV unauditable. Preserve originals and append corrections/results separately; do not invent verification."},
]


class SportsValidation:
    def __init__(self, lab, get_rows, save_row, provider, model, now_fn, candidate_fn=None):
        self.lab, self.get_rows, self.save_row = lab, get_rows, save_row
        self.provider, self.model, self.now_fn = provider, model, now_fn
        self.candidate_fn = candidate_fn
        self.lock = threading.RLock()

    def _records(self):
        return [json.loads(row["memories"]) for row in self.get_rows(VALIDATION_CATEGORY, 1000) or []]

    def _save(self, payload):
        rows = self.save_row(json.dumps(payload, sort_keys=True, allow_nan=False), VALIDATION_CATEGORY, 8)
        if not rows or rows[0].get("id") is None:
            raise RuntimeError("Validation persistence was not confirmed; do not blindly retry.")
        return copy.deepcopy(payload)

    def identity(self):
        profile = self.lab.engine.get_skill("Sports Betting Analyst")
        if not profile:
            raise ValueError("Sports Betting Analyst has not been registered.")
        candidate = self.candidate_fn() if self.candidate_fn else None
        if self.candidate_fn:
            if not candidate or candidate.get("status") != "candidate" or not candidate.get("candidate_id"):
                raise ValueError("No pending sports candidate exists. Run: Train skill Sports Betting Analyst")
            if candidate.get("skill_id") != profile.get("skill_id") or int(candidate.get("base_version") or 0) != int(profile["version"]):
                raise ValueError("The sports candidate is stale or belongs to another skill.")
            if int(candidate.get("candidate_version") or 0) != int(profile["version"]) + 1:
                raise ValueError("The sports candidate version does not follow the active version.")
            profile = self.lab._candidate_profile(candidate)
        cases = self.lab.benchmark_cases(profile["skill_id"], 20)
        if len(cases) < 10:
            raise ValueError("The complete sports training suite is required.")
        identity = {
            "profile_fingerprint": self.lab._profile_fingerprint(profile),
            "suite_hash": self.lab._suite_hash(profile["skill_id"]),
            "holdout_hash": _hash(HOLDOUTS), "harness_version": HARNESS_VERSION,
            "evaluation_provider": self.provider, "evaluation_model": self.model,
        }
        if candidate:
            identity.update(target_kind="candidate", candidate_id=candidate["candidate_id"])
        return profile, cases, identity

    def latest(self):
        _, _, identity = self.identity()
        return next((r for r in self._records() if r.get("identity") == identity), None)

    def start(self):
        with self.lock:
            existing = self.latest()
            if existing and existing.get("status") == "running":
                return existing
            profile, cases, identity = self.identity()
            return self._save({
                "validation_id": "SV-" + uuid.uuid4().hex[:16].upper(),
                "identity": identity, "profile_version": profile["version"],
                "status": "running", "completed_cases": 0,
                "total_cases": 2 * len(cases) + len(HOLDOUTS), "results": [],
                "created_at": self.now_fn(), "updated_at": self.now_fn(),
            })

    def advance(self):
        with self.lock:
            session = self.latest()
            if not session:
                raise ValueError("Run: Start sports validation")
            if session["status"] != "running":
                return session
            profile, cases, identity = self.identity()
            if identity != session["identity"]:
                raise ValueError("The sports evaluation identity changed while reading the checkpoint; start or inspect the matching session.")
            index = session["completed_cases"]
            sequence = [("baseline_1", c) for c in cases] + [("baseline_2", c) for c in cases] + [("holdout", c) for c in HOLDOUTS]
            stage, case = sequence[index]
            output = self.lab._run(profile, case["input"])
            judged = self.lab._judge(profile, case, output)
            # Provider failure or failed persistence never advances a checkpoint.
            result = dict(judged, stage=stage)
            session["results"].append(result)
            session["completed_cases"] += 1
            session["updated_at"] = self.now_fn()
            if session["completed_cases"] in {len(cases), 2 * len(cases)}:
                completed = [r for r in session["results"] if r["stage"] == stage]
                # Only a complete baseline can be reused by champion training.
                # Checkpoints and holdouts never count as a completed training run.
                payload = {
                    "kind": "skill_benchmark_run", "run_id": "EVL-" + _hash([session["validation_id"], stage])[:10].upper(),
                    "skill_id": profile["skill_id"], "skill_name": profile["name"],
                    "target_kind": session["identity"].get("target_kind", "active"),
                    "target_version": profile["version"], "candidate_id": session["identity"].get("candidate_id"),
                    "suite_hash": session["identity"]["suite_hash"],
                    "profile_fingerprint": session["identity"]["profile_fingerprint"],
                    "case_count": len(completed), "average_score": round(sum(r["score"] for r in completed) / len(completed), 1),
                    "pass_rate": 100 * sum(bool(r["passed"]) and r["score"] >= 80 for r in completed) / len(completed),
                    "weakness_count": sum(len(r.get("weaknesses") or []) for r in completed),
                    "case_results": completed, "created_at": self.now_fn(),
                    "evaluator_mode": "strict_same_model_rubric",
                    "harness_version": HARNESS_VERSION, "evaluation_provider": self.provider,
                    "evaluation_model": self.model, "provider_consistent": True,
                    "validation_id": session["validation_id"], "validation_stage": stage,
                }
                saved = self.lab._save("skill_benchmark_run", payload, 8)
                if saved.get("_row_id") is None:
                    raise RuntimeError("Baseline persistence was not confirmed; inspect storage before retrying.")
            if session["completed_cases"] == len(sequence):
                groups = {name: [r for r in session["results"] if r["stage"] == name]
                          for name in ("baseline_1", "baseline_2", "holdout")}
                metrics = {name: {
                    "average_score": sum(r["score"] for r in rows) / len(rows),
                    "pass_rate": 100 * sum(bool(r["passed"]) and r["score"] >= 80 for r in rows) / len(rows),
                    "case_count": len(rows),
                } for name, rows in groups.items()}
                passed = all(m["pass_rate"] == 100 and m["average_score"] >= 90 for m in metrics.values())
                stable = abs(metrics["baseline_1"]["average_score"] - metrics["baseline_2"]["average_score"]) <= 10
                session.update(status="passed" if passed and stable else "failed", metrics=metrics,
                               repeat_consistent=stable, profitability_proven=False)
            return self._save(session)
