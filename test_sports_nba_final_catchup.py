"""Retry absent recent native finals without retrospective predictions or grading."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sports_nba_final_catchup as catchup
import test_sports_nba_final_games_page_v3 as originals

NOW = datetime(2026, 10, 22, 14, 11, tzinfo=timezone.utc)


def missing(game='0022600001', start='2026-10-20T23:00:00+00:00', **kwargs):
    return dict(nba_game_id=game, nba_saved_start_utc=start, espn_saved_start_utc=start,
                quarantined=False, result_observation=None,
                reason='NO_RETAINED_NATIVE_FINAL_FOR_FROZEN_GAME', **kwargs)


class FinalCatchupTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.rows = [missing()]
        self.audit = patch.object(catchup.history, 'build', side_effect=lambda *a, **kw: {'rows': self.rows})
        self.audit.start(); self.addCleanup(self.audit.stop)

    def test_only_unique_missing_dates_two_or_three_eastern_days_back(self):
        self.rows += [missing('0022600002'), missing('0022600003', '2026-10-19T23:00:00+00:00')]
        before = deepcopy(self.rows)
        plan = catchup.build_plan(self.base, now=NOW)
        self.assertEqual([r['days_back'] for r in plan['requests']], [2, 3])
        self.assertEqual(plan['requests'][0]['nba_game_ids'], ['0022600001', '0022600002'])
        self.assertEqual(self.rows, before)
        self.assertEqual(list(self.base.iterdir()), [])
        self.assertFalse(plan['collection_requested'])

    def test_today_yesterday_future_and_expired_dates_are_not_retried(self):
        self.rows = [missing(str(i), f'2026-10-{day}T23:00:00+00:00')
                     for i, day in enumerate(('18', '21', '22', '23'))]
        plan = catchup.build_plan(self.base, now=NOW)
        self.assertEqual(plan['requests'], [])
        self.assertEqual(plan['outside_retry_window_game_ids'], ['0'])
        with patch.object(catchup.post, 'collect') as collector:
            report = catchup.collect(self.base, clock=lambda: NOW)
        collector.assert_not_called()
        self.assertEqual(catchup.publication_paths(self.base, report), [])

    def test_conflicting_completed_or_missing_provider_evidence_does_not_trigger_native_retry(self):
        for change in ({'quarantined': True}, {'result_observation': {'home_score': 100}},
                       {'reason': 'NO_RETAINED_PROVIDER_FINAL_FOR_FROZEN_GAME'},
                       {'espn_saved_start_utc': '2026-10-21T05:00:00+00:00'}):
            with self.subTest(change=change):
                row = missing(); row.update(change); self.rows = [row]
                self.assertEqual(catchup.build_plan(self.base, now=NOW)['requests'], [])

    def test_eastern_date_controls_retry_across_utc_midnight(self):
        self.rows = [missing(start='2026-10-21T01:00:00+00:00')]
        self.assertEqual(catchup.build_plan(self.base, now=NOW)['requests'][0]['requested_date'], '2026-10-20')

    def test_actual_collector_preserves_original_bytes_and_publication_replays_only_listed_capture(self):
        originals.FinalBreakStatusTests.setUpClass(); raw = originals.FinalBreakStatusTests.original
        moments = iter(NOW+timedelta(seconds=i) for i in range(3)); urls = []
        report = catchup.collect(self.base, clock=lambda: next(moments), fetch=lambda url: urls.append(url) or raw)
        self.assertEqual(urls, ['https://www.nba.com/games?date=2026-10-20'])
        paths = catchup.publication_paths(self.base, report)
        self.assertEqual(len(paths), 1)
        manifest = json.loads((self.base/paths[0]/'manifest.json').read_text())
        self.assertEqual(manifest['supported_final_game_count'], 3)
        # An unrelated partial receipt must never be swept into publication.
        partial = self.base/catchup.post.ROOT/'20261022T150000000000Z'; partial.mkdir()
        (partial/'nba_games.html.gz').write_bytes(b'incomplete')
        self.assertEqual(catchup.publication_paths(self.base, report), paths)
        (self.base/paths[0]/'manifest.json').write_text('{}')
        with self.assertRaises((ValueError, KeyError)):
            catchup.publication_paths(self.base, report)

    def test_midnight_crossing_blocks_network_until_plan_is_rebuilt(self):
        moments = iter((NOW, NOW+timedelta(days=1)))
        with patch.object(catchup.post.shared, 'fetch_page') as fetch:
            with self.assertRaisesRegex(ValueError, 'midnight'):
                catchup.collect(self.base, clock=lambda: next(moments))
        fetch.assert_not_called()
        self.assertFalse((self.base/catchup.post.ROOT).exists())

    def test_two_dates_are_collected_once_each_with_no_result_claim_from_opaque_pages(self):
        self.rows += [missing('0022600002'), missing('0022600003', '2026-10-19T23:00:00+00:00')]
        moments = iter(NOW+timedelta(seconds=i) for i in range(5)); urls = []
        report = catchup.collect(self.base, clock=lambda: next(moments),
                                 fetch=lambda url: urls.append(url) or b'<html>unavailable</html>')
        self.assertEqual(urls, ['https://www.nba.com/games?date=2026-10-20',
                                'https://www.nba.com/games?date=2026-10-19'])
        self.assertEqual(len(catchup.publication_paths(self.base, report)), 2)
        self.assertEqual(report['outcomes_enrolled'], 0)

    def test_failed_retained_source_replay_blocks_network_and_writes(self):
        with patch.object(catchup.history, 'build', side_effect=ValueError('corrupt original')):
            with patch.object(catchup.post, 'collect') as collector:
                with self.assertRaisesRegex(ValueError, 'corrupt original'):
                    catchup.collect(self.base, clock=lambda: NOW)
        collector.assert_not_called()
        self.assertEqual(list(self.base.iterdir()), [])

    def test_incomplete_or_forged_collection_cannot_produce_publication_paths(self):
        plan = catchup.build_plan(self.base, now=NOW)
        for change in ({}, {'collection_requested': True},
                       {'collection_requested': True, 'requests': [], 'actual_wagers': False},
                       {'collection_requested': True, 'requests': [], 'forecasting_enabled': True}):
            report = deepcopy(plan); report.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                catchup.publication_paths(self.base, report)

    def test_unsupported_source_is_retained_as_opaque_without_enrolling_results(self):
        moments = iter(NOW+timedelta(seconds=i) for i in range(3))
        report = catchup.collect(self.base, clock=lambda: next(moments), fetch=lambda url: b'<html>unavailable</html>')
        paths = catchup.publication_paths(self.base, report)
        manifest = json.loads((self.base/paths[0]/'manifest.json').read_text())
        self.assertEqual(manifest['supported_final_game_count'], 0)
        self.assertIsNone(manifest['parsed_final_page'])
        self.assertEqual(report['outcomes_enrolled'], 0)
        self.assertIs(report['NO_BET'], True); self.assertEqual(report['actual_wagers'], 0)


if __name__ == '__main__':
    unittest.main()
