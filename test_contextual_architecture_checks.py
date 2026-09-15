import unittest

import app_v2_9_5 as app295


SKILL = {
    'skill_id': 'tyler-ai-developer',
    'name': 'Tyler AI Developer',
}


class ContextualArchitectureCheckTests(unittest.TestCase):
    def test_render_deployment_request_does_not_trigger_email_checks(self):
        request = (
            'I deployed a new Tyler AI update to GitHub, but the live Render site '
            'still shows the old version. Diagnose it without risking the stable build.'
        )
        output = (
            'Check the Render branch, start command, build logs, environment variables, '
            'and smoke tests. Tyler AI also uses Supabase, Groq, Tavily, and n8n.'
        )
        checks = app295._contextual_architecture_checks(SKILL, request, output)
        self.assertEqual(checks, {})
        self.assertFalse(app295._email_check_relevant(request))

    def test_email_unauthorized_request_triggers_email_checks(self):
        request = (
            'Email sending sometimes fails with an unauthorized error. Fix the Tyler AI path.'
        )
        output = (
            'Inspect send_email_via_n8n(), compare N8N_AUTH_HEADER and N8N_WEBHOOK_KEY '
            'with the n8n webhook, and verify the n8n execution before retrying.'
        )
        checks = app295._contextual_architecture_checks(SKILL, request, output)
        self.assertTrue(app295._email_check_relevant(request))
        self.assertTrue(checks['mentions_actual_email_path'])
        self.assertTrue(checks['mentions_auth_configuration'])
        self.assertTrue(checks['avoids_invented_supabase_email_path'])
        self.assertTrue(checks['avoids_unsafe_automatic_retry'])

    def test_n8n_auth_request_triggers_email_auth_checks(self):
        request = 'The n8n webhook returns unauthorized. Check the auth header and key.'
        self.assertTrue(app295._email_check_relevant(request))

    def test_generic_n8n_mention_does_not_trigger_email_checks(self):
        request = 'Explain how n8n fits into the Tyler AI architecture.'
        self.assertFalse(app295._email_check_relevant(request))

    def test_non_developer_skill_never_gets_tyler_architecture_checks(self):
        skill = {'skill_id': 'job-search', 'name': 'Job Search'}
        checks = app295._contextual_architecture_checks(
            skill,
            'Email sending fails with unauthorized.',
            'Check n8n.',
        )
        self.assertEqual(checks, {})


if __name__ == '__main__':
    unittest.main()
