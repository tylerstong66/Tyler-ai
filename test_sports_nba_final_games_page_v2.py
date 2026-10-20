"""Synthetic null-envelope finals preserve the original regulation-final policy."""
import copy
import hashlib
import json
import unittest
import sports_nba_final_games_page as v1
import sports_nba_final_games_page_v2 as v2
import test_sports_nba_final_games_page as fixtures


class NativeFinalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.FinalGamesPageTests.setUpClass()
        cls.payload = copy.deepcopy(fixtures.FinalGamesPageTests.payload)
        cls.payload['props']['pageProps']['isDateOverrideActive'] = None

    def raw(self, value):
        return b'<script id="__NEXT_DATA__" type="application/json">'+json.dumps(value).encode()+b'</script>'

    def parse(self, value=None, **kwargs):
        return v2.parse(self.raw(self.payload if value is None else value),
                        **{'requested_date': '2026-04-10', 'season': '2025-26',
                           'observed_at': fixtures.NOW, **kwargs})

    def test_source_bytes_and_disabled_claims_are_bound_to_v2(self):
        result = self.parse()
        original = v1.parse(fixtures.FinalGamesPageTests.raw,
                            requested_date='2026-04-10', season='2025-26', observed_at=fixtures.NOW)
        self.assertEqual(result['games'], original['games'])
        self.assertEqual(result['daily_game_count'], 15)
        self.assertEqual(result['original_body_sha256'], hashlib.sha256(self.raw(self.payload)).hexdigest())
        self.assertIn('v2', result['schema'])
        for key in ('official_final_results_verified', 'settlement_enabled',
                    'historical_evaluation_enabled', 'forecasting_enabled',
                    'model_training_enabled', 'promotion_allowed', 'date_override_active_attested'):
            self.assertIs(result[key], False)
        with self.assertRaises(ValueError):
            v1.parse(self.raw(self.payload), requested_date='2026-04-10',
                     season='2025-26', observed_at=fixtures.NOW)

    def test_missing_and_nonnull_ui_flags_are_not_v2(self):
        for flag in (True, False, 0, 1, 'null'):
            value = copy.deepcopy(self.payload)
            value['props']['pageProps']['isDateOverrideActive'] = flag
            with self.subTest(flag=flag), self.assertRaises(ValueError): self.parse(value)
        value = copy.deepcopy(self.payload); del value['props']['pageProps']['isDateOverrideActive']
        with self.assertRaises(ValueError): self.parse(value)

    def test_original_adversarial_final_cases_still_reject(self):
        case = fixtures.FinalGamesPageTests()
        case.payload = self.payload
        case.raw = self.raw(self.payload)
        case.parse = self.parse
        for method in ('test_nonfinal_overtime_postseason_postponed_cancelled_unknown_fail',
                       'test_game_season_franchise_and_side_identity_fail',
                       'test_noninteger_negative_and_inconsistent_period_scores_fail',
                       'test_tied_final_with_internally_consistent_totals_fails',
                       'test_time_date_missing_actual_time_and_early_observation_fail',
                       'test_page_completeness_route_and_duplicate_identities_fail'):
            with self.subTest(method=method): getattr(case, method)()


if __name__ == '__main__': unittest.main()
