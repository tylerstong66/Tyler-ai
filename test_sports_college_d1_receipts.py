"""Exercise the full Division I receipt route independently from FBS fixtures."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlparse, parse_qs

import sports_expansion_observer as espn
import sports_ncaa_official_source as ncaa
import sports_ncaa_espn_identity as identity
import sports_college_final_receipts as receipts
import sports_college_result_dataset as dataset
from test_sports_ncaa_espn_identity import official_game, espn_game

AT = datetime(2026, 11, 4, 23, tzinfo=timezone.utc)
START = datetime(2026, 11, 4, 19, tzinfo=timezone.utc)


class DivisionIReceiptTests(unittest.TestCase):
    def seed(self, root, *, away='Kansas', espn_away='Kansas', completed=True):
        def official(url):
            params = json.loads(parse_qs(urlparse(url).query)['variables'][0])
            contests = []
            if params['sportCode'] == 'MBB' and params.get('contestDate') == '2026/11/04':
                contests = [official_game(when=int(START.timestamp()), home='Duke',
                                          away=away, final=completed)]
            return json.dumps({'data': {'contests': contests}}).encode()
        ncaa.run(official, base=root, now=AT, days_ahead=0)
        def provider(url):
            events = []
            if 'basketball/mens-college-basketball' in url and 'dates=20261104' in url:
                events = [espn_game(start=START.isoformat(), home='Duke',
                                    away=espn_away, completed=completed)]
            return json.dumps({'count': len(events), 'events': events}).encode()
        espn.capture(provider, base=root, now=AT, days_ahead=0)
        at = AT + timedelta(minutes=1)
        identity.run(base=root, now=at)
        return at.strftime('%Y%m%dT%H%M%S%fZ')

    def test_original_d1_archives_produce_only_research_final(self):
        with tempfile.TemporaryDirectory() as td:
            stamp = self.seed(Path(td))
            out = receipts.build(td, stamp)
            self.assertEqual(out['two_source_final_agreements'], 1)
            row = out['corroborated_research_only'][0]
            self.assertEqual(row['league'], 'NCAAM_D1')
            self.assertEqual(row['ncaa_home_school'], 'Duke')
            self.assertFalse(row['eligible_for_historical_evaluation'])
            self.assertTrue(row['result_observation_chronology_verified'])
            combined = dataset.assemble(td, [stamp])
            self.assertEqual(combined['unique_corroborated_games'], 1)
            self.assertFalse(combined['model_training_enabled'])
            self.assertTrue(combined['NO_BET'])

    def test_football_alias_policy_never_imposed_on_d1_school_identity(self):
        with tempfile.TemporaryDirectory() as td:
            stamp = self.seed(Path(td), away='Penn St.', espn_away='Penn State')
            out = receipts.build(td, stamp)
            self.assertEqual(out['two_source_final_agreements'], 0)
            self.assertEqual(out['pending'][0]['reason'], 'NO_UNAMBIGUOUS_NCAA_GAME_ID')

    def test_d1_nonfinal_source_is_not_backfilled_as_result(self):
        with tempfile.TemporaryDirectory() as td:
            stamp = self.seed(Path(td), completed=False)
            out = receipts.build(td, stamp)
            self.assertEqual(out['two_source_final_agreements'], 0)
            self.assertEqual(out['pending'][0]['reason'], 'BOTH_SOURCES_NOT_FINAL')


if __name__ == '__main__':
    unittest.main()
