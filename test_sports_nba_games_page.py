import copy
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

import sports_nba_games_page as page
import sports_nba_schedule_slots as slots

ROOT = Path(__file__).parent/'benchmarks/nba_games_page_v1/initial_probe'
NOW = datetime(2026, 10, 20, 11, 29, 34, 339098, tzinfo=timezone.utc)


class GamesPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = gzip.decompress((ROOT/'official_games_page.html.gz').read_bytes())
        cls.payload = json.loads(re.search(rb'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', cls.raw, re.S)[1])

    def parse(self, value=None, **kwargs):
        raw = self.raw if value is None else (
            b'<html><script id="__NEXT_DATA__" type="application/json">'+
            json.dumps(value).encode()+b'</script></html>')
        return page.parse(raw, **{'requested_date': '2026-10-20', 'season': '2026-27',
                                 'observed_at': NOW, **kwargs})

    def mutate(self, path, value):
        result = copy.deepcopy(self.payload); current = result
        for part in path[:-1]: current = current[part]
        current[path[-1]] = value
        return result

    def test_original_runner_archives_hashes_and_counts(self):
        manifest = json.loads((ROOT/'manifest.json').read_text())
        self.assertEqual(manifest['probe_started_at_utc'], NOW.isoformat())
        for row, count in zip(manifest['responses'], [3, 11]):
            raw = gzip.decompress((ROOT/row['repository_archive_file']).read_bytes())
            self.assertEqual(len(raw), row['response_body_bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['response_body_sha256'])
            result = page.parse(raw, requested_date=row['url'].split('date=')[1],
                                season='2026-27', observed_at=NOW)
            self.assertEqual(result['daily_game_count'], count)
            for key in ('full_season_schedule_verified', 'official_final_results_verified',
                        'collector_fallback_enabled', 'feature_collection_enabled',
                        'receipt_clock_independently_attested', 'forecasting_enabled',
                        'model_training_enabled', 'promotion_allowed'):
                self.assertIs(result[key], False)
            self.assertIs(result['NO_BET'], True)
            self.assertEqual(result['actual_wagers'], 0)

    def test_actual_cards_match_prior_owned_schedule_exactly(self):
        old = Path(__file__).parent/'benchmarks/college_nba_source_v1/nba_official/captures/20261019T132650150333Z/nba_schedule.json.gz'
        games, _ = slots.parse(gzip.decompress(old.read_bytes()), observed_at='2026-10-19T13:26:50.150333+00:00')
        index = {g['nba_game_id']: g for g in games}
        for row in json.loads((ROOT/'manifest.json').read_text())['responses']:
            result = page.parse(gzip.decompress((ROOT/row['repository_archive_file']).read_bytes()),
                requested_date=row['url'].split('date=')[1], season='2026-27', observed_at=NOW)
            for game in result['games']:
                for key in ('home_tricode', 'away_tricode', 'tipoff_utc', 'nba_status'):
                    self.assertEqual(game[key], index[game['nba_game_id']][key])

    def test_route_date_locale_errors_fail(self):
        prefix = ['props', 'pageProps']
        mutations = [(['page'], '/schedule'), (['query'], {'date': '2026-10-21'}),
                     (['locale'], 'es'), (['isFallback'], True),
                     (prefix+['selectedDate'], '2026-10-21'),
                     (prefix+['hasError'], True), (prefix+['isDateOverrideActive'], False)]
        for path, value in mutations:
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.parse(self.mutate(path, value))

    def test_pagination_incomplete_counts_and_unknown_modules_fail(self):
        feed = ['props', 'pageProps', 'gameCardFeed']
        mutations = [(feed+['nextPageToken'], 'next'), (feed+['previousPageToken'], 'prev'),
            (feed+['modules'], []), (feed+['modules', 0, 'moduleType'], 'carousel'),
            (['props', 'pageProps', 'allGamesInCurrentYear', '2026', '2026-10-20'], True)]
        for path, value in mutations:
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.parse(self.mutate(path, value))

    def test_game_identity_status_and_franchise_corruption_fail(self):
        card = ['props', 'pageProps', 'gameCardFeed', 'modules', 0, 'cards', 0]
        g = card+['cardData']
        mutations = [(card+['cardType'], 'ad'), (g+['gameId'], '0022500001'),
            (g+['gameId'], '002260000１'), (g+['gameId'], '002260000١'),
            (g+['gameId'], '00226００００１'),
            (g+['gameId'], '0042600001'), (g+['seasonYear'], '2025-26'),
            (g+['seasonType'], 'Pre Season'), (g+['leagueId'], '10'),
            (g+['homeTeam', 'teamId'], 1610612738),
            (g+['homeTeam', 'teamTricode'], 'BOS'), (g+['awayTeam', 'score'], 1),
            (g+['gameStatus'], True), (g+['gameStatus'], 2), (g+['gameStatus'], 3),
            (g+['gameState'], 2), (g+['period'], 1), (g+['ifNecessary'], True),
            (g+['gameSubtype'], 'Postponed'), (g+['actualStartTimeUTC'], '2026-10-20T19:00:00Z'),
            (g+['gameStatusText'], 'Postponed'), (g+['gameStatusText'], 'TBD'),
            (g+['actualEndTimeUTC'], '2026-10-20T22:00:00Z'),
            (g+['gameTimeUtc'], '2026-10-20T19:00:00'),
            (g+['gameTimeUtc'], '2026-10-21T19:00:00Z')]
        for path, value in mutations:
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.parse(self.mutate(path, value))

    def test_duplicate_games_or_franchises_fail(self):
        data = copy.deepcopy(self.payload)
        cards = data['props']['pageProps']['gameCardFeed']['modules'][0]['cards']
        cards[1] = copy.deepcopy(cards[0])
        with self.assertRaises(ValueError): self.parse(data)
        cards[1]['cardData']['gameId'] = '0022600002'
        with self.assertRaises(ValueError): self.parse(data)

    def test_clock_and_input_bounds_fail_before_acceptance(self):
        for kwargs in ({'observed_at': NOW.replace(tzinfo=None)},
                       {'observed_at': datetime(2026, 10, 20, 19, tzinfo=timezone.utc)},
                       {'season': '2025-26'}, {'season': '2026-28'},
                       {'requested_date': '2026-1-20'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError): self.parse(**kwargs)
        for raw in (b'', b'x'*(page.MAX_BYTES+1), b'\xff', b'<html>captcha</html>'):
            with self.assertRaises(ValueError):
                page.parse(raw, requested_date='2026-10-20', season='2026-27', observed_at=NOW)

    def test_embedded_script_and_json_ambiguity_fail(self):
        script = b'<script id="__NEXT_DATA__" type="application/json">'+json.dumps(self.payload).encode()+b'</script>'
        cases = [script+script, script[:-9], script.replace(b'type="application/json"', b'type="text/javascript"'),
                 script.replace(b'id="__NEXT_DATA__"', b'id="__NEXT_DATA__" src="https://example.com/x"'),
                 script.replace(b'"page": "/games"', b'"page": "/games", "page": "/games"'),
                 script.replace(b'"isFallback": false', b'"isFallback": NaN')]
        for raw in cases:
            with self.subTest(raw_size=len(raw)), self.assertRaises(ValueError):
                page.parse(raw, requested_date='2026-10-20', season='2026-27', observed_at=NOW)

    def test_empty_calendar_day_explicit_zero_only(self):
        data = copy.deepcopy(self.payload); data['query'] = {'date': '2026-10-19'}
        p = data['props']['pageProps']; p['selectedDate'] = '2026-10-19'
        p['gameCardFeed']['modules'] = []
        self.assertEqual(self.parse(data, requested_date='2026-10-19')['daily_game_count'], 0)
        del p['allGamesInCurrentYear']['2026']['2026-10-19']
        with self.assertRaises(ValueError): self.parse(data, requested_date='2026-10-19')

    def test_offset_clock_normalizes_without_changing_results(self):
        result = self.parse(observed_at=NOW.astimezone(timezone(timedelta(hours=5, minutes=30))))
        self.assertEqual(result, self.parse())

    def test_initial_replay_uses_pinned_bodies_and_original_clock(self):
        result = page.replay_initial(Path(__file__).parent)
        self.assertEqual(result['daily_game_count'], 14)
        self.assertEqual(result['original_observation_clock'], NOW.isoformat())
        self.assertIs(result['archive_body_bindings_replayed'], True)
        self.assertIs(result['fresh_source_observation'], False)
        self.assertIs(result['collector_fallback_enabled'], False)

    def test_modified_manifest_or_archived_body_cannot_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)/'benchmarks/nba_games_page_v1/initial_probe'
            shutil.copytree(ROOT, destination)
            manifest = destination/'manifest.json'; original = manifest.read_bytes()
            manifest.write_bytes(original+b'\n')
            with self.assertRaisesRegex(ValueError, 'manifest changed'): page.replay_initial(folder)
            manifest.write_bytes(original)
            body = destination/'official_games_page.html.gz'
            body.write_bytes(gzip.compress(self.raw.replace(b'Celtics', b'Altered')))
            with self.assertRaisesRegex(ValueError, 'binding disagrees'): page.replay_initial(folder)

    def test_decompression_bomb_rejected_before_unbounded_parsing(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)/'benchmarks/nba_games_page_v1/initial_probe'
            shutil.copytree(ROOT, destination)
            (destination/'official_games_page.html.gz').write_bytes(gzip.compress(b'x'*(page.MAX_BYTES+1)))
            with self.assertRaisesRegex(ValueError, 'maximum response size'): page.replay_initial(folder)


if __name__ == '__main__': unittest.main()
