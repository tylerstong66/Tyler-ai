"""Historical independent result joins cannot borrow 2026 alias assumptions."""
from pathlib import Path
import json
import tempfile
import unittest
from datetime import datetime, timezone

import sports_expansion_historical_capture as history
import sports_ncaa_historical_owned as owned
import sports_historical_fbs_crosscheck as crosscheck
from test_sports_ncaa_espn_identity import official_game, espn_game

NOW = datetime(2026, 10, 18, tzinfo=timezone.utc)
START = datetime(2024, 8, 24, 17, tzinfo=timezone.utc)


class HistoricalFbsCrosscheckTests(unittest.TestCase):
    def seed(self, root, *, home='Tulsa', espn_home='Tulsa', conflict=False,
             duplicate=False, location=True):
        game = official_game(when=int(START.timestamp()), home=home, final=True)
        raw = json.dumps({'data': {'contests': [game]}}).encode()
        owned.capture(lambda _: raw, base=root, now=NOW, per_run=1)
        plan = {sport: {split: [bounds[0]] for split, bounds in splits.items()}
                for sport, splits in history.SEASONS.items()}
        def fetch(url):
            events = []
            if 'football/college-football' in url:
                event = espn_game(start=START.isoformat(), home=espn_home, completed=True)
                teams = event['competitions'][0]['competitors']
                if conflict:
                    teams[0]['score'] = '31'
                if not location:
                    teams[0]['team'].pop('location')
                events.append(event)
                if duplicate:
                    events.append({**event, 'id': '401100002'})
            return json.dumps({'events': events, 'count': len(events)}).encode()
        history.capture(fetch, base=root, now=NOW, per_league=1, date_plan=plan)

    def test_original_archives_join_with_two_hash_linked_sources(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(Path(td)); out = crosscheck.build(td, now=NOW)
            self.assertEqual(out['two_source_final_agreements'], 1)
            row = out['corroborated_research_only'][0]
            self.assertTrue(row['postgame_source_chronology_verified'])
            self.assertEqual(len(row['ncaa_receipts'][0]['response_sha256']), 64)
            self.assertEqual(len(row['espn_receipts'][0]['receipt_sha256']), 64)
            for key in ('training_allowed', 'historical_evaluation_enabled',
                        'forecasting_enabled', 'promotion_allowed'):
                self.assertIs(out[key], False)
            self.assertTrue(out['NO_BET']); self.assertEqual(out['actual_wagers'], 0)

    def test_current_season_aliases_not_reused_for_historical_school_names(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(Path(td), home='Mississippi St.', espn_home='Mississippi State')
            out = crosscheck.build(td, now=NOW)
            self.assertEqual(out['two_source_final_agreements'], 0)
            self.assertEqual(out['pending'][0]['reason'], 'NO_UNAMBIGUOUS_NCAA_GAME_ID')

    def test_score_conflict_duplicate_mapping_and_missing_location_excluded(self):
        for kwargs, reason in (({'conflict': True}, 'CONFLICTING_FINAL_SCORES_NO_GRADE'),
                               ({'duplicate': True}, 'NON_BIJECTIVE_GAME_IDENTITY'),
                               ({'location': False}, 'ESPN_SCHOOL_LOCATION_UNAVAILABLE')):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as td:
                self.seed(Path(td), **kwargs); out = crosscheck.build(td, now=NOW)
                self.assertEqual(out['two_source_final_agreements'], 0)
                self.assertTrue(all(row['reason'] == reason for row in out['pending']))

    def test_modified_independent_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); self.seed(root)
            next((root/owned.ROOT/'train').glob('*.json.gz')).write_bytes(b'bad')
            with self.assertRaises(ValueError):
                crosscheck.build(root, now=NOW)


if __name__ == '__main__':
    unittest.main()
