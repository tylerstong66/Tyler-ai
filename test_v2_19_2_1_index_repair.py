import unittest

import app_v2_19_2_1 as v21921


class MutationIndexRepairTests(unittest.TestCase):
    def setUp(self):
        self.parent = {
            'instructions': ['I1', 'I2'],
            'success_criteria': ['C1', 'C2', 'C3'],
            'allowed_tools': ['reason'],
        }

    def test_high_instruction_index_clamps_to_last_existing_line(self):
        fixed = v21921._repair_target_index(self.parent, {
            'target_kind': 'instruction', 'target_index': 99,
            'replacement': 'I2 improved', 'rationale': 'target weak case',
        })
        self.assertEqual(fixed['requested_target_index'], 99)
        self.assertEqual(fixed['target_index'], 2)
        self.assertTrue(fixed['index_repaired'])

        instructions, criteria, diff = v21921._single_mutation_with_index_repair(
            self.parent,
            {
                'target_kind': 'instruction', 'target_index': 99,
                'replacement': 'I2 improved', 'rationale': 'target weak case',
            },
        )
        self.assertEqual(instructions, ['I1', 'I2 improved'])
        self.assertEqual(criteria, ['C1', 'C2', 'C3'])
        self.assertEqual(diff['requested_index'], 99)
        self.assertEqual(diff['resolved_index'], 2)
        self.assertTrue(diff['index_repaired'])

    def test_zero_criterion_index_clamps_to_first_existing_line(self):
        instructions, criteria, diff = v21921._single_mutation_with_index_repair(
            self.parent,
            {
                'target_kind': 'criterion', 'target_index': 0,
                'replacement': 'C1 improved', 'rationale': 'target weak case',
            },
        )
        self.assertEqual(instructions, ['I1', 'I2'])
        self.assertEqual(criteria, ['C1 improved', 'C2', 'C3'])
        self.assertEqual(diff['requested_index'], 0)
        self.assertEqual(diff['resolved_index'], 1)
        self.assertTrue(diff['index_repaired'])

    def test_valid_index_is_not_changed(self):
        instructions, criteria, diff = v21921._single_mutation_with_index_repair(
            self.parent,
            {
                'target_kind': 'criterion', 'target_index': 2,
                'replacement': 'C2 improved', 'rationale': 'target weak case',
            },
        )
        self.assertEqual(criteria, ['C1', 'C2 improved', 'C3'])
        self.assertFalse(diff['index_repaired'])
        self.assertEqual(diff['requested_index'], 2)
        self.assertEqual(diff['resolved_index'], 2)

    def test_empty_selected_section_still_fails_closed(self):
        parent = dict(self.parent)
        parent['success_criteria'] = []
        with self.assertRaisesRegex(RuntimeError, 'no mutable lines'):
            v21921._repair_target_index(parent, {
                'target_kind': 'criterion', 'target_index': 5,
                'replacement': 'x', 'rationale': '',
            })

    def test_version_and_safety_flags(self):
        self.assertEqual(v21921.VERSION_SHORT, 'v2.19.2.1')
        self.assertLessEqual(
            v21921.ITERATIVE_BENCHMARK_OUTPUT_BUDGET + v21921.ITERATIVE_CANDIDATE_OUTPUT_TOKENS,
            1000,
        )
        self.assertFalse(v21921.TRAINER.status()['automatic_activation'])
        self.assertIn('app_v2_19_2_1.py', v21921.EXECUTOR.safe_source_files_fn())


if __name__ == '__main__':
    unittest.main()
