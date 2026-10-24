import copy
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

import sports_nba_final_games_page as final
import sports_nba_games_page as page
import sports_nba_historical_owned as historical

SOURCE = Path(__file__).parent
NOW = datetime(2026, 10, 20, 12, 9, 26, 334105, tzinfo=timezone.utc)
CARD = ['props', 'pageProps', 'gameCardFeed', 'modules', 0, 'cards', 0, 'cardData']


class FinalGamesPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = gzip.decompress((SOURCE/final.FIXTURE_ROOT/'nba_games.html.gz').read_bytes())
        cls.payload = json.loads(re.search(rb'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', cls.raw, re.S)[1])

    def parse(self, value=None, **kwargs):
        raw = self.raw if value is None else (
            b'<script id="__NEXT_DATA__" type="application/json">'+json.dumps(value).encode()+b'</script>')
        return final.parse(raw, **{'requested_date': '2026-04-10', 'season': '2025-26',
                                 'observed_at': NOW, **kwargs})

    def mutate(self, path, value):
        result = copy.deepcopy(self.payload); current = result
        for part in path[:-1]: current = current[part]
        current[path[-1]] = value
        return result

    def test_original_diagnostic_replay_and_disabled_claims(self):
        result = final.replay_reference(SOURCE)
        self.assertEqual(result['daily_game_count'], 15)
        self.assertEqual(result['original_body_sha256'], '2d50e1ed52824252deb3109552f2f497e10f93999d67540b3efb9021f129a3bc')
        self.assertEqual(result['observed_at_utc'], NOW.isoformat())
        self.assertTrue(result['NO_BET']); self.assertEqual(result['actual_wagers'], 0)
        for key in ('official_final_results_verified', 'actual_tipoff_time_attested',
                    'source_origin_independently_attested', 'receipt_clock_independently_attested',
                    'collector_fallback_enabled', 'settlement_enabled', 'historical_evaluation_enabled',
                    'feature_collection_enabled', 'forecasting_enabled', 'model_training_enabled',
                    'promotion_allowed', 'fresh_source_observation', 'available_at_historical_pregame_freeze'):
            self.assertIs(result[key], False)

    def test_original_final_identities_and_scores_match_separate_owned_season(self):
        saved = historical.verify(SOURCE, 'validation', now=NOW)
        self.assertIsNotNone(saved)
        index = {g['nba_game_id']: g for g in saved['parsed_nba_games']}
        for game in self.parse()['games']:
            for key in ('home_tricode', 'away_tricode', 'tipoff_utc', 'nba_status',
                        'nba_home_score', 'nba_away_score', 'kind'):
                self.assertEqual(game[key], index[game['nba_game_id']][key])

    def test_nonfinal_overtime_postseason_postponed_cancelled_unknown_fail(self):
        cases = [('gameStatus', 1), ('gameStatus', 2), ('gameStatus', True),
                 ('gameState', 2), ('period', 5), ('period', True),
                 ('gameStatusText', 'Final/OT'), ('gameStatusText', 'Postponed'),
                 ('gameStatusText', 'Canceled'), ('gameClock', 'PT01M00.00S'),
                 ('gameBreakStatus', 'HALFTIME'), ('gameSubtype', 'Postponed'),
                 ('seasonType', 'Playoffs'), ('ifNecessary', True)]
        for key, value in cases:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.parse(self.mutate(CARD+[key], value))

    def test_game_season_franchise_and_side_identity_fail(self):
        for path, value in [(['gameId'], '0022601171'), (['gameId'], '0042501171'),
                (['gameId'], '002250117１'), (['gameId'], '002250117١'),
                (['gameId'], '00225０１１７１'),
                (['seasonYear'], '2026-27'), (['leagueId'], '10'),
                (['homeTeam', 'teamId'], True), (['homeTeam', 'teamId'], 1610612738),
                (['homeTeam', 'teamTricode'], 'BOS')]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.parse(self.mutate(CARD+path, value))
        p = copy.deepcopy(self.payload)
        cards = p['props']['pageProps']['gameCardFeed']['modules'][0]['cards']
        cards[0]['cardData']['homeTeam'] = copy.deepcopy(cards[0]['cardData']['awayTeam'])
        with self.assertRaises(ValueError): self.parse(p)

    def test_noninteger_negative_and_inconsistent_period_scores_fail(self):
        for path, value in [(['score'], True), (['score'], -1), (['score'], 100.0),
                (['score'], 101), (['periods'], []), (['periods', 0, 'period'], True),
                (['periods', 0, 'period'], 2), (['periods', 0, 'score'], True),
                (['periods', 0, 'score'], -1), (['periods', 0, 'score'], 31)]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.parse(self.mutate(CARD+['homeTeam']+path, value))

    def test_tied_final_with_internally_consistent_totals_fails(self):
        p = copy.deepcopy(self.payload)
        game = p['props']['pageProps']['gameCardFeed']['modules'][0]['cards'][0]['cardData']
        game['awayTeam']['score'] = game['homeTeam']['score']
        game['awayTeam']['periods'] = copy.deepcopy(game['homeTeam']['periods'])
        with self.assertRaisesRegex(ValueError, 'Tied'): self.parse(p)

    def test_time_date_missing_actual_time_and_early_observation_fail(self):
        for key, value in [('actualStartTimeUTC', None), ('actualEndTimeUTC', None),
                ('actualStartTimeUTC', '2026-04-10T22:00:00Z'),
                ('actualEndTimeUTC', '2026-04-10T23:10:48Z'),
                ('actualEndTimeUTC', '2026-10-21T00:00:00Z'),
                ('gameTimeUtc', '2026-04-11T23:00:00Z'),
                ('actualEndTimeUTC', '2026-04-11T01:28:52')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.parse(self.mutate(CARD+[key], value))
        for clock in (NOW.replace(tzinfo=None), datetime(2026, 4, 10, 23, tzinfo=timezone.utc)):
            with self.subTest(clock=clock), self.assertRaises(ValueError): self.parse(observed_at=clock)

    def test_page_completeness_route_and_duplicate_identities_fail(self):
        prefix = ['props', 'pageProps']
        for path, value in [(['query'], {'date': '2026-04-11'}), (['isFallback'], True),
                (prefix+['hasError'], True), (prefix+['isDateOverrideActive'], False),
                (prefix+['gameCardFeed', 'nextPageToken'], 'next'),
                (prefix+['allGamesInCurrentYear', '2026', '2026-04-10'], 14),
                (prefix+['gameCardFeed', 'modules'], [])]:
            with self.subTest(path=path), self.assertRaises(ValueError): self.parse(self.mutate(path, value))
        p = copy.deepcopy(self.payload)
        cards = p['props']['pageProps']['gameCardFeed']['modules'][0]['cards']
        cards[1] = copy.deepcopy(cards[0])
        with self.assertRaises(ValueError): self.parse(p)

    def test_embedded_json_duplicate_and_ambiguous_scripts_fail(self):
        for raw in (b'denied', self.raw+self.raw,
                    b'<script id="__NEXT_DATA__" type="application/json">{"page":1,"page":2}</script>'):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                final.parse(raw, requested_date='2026-04-10', season='2025-26', observed_at=NOW)

    def test_original_final_cannot_enter_pregame_parser(self):
        with self.assertRaises(ValueError):
            page.parse(self.raw, requested_date='2026-04-10', season='2025-26', observed_at=NOW)

    def test_modified_fixture_or_symlink_rejected_without_writing_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td)/final.FIXTURE_ROOT; shutil.copytree(SOURCE/final.FIXTURE_ROOT, dest)
            manifest = dest/'manifest.json'; original = manifest.read_bytes()
            manifest.write_bytes(original+b'\n')
            with self.assertRaisesRegex(ValueError, 'manifest changed'): final.replay_reference(td)
            manifest.write_bytes(original)
            blob = dest/'nba_games.html.gz'; compressed = blob.read_bytes()
            blob.write_bytes(gzip.compress(self.raw+b'\n'))
            with self.assertRaisesRegex(ValueError, 'binding disagrees'): final.replay_reference(td)
            blob.write_bytes(compressed)
            outside = Path(td)/'relocated'; dest.rename(outside)
            dest.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'Symlink'): final.replay_reference(td)
        self.assertEqual(hashlib.sha256((SOURCE/final.FIXTURE_ROOT/'manifest.json').read_bytes()).hexdigest(),
                         final.FIXTURE_MANIFEST_SHA256)


if __name__ == '__main__': unittest.main()
