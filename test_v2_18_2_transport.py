import unittest

import app_v2_18_2 as hotfix
from skill_lab import SkillPromotionLab
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class CaptureEngine:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def complete(self, messages, tokens=0, temperature=0, json_mode=False):
        self.calls.append({
            'messages': messages,
            'tokens': int(tokens),
            'temperature': temperature,
            'json_mode': bool(json_mode),
        })
        return self.reply


class DummyJudgeLab:
    def __init__(self, reply='SCORE=92\nWEAKNESSES=none'):
        self.engine = CaptureEngine(reply)
        self._benchmark_judge_tokens = 68


class ProviderSafeTransportTests(unittest.TestCase):
    def test_tagged_judge_parser_accepts_compact_output(self):
        parsed = hotfix._parse_tagged_judge(
            'SCORE=91\nWEAKNESSES=needs exact commit check || missing rollback note'
        )
        self.assertEqual(parsed['score'], 91)
        self.assertTrue(parsed['passed'])
        self.assertEqual(len(parsed['weaknesses']), 2)

    def test_tagged_judge_parser_fails_closed_on_bad_format(self):
        parsed = hotfix._parse_tagged_judge('Looks good to me.')
        self.assertEqual(parsed['score'], 0)
        self.assertFalse(parsed['passed'])
        self.assertIn('evaluator_format_unparseable', parsed['weaknesses'])

    def test_benchmark_judge_never_uses_provider_json_mode(self):
        lab = DummyJudgeLab()
        profile = {'name': 'Test', 'success_criteria': ['Grounded']}
        case = {
            'case_id': 'one',
            'input': 'Do work',
            'expected_behavior': 'Use evidence',
            'criteria': ['grounded'],
        }
        result = hotfix._provider_safe_judge(lab, profile, case, 'Verified answer')
        self.assertEqual(result['score'], 92)
        self.assertTrue(result['passed'])
        self.assertEqual(lab.engine.calls[0]['tokens'], 68)
        self.assertFalse(lab.engine.calls[0]['json_mode'])

    def test_candidate_parser_reads_tagged_profile(self):
        parsed = hotfix._parse_candidate_text(
            'INSTRUCTIONS=Inspect code first || Run targeted tests\n'
            'CRITERIA=Grounded || Verified\n'
            'RATIONALE=Improves verification discipline.'
        )
        self.assertEqual(parsed['instructions'], ['Inspect code first', 'Run targeted tests'])
        self.assertEqual(parsed['success_criteria'], ['Grounded', 'Verified'])
        self.assertEqual(parsed['rationale'], 'Improves verification discipline.')

    def test_candidate_generation_avoids_json_mode_and_preserves_tools(self):
        store = MemoryStore()
        engine = FakeEngine()
        lab = SkillPromotionLab(
            engine,
            store.get_rows,
            store.save_row,
            now_fn=lambda: '2026-09-16T23:00:00+00:00',
        )
        active = engine.create_or_update_skill(
            'Test Skill',
            'Do safe work.',
            instructions=['Inspect first'],
            success_criteria=['Correct'],
            allowed_tools=['reason'],
        )
        candidate = hotfix._provider_safe_propose_candidate(lab, 'Test Skill')
        self.assertEqual(candidate['allowed_tools'], active['allowed_tools'])
        self.assertFalse(engine.calls[-1][1])
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)

    def test_hotfix_keeps_benchmark_budget_and_human_gate(self):
        self.assertEqual(hotfix.BENCHMARK_OUTPUT_BUDGET, 850)
        status = hotfix.SKILL_LAB.status()
        self.assertFalse(status['automatic_skill_promotion_enabled'])
        self.assertTrue(status['human_approval_required_for_promotion'])

    def test_version_and_source_inventory(self):
        self.assertEqual(hotfix.VERSION_SHORT, 'v2.18.2')
        self.assertEqual(hotfix.BENCHMARK_TRANSPORT, 'plain_tagged_v1')
        self.assertIn('app_v2_18_2.py', hotfix.EXECUTOR.safe_source_files_fn())


if __name__ == '__main__':
    unittest.main()
