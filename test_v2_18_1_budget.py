import json
import unittest

import app_v2_18_1 as hotfix


class CaptureEngine:
    def __init__(self):
        self.calls = []

    def complete(self, messages, tokens=0, temperature=0, json_mode=False):
        self.calls.append({
            'tokens': int(tokens),
            'json_mode': bool(json_mode),
            'messages': messages,
        })
        if json_mode:
            return json.dumps({'score': 90, 'passed': True, 'weaknesses': []})
        return 'Concise grounded benchmark answer.'


class DummyLab:
    def __init__(self, run_tokens, judge_tokens):
        self.engine = CaptureEngine()
        self._benchmark_run_tokens = run_tokens
        self._benchmark_judge_tokens = judge_tokens

    def _context(self, profile):
        return 'ACTIVE SKILL: Test\nPROFILE VERSION: 1'


class SkillLabBudgetTests(unittest.TestCase):
    def test_five_case_suite_fits_observed_otpm_ceiling(self):
        run_tokens, judge_tokens = hotfix._allocate_benchmark_budget(5)
        self.assertEqual((run_tokens, judge_tokens), (102, 68))
        self.assertLessEqual((run_tokens + judge_tokens) * 5, hotfix.BENCHMARK_OUTPUT_BUDGET)
        self.assertLess(hotfix.BENCHMARK_OUTPUT_BUDGET, 1000)

    def test_supported_suite_sizes_never_exceed_budget(self):
        for case_count in range(1, 21):
            run_tokens, judge_tokens = hotfix._allocate_benchmark_budget(case_count)
            self.assertGreater(run_tokens, 0)
            self.assertGreater(judge_tokens, 0)
            self.assertLessEqual(
                (run_tokens + judge_tokens) * case_count,
                hotfix.BENCHMARK_OUTPUT_BUDGET,
                msg=f'case_count={case_count}',
            )

    def test_run_and_judge_use_allocated_caps(self):
        run_tokens, judge_tokens = hotfix._allocate_benchmark_budget(5)
        lab = DummyLab(run_tokens, judge_tokens)
        profile = {'name': 'Test', 'success_criteria': ['Correct']}
        case = {
            'case_id': 'case-one',
            'input': 'Test request',
            'expected_behavior': 'Grounded answer',
            'criteria': ['grounded'],
        }
        answer = hotfix._budgeted_run(lab, profile, case['input'])
        judged = hotfix._budgeted_judge(lab, profile, case, answer)
        self.assertEqual(lab.engine.calls[0]['tokens'], run_tokens)
        self.assertEqual(lab.engine.calls[1]['tokens'], judge_tokens)
        self.assertFalse(lab.engine.calls[0]['json_mode'])
        self.assertTrue(lab.engine.calls[1]['json_mode'])
        self.assertEqual(judged['score'], 90)
        self.assertTrue(judged['passed'])

    def test_hotfix_keeps_human_skill_promotion_gate(self):
        status = hotfix.SKILL_LAB.status()
        self.assertFalse(status['automatic_skill_promotion_enabled'])
        self.assertTrue(status['human_approval_required_for_promotion'])

    def test_version_and_source_inventory(self):
        self.assertEqual(hotfix.VERSION_SHORT, 'v2.18.1')
        self.assertIn('app_v2_18_1.py', hotfix.EXECUTOR.safe_source_files_fn())


if __name__ == '__main__':
    unittest.main()
