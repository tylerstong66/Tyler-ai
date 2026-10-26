"""Independent NBA/FBS/D1 historical receipts cannot hide conflicting JSON."""
import tempfile
import unittest
from pathlib import Path

import sports_nba_historical_owned as nba
import sports_ncaa_historical_owned as fbs
import sports_ncaa_d1_historical_owned as d1
from test_sports_nba_historical_owned import original as nba_original, NOW as NBA_NOW
from test_sports_ncaa_historical_owned import payload as fbs_original, NOW as FBS_NOW
from test_sports_ncaa_d1_historical_owned import fetch as d1_fetch, NOW as D1_NOW


class IndependentHistoricalStrictJsonTests(unittest.TestCase):
    def test_ambiguous_receipt_blocks_replay_and_future_acquisition(self):
        cohorts = (
            ('NBA', nba, lambda _: nba_original(), NBA_NOW,
             lambda root: root / nba.ROOT / 'train' / '2024-25.receipt.json',
             lambda root: nba.verify(root, 'train', now=NBA_NOW),
             lambda root, fetch: nba.capture(fetch, base=root, now=NBA_NOW)),
            ('NCAAF_FBS', fbs, lambda _: fbs_original(), FBS_NOW,
             lambda root: root / fbs.ROOT / 'train' / 'week-01.receipt.json',
             lambda root: fbs.verify(root, 'train', 1, now=FBS_NOW),
             lambda root, fetch: fbs.capture(fetch, base=root, now=FBS_NOW, per_run=1)),
            ('NCAAM_D1', d1, d1_fetch, D1_NOW,
             lambda root: root / d1.ROOT / 'train' / '2024-11-04.receipt.json',
             lambda root: d1.verify(root, 'train', '2024-11-04', now=D1_NOW),
             lambda root, fetch: d1.capture(fetch, base=root, now=D1_NOW, per_run=1)),
        )
        for league, _, source, now, receipt_path, verify, capture in cohorts:
            for kind, suffix, expected in (
                ('duplicate_guard', b',"NO_BET":true}', 'Duplicate key'),
                ('nonfinite_field', b',"unsupported":NaN}', 'Non-finite'),
            ):
                with self.subTest(league=league, kind=kind), tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    capture(root, source)
                    receipt = receipt_path(root)
                    original = receipt.read_bytes().rstrip()
                    receipt.write_bytes(original[:-1] + suffix)
                    with self.assertRaisesRegex(ValueError, expected):
                        verify(root)
                    with self.assertRaisesRegex(ValueError, expected):
                        capture(root, lambda _: self.fail('Invalid receipt must block outbound fetch'))
                    self.assertEqual(receipt.read_bytes(), original[:-1] + suffix)


if __name__ == '__main__':
    unittest.main()
