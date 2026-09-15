import unittest
from unittest.mock import patch

import app_v2_9_7 as app297


DEVELOPER_SKILL = {
    'skill_id': 'tyler-ai-developer',
    'name': 'Tyler AI Developer',
    'purpose': 'Develop Tyler AI safely.',
    'version': 1,
}

OTHER_SKILL = {
    'skill_id': 'job-search',
    'name': 'Job Search',
    'purpose': 'Find jobs.',
    'version': 1,
}


class CodeGroundedDeveloperTests(unittest.TestCase):
    def test_grounding_reads_real_deployed_source(self):
        snapshot = app297._developer_grounding(
            'Review the current architecture and recommend the next upgrade.',
            max_chars=30000,
        )
        self.assertIn('VERIFIED LOCAL SOURCE SNAPSHOT', snapshot)
        self.assertIn('app.py', snapshot)
        self.assertIn('skill_engine.py', snapshot)
        self.assertIn('Runtime requirements:', snapshot)
        self.assertIn('send_email_via_n8n', snapshot)
        self.assertIn('task', snapshot.lower())

    def test_developer_prompt_uses_verified_source_and_blocks_guessing(self):
        captured = {}

        def complete(messages, tokens=700, temperature=0.2, json_mode=False):
            captured['messages'] = messages
            captured['tokens'] = tokens
            captured['temperature'] = temperature
            return 'grounded answer'

        with patch.object(app297._ENGINE, 'get_skill', return_value=DEVELOPER_SKILL), \
             patch.object(app297._ENGINE, 'build_context', return_value='ACTIVE SKILL: Tyler AI Developer'), \
             patch.object(app297, '_developer_grounding', return_value='VERIFIED LOCAL SOURCE SNAPSHOT\napp.py functions: send_email_via_n8n, save_task_state'), \
             patch.object(app297._ENGINE, 'complete', side_effect=complete):
            result = app297._run_code_grounded_skill(
                'Tyler AI Developer',
                'Review the architecture.',
            )

        self.assertEqual(result, 'grounded answer')
        system = captured['messages'][0]['content']
        self.assertIn('VERIFIED LOCAL SOURCE SNAPSHOT', system)
        self.assertIn('Do not invent tables', system)
        self.assertIn('Do not propose a feature as new if', system)
        self.assertIn('Do not open with a disclaimer', system)
        self.assertEqual(captured['tokens'], 2200)
        self.assertEqual(captured['temperature'], 0.1)

    def test_non_developer_skill_uses_existing_runner(self):
        with patch.object(app297._ENGINE, 'get_skill', return_value=OTHER_SKILL), \
             patch.object(app297, '_ORIGINAL_RUN_SKILL', return_value='original runner') as original:
            result = app297._run_code_grounded_skill('Job Search', 'Find a job')
        self.assertEqual(result, 'original runner')
        original.assert_called_once_with('Job Search', 'Find a job')

    def test_source_snapshot_does_not_read_environment_secret_values(self):
        with patch.dict('os.environ', {'GROQ_API_KEY': 'super-secret-value'}, clear=False):
            snapshot = app297._developer_grounding('Review Groq configuration.', max_chars=30000)
        self.assertNotIn('super-secret-value', snapshot)


if __name__ == '__main__':
    unittest.main()
