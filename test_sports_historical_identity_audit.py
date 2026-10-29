"""Cross-date and cross-split provider contamination stays excluded."""
import json
import tempfile
import unittest
from unittest.mock import patch
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

    def test_relabelled_same_matchup_at_exact_start_quarantines_both_ids(self):
        for collision in (True, False):
            with self.subTest(collision=collision), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                plan = {sport: {split: [bounds[0]] for split, bounds in splits.items()}
                        for sport, splits in history.SEASONS.items()}
                nba_first = datetime.fromisoformat(plan['NBA']['train'][0])
                nba_second = (nba_first + timedelta(days=1)).date().isoformat()
                plan['NBA']['train'].append(nba_second)
                def fetch(url):
                    sport = next(s for s, cfg in source.LEAGUES.items()
                                 if cfg['path'] in url)
                    day = datetime.strptime(parse_qs(urlparse(url).query)['dates'][0],
                                            '%Y%m%d').date().isoformat()
                    obj = json.loads(payload())
                    game = obj['events'][0]
                    if sport == 'NBA' and day in plan['NBA']['train']:
                        game['id'] = ('401000125' if day == nba_second else '401000123')
                        if collision or day != nba_second:
                            game['date'] = nba_second + 'T00:30:00Z'
                        else:
                            game['date'] = nba_second + 'T23:00:00Z'
                    else:
                        game['id'] = '401000124' if day.startswith('2025') else '401000123'
                        game['date'] = day + 'T23:00:00Z'
                    return json.dumps(obj).encode()
                history.capture(fetch, base=root, now=CLOCK, per_league=3,
                                date_plan=plan)
                out = audit.audit(root, now=CLOCK)
                self.assertEqual(out['quarantined_game_ids'], 2 if collision else 0)
                self.assertEqual(out['quarantined_relabelled_game_ids'],
                                 2 if collision else 0)
                if collision:
                    self.assertEqual(
                        {r['game_id'] for r in out['quarantined']},
                        {'401000123', '401000125'})
                    self.assertTrue(all(
                        'SAME_EVENT_FINGERPRINT_MULTIPLE_GAME_IDS' in r['reasons']
                        for r in out['quarantined']))
                    self.assertEqual(
                        out['cohorts']['NBA']['train']['nonconflicting_provider_game_ids'],
                        0)
                else:
                    self.assertEqual(
                        out['cohorts']['NBA']['train']['nonconflicting_provider_game_ids'],
                        2)
                self.assertFalse(out['training_allowed'])
                self.assertTrue(out['NO_BET'])

    def test_simultaneous_team_in_two_distinct_games_quarantines_both_ids(self):
        # Same team as home or away is impossible at one exact kickoff.
        # Independent same-time matchups and a later legitimate game stay clean.
        for scenario in ('same_home', 'same_away', 'later_start', 'disjoint'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                plan = {sport: {split: [bounds[0]] for split, bounds in splits.items()}
                        for sport, splits in history.SEASONS.items()}
                def fetch(url):
                    sport = next(s for s, cfg in source.LEAGUES.items()
                                 if cfg['path'] in url)
                    day = datetime.strptime(
                        parse_qs(urlparse(url).query)['dates'][0],
                        '%Y%m%d').date().isoformat()
                    obj = json.loads(payload())
                    game = obj['events'][0]
                    game['id'] = '401000124' if day.startswith('2025') else '401000123'
                    game['date'] = day + 'T23:00:00Z'
                    if sport == 'NBA' and day == plan['NBA']['train'][0]:
                        other = json.loads(json.dumps(game))
                        other['id'] = '401000125'
                        opponents = other['competitions'][0]['competitors']
                        if scenario == 'same_away':
                            opponents[0]['team']['id'] = '300'
                            opponents[1]['team']['id'] = '100'
                        else:
                            opponents[0]['team']['id'] = (
                                '400' if scenario == 'disjoint' else '100')
                            opponents[1]['team']['id'] = '300'
                        if scenario == 'later_start':
                            other['date'] = (datetime.strptime(day, '%Y-%m-%d') +
                                             timedelta(days=1, hours=5)).isoformat() + 'Z'
                        obj['events'].append(other)
                        obj['count'] = 2
                    return json.dumps(obj).encode()
                history.capture(fetch, base=root, now=CLOCK, per_league=2,
                                date_plan=plan)
                out = audit.audit(root, now=CLOCK)
                collision = scenario in ('same_home', 'same_away')
                self.assertEqual(out['quarantined_simultaneous_team_game_ids'],
                                 2 if collision else 0)
                self.assertEqual(out['quarantined_game_ids'],
                                 2 if collision else 0)
                self.assertEqual(
                    out['cohorts']['NBA']['train']['nonconflicting_provider_game_ids'],
                    0 if collision else 2)
                if collision:
                    self.assertEqual({row['game_id'] for row in out['quarantined']},
                                     {'401000123', '401000125'})
                    self.assertTrue(all(
                        'TEAM_SCHEDULED_IN_SIMULTANEOUS_GAME_IDS' in row['reasons']
                        for row in out['quarantined']))
                self.assertFalse(out['training_allowed'])
                self.assertFalse(out['forecasting_enabled'])
                self.assertTrue(out['NO_BET'])

    def test_near_start_provider_id_relabelling_quarantines_both_games(self):
        # A shifted start defeats the exact-time identity guard. Neither a
        # changed opponent nor a UTC date boundary can launder the new ID.
        # Exactly four hours is the conservative noncollision boundary.
        for scenario in ('same_matchup', 'changed_opponent',
                         'four_hour_boundary', 'disjoint'):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                plan = {sport: {split: [bounds[0]] for split, bounds in splits.items()}
                        for sport, splits in history.SEASONS.items()}
                def fetch(url):
                    sport = next(s for s, cfg in source.LEAGUES.items()
                                 if cfg['path'] in url)
                    day = datetime.strptime(
                        parse_qs(urlparse(url).query)['dates'][0],
                        '%Y%m%d').date().isoformat()
                    obj = json.loads(payload())
                    first = obj['events'][0]
                    first['id'] = '401000124' if day.startswith('2025') else '401000123'
                    first['date'] = day + 'T23:00:00Z'
                    if sport == 'NBA' and day == plan['NBA']['train'][0]:
                        second = json.loads(json.dumps(first))
                        second['id'] = '401000125'
                        hours = 4 if scenario == 'four_hour_boundary' else 2
                        second['date'] = (
                            datetime.fromisoformat(day + 'T23:00:00+00:00')
                            + timedelta(hours=hours)).isoformat()
                        if scenario in ('changed_opponent', 'disjoint'):
                            sides = second['competitions'][0]['competitors']
                            sides[1]['team']['id'] = '300'
                            if scenario == 'disjoint':
                                sides[0]['team']['id'] = '400'
                        obj['events'].append(second)
                        obj['count'] = 2
                    return json.dumps(obj).encode()
                history.capture(fetch, base=root, now=CLOCK, per_league=2,
                                date_plan=plan)
                out = audit.audit(root, now=CLOCK)
                collision = scenario in ('same_matchup', 'changed_opponent')
                self.assertEqual(out['quarantined_simultaneous_team_game_ids'], 0)
                self.assertEqual(out['quarantined_relabelled_game_ids'], 0)
                self.assertEqual(out['quarantined_near_start_team_game_ids'],
                                 2 if collision else 0)
                self.assertEqual(out['quarantined_game_ids'], 2 if collision else 0)
                if collision:
                    self.assertEqual({row['game_id'] for row in out['quarantined']},
                                     {'401000123', '401000125'})
                    self.assertTrue(all(
                        'TEAM_STARTS_LESS_THAN_FOUR_HOURS_APART_ACROSS_GAME_IDS'
                        in row['reasons'] for row in out['quarantined']))
                self.assertEqual(
                    out['cohorts']['NBA']['train']['nonconflicting_provider_game_ids'],
                    0 if collision else 2)
                self.assertFalse(out['training_allowed'])
                self.assertFalse(out['forecasting_enabled'])
                self.assertTrue(out['NO_BET'])

    def test_direct_identity_audit_rejects_replaced_receipt_after_verification(self):
        for tamper in ('duplicate_key', 'forged_score', 'future_observation'):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as td:
                root=Path(td); self.seed(root)
                day=history.SEASONS['NBA']['train'][0]
                receipt=root/history.ROOT/'sources'/'NBA'/'train'/(day+'.receipt.json')
                saved=json.loads(receipt.read_bytes())
                if tamper=='duplicate_key':
                    raw=receipt.read_bytes().rstrip()
                    receipt.write_bytes(raw[:-1]+b',"NO_BET":true}')
                elif tamper=='forged_score':
                    saved['parsed_provider_scoreboard']['games'][0]['home_score']=999
                    receipt.write_text(json.dumps(saved))
                else:
                    saved['recorded_at_utc']='2030-01-01T00:00:00Z'
                    receipt.write_text(json.dumps(saved))
                # The first archive check has already passed; simulate replacement
                # before the audit's own read without weakening other source checks.
                original_verify=history.verify_existing
                def prior_check(base, league, split, selected_day, *, as_of=None):
                    if (league, split, selected_day)==('NBA','train',day):
                        return True
                    return original_verify(base,league,split,selected_day,as_of=as_of)
                with patch.object(history,'verify_existing',side_effect=prior_check):
                    with self.assertRaises(ValueError):
                        audit.audit(root,now=CLOCK)

    def test_source_corruption_aborts_audit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); self.seed(root)
            next((root/history.ROOT/'sources').glob('*/*/*.json.gz')).write_bytes(b'bad')
            with self.assertRaises(ValueError):
                audit.audit(root, now=CLOCK)


if __name__ == '__main__':
    unittest.main()
