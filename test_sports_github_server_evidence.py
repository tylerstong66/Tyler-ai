from copy import deepcopy
from datetime import datetime, timezone
import base64
import hashlib
import json
import unittest
from unittest.mock import MagicMock, patch

import sports_github_server_evidence as server

NOW = datetime(2026, 10, 19, 18, tzinfo=timezone.utc)
PATH = 'benchmarks/example/records/123.json'
SHA = 'a'*40


class ServerEvidenceTests(unittest.TestCase):
    def run_data(self):
        return {'id': 100, 'head_sha': SHA, 'repository': {'full_name': server.REPOSITORY},
                'head_repository': {'full_name': server.REPOSITORY}, 'path': '.github/workflows/check.yml',
                'event': 'push', 'created_at': '2026-10-19T13:00:00Z'}

    def observe(self, data):
        return server.run_observation(100, now=NOW, workflow='.github/workflows/check.yml',
                                      events=('push',), fetch=lambda _: deepcopy(data))

    def response(self, *, code=200, chunks=None):
        response = MagicMock(); response.status_code = code
        response.iter_content.return_value = chunks if chunks is not None else [b'{"id":100}']
        response.__enter__.return_value = response
        return response

    def test_valid_server_metadata_preserves_original_timestamp_string(self):
        result = self.observe(self.run_data())
        self.assertEqual(result['server_created_at_utc'], '2026-10-19T13:00:00Z')
        self.assertEqual(result['head_sha'], SHA)

    def test_run_metadata_wrong_identity_or_bool_id_fails(self):
        for key, value in [('id', True), ('repository', {'full_name': 'other/repo'}),
                ('head_repository', {'full_name': 'fork/repo'}), ('path', 'other'),
                ('event', 'schedule'), ('head_sha', 'main')]:
            with self.subTest(key=key):
                data = self.run_data(); data[key] = value
                with self.assertRaises(ValueError): self.observe(data)

    def test_naive_future_and_missing_server_time_fail(self):
        for timestamp in ('2026-10-19T13:00:00', '2026-10-20T13:00:00Z', None):
            data = self.run_data(); data['created_at'] = timestamp
            with self.assertRaises(ValueError): self.observe(data)

    def test_exact_blob_uses_git_object_header_and_decoded_original_bytes(self):
        raw = b'original JSON bytes\n'; expected = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        item = {'type': 'file', 'path': PATH, 'sha': expected, 'size': len(raw),
                'encoding': 'base64', 'content': base64.b64encode(raw).decode()+'\n'}
        urls = []
        def fetch(url): urls.append(url); return item
        self.assertEqual(server.verify_blob(PATH, raw, SHA, fetch=fetch), expected)
        self.assertEqual(urls, [server.API+'/contents/'+PATH+'?ref='+SHA])

    def test_unbounded_bytes_traversal_query_paths_and_mutable_refs_fail_before_fetch(self):
        for path in ('../other.json', 'benchmarks/x/../other.json', '/benchmarks/x/1.json',
                     'benchmarks/x/1.json?ref=main', 'benchmarks/x/1.txt'):
            with patch.object(server.requests, 'get') as get:
                with self.assertRaises(ValueError): server.fetch_json(server.API+'/contents/'+path+'?ref='+SHA)
                get.assert_not_called()
        for raw, sha in ((b'x'*1_000_001, SHA), ('not bytes', SHA), (b'x', 'main')):
            with self.assertRaises(ValueError): server.verify_blob(PATH, raw, sha, fetch=lambda _: self.fail('unexpected fetch'))

    def test_fixed_origin_routes_reject_foreign_repositories_and_other_endpoints(self):
        for url in ('https://evil.example/test', server.API+'/../other/actions/runs/1',
                    server.API+'/issues/1', server.API+'/actions/runs/0',
                    server.API+'/contents/'+PATH+'?ref=main'):
            with patch.object(server.requests, 'get') as get:
                with self.assertRaises(ValueError): server.fetch_json(url)
                get.assert_not_called()

    def test_transport_has_timeouts_bounded_streaming_and_no_redirects(self):
        response = self.response()
        with patch.object(server.requests, 'get', return_value=response) as get:
            self.assertEqual(server.fetch_json(server.API+'/actions/runs/100'), {'id': 100})
            self.assertFalse(get.call_args.kwargs['allow_redirects'])
            self.assertTrue(get.call_args.kwargs['stream'])
            self.assertEqual(get.call_args.kwargs['timeout'], (10, 30))
            response.iter_content.assert_called_once_with(65536)

    def test_redirect_and_oversized_responses_never_become_evidence(self):
        for response in (self.response(code=302), self.response(chunks=[b'a'*700000, b'b'*400000])):
            with patch.object(server.requests, 'get', return_value=response):
                with self.assertRaises(ValueError): server.fetch_json(server.API+'/actions/runs/100')

    def test_non_object_json_and_malformed_response_fail(self):
        for raw in (b'[]', b'not-json'):
            with patch.object(server.requests, 'get', return_value=self.response(chunks=[raw])):
                with self.assertRaises(ValueError): server.fetch_json(server.API+'/actions/runs/100')

    def test_optional_token_is_in_header_only(self):
        with patch.dict(server.os.environ, {'GITHUB_TOKEN': 'unit-test-token'}), \
             patch.object(server.requests, 'get', return_value=self.response()) as get:
            server.fetch_json(server.API+'/actions/runs/100')
            self.assertEqual(get.call_args.kwargs['headers']['Authorization'], 'Bearer unit-test-token')
            self.assertNotIn('unit-test-token', get.call_args.args[0])


if __name__ == '__main__': unittest.main()
