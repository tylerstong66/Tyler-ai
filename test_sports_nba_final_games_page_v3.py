"""Observed native Final break-status bytes and isolated synthetic adversarial cases."""
import copy
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import sports_nba_final_games_page_v2 as v2
import sports_nba_final_games_page_v3 as v3
import test_sports_nba_final_games_page as adversarial

SOURCE = Path(__file__).parent
CAPTURE = '20261021T100537057931Z'
NOW = datetime(2026, 10, 21, 11, tzinfo=timezone.utc)


class FinalBreakStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = SOURCE / v3.receipts.ROOT / CAPTURE
        cls.original_manifest = (root / 'manifest.json').read_bytes()
        cls.manifest = json.loads(cls.original_manifest)
        cls.original = gzip.decompress((root / 'nba_games.html.gz').read_bytes())
        cls.payload = json.loads(re.search(rb'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', cls.original, re.S)[1])

    def parse(self, value=None, **kwargs):
        raw = self.original if value is None else (b'<script id="__NEXT_DATA__" type="application/json">'
              + json.dumps(value).encode() + b'</script>')
        return v3.parse(raw, **{'requested_date': '2026-10-20', 'season': '2026-27',
                               'observed_at': NOW, **kwargs})

    def test_actual_original_receipt_replays_without_rewriting_or_grading(self):
        report = v3.inspect(SOURCE, CAPTURE, now=NOW)
        self.assertEqual(report['daily_game_count'], 3)
        self.assertEqual([g['nba_game_id'] for g in report['games']],
                         ['0022600001', '0022600002', '0022600003'])
        self.assertEqual(report['original_body_sha256'], '2be5aae7d00b49c52432de7e79bdf03e0facd646fbffba9aaf25f522be718bbf')
        self.assertEqual(report['original_receipt_manifest_sha256'], hashlib.sha256(self.original_manifest).hexdigest())
        self.assertEqual(report['original_receipt_page_status'], 'UNSUPPORTED_OR_NOT_COMPLETE_FINAL_PAGE')
        self.assertEqual(report['outcomes_enrolled'], 0)
        self.assertTrue(report['NO_BET']); self.assertEqual(report['actual_wagers'], 0)
        for key in ('receipt_rewritten', 'prediction_accuracy_computed',
                    'official_final_results_verified', 'independent_final_agreement_verified',
                    'forecasting_enabled', 'settlement_enabled', 'model_training_enabled', 'promotion_allowed'):
            self.assertIs(report[key], False)
        with self.assertRaisesRegex(ValueError, 'regulation-final status'):
            v2.parse(self.original, requested_date='2026-10-20', season='2026-27', observed_at=NOW)

    def test_only_explicit_final_break_status_and_null_envelope_are_supported(self):
        for flag in ('', 'HALFTIME', 'Final/OT', None, True):
            value = copy.deepcopy(self.payload)
            value['props']['pageProps']['gameCardFeed']['modules'][0]['cards'][0]['cardData']['gameBreakStatus'] = flag
            with self.subTest(flag=flag), self.assertRaises(ValueError): self.parse(value)
        for flag in (True, False, 1, 'null'):
            value = copy.deepcopy(self.payload); value['props']['pageProps']['isDateOverrideActive'] = flag
            with self.subTest(flag=flag), self.assertRaises(ValueError): self.parse(value)

    def test_existing_adversarial_final_contract_still_rejects(self):
        # Apply the old mutations to synthetic reference cards with the new
        # flag; no mutation is retained as an original source observation.
        adversarial.FinalGamesPageTests.setUpClass()
        payload = copy.deepcopy(adversarial.FinalGamesPageTests.payload)
        payload['props']['pageProps']['isDateOverrideActive'] = None
        for module in payload['props']['pageProps']['gameCardFeed']['modules']:
            for card in module['cards']: card['cardData']['gameBreakStatus'] = 'Final'
        case = adversarial.FinalGamesPageTests(); case.payload = payload
        def parse(value=None, **kwargs):
            raw = b'<script id="__NEXT_DATA__" type="application/json">'+json.dumps(payload if value is None else value).encode()+b'</script>'
            return v3.parse(raw, **{'requested_date': '2026-04-10', 'season': '2025-26',
                                   'observed_at': adversarial.NOW, **kwargs})
        case.parse = parse
        for method in ('test_nonfinal_overtime_postseason_postponed_cancelled_unknown_fail',
                       'test_game_season_franchise_and_side_identity_fail',
                       'test_noninteger_negative_and_inconsistent_period_scores_fail',
                       'test_tied_final_with_internally_consistent_totals_fails',
                       'test_time_date_missing_actual_time_and_early_observation_fail',
                       'test_page_completeness_route_and_duplicate_identities_fail'):
            with self.subTest(method=method): getattr(case, method)()

    def test_unverified_or_future_receipt_is_rejected_before_diagnostic_parser(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(v3, 'parse') as parser:
            with self.assertRaises(ValueError): v3.inspect(tmp, '../escape', now=NOW)
            parser.assert_not_called()
        with patch.object(v3, 'parse') as parser:
            with self.assertRaises(ValueError): v3.inspect(SOURCE, CAPTURE, now=NOW.replace(hour=9))
            parser.assert_not_called()


if __name__ == '__main__': unittest.main()
