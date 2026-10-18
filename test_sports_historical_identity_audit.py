"""Cross-date and cross-split provider contamination stays excluded."""
import json
import tempfile
import unittest
from pathlib import Path
from test_sports_expansion_historical_capture import CLOCK, payload
from datetime import datetime, timedelta
import sports_expansion_observer as source
from urllib.parse import urlparse, parse_qs
import sports_expansion_historical_capture as history
import sports_historical_identity_audit as audit


class HistoricalIdentityAuditTests(unittest.TestCase):
    def seed(self, root, *, duplicate_id=False, wrong_date=False):
        def fetch(url):
            obj = json.loads(payload())
            game = obj['events'][0]
            day = parse_qs(urlparse(url).query)['dates'][0]
            game['date'] = datetime.strptime(day, '%Y%m%d').strftime('%Y-%m-%dT23:00:00Z')
            if day.startswith('2025'):
                game['id'] = '401000123' if duplicate_id else '401000124'
            if wrong_date:
                game['date'] = '2026-10-21T23:00:00Z'
            return json.dumps(obj).encode()
        plan = {sport: {split: [bounds[0]] for split, bounds in splits.items()}
                for sport, splits in history.SEASONS.items()}
        history.capture(fetch, base=root, now=CLOCK, per_league=2, date_plan=plan)

    def test_clean_source_ids_remain_separate_by_sport_and_split(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(Path(td)); out = audit.audit(td, now=CLOCK)
            self.assertEqual(out['verified_source_days'], 6)
            self.assertEqual(out['unique_provider_game_ids'], 6)
            self.assertEqual(out['quarantined_game_ids'], 0)
            self.assertFalse(out['training_allowed'])
            self.assertFalse(out['historical_evaluation_enabled'])
            self.assertFalse(out['independently_verified_official_results'])
            self.assertEqual(out['actual_wagers'], 0)

    def test_same_game_id_in_train_and_validation_is_quarantined(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(Path(td), duplicate_id=True); out = audit.audit(td, now=CLOCK)
            self.assertEqual(out['quarantined_game_ids'], 3)
            self.assertTrue(all('GAME_ID_PRESENT_IN_TRAIN_AND_VALIDATION' in row['reasons']
                                for row in out['quarantined']))
            self.assertTrue(all(out['cohorts'][sport]['train']['nonconflicting_provider_game_ids'] == 0
                                for sport in history.ORDER))

    def test_out_of_split_future_event_cannot_be_historical_result(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(Path(td), wrong_date=True); out = audit.audit(td, now=CLOCK)
            self.assertEqual(out['quarantined_game_ids'], 6)
            self.assertTrue(all('EVENT_OUTSIDE_DECLARED_SPLIT' in row['reasons']
                                and 'FINAL_OBSERVED_AT_OR_BEFORE_SAVED_START' in row['reasons']
                                for row in out['quarantined']))

    def test_identical_neighbor_day_game_is_counted_once_and_score_drift_quarantined(self):
        for drift in (False, True):
            with self.subTest(drift=drift), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                plan = {}
                for sport, splits in history.SEASONS.items():
                    first = datetime.fromisoformat(splits['train'][0])
                    plan[sport] = {'train': [first.date().isoformat(),
                                             (first + timedelta(days=1)).date().isoformat()],
                                   'validation': [splits['validation'][0]]}
                def fetch(url):
                    sport = next(s for s, cfg in source.LEAGUES.items() if cfg['path'] in url)
                    first = datetime.fromisoformat(plan[sport]['train'][0])
                    obj = json.loads(payload()); game = obj['events'][0]
                    game['date'] = (first + timedelta(days=1, minutes=30)).isoformat() + 'Z'
                    day = parse_qs(urlparse(url).query)['dates'][0]
                    if drift and day != first.strftime('%Y%m%d'):
                        game['competitions'][0]['competitors'][0]['score'] = '75'
                    return json.dumps(obj).encode()
                history.capture(fetch, base=root, now=CLOCK, per_league=2, date_plan=plan)
                out = audit.audit(root, now=CLOCK)
                self.assertEqual(out['unique_provider_game_ids'], 3)
                self.assertEqual(out['repeated_same_game_observations'], 3)
                self.assertEqual(out['quarantined_game_ids'], 3 if drift else 0)
                if drift:
                    self.assertTrue(all('CONFLICTING_ARCHIVED_GAME_OBSERVATIONS' in row['reasons']
                                        for row in out['quarantined']))

    def test_source_corruption_aborts_audit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); self.seed(root)
            next((root/history.ROOT/'sources').glob('*/*/*.json.gz')).write_bytes(b'bad')
            with self.assertRaises(ValueError):
                audit.audit(root, now=CLOCK)


if __name__ == '__main__':
    unittest.main()
