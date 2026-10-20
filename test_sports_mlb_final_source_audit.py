"""Pending-source diagnostics preserve immutable records and never grade."""
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
import io
import json
import tempfile
import unittest

import sports_mlb_final_source_audit as audit
from sports_mlb_prop_prospective import freeze_pregame_hit_props, write_exclusive_json, _seal
from test_sports_mlb_prop_prospective import OfficialReader, AFTER


class FinalSourceAuditTests(unittest.TestCase):
    def prepare(self, root):
        reader = OfficialReader()
        record = freeze_pregame_hit_props(849810, 683734, 'away', reader=reader)
        path = Path(root)/'predictions'/'849810_683734.json'
        write_exclusive_json(path, record)
        return reader, path

    def test_real_conflict_shape_is_reported_without_settlement_or_rewrite(self):
        with tempfile.TemporaryDirectory() as root:
            reader, path = self.prepare(root); before = path.read_bytes()
            reader.now = AFTER; reader.final = True
            original = reader.load
            def changed(*args, **kwargs):
                data, receipt = original(*args, **kwargs)
                data['gameData']['teams'] = {'home': {'id': 114}, 'away': {'id': 139}}
                data['gameData']['datetime']['dateTime'] = '2026-10-18T21:08:00Z'
                return data, receipt
            reader.load = changed
            report = audit.audit(root, reader=reader)
            row = report['records'][0]
            self.assertEqual(row['conflicts'], ['home_id', 'away_id', 'scheduled_start'])
            self.assertEqual(row['status'], 'SOURCE_IDENTITY_OR_START_CONFLICT')
            self.assertEqual(report['conflicting_records'], 1)
            self.assertFalse(report['settlement_enabled'])
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse((Path(root)/'settlements').exists())

    def test_matching_final_is_only_identity_evidence_and_shared_game_is_fetched_once(self):
        with tempfile.TemporaryDirectory() as root:
            reader, path = self.prepare(root)
            core = json.loads(path.read_text()); core.pop('record_digest_sha256')
            core['hitter_id'] = 700001
            write_exclusive_json(path.with_name('849810_700001.json'), _seal(core))
            reader.now = AFTER; reader.final = True; reader.audit.clear()
            report = audit.audit(root, reader=reader)
            self.assertEqual(report['pending_records'], 2)
            self.assertEqual(report['attempted_unique_games'], 1)
            self.assertEqual(len(reader.audit), 1)
            self.assertTrue(all(r['status'] == 'IDENTITY_MATCH_ONLY_NOT_SETTLEMENT' for r in report['records']))
            self.assertEqual(report['actual_wagers'], 0)

    def test_complete_preflight_precedes_any_network(self):
        with tempfile.TemporaryDirectory() as root:
            reader, path = self.prepare(root)
            other = path.with_name('849810_700002.json')
            other.write_bytes(path.read_bytes())
            with patch.object(reader, 'load', side_effect=AssertionError('unexpected network')):
                with self.assertRaisesRegex(ValueError, 'scope'):
                    audit.audit(root, reader=reader)

    def test_future_records_and_invalid_budgets_make_no_requests(self):
        with tempfile.TemporaryDirectory() as root:
            reader, path = self.prepare(root)
            with patch.object(reader, 'load', side_effect=AssertionError('unexpected network')):
                report = audit.audit(root, reader=reader)
                self.assertEqual(report['records'][0]['status'], 'FUTURE_SAVED_START_NOT_OBSERVED')
                for bound in (True, 0, 13):
                    with self.assertRaises(ValueError):
                        audit.audit(root, reader=reader, max_games=bound)

    def test_budget_deferral_and_network_failure_are_explicit_and_redacted(self):
        with tempfile.TemporaryDirectory() as root:
            reader, path = self.prepare(root)
            core = json.loads(path.read_text()); core.pop('record_digest_sha256')
            core['game_id'] = 849811
            write_exclusive_json(path.with_name('849811_683734.json'), _seal(core))
            reader.now = AFTER
            with patch.object(reader, 'load', side_effect=audit.requests.Timeout('secret-proxy-password')) as get:
                report = audit.audit(root, reader=reader, max_games=1)
                self.assertEqual(get.call_count, 1)
            self.assertEqual(report['deferred_unique_games'], 1)
            self.assertEqual([r['status'] for r in report['records']], ['SOURCE_UNAVAILABLE', 'DEFERRED_GAME_BUDGET'])
            self.assertNotIn('secret-proxy-password', json.dumps(report))

    def test_symlinked_prediction_directory_fails_before_network(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as external:
            reader, path = self.prepare(external)
            (Path(root)/'predictions').symlink_to(path.parent, target_is_directory=True)
            with patch.object(reader, 'load', side_effect=AssertionError('unexpected network')):
                with self.assertRaises(ValueError):
                    audit.audit(root, reader=reader)

    def test_cli_requires_explicit_observation_and_refuses_existing_destination(self):
        with patch('sys.argv', ['audit']), patch.object(audit, 'audit') as run, redirect_stdout(io.StringIO()):
            audit.main(); run.assert_not_called()
        with tempfile.TemporaryDirectory() as root, patch('sys.argv', ['audit', '--observe', '--output-dir', root]):
            with patch.object(audit, 'audit') as run, self.assertRaises(FileExistsError):
                audit.main()
            run.assert_not_called()


if __name__ == '__main__': unittest.main()
