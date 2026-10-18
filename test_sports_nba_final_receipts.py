"""NBA result agreement never enables training, forecasting or wagers."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import tempfile
import unittest

import sports_expansion_observer as espn
import sports_nba_official_schedule_audit as nba
import sports_nba_final_receipts as finals
from test_sports_nba_official_schedule_audit import official_games, espn_event

AT = datetime(2026, 10, 20, 23, tzinfo=timezone.utc)


class NbaFinalReceiptTests(unittest.TestCase):
    def seed(self, root, *, at=AT, score=106, nfinal=True, efinal=True, duplicate=False, postponed=None, stage=2, nba_id=None):
        def fetch(url):
            if 'basketball/nba' in url and 'dates=20261020' in url:
                e = espn_event()
                e['season']['type'] = stage
                if efinal:
                    e['status']['type'] = {'state': 'post', 'completed': True}
                    e['competitions'][0]['competitors'][0]['score'] = str(score)
                    e['competitions'][0]['competitors'][1]['score'] = '104'
                events = [e]
                if duplicate:
                    events.append({**e, 'id': '401234568'})
                return json.dumps({'events': events, 'count': len(events)}).encode()
            return b'{"events":[],"count":0}'
        espn.capture(fetch, base=root, now=at, days_ahead=0)
        obj = json.loads(official_games())
        game = obj['leagueSchedule']['gameDates'][0]['games'][0]
        if nba_id is not None:
            game['gameId'] = nba_id
        game['postponedStatus'] = postponed
        if nfinal:
            game['gameStatus'] = 3
            game['homeTeam']['score'] = 106
            game['awayTeam']['score'] = 104
        now = at + timedelta(minutes=1)
        nba.run(lambda _: json.dumps(obj).encode(), base=root, now=now)
        return now.strftime('%Y%m%dT%H%M%S%fZ')

    def test_archived_raw_finals_with_provenance_and_postgame_chronology(self):
        with tempfile.TemporaryDirectory() as td:
            stamp = self.seed(Path(td)); out = finals.build(td, stamp)
            self.assertEqual(out['two_source_final_agreements'], 1)
            self.assertTrue(out['source_archive_sha256_verified'])
            self.assertEqual(len(out['nba_response_sha256']), 64)
            self.assertEqual(out['corroborated_research_only'][0]['home_score'], 106)
            for key in ('historical_evaluation_enabled', 'model_training_enabled',
                        'forecasting_enabled', 'promotion_allowed'):
                self.assertIs(out[key], False)
            self.assertTrue(out['NO_BET']); self.assertEqual(out['actual_wagers'], 0)

    def test_pending_conflicting_and_duplicate_games_never_become_labels(self):
        cases = (({'efinal': False}, 'BOTH_SOURCES_NOT_FINAL'),
                 ({'score': 107}, 'CONFLICTING_FINAL_SCORES_NO_GRADE'),
                 ({'duplicate': True}, 'NON_BIJECTIVE_GAME_IDENTITY'),
                 ({'postponed': 'Y'}, 'POSTPONED_OR_UNKNOWN_NBA_STATUS'),
                 ({'stage': 3}, 'NBA_ESPN_SEASON_STAGE_MISMATCH'),
                 ({'nba_id': '0022500000'}, 'NBA_GAME_ID_SEASON_MISMATCH'),
                 ({'at': AT - timedelta(hours=4)}, 'FINAL_OBSERVED_AT_OR_BEFORE_SAVED_START'))
        for kwargs, reason in cases:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as td:
                stamp = self.seed(Path(td), **kwargs); out = finals.build(td, stamp)
                self.assertEqual(out['two_source_final_agreements'], 0)
                self.assertTrue(all(row['reason'] == reason for row in out['pending']))

    def test_official_timestamp_and_endpoint_mutation_fail_closed(self):
        for field, value in (('created_at_utc', '2026-10-21T01:00:00Z'),
                             ('nba_official_source_url', 'https://example.org/fake')):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                root = Path(td); stamp = self.seed(root)
                path = root / nba.ROOT / 'captures' / stamp / 'manifest.json'
                obj = json.loads(path.read_bytes()); obj[field] = value
                path.write_text(json.dumps(obj))
                with self.assertRaises(ValueError):
                    finals.build(root, stamp)

    def test_corrupted_original_bytes_and_invalid_identifier_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); stamp = self.seed(root)
            (root / nba.ROOT / 'captures' / stamp / 'nba_schedule.json.gz').write_bytes(b'bad')
            with self.assertRaises(ValueError):
                finals.build(root, stamp)
        with self.assertRaisesRegex(ValueError, 'identifier'):
            finals.build('.', '../outside')


if __name__ == '__main__':
    unittest.main()
