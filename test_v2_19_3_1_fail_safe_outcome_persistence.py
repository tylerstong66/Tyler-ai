import json
import unittest

import app_v2_19_3_1 as v21931
import skill_lab as labmod
from skill_lab import SkillPromotionLab
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class FakeResponse:
    def __init__(self, rows=None, ok=True):
        self._rows = rows or []
        self.ok = ok

    def json(self):
        return list(self._rows)


class FailSafeOutcomePersistenceTests(unittest.TestCase):
    def setUp(self):
        v21931._HISTORY_CACHE.clear()
        v21931._LOCAL_OUTCOMES.clear()

    def make_lab(self):
        store = MemoryStore()
        engine = FakeEngine()
        lab = SkillPromotionLab(
            engine, store.get_rows, store.save_row,
            minimum_candidate_score=80, minimum_improvement=1,
        )
        active = engine.create_or_update_skill(
            "Test Skill",
            "Do safe developer work.",
            instructions=["Inspect current code.", "Report only verified state."],
            success_criteria=["Changes are grounded.", "Claims are verified."],
            allowed_tools=["reason", "github"],
        )
        return store, engine, lab, active

    def sample_result(self):
        return {
            "mode": "candidate_round",
            "session": {"session_id": "TRN-FAILSAFE01"},
            "round": {"round_number": 6},
            "candidate": {
                "candidate_id": "CND-FAILSAFE1",
                "skill_id": "test-skill",
                "base_version": 1,
                "parent_candidate_id": "CND-CHAMPION1",
                "parent_verified_score": 65.0,
                "parent_verified_pass_rate": 60.0,
                "mutation_target_case_id": "case-b",
                "mutation_target_weakness": "Needs stronger verification.",
                "mutation_diff": {
                    "kind": "instruction",
                    "resolved_index": 2,
                    "before": "Report only verified state.",
                    "after": "Report only state verified against current repository evidence.",
                },
            },
            "evaluation": {
                "run_id": "EVL-FAILSAFE1",
                "average_score": 48.0,
                "pass_rate": 40.0,
                "case_results": [
                    {"case_id": "case-a", "score": 60, "weaknesses": []},
                    {"case_id": "case-b", "score": 36, "weaknesses": ["Verification regressed."]},
                ],
            },
        }

    def test_completed_round_wrapper_performs_zero_post_benchmark_storage_io(self):
        result = self.sample_result()
        original_core = v21931._CORE_ADVANCE
        original_records = v21931.SKILL_LAB._records
        original_save = v21931.SKILL_LAB._save

        def forbidden(*args, **kwargs):
            raise AssertionError("post-benchmark storage I/O was attempted")

        try:
            v21931._CORE_ADVANCE = lambda skill_name: dict(result)
            v21931.SKILL_LAB._records = forbidden
            v21931.SKILL_LAB._save = forbidden
            out = v21931._advance_fail_safe(object(), "test-skill")
        finally:
            v21931._CORE_ADVANCE = original_core
            v21931.SKILL_LAB._records = original_records
            v21931.SKILL_LAB._save = original_save

        self.assertEqual(out["evaluation"]["run_id"], "EVL-FAILSAFE1")
        self.assertEqual(out["mutation_outcome"]["score_delta"], -17.0)
        self.assertEqual(out["mutation_outcome"]["pass_rate_delta"], -20.0)
        self.assertTrue(out["mutation_outcome"]["persisted_via_existing_records"])
        meta = out["mutation_outcome_persistence"]
        self.assertEqual(meta["post_benchmark_database_reads"], 0)
        self.assertEqual(meta["post_benchmark_database_writes"], 0)
        self.assertTrue(meta["response_fail_safe"])

    def test_deterministic_outcome_id_is_idempotent_for_same_completed_run(self):
        first = v21931._outcome_from_completed_result(self.sample_result())
        second = v21931._outcome_from_completed_result(self.sample_result())
        self.assertEqual(first["outcome_id"], second["outcome_id"])
        self.assertEqual(first["candidate_id"], second["candidate_id"])
        self.assertEqual(first["evaluation_id"], second["evaluation_id"])
        self.assertEqual(first["outcome"], "harmful")

    def test_bounded_supabase_history_read_uses_short_timeout(self):
        old_url = getattr(v21931.base, "SUPABASE_URL", "")
        old_get = v21931.base.requests.get
        old_headers = v21931.base.supabase_headers
        calls = []

        row = {
            "id": 1,
            "created_at": "2026-09-18T11:00:00+00:00",
            "memories": json.dumps({"kind": "x", "candidate_id": "CND-X"}),
            "category": "skill_candidate",
            "importance": 8,
        }

        def fake_get(url, headers=None, params=None, timeout=None):
            calls.append({
                "url": url, "headers": headers, "params": params, "timeout": timeout,
            })
            return FakeResponse([row], ok=True)

        try:
            v21931.base.SUPABASE_URL = "https://example.supabase.co"
            v21931.base.requests.get = fake_get
            v21931.base.supabase_headers = lambda: {"apikey": "test"}
            rows = v21931._bounded_records(v21931.SKILL_LAB, "skill_candidate", 20)
        finally:
            v21931.base.SUPABASE_URL = old_url
            v21931.base.requests.get = old_get
            v21931.base.supabase_headers = old_headers

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            calls[0]["timeout"],
            (
                v21931.OUTCOME_DB_CONNECT_TIMEOUT_SECONDS,
                v21931.OUTCOME_DB_READ_TIMEOUT_SECONDS,
            ),
        )
        self.assertLess(v21931.OUTCOME_DB_READ_TIMEOUT_SECONDS, 5.0)

    def test_durable_history_uses_bulk_reads_and_cache_not_n_plus_one(self):
        store, engine, lab, active = self.make_lab()
        candidate = {
            "kind": "skill_candidate",
            "candidate_id": "CND-HISTORY1",
            "skill_id": active["skill_id"],
            "name": active["name"],
            "purpose": active["purpose"],
            "base_version": 1,
            "candidate_version": 2,
            "parent_candidate_id": "CND-PARENT1",
            "parent_verified_score": 65.0,
            "parent_verified_pass_rate": 60.0,
            "mutation_diff": {
                "kind": "criterion",
                "resolved_index": 2,
                "before": "Claims are verified.",
                "after": "Claims are verified against exact current state.",
            },
            "instructions": list(active["instructions"]),
            "success_criteria": [
                active["success_criteria"][0],
                "Claims are verified against exact current state.",
            ],
            "allowed_tools": list(active["allowed_tools"]),
            "status": "candidate",
        }
        fingerprint = lab._profile_fingerprint(lab._candidate_profile(candidate))
        active_run = {
            "kind": "skill_benchmark_run",
            "run_id": "EVL-ACTIVE1",
            "skill_id": active["skill_id"],
            "target_kind": "active",
            "suite_hash": "suite-current",
            "average_score": 56.0,
            "pass_rate": 40.0,
        }
        candidate_run = {
            "kind": "skill_benchmark_run",
            "run_id": "EVL-HISTORY1",
            "skill_id": active["skill_id"],
            "target_kind": "candidate",
            "candidate_id": candidate["candidate_id"],
            "suite_hash": "suite-current",
            "profile_fingerprint": fingerprint,
            "average_score": 69.0,
            "pass_rate": 60.0,
            "case_results": [{"case_id": "case-b", "score": 69, "weaknesses": []}],
        }

        original = v21931._bounded_records
        calls = []

        def fake_records(_lab, category, limit):
            calls.append(category)
            if category == v21931.MUTATION_OUTCOME_CATEGORY:
                return []
            if category == labmod.SKILL_CANDIDATE_CATEGORY:
                return [candidate]
            if category == labmod.SKILL_BENCHMARK_RUN_CATEGORY:
                return [active_run, candidate_run]
            return []

        try:
            v21931._bounded_records = fake_records
            first = v21931._durable_history(lab, active)
            second = v21931._durable_history(lab, active)
        finally:
            v21931._bounded_records = original

        self.assertEqual(len(calls), 3)
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]["score_delta"], 4.0)
        self.assertEqual(first[0]["outcome"], "beneficial")
        self.assertEqual(second[0]["outcome_id"], first[0]["outcome_id"])

    def test_local_completed_outcome_is_immediately_available_to_learning_context(self):
        store, engine, lab, active = self.make_lab()
        original_history = v21931._durable_history
        try:
            v21931._durable_history = lambda _lab, _active: []
            result = self.sample_result()
            result["candidate"]["skill_id"] = active["skill_id"]
            outcome = v21931._outcome_from_completed_result(result)
            v21931._remember_local_outcome(outcome)
            context = v21931._build_learning_context_v21931(lab, active)
        finally:
            v21931._durable_history = original_history

        self.assertEqual(context["outcome_count"], 1)
        self.assertEqual(context["harmful"][0]["outcome_id"], outcome["outcome_id"])
        self.assertLess(
            context["direction_stats"]["instruction#2"]["direction_value"], 0
        )

    def test_version_budget_and_safety_gates_are_preserved(self):
        self.assertEqual(v21931.VERSION_SHORT, "v2.19.3.1")
        self.assertEqual(v21931.MAX_MUTATED_FIELDS, 1)
        self.assertEqual(v21931.MAX_NOVELTY_OPTIONS, 3)
        self.assertLessEqual(
            v21931.ITERATIVE_BENCHMARK_OUTPUT_BUDGET
            + v21931.ITERATIVE_CANDIDATE_OUTPUT_TOKENS,
            1000,
        )
        status = v21931.TRAINER.status()
        self.assertFalse(status["automatic_activation"])
        self.assertTrue(status["human_promotion_required"])
        self.assertIn("app_v2_19_3_1.py", v21931.EXECUTOR.safe_source_files_fn())


if __name__ == "__main__":
    unittest.main()
