"""Offline NBA-owned regulation-final daily page parsing; no settlement writes."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

import sports_nba_games_page as page
from sports_expansion_audit import archive_path, bounded_gzip_read

FIXTURE_ROOT = Path('benchmarks/nba_games_page_v1/reference_final_probe')
FIXTURE_MANIFEST_SHA256 = 'd0f4d911c440607b450b52eb5e07e489034661fab83c73355027b01e52a81c3d'


def _parse(raw, *, requested_date, season, observed_at, document_reader):
    """Accept only the inspected complete regular-season regulation-final shape.

    Overtime, mixed live/pregame, postponed and postseason pages fail closed.
    Reported actual times are consistency checks, not independent attestations.
    """
    day, observed, modules, expected = document_reader(raw, requested_date=requested_date,
        season=season, observed_at=observed_at)
    games = []; seen = set(); seen_teams = set()
    try:
        for module in modules:
            if module['moduleType'] != 'list' or not isinstance(module['cards'], list):
                raise ValueError('Unsupported NBA final module')
            for card in module['cards']:
                if card['cardType'] != 'game': raise ValueError('Unsupported NBA final card')
                game = card['cardData']; identifier = game['gameId']
                if (not isinstance(identifier, str)
                        or not re.fullmatch('002'+season[2:4]+r'\d{5}', identifier)
                        or identifier in seen or game['leagueId'] != '00'
                        or game['seasonYear'] != season or game['seasonType'] != 'Regular Season'):
                    raise ValueError('Invalid NBA final regular-season identity')
                seen.add(identifier)
                if (type(game['gameStatus']) is not int or game['gameStatus'] != 3
                        or type(game['gameState']) is not int or game['gameState'] != 3
                        or type(game['period']) is not int or game['period'] != 4
                        or game['gameStatusText'] != 'Final' or game['gameClock'] != 'PT00M00.00S'
                        or game['gameBreakStatus'] != '' or game['gameSubtype'] != ''
                        or game['ifNecessary'] is not False):
                    raise ValueError('Unsupported NBA regulation-final status')
                tip = page._utc(game['gameTimeUtc'])
                started = page._utc(game['actualStartTimeUTC'])
                ended = page._utc(game['actualEndTimeUTC'])
                if tip.astimezone(page.EASTERN).date() != day or not tip <= started < ended <= observed:
                    raise ValueError('NBA final source time/date disagreement')
                sides = {}
                for side in ('home', 'away'):
                    team = game[side+'Team']; tid = team['teamId']; tri = team['teamTricode']
                    if (type(tid) is not int or tid not in page.TEAMS or page.TEAMS[tid] != tri
                            or tid in seen_teams or type(team['score']) is not int or team['score'] < 0):
                        raise ValueError('NBA final franchise/side/score identity mismatch')
                    periods = team['periods']
                    if (not isinstance(periods, list) or len(periods) != 4
                            or any(type(p['period']) is not int or p['period'] != i
                                   or type(p['score']) is not int or p['score'] < 0
                                   for i, p in enumerate(periods, 1))
                            or sum(p['score'] for p in periods) != team['score']):
                        raise ValueError('NBA final period scores disagree with total')
                    seen_teams.add(tid); sides[side] = (tid, tri, team['score'])
                if sides['home'][2] == sides['away'][2]:
                    raise ValueError('Tied NBA final is unsupported')
                games.append({'nba_game_id': identifier, 'kind': 'regular',
                    'home_team_id': sides['home'][0], 'home_tricode': sides['home'][1],
                    'away_team_id': sides['away'][0], 'away_tricode': sides['away'][1],
                    'tipoff_utc': tip.isoformat(), 'nba_status': 3,
                    'nba_postponed_status': None,
                    'nba_home_score': sides['home'][2], 'nba_away_score': sides['away'][2],
                    'source_reported_actual_start_utc': started.isoformat(),
                    'source_reported_actual_end_utc': ended.isoformat()})
        if len(games) != expected: raise ValueError('NBA final cards disagree with calendar count')
    except (KeyError, TypeError, AttributeError, RecursionError) as error:
        raise ValueError('Malformed NBA final card shape') from error
    return {'schema': 'tyler-nba-owned-daily-regulation-final-page-v1',
        'requested_date': requested_date, 'season': season,
        'observed_at_utc': observed.isoformat(), 'original_body_sha256': hashlib.sha256(raw).hexdigest(),
        'daily_game_count': len(games), 'games': sorted(games, key=lambda g: g['nba_game_id']),
        'source_scope': 'ONE_REQUESTED_EASTERN_DATE_REGULATION_FINALS_ONLY',
        'full_season_schedule_verified': False, 'official_final_results_verified': False,
        'actual_tipoff_time_attested': False, 'source_origin_independently_attested': False,
        'receipt_clock_independently_attested': False, 'collector_fallback_enabled': False,
        'settlement_enabled': False, 'historical_evaluation_enabled': False,
        'feature_collection_enabled': False, 'forecasting_enabled': False,
        'model_training_enabled': False, 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


def parse(raw, *, requested_date, season, observed_at):
    """Original v1 final reader, including its strict true-envelope contract."""
    return _parse(raw, requested_date=requested_date, season=season,
                  observed_at=observed_at, document_reader=page.document)


def replay_reference(base=Path('.')):
    root = Path(base)/FIXTURE_ROOT
    manifest_path = archive_path(root/'manifest.json')
    if manifest_path.stat().st_size > 1_000_000:
        raise ValueError('Oversized NBA final fixture manifest')
    manifest_raw = manifest_path.read_bytes()
    if hashlib.sha256(manifest_raw).hexdigest() != FIXTURE_MANIFEST_SHA256:
        raise ValueError('NBA reference final diagnostic manifest changed')
    manifest = json.loads(manifest_raw)
    blob = archive_path(root/manifest['repository_archive_file'])
    if blob.stat().st_size > page.MAX_BYTES: raise ValueError('Oversized NBA final archive')
    raw = bounded_gzip_read(blob.read_bytes(), page.MAX_BYTES)
    if (len(raw) != manifest['response_body_bytes']
            or hashlib.sha256(raw).hexdigest() != manifest['response_body_sha256']):
        raise ValueError('NBA reference final response binding disagrees')
    result = parse(raw, requested_date='2026-04-10', season='2025-26',
                   observed_at=datetime.fromisoformat(manifest['probe_started_at_utc']))
    return {**result, 'fresh_source_observation': False,
        'reference_fixture_only': True, 'available_at_historical_pregame_freeze': False,
        'fixture_manifest_sha256': FIXTURE_MANIFEST_SHA256,
        'diagnostic_workflow_run_id': manifest['workflow_run_id']}


if __name__ == '__main__':
    print(json.dumps(replay_reference(), sort_keys=True, indent=2))
