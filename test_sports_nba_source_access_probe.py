from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
import gzip
import io
import json
import os
import tempfile
import unittest

import sports_nba_source_access_probe as probe

NOW = datetime(2026, 10, 20, 1, tzinfo=timezone.utc)


def response(code, chunks=None):
    value = MagicMock(); value.status_code = code
    value.__enter__.return_value = value
    value.iter_content.return_value = chunks if chunks is not None else [b'{"example":"unvalidated"}']
    return value


class NbaAccessProbeTests(unittest.TestCase):
    def test_fixed_endpoints_eastern_date_timeouts_and_no_auth_or_redirects(self):
        calls = []
        def get(url, **kwargs): calls.append((url, kwargs)); return response(403)
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {'GITHUB_TOKEN': 'never-forward-this'}):
            report = probe.run(Path(td)/'probe', now=NOW, get=get)
        self.assertEqual(len(calls), 3)
        self.assertTrue(calls[-1][0].endswith('?date=2026-10-19'))
        for url, options in calls:
            self.assertIn(url.split('/')[2], ('cdn.nba.com', 'www.nba.com'))
            self.assertIs(options['allow_redirects'], False)
            self.assertIs(options['stream'], True)
            self.assertEqual(options['timeout'], (10, 20))
            self.assertNotIn('Authorization', options['headers'])
        self.assertTrue(all(not r['payload_archived'] for r in report['requests']))
        self.assertFalse(report['source_payload_validated'])

    def test_forbidden_and_redirected_responses_are_not_archived_or_followed(self):
        replies = iter([response(403), response(302), response(200, [b'{"games":[]}'])])
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)/'probe'; report = probe.run(output, now=NOW, get=lambda *a, **k: next(replies))
            self.assertEqual([r['http_status'] for r in report['requests']], [403, 302, 200])
            files = list(output.glob('*.response.gz')); self.assertEqual(len(files), 1)
            self.assertEqual(gzip.decompress(files[0].read_bytes()), b'{"games":[]}')
            self.assertFalse(report['independent_nba_schedule_verified'])

    def test_html_success_remains_unvalidated_opaque_diagnostic_bytes(self):
        raw = b'<html>unverified response</html>'
        with tempfile.TemporaryDirectory() as td:
            report = probe.run(Path(td)/'probe', now=NOW, get=lambda *a, **k: response(200, [raw]))
            self.assertTrue(all(r['payload_archived'] for r in report['requests']))
            self.assertTrue(all(r['json_top_level_type'] == 'NON_JSON' for r in report['requests']))
            self.assertTrue(all(not r['source_payload_validated'] for r in report['requests']))

    def test_oversized_payload_has_no_complete_archive_or_source_claim(self):
        with tempfile.TemporaryDirectory() as td, patch.object(probe, 'MAX_BYTES', 10):
            output = Path(td)/'probe'
            report = probe.run(output, now=NOW, get=lambda *a, **k: response(200, [b'a'*11]))
            self.assertTrue(all(r['error_type'] == 'ValueError' for r in report['requests']))
            self.assertTrue(all(not r['payload_complete'] for r in report['requests']))
            self.assertFalse(list(output.glob('*.response.gz')))

    def test_network_error_messages_cannot_expose_environment_or_proxy_secrets(self):
        def get(*args, **kwargs): raise probe.requests.Timeout('proxy-password-must-not-appear')
        with tempfile.TemporaryDirectory() as td:
            report = probe.run(Path(td)/'probe', now=NOW, get=get)
            self.assertTrue(all(r['error_type'] == 'Timeout' for r in report['requests']))
            self.assertNotIn('proxy-password', json.dumps(report))

    def test_existing_output_or_naive_clock_fails_before_network(self):
        with tempfile.TemporaryDirectory() as td:
            for clock in (NOW, NOW.replace(tzinfo=None)):
                with self.subTest(clock=clock), self.assertRaises((ValueError, FileExistsError)):
                    probe.run(Path(td), now=clock, get=lambda *a, **k: self.fail('unexpected network'))

    def test_cli_without_explicit_probe_makes_no_network_or_files(self):
        with patch('sys.argv', ['probe']), patch.object(probe.requests, 'get') as get, redirect_stdout(io.StringIO()) as output:
            probe.main()
            get.assert_not_called(); self.assertFalse(json.loads(output.getvalue())['probe_requested'])


if __name__ == '__main__': unittest.main()
