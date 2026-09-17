"""Champion-based iterative training for Tyler AI v2.19.1.

A verified champion is the strongest consistently re-tested candidate for the current
active skill version and benchmark suite. New candidates evolve from that champion,
not from the weaker active profile, while the active skill remains unchanged until
the existing human promotion gate is explicitly approved and executed.
"""

from skill_iteration import (
    IterativeSkillTrainer,
    SKILL_TRAINING_ROUND_CATEGORY,
    SKILL_TRAINING_SESSION_CATEGORY,
)
from skill_lab import (
    SKILL_BENCHMARK_RUN_CATEGORY,
    SKILL_CANDIDATE_CATEGORY,
    _hash,
)

SKILL_CHAMPION_CHECK_CATEGORY = "skill_champion_check"
SKILL_CHAMPION_CATEGORIES = {SKILL_CHAMPION_CHECK_CATEGORY}


class ChampionSkillTrainer(IterativeSkillTrainer):
    """Persist a conservative champion and require a second benchmark to verify it."""

    def __init__(
        self,
        lab,
        get_rows,
        save_row,
        now_fn=None,
        max_rounds=6,
        consistency_tolerance=10.0,
    ):
        super().__init__(lab, get_rows, save_row, now_fn=now_fn, max_rounds=max_rounds)
        self.consistency_tolerance = max(0.0, float(consistency_tolerance))

    def _candidate_by_id(self, skill_name, candidate_id):
        target = str(candidate_id or "").upper()
        for item in self.lab.candidates(skill_name, 200):
            if str(item.get("candidate_id") or "").upper() == target:
                return item
        return None

    def _valid_candidate_runs(self, active, candidate):
        if not candidate:
            return []
        suite = self.lab._suite_hash(active["skill_id"])
        profile = self.lab._candidate_profile(candidate)
        fingerprint = self.lab._profile_fingerprint(profile)
        out = []
        for run in self.lab.evaluations(active["skill_id"], "candidate", 300):
            if run.get("candidate_id") != candidate.get("candidate_id"):
                continue
            if run.get("suite_hash") != suite:
                continue
            if run.get("profile_fingerprint") != fingerprint:
                continue
            out.append(run)
        return out

    def historical_best(self, skill_name):
        """Return the strongest one-run candidate for the current active/suite."""
        active = self.lab.engine.get_skill(skill_name)
        if not active:
            return None
        candidates = {}
        for item in self.lab.candidates(active["skill_id"], 300):
            cid = item.get("candidate_id")
            if (
                cid
                and cid not in candidates
                and item.get("status") == "candidate"
                and int(item.get("base_version") or -1) == int(active.get("version") or 0)
            ):
                candidates[cid] = item

        best = None
        for candidate in candidates.values():
            runs = self._valid_candidate_runs(active, candidate)
            if not runs:
                continue
            run = runs[0]
            value = (
                float(run.get("average_score") or 0),
                float(run.get("pass_rate") or 0),
                -int(run.get("weakness_count") or 0),
            )
            if best is None or value > best["sort_value"]:
                best = {"candidate": candidate, "run": run, "sort_value": value}
        return best

    def _evaluate_specific_candidate(self, candidate):
        """Benchmark one explicit candidate instead of whichever record is newest."""
        active = self.lab.engine.get_skill(candidate.get("skill_id"))
        if not active:
            raise ValueError("Active skill is missing.")
        if int(candidate.get("base_version") or -1) != int(active.get("version") or 0):
            raise ValueError("Candidate is stale because the active skill version changed.")
        cases = self.lab.benchmark_cases(active["skill_id"], 20)
        if not cases:
            raise ValueError("No benchmark cases exist for this skill.")

        profile = self.lab._candidate_profile(candidate)
        results = [
            self.lab._judge(profile, case, self.lab._run(profile, case.get("input")))
            for case in cases
        ]
        scores = [int(x.get("score") or 0) for x in results]
        average = round(sum(scores) / len(scores), 1) if scores else 0.0
        pass_rate = (
            round(100 * sum(1 for x in results if x.get("passed")) / len(results), 1)
            if results else 0.0
        )
        created = self._now().isoformat()
        payload = {
            "kind": "skill_benchmark_run",
            "run_id": "EVL-" + _hash([
                active["skill_id"],
                "candidate",
                candidate.get("candidate_id"),
                profile.get("version"),
                created,
            ])[:10].upper(),
            "skill_id": active["skill_id"],
            "skill_name": active.get("name"),
            "target_kind": "candidate",
            "target_version": int(profile.get("version") or 1),
            "candidate_id": candidate.get("candidate_id"),
            "suite_hash": self.lab._suite_hash(active["skill_id"]),
            "profile_fingerprint": self.lab._profile_fingerprint(profile),
            "case_count": len(results),
            "average_score": average,
            "pass_rate": pass_rate,
            "weakness_count": sum(len(x.get("weaknesses") or []) for x in results),
            "case_results": results,
            "evaluator_mode": "strict_same_model_rubric",
            "created_at": created,
        }
        return self.lab._save(SKILL_BENCHMARK_RUN_CATEGORY, payload, 7)

    def _save_session(self, session, importance=8):
        clean = {k: v for k, v in dict(session or {}).items() if not str(k).startswith("_")}
        return self._save(SKILL_TRAINING_SESSION_CATEGORY, clean, importance)

    def _refresh_candidate(self, candidate, **updates):
        clean = {k: v for k, v in dict(candidate or {}).items() if not str(k).startswith("_")}
        clean.update(updates)
        return self.lab._save(SKILL_CANDIDATE_CATEGORY, clean, 8)

    def _reference(self, session):
        if session.get("champion_verified") and session.get("champion_candidate_id"):
            return {
                "candidate_id": session.get("champion_candidate_id"),
                "score": float(session.get("champion_score") or 0),
                "pass_rate": float(session.get("champion_pass_rate") or 0),
                "source": "verified_candidate",
            }
        return {
            "candidate_id": None,
            "score": float(session.get("baseline_average_score") or 0),
            "pass_rate": float(session.get("baseline_pass_rate") or 0),
            "source": "active_baseline",
        }

    def _beats_reference(self, session, run):
        ref = self._reference(session)
        score = float(run.get("average_score") or 0)
        pass_rate = float(run.get("pass_rate") or 0)
        measurable = (
            score >= ref["score"] + self.lab.minimum_improvement
            or pass_rate >= ref["pass_rate"] + self.lab.minimum_improvement
        )
        not_worse = score >= ref["score"] and pass_rate >= ref["pass_rate"]
        return {
            "reference_candidate_id": ref["candidate_id"],
            "reference_score": ref["score"],
            "reference_pass_rate": ref["pass_rate"],
            "candidate_score": score,
            "candidate_pass_rate": pass_rate,
            "candidate_not_worse_than_champion": bool(not_worse),
            "measurable_champion_improvement": bool(measurable),
            "beats_champion": bool(not_worse and measurable),
        }

    def _seed_champion_state(self, session):
        baseline_score = float(session.get("baseline_average_score") or 0)
        baseline_pass = float(session.get("baseline_pass_rate") or 0)
        best = self.historical_best(session["skill_id"])
        if not best:
            return dict(session)

        run = best["run"]
        score = float(run.get("average_score") or 0)
        pass_rate = float(run.get("pass_rate") or 0)
        improved = (
            score >= baseline_score
            and pass_rate >= baseline_pass
            and (
                score >= baseline_score + self.lab.minimum_improvement
                or pass_rate >= baseline_pass + self.lab.minimum_improvement
            )
        )
        if not improved:
            return dict(session)

        seeded = dict(session)
        seeded.update({
            "status": "champion_confirmation_required",
            "champion_candidate_id": None,
            "champion_score": baseline_score,
            "champion_pass_rate": baseline_pass,
            "champion_verified": True,
            "champion_source": "active_baseline",
            "pending_champion_candidate_id": best["candidate"].get("candidate_id"),
            "pending_champion_initial_evaluation_id": run.get("run_id"),
            "pending_champion_initial_score": score,
            "pending_champion_initial_pass_rate": pass_rate,
            "pending_champion_source": "historical_best",
            "consistency_checks_required": 2,
            "updated_at": self._now().isoformat(),
        })
        return seeded

    def start(self, skill_name, restart=False):
        active = self.lab.engine.get_skill(skill_name)
        if not active:
            raise ValueError(f"Skill {skill_name!r} was not found.")

        current = self.latest_session(active["skill_id"])
        if current and current.get("status") not in self.TERMINAL and not restart:
            return current

        session = super().start(active["skill_id"], restart=True)
        session = dict(session)
        session.update({
            "champion_candidate_id": None,
            "champion_score": float(session.get("baseline_average_score") or 0),
            "champion_pass_rate": float(session.get("baseline_pass_rate") or 0),
            "champion_verified": True,
            "champion_source": "active_baseline",
            "consistency_tolerance": self.consistency_tolerance,
            "consistency_checks_required": 2,
            "pending_champion_candidate_id": None,
        })
        session = self._seed_champion_state(session)
        return self._save_session(session, 8)

    def champion_candidate(self, skill_name):
        session = self.latest_session(skill_name)
        if not session or not session.get("champion_verified"):
            return None
        cid = session.get("champion_candidate_id")
        return self._candidate_by_id(skill_name, cid) if cid else None

    def _confirm_pending(self, session):
        ok, reason = self._validate_session(session)
        if not ok:
            stale = dict(session)
            stale.update({
                "status": "stale",
                "stale_reason": reason,
                "updated_at": self._now().isoformat(),
            })
            self._save_session(stale, 9)
            raise ValueError("Training session became stale: " + reason)

        candidate = self._candidate_by_id(
            session["skill_id"], session.get("pending_champion_candidate_id")
        )
        if not candidate:
            raise ValueError("Pending champion candidate is missing.")

        confirmation = self._evaluate_specific_candidate(candidate)
        first_score = float(session.get("pending_champion_initial_score") or 0)
        first_pass = float(session.get("pending_champion_initial_pass_rate") or 0)
        second_score = float(confirmation.get("average_score") or 0)
        second_pass = float(confirmation.get("pass_rate") or 0)
        reference = self._reference(session)

        mean_score = round((first_score + second_score) / 2.0, 1)
        mean_pass = round((first_pass + second_pass) / 2.0, 1)
        score_spread = round(abs(first_score - second_score), 1)
        not_worse = second_score >= reference["score"] and second_pass >= reference["pass_rate"]
        measurable = (
            mean_score >= reference["score"] + self.lab.minimum_improvement
            or mean_pass >= reference["pass_rate"] + self.lab.minimum_improvement
        )
        consistent = score_spread <= self.consistency_tolerance
        confirmed = bool(not_worse and measurable and consistent)

        check = {
            "kind": "skill_champion_check",
            "session_id": session.get("session_id"),
            "skill_id": session.get("skill_id"),
            "candidate_id": candidate.get("candidate_id"),
            "reference_candidate_id": reference["candidate_id"],
            "reference_score": reference["score"],
            "reference_pass_rate": reference["pass_rate"],
            "initial_evaluation_id": session.get("pending_champion_initial_evaluation_id"),
            "confirmation_evaluation_id": confirmation.get("run_id"),
            "initial_score": first_score,
            "confirmation_score": second_score,
            "confirmed_average_score": mean_score,
            "initial_pass_rate": first_pass,
            "confirmation_pass_rate": second_pass,
            "confirmed_average_pass_rate": mean_pass,
            "score_spread": score_spread,
            "consistency_tolerance": self.consistency_tolerance,
            "consistent": bool(consistent),
            "confirmed": bool(confirmed),
            "created_at": self._now().isoformat(),
        }
        saved_check = self._save(SKILL_CHAMPION_CHECK_CATEGORY, check, 8)

        updated = dict(session)
        updated.update({
            "last_confirmation_candidate_id": candidate.get("candidate_id"),
            "last_confirmation_evaluation_id": confirmation.get("run_id"),
            "last_consistency_passed": bool(confirmed),
            "pending_champion_candidate_id": None,
            "pending_champion_initial_evaluation_id": None,
            "pending_champion_initial_score": None,
            "pending_champion_initial_pass_rate": None,
            "updated_at": self._now().isoformat(),
        })

        active = self.lab.engine.get_skill(session["skill_id"])
        active_run = self.lab._valid_eval(active, "active")
        metrics = self.lab._metrics(active_run, confirmation)

        if confirmed:
            updated.update({
                "champion_candidate_id": candidate.get("candidate_id"),
                "champion_score": mean_score,
                "champion_pass_rate": mean_pass,
                "champion_verified": True,
                "champion_source": "confirmed_candidate",
                "best_candidate_id": candidate.get("candidate_id"),
                "best_candidate_score": max(
                    mean_score, float(session.get("best_candidate_score") or 0)
                ),
            })
            self._refresh_candidate(
                candidate,
                champion_verified=True,
                champion_confirmed_score=mean_score,
                champion_confirmed_pass_rate=mean_pass,
                champion_confirmation_evaluation_id=confirmation.get("run_id"),
            )
            both_meet_floor = (
                first_score >= self.lab.minimum_candidate_score
                and second_score >= self.lab.minimum_candidate_score
            )
            if both_meet_floor and metrics.get("gate_passed"):
                updated["status"] = "quality_gate_passed"
            elif int(updated.get("rounds_completed") or 0) >= int(
                updated.get("max_rounds") or self.max_rounds
            ):
                updated["status"] = "exhausted"
            else:
                updated["status"] = "needs_next_round"
        elif int(updated.get("rounds_completed") or 0) >= int(
            updated.get("max_rounds") or self.max_rounds
        ):
            updated["status"] = "exhausted"
        else:
            updated["status"] = "needs_next_round"

        saved_session = self._save_session(
            updated, 9 if updated.get("status") == "quality_gate_passed" else 8
        )
        return {
            "mode": "champion_confirmation",
            "session": saved_session,
            "candidate": candidate,
            "evaluation": confirmation,
            "metrics": metrics,
            "champion_check": saved_check,
        }

    def advance(self, skill_name):
        session = self.latest_session(skill_name)
        if not session:
            raise ValueError("No champion training session exists. Start one first.")
        if session.get("status") == "champion_confirmation_required":
            return self._confirm_pending(session)
        if session.get("status") == "quality_gate_passed":
            raise ValueError(
                "Training already has a consistently verified candidate that passed the quality gate."
            )
        if session.get("status") in {"exhausted", "cancelled", "stale"}:
            raise ValueError("Training session is not eligible for another round.")

        ok, reason = self._validate_session(session)
        if not ok:
            stale = dict(session)
            stale.update({
                "status": "stale",
                "stale_reason": reason,
                "updated_at": self._now().isoformat(),
            })
            self._save_session(stale, 9)
            raise ValueError("Training session became stale: " + reason)

        active = self.lab.engine.get_skill(session["skill_id"])
        active_run = self.lab._valid_eval(active, "active")
        candidate = self.lab.propose_candidate(active["skill_id"])
        candidate_run = self.lab.evaluate(active["skill_id"], "candidate")
        active_metrics = self.lab._metrics(active_run, candidate_run)
        champion_metrics = self._beats_reference(session, candidate_run)

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
            "weaknesses": [str(x).strip() for x in weaknesses if str(x).strip()][:20],
            "metrics": active_metrics,
            "champion_metrics": champion_metrics,
            "gate_passed": False,
            "created_at": self._now().isoformat(),
        }
        saved_round = self._save(SKILL_TRAINING_ROUND_CATEGORY, round_payload, 8)

        updated = dict(session)
        updated.update({
            "rounds_completed": round_number,
            "last_candidate_id": candidate.get("candidate_id"),
            "last_candidate_evaluation_id": candidate_run.get("run_id"),
            "last_candidate_score": float(candidate_run.get("average_score") or 0),
            "last_candidate_pass_rate": float(candidate_run.get("pass_rate") or 0),
            "last_gate_passed": False,
            "updated_at": self._now().isoformat(),
        })

        if champion_metrics.get("beats_champion"):
            updated.update({
                "status": "champion_confirmation_required",
                "pending_champion_candidate_id": candidate.get("candidate_id"),
                "pending_champion_initial_evaluation_id": candidate_run.get("run_id"),
                "pending_champion_initial_score": float(candidate_run.get("average_score") or 0),
                "pending_champion_initial_pass_rate": float(candidate_run.get("pass_rate") or 0),
                "pending_champion_source": "new_training_round",
            })
        elif round_number >= int(session.get("max_rounds") or self.max_rounds):
            updated["status"] = "exhausted"
        else:
            updated["status"] = "needs_next_round"

        saved_session = self._save_session(updated, 8)
        return {
            "mode": "candidate_round",
            "session": saved_session,
            "round": saved_round,
            "candidate": candidate,
            "evaluation": candidate_run,
            "metrics": active_metrics,
            "champion_metrics": champion_metrics,
        }

    def status(self, skill_name=None):
        out = super().status(skill_name)
        out.update({
            "champion_based_training": True,
            "champion_requires_confirmation": True,
            "consistency_checks_per_champion": 2,
            "consistency_tolerance": self.consistency_tolerance,
            "automatic_activation": False,
            "human_promotion_required": True,
        })
        return out
