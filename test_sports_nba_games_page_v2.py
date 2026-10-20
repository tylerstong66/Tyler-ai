"""Synthetic null-envelope cases based on the pinned v1 body, not new receipts."""
import copy
import json
import unittest

import sports_nba_games_page as v1
import sports_nba_games_page_v2 as v2
import test_sports_nba_games_page as fixtures
from test_sports_nba_games_page import NOW


class NullEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.GamesPageTests.setUpClass()
        cls.original = fixtures.GamesPageTests.payload

    def raw(self, value):
        return (b'<script id="__NEXT_DATA__" type="application/json">'
                + json.dumps(value).encode()+b'</script>')

    def payload(self):
        value = copy.deepcopy(self.original)
        value['props']['pageProps']['isDateOverrideActive'] = None
        return value

    def parse(self, value, **kwargs):
        return v2.parse(self.raw(value), requested_date='2026-10-20',
                        season='2026-27', observed_at=kwargs.get('observed_at', NOW))

    def test_version_and_native_byte_binding_without_changing_v1(self):
        value = self.payload(); raw = self.raw(value)
        result = self.parse(value)
        expected = v1.parse(fixtures.GamesPageTests.raw, requested_date='2026-10-20',
                            season='2026-27', observed_at=NOW)
        self.assertEqual(result['games'], expected['games'])
        import hashlib
        self.assertEqual(result['original_body_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['date_override_field_state'], 'EXPLICIT_NULL')
        self.assertIn('v2', result['schema'])
        for key in ('forecasting_enabled', 'feature_collection_enabled',
                    'model_training_enabled', 'promotion_allowed',
                    'date_override_active_attested', 'collector_fallback_enabled'):
            self.assertIs(result[key], False)
        with self.assertRaises(ValueError):
            v1.parse(raw, requested_date='2026-10-20', season='2026-27', observed_at=NOW)

    def test_missing_and_nonnull_flags_fail_in_v2(self):
        for flag in (True, False, 0, 1, '', 'null', [], {}):
            value = self.payload()
            value['props']['pageProps']['isDateOverrideActive'] = flag
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                self.parse(value)
        value = self.payload(); del value['props']['pageProps']['isDateOverrideActive']
        with self.assertRaises(ValueError): self.parse(value)

    def test_all_original_adversarial_cases_use_same_game_validation(self):
        # Run the original corruption cases through the v2 envelope. These are
        # synthetic mutations; they do not certify a native live source.
        case = fixtures.GamesPageTests()
        case.payload = self.payload()
        case.raw = self.raw(case.payload)
        def parse(value=None, **kwargs):
            raw = case.raw if value is None else self.raw(value)
            return v2.parse(raw, **{'requested_date': '2026-10-20',
                            'season': '2026-27', 'observed_at': NOW, **kwargs})
        case.parse = parse
        for method in ('test_route_date_locale_errors_fail',
                       'test_pagination_incomplete_counts_and_unknown_modules_fail',
                       'test_game_identity_status_and_franchise_corruption_fail',
                       'test_duplicate_games_or_franchises_fail',
                       'test_embedded_script_and_json_ambiguity_fail',
                       'test_empty_calendar_day_explicit_zero_only'):
            with self.subTest(method=method): getattr(case, method)()

    def test_late_and_naive_observations_fail(self):
        from datetime import datetime, timezone
        for observed in (NOW.replace(tzinfo=None),
                         datetime(2026, 10, 21, tzinfo=timezone.utc)):
            with self.assertRaises(ValueError):
                self.parse(self.payload(), observed_at=observed)


if __name__ == '__main__': unittest.main()
