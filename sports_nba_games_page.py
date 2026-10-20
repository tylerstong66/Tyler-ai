"""Strict offline parsing of NBA-owned daily pregame HTML; no collector fallback."""
from datetime import date, datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo
from sports_expansion_audit import bounded_gzip_read

MAX_BYTES = 8_000_000
INITIAL_MANIFEST_SHA256 = 'c9b7908c9458bc6cf540a61f7921311c7b2a8a5980503d2af9f8e13bf6372aeb'
EASTERN = ZoneInfo('America/New_York')
# NBA franchise IDs/tricodes, cross-checked against the archived owned schedule.
TEAMS = dict(zip(range(1610612737, 1610612767),
    'ATL BOS CLE NOP CHI DAL DEN GSW HOU LAC LAL MIA MIL MIN BKN NYK ORL IND PHI PHX POR SAC SAS OKC TOR UTA MEM WAS DET CHA'.split()))


class _NextData(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.matches = 0; self.active = False; self.parts = []; self.closed = False

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and any(k == 'id' and v == '__NEXT_DATA__' for k, v in attrs):
            self.matches += 1
            if (self.matches != 1 or len(attrs) != len(dict(attrs))
                    or dict(attrs).get('type') != 'application/json'
                    or 'src' in dict(attrs)):
                raise ValueError('Ambiguous NBA embedded data script')
            self.active = True

    def handle_data(self, data):
        if self.active: self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.active = False; self.closed = True


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('Duplicate NBA JSON key')
        result[key] = value
    return result


def _reject_constant(_):
    raise ValueError('Nonfinite NBA JSON')


def _utc(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):
        raise ValueError('NBA game requires explicit UTC seconds')
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def parse(raw, *, requested_date, season, observed_at):
    """Return complete daily pregame identities, never a full-season schedule.

    v1 deliberately rejects live/final/cancelled games until their source shapes
    have separately been inspected. All games in a page must pass together.
    """
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_BYTES:
        raise ValueError('Missing or oversized NBA games page')
    if (not isinstance(requested_date, str)
            or not re.fullmatch(r'20\d{2}-\d{2}-\d{2}', requested_date)):
        raise ValueError('Explicit NBA calendar date required')
    day = date.fromisoformat(requested_date)
    if (not isinstance(season, str) or not re.fullmatch(r'20\d{2}-\d{2}', season)
            or int(season[-2:]) != (int(season[:4])+1) % 100
            or (day.year if day.month >= 7 else day.year-1) != int(season[:4])):
        raise ValueError('NBA page season/date mismatch')
    if not isinstance(observed_at, datetime) or observed_at.tzinfo is None:
        raise ValueError('Aware NBA observation clock required')
    observed = observed_at.astimezone(timezone.utc)
    try:
        parser = _NextData(); parser.feed(raw.decode('utf-8')); parser.close()
        if parser.matches != 1 or not parser.closed or parser.active:
            raise ValueError('Missing or unclosed NBA embedded data')
        root = json.loads(''.join(parser.parts), object_pairs_hook=_object,
                          parse_constant=_reject_constant)
        if (root['page'] != '/games' or root['query'] != {'date': requested_date}
                or root['locale'] != 'en' or root.get('isFallback') is not False):
            raise ValueError('NBA page route/date/locale mismatch')
        page = root['props']['pageProps']
        if (page['hasError'] is not False or page['selectedDate'] != requested_date
                or page['isDateOverrideActive'] is not True):
            raise ValueError('NBA page date override missing')
        feed = page['gameCardFeed']
        if feed['nextPageToken'] is not None or feed['previousPageToken'] is not None:
            raise ValueError('Paginated NBA page is incomplete')
        modules = feed['modules']
        expected = page['allGamesInCurrentYear'][str(day.year)][requested_date]
        if type(expected) is not int or not 0 <= expected <= 30 or not isinstance(modules, list):
            raise ValueError('Invalid NBA daily calendar count')
        games = []; seen = set(); seen_teams = set()
        for module in modules:
            if module['moduleType'] != 'list' or not isinstance(module['cards'], list):
                raise ValueError('Unsupported NBA daily module')
            for card in module['cards']:
                if card['cardType'] != 'game': raise ValueError('Unsupported NBA daily card')
                game = card['cardData']; identifier = game['gameId']
                if (not isinstance(identifier, str)
                        or not re.fullmatch('002'+season[2:4]+r'\d{5}', identifier)
                        or identifier in seen or game['leagueId'] != '00'
                        or game['seasonYear'] != season or game['seasonType'] != 'Regular Season'):
                    raise ValueError('Invalid NBA regular-season game identity')
                seen.add(identifier)
                if (type(game['gameStatus']) is not int or game['gameStatus'] != 1
                        or type(game['gameState']) is not int or game['gameState'] != 1
                        or type(game['period']) is not int or game['period'] != 0
                        or game['gameSubtype'] != '' or game['ifNecessary'] is not False
                        or game['actualStartTimeUTC'] is not None
                        or game['actualEndTimeUTC'] is not None):
                    raise ValueError('NBA page game is not supported scheduled pregame')
                tip = _utc(game['gameTimeUtc'])
                if tip <= observed or tip.astimezone(EASTERN).date() != day:
                    raise ValueError('NBA pregame time/date disagrees with observation')
                expected_text = tip.astimezone(EASTERN).strftime('%I:%M %p').lstrip('0').lower()+' ET'
                if game['gameStatusText'] != expected_text:
                    raise ValueError('NBA pregame status text disagrees with saved start')
                sides = {}
                for side in ('home', 'away'):
                    team = game[side+'Team']; tid = team['teamId']; tri = team['teamTricode']
                    if (type(tid) is not int or tid not in TEAMS or TEAMS[tid] != tri
                            or tid in seen_teams or type(team['score']) is not int or team['score'] != 0):
                        raise ValueError('NBA franchise/side/score identity mismatch')
                    seen_teams.add(tid); sides[side] = (tid, tri)
                games.append({'nba_game_id': identifier, 'kind': 'regular',
                    'home_team_id': sides['home'][0], 'home_tricode': sides['home'][1],
                    'away_team_id': sides['away'][0], 'away_tricode': sides['away'][1],
                    'tipoff_utc': tip.isoformat(), 'nba_status': 1,
                    'nba_home_score': None, 'nba_away_score': None})
        if len(games) != expected: raise ValueError('NBA cards disagree with daily calendar count')
    except (KeyError, TypeError, UnicodeError, AttributeError, RecursionError) as error:
        raise ValueError('Malformed NBA daily source shape') from error
    return {'schema': 'tyler-nba-owned-daily-pregame-page-v1',
        'requested_date': requested_date, 'season': season,
        'observed_at_utc': observed.isoformat(),
        'original_body_sha256': hashlib.sha256(raw).hexdigest(),
        'daily_game_count': len(games), 'games': sorted(games, key=lambda g: g['nba_game_id']),
        'source_scope': 'ONE_REQUESTED_EASTERN_DATE_ONLY', 'full_season_schedule_verified': False,
        'official_final_results_verified': False, 'actual_tipoff_time_attested': False,
        'receipt_clock_independently_attested': False, 'collector_fallback_enabled': False,
        'feature_collection_enabled': False, 'forecasting_enabled': False,
        'model_training_enabled': False, 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


def replay_initial(base=Path('.')):
    """Replay the pinned example at its original clock, not as a fresh source."""
    root = Path(base)/'benchmarks/nba_games_page_v1/initial_probe'
    raw_manifest = (root/'manifest.json').read_bytes()
    if hashlib.sha256(raw_manifest).hexdigest() != INITIAL_MANIFEST_SHA256:
        raise ValueError('NBA initial diagnostic manifest changed')
    manifest = json.loads(raw_manifest); reports = []
    observed = datetime.fromisoformat(manifest['probe_started_at_utc'])
    for row in manifest['responses']:
        compressed = (root/row['repository_archive_file']).read_bytes()
        if len(compressed) > MAX_BYTES: raise ValueError('Oversized compressed NBA archive')
        raw = bounded_gzip_read(compressed, MAX_BYTES)
        if (len(raw) != row['response_body_bytes']
                or hashlib.sha256(raw).hexdigest() != row['response_body_sha256']):
            raise ValueError('NBA diagnostic original response binding disagrees')
        reports.append(parse(raw, requested_date=row['url'].split('date=')[1],
                             season='2026-27', observed_at=observed))
    return {'schema': 'tyler-nba-owned-daily-initial-replay-v1',
        'manifest_sha256': INITIAL_MANIFEST_SHA256, 'original_observation_clock': observed.isoformat(),
        'pages': reports, 'daily_game_count': sum(r['daily_game_count'] for r in reports),
        'archive_body_bindings_replayed': True, 'fresh_source_observation': False,
        'source_origin_independently_attested': False, 'receipt_clock_independently_attested': False,
        'collector_fallback_enabled': False, 'feature_collection_enabled': False,
        'forecasting_enabled': False, 'NO_BET': True, 'actual_wagers': 0}


if __name__ == '__main__':
    print(json.dumps(replay_initial(), sort_keys=True, indent=2))
