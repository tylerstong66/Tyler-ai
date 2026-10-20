"""Static archive redirects must fail before reads, fetches or append writes."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

import sports_expansion_historical_capture as provider
import sports_expansion_observer as observer
import sports_ncaa_historical_owned as fbs
import sports_ncaa_d1_historical_owned as d1
import sports_nba_historical_owned as nba
import sports_nba_schedule_receipts as schedule
import sports_nba_official_schedule_audit as official
from test_sports_ncaa_historical_owned import payload as fbs_payload
from test_sports_ncaa_d1_historical_owned import fetch as d1_fetch
from test_sports_nba_historical_owned import original as nba_payload
import test_sports_nba_schedule_receipts as schedule_fixtures

NOW = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)


class HistoricalArchivePathTests(unittest.TestCase):
    def setup_source(self, kind, base):
        if kind == 'FBS':
            fbs.capture(lambda _: fbs_payload(), base=base, now=NOW, per_run=1)
            return (base/fbs.ROOT/'train', 'week-01',
                    lambda: fbs.verify(base, 'train', 1, now=NOW),
                    lambda: fbs.capture(self.no_fetch, base=base, now=NOW, per_run=1))
        if kind == 'D1':
            d1.capture(d1_fetch, base=base, now=NOW, per_run=1)
            return (base/d1.ROOT/'train', '2024-11-04',
                    lambda: d1.verify(base, 'train', '2024-11-04', now=NOW),
                    lambda: d1.capture(self.no_fetch, base=base, now=NOW, per_run=1))
        if kind == 'NBA':
            nba.capture(lambda _: nba_payload(), base=base, now=NOW)
            return (base/nba.ROOT/'train', '2024-25',
                    lambda: nba.verify(base, 'train', now=NOW),
                    lambda: nba.capture(self.no_fetch, base=base, now=NOW))
        plan = {sport: {'train': ['2024-10-22'], 'validation': ['2025-10-21']}
                for sport in provider.ORDER}
        provider.capture(lambda _: b'{"events":[],"count":0}', base=base, now=NOW, date_plan=plan)
        return (base/provider.ROOT/'sources'/'NBA'/'train', '2024-10-22',
                lambda: provider.verify_existing(base, 'NBA', 'train', '2024-10-22', as_of=NOW),
                lambda: provider.capture(self.no_fetch, base=base, now=NOW, date_plan=plan))

    def no_fetch(self, url):
        self.fail('Invalid archive must block all network requests')

    def test_all_historical_readers_reject_symlinked_files_folders_and_ancestors(self):
        for kind in ('FBS', 'D1', 'NBA', 'ESPN'):
            for location in ('folder', 'ancestor', 'receipt', 'blob'):
                with self.subTest(kind=kind, location=location), tempfile.TemporaryDirectory() as td:
                    base = Path(td); folder, stem, verify, capture = self.setup_source(kind, base)
                    target = {'folder': folder, 'ancestor': base/'benchmarks',
                              'receipt': folder/(stem+'.receipt.json'),
                              'blob': folder/(stem+'.json.gz')}[location]
                    outside = base/'relocated'; target.rename(outside)
                    target.symlink_to(outside, target_is_directory=outside.is_dir())
                    with self.assertRaisesRegex(ValueError, 'Symlink'): verify()
                    with self.assertRaisesRegex(ValueError, 'Symlink'): capture()

    def test_dangling_historical_root_does_not_masquerade_as_missing_sources(self):
        for kind in ('FBS', 'D1', 'NBA', 'ESPN'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); folder, stem, verify, capture = self.setup_source(kind, base)
                folder.rename(base/'original')
                folder.symlink_to(base/'absent', target_is_directory=True)
                with self.assertRaisesRegex(ValueError, 'Symlink'): verify()
                with self.assertRaisesRegex(ValueError, 'Symlink'): capture()

    def test_nba_schedule_and_linked_provider_reject_redirected_paths(self):
        for location in ('nba_folder', 'ancestor', 'nba_manifest', 'nba_blob', 'provider_folder'):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as td:
                base = Path(td); stamp = schedule_fixtures.ReceiptReplayTests().seed(base)
                folder = base/official.ROOT/'captures'/stamp
                target = {'nba_folder': folder, 'ancestor': base/'benchmarks',
                          'nba_manifest': folder/'manifest.json',
                          'nba_blob': folder/'nba_schedule.json.gz',
                          'provider_folder': next((base/observer.ROOT/'captures').iterdir())}[location]
                outside = base/'relocated'; target.rename(outside)
                target.symlink_to(outside, target_is_directory=outside.is_dir())
                with self.assertRaisesRegex(ValueError, 'Symlink'): schedule.verify(base, stamp)

    def test_historical_receipts_must_be_bounded_regular_files(self):
        for kind in ('FBS', 'D1', 'NBA', 'ESPN'):
            for fault in ('directory', 'oversized'):
                with self.subTest(kind=kind, fault=fault), tempfile.TemporaryDirectory() as td:
                    base = Path(td); folder, stem, verify, _ = self.setup_source(kind, base)
                    target = folder/(stem+'.receipt.json')
                    target.unlink()
                    if fault == 'directory': target.mkdir()
                    else:
                        with target.open('wb') as stream: stream.truncate(provider.MAX_BLOB_SIZE+1)
                    with self.assertRaises(ValueError): verify()


if __name__ == '__main__': unittest.main()
