"""Source capture destinations cannot redirect new archive writes."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

import sports_expansion_observer as espn
import sports_ncaa_official_source as ncaa
import sports_ncaa_espn_identity as identity
import sports_nba_official_schedule_audit as nba
import test_sports_ncaa_espn_identity as college_fixtures
import test_sports_nba_official_schedule_audit as nba_fixtures
from test_sports_ncaa_official_source import raw, contest

AT = datetime(2026, 10, 17, 14, tzinfo=timezone.utc)


class SourceDestinationPathTests(unittest.TestCase):
    def test_redirected_capture_roots_or_ancestors_block_all_collectors(self):
        for kind, module in (('ESPN', espn), ('NCAA', ncaa), ('NBA', nba), ('identity', identity)):
            for location in ('capture_root', 'ancestor', 'dangling_root'):
                with self.subTest(kind=kind, location=location), tempfile.TemporaryDirectory() as td:
                    base = Path(td); calls = []
                    if kind == 'NBA': nba_fixtures.NbaOfficialCorroborationTests().espn_root(base)
                    if kind == 'identity': college_fixtures.CollegeIdentityTests().seed(base)
                    target = base/module.ROOT/'captures' if location != 'ancestor' else base/'benchmarks'
                    outside = base/'outside'
                    if target.exists(): target.rename(outside)
                    elif location != 'dangling_root': outside.mkdir()
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.symlink_to(outside, target_is_directory=True)
                    before = {p.relative_to(outside): p.read_bytes() for p in outside.rglob('*') if p.is_file()}
                    def fetch(url):
                        calls.append(url)
                        return (b'{"events":[],"count":0}' if kind == 'ESPN' else
                                raw(contest()) if kind == 'NCAA' else nba_fixtures.official_games())
                    with self.assertRaisesRegex(ValueError, 'Symlink'):
                        if kind == 'ESPN': espn.capture(fetch, base=base, now=AT, days_ahead=0)
                        elif kind == 'NCAA': ncaa.run(fetch, base=base, now=AT, days_ahead=0)
                        elif kind == 'NBA': nba.run(fetch, base=base, now=AT)
                        else: identity.run(base=base, now=AT+timedelta(minutes=10))
                    self.assertEqual(calls, [])
                    self.assertEqual(before, {p.relative_to(outside): p.read_bytes() for p in outside.rglob('*') if p.is_file()})


if __name__ == '__main__': unittest.main()
