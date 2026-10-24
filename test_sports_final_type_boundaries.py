"""Malformed source types must never become corroborated final observations."""
import json
import unittest

import sports_college_dual_source_finals as college
import sports_expansion_observer as observer
import sports_nba_final_receipts as nba
import sports_nba_official_schedule_audit as schedule
from test_sports_college_dual_source_finals import rows
from test_sports_expansion_observer import event, payload
from test_sports_nba_official_schedule_audit import official_games


class FinalTypeBoundaryTests(unittest.TestCase):
    def test_noninteger_season_stages_are_excluded_in_each_source_cohort(self):
        for league in observer.LEAGUES:
            for stage in (2.0, 3.0, True, False, '2', None):
                with self.subTest(league=league, stage=stage):
                    out = observer.parse_scoreboard(payload(event(123, league, stage=stage)), league)
                    self.assertEqual(out['eligible_observed'], 0)
                    self.assertEqual(len(out['excluded']), 1)

    def test_college_final_flags_require_exact_true(self):
        for league in ('NCAAF_FBS', 'NCAAM_D1'):
            for source, field in ((0, 'provider_reported_final'), (1, 'provider_completed')):
                for value in (1, 'true', [True]):
                    with self.subTest(league=league, field=field, value=value):
                        n, e = rows(); n['league'] = e['league'] = league
                        (n, e)[source][field] = value
                        out = college.classify([n], [e])
                        self.assertEqual(out['two_source_final_agreements'], 0)
                        self.assertEqual(out['pending'][0]['reason'], 'BOTH_SOURCES_NOT_FINAL')

    def test_college_provider_scores_require_exact_integers(self):
        for league in ('NCAAF_FBS', 'NCAAM_D1'):
            for field, value in (('home_score', 28.0), ('away_score', 21.0),
                                 ('home_score', True), ('away_score', False)):
                with self.subTest(league=league, field=field, value=value):
                    n, e = rows(); n['league'] = e['league'] = league
                    if type(value) is bool:
                        n['ncaa_' + field] = int(value)
                    e[field] = value
                    with self.assertRaisesRegex(ValueError, 'final'):
                        college.classify([n], [e])

    def test_nba_classifier_rejects_equal_float_status_and_stage(self):
        official = schedule.official_games(official_games())[:1]
        official[0].update(nba_status=3, nba_home_score=106, nba_away_score=104)
        provider = {'401234567': {'espn_game_id': '401234567',
            'scheduled_start_utc': official[0]['tipoff_utc'],
            'home_tricode': 'NYK', 'away_tricode': 'BOS',
            'home_team_id': '18', 'away_team_id': '2',
            'season_stage': 2, 'provider_completed': True, 'home_score': 106, 'away_score': 104}}
        for target, field, value, reason in (
                ('nba', 'nba_status', 3.0, 'BOTH_SOURCES_NOT_FINAL'),
                ('espn', 'season_stage', 2.0, 'NBA_ESPN_SEASON_STAGE_MISMATCH')):
            with self.subTest(field=field):
                n = json.loads(json.dumps(official)); e = json.loads(json.dumps(provider))
                (n[0] if target == 'nba' else e['401234567'])[field] = value
                out = nba.classify(n, e, nba_observed_at='2026-10-21T01:00:00Z',
                                   espn_observed_at='2026-10-21T01:00:00Z')
                self.assertEqual(out['two_source_final_agreements'], 0)
                self.assertEqual(out['pending'][0]['reason'], reason)
                self.assertFalse(out['model_training_enabled'])
                self.assertFalse(out['forecasting_enabled'])
                self.assertFalse(out['promotion_allowed'])
                self.assertIs(out['NO_BET'], True)
                self.assertEqual(out['actual_wagers'], 0)
