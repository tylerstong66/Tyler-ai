"""Read-only identity and schedule drift across independently frozen MLB cohorts."""
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import hashlib
import json
import re

import sports_benchmark_review as review
import sports_mlb_prop_prospective as props
import sports_mlb_source_archives as archives
from sports_mlb_sources import positive_id, utc

TEAM_ROOT = Path('benchmarks/two_way_prospective/mlb')
HITTER_ROOT = Path('benchmarks/mlb_hitter_props_shadow_v1')
HEX = re.compile(r'[0-9a-f]{64}')


def _read(path, limit=3_000_000):
    if path.is_symlink() or path.parent.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError('Missing or invalid bounded cohort input')
    raw = path.read_bytes()
    return raw, json.loads(raw)


def _digest(value):
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise ValueError('Missing original source digest')
    return value


def _id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[1-9][0-9]*', value):
        raise ValueError('Invalid official MLB cohort ID')
    return int(value)


def _team(path, base):
    raw, row = _read(path)
    if row.get('sha256') != review.digest({k: v for k, v in row.items() if k != 'sha256'}):
        raise ValueError('Team-winner forecast digest mismatch')
    game = _id(row['game_id']); home = _id(row['home_id']); away = _id(row['away_id'])
    if (path.name != str(game)+'.json' or row.get('sport') != 'MLB' or home == away
            or row.get('NO_BET') is not True or type(row.get('actual_wagers')) is not int
            or row['actual_wagers'] != 0
            or not utc(row['generated_at']) <= utc(row['recorded_at']) < utc(row['kickoff'])):
        raise ValueError('Invalid original team-winner identity, chronology or no-bet guard')
    evidence = []; official = []; provider = []
    for receipt in row['source_snapshots']:
        at = utc(receipt['retrieved_at'])
        if at > utc(row['generated_at']):
            raise ValueError('Team source follows original generation')
        digest = _digest(receipt['sha256'])
        expected = (TEAM_ROOT/'snapshots'/(digest+'.json')).as_posix()
        if receipt['path'] != expected:
            raise ValueError('Unexpected team source snapshot path')
        content, data = _read(base/expected)
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError('Original reduced team source bytes changed')
        uri = urlparse(receipt['source_url'])
        if uri.scheme != 'https' or uri.username or uri.password or uri.fragment:
            raise ValueError('Invalid original team source origin')
        kind = 'REDUCED_OTHER_SOURCE'
        if uri.netloc == 'statsapi.mlb.com' and uri.path == '/api/v1/schedule':
            kind = 'REDUCED_OFFICIAL_SCHEDULE'
            if not isinstance(data, list): raise ValueError('Malformed original official schedule')
            official += [item for item in data if item.get('game_id') == row['game_id']]
        elif uri.netloc == 'site.api.espn.com' and uri.path == '/apis/site/v2/sports/baseball/mlb/scoreboard':
            kind = 'REDUCED_ESPN_SCHEDULE'
            if not isinstance(data, list): raise ValueError('Malformed original ESPN schedule')
            provider += [item for item in data if item.get('event_id') == row['event_id']]
        elif uri.netloc != 'statsapi.mlb.com' or not re.fullmatch(r'/api/v1\.1/game/[1-9][0-9]*/feed/live', uri.path):
            raise ValueError('Unrecognized original team source endpoint')
        evidence.append({'path': expected, 'snapshot_sha256': digest,
                         'original_response_sha256_digest_only': _digest(receipt['response_sha256']),
                         'source_url': receipt['source_url'], 'retrieved_at_utc': at.isoformat(), 'kind': kind})
    if not official or not provider:
        raise ValueError('Original target lacks retained official/ESPN schedule claims')
    for claim in official:
        if (claim.get('home_id') != row['home_id'] or claim.get('away_id') != row['away_id']
                or utc(claim['kickoff']) != utc(row['kickoff'])
                or claim.get('state') != 'pre' or claim.get('completed') is not False):
            raise ValueError('Original official schedule disagrees with frozen team forecast')
    for claim in provider:
        if (any(claim.get(k) != row[k] for k in ('home', 'away'))
                or utc(claim['kickoff']) != utc(row['kickoff'])
                or claim.get('state') != 'pre' or claim.get('completed') is not False):
            raise ValueError('Original ESPN schedule disagrees with frozen team forecast')
    return row, {'file_sha256': hashlib.sha256(raw).hexdigest(), 'record_digest_sha256': row['sha256'],
                 'frozen_at_utc': row['recorded_at'], 'generated_at_utc': row['generated_at'],
                 'saved_start_utc': row['kickoff'], 'reduced_source_snapshots_verified': evidence,
                 'original_response_bytes_replayed': False, 'independent_publication_time_attested': False}


def _hitter(path, base):
    raw, saved = _read(path); row = props._verify(saved)
    game = positive_id(row['game_id'], 'game_id'); hitter = positive_id(row['hitter_id'], 'hitter_id')
    home_side = row['hitter_side']
    if (path.name != str(game)+'_'+str(hitter)+'.json' or row.get('schema') != props.SPORTS_VERSION
            or row.get('model') != props.MODEL_NAME or home_side not in ('home', 'away')
            or row.get('status') != 'IMMUTABLE_PREGAME_SHADOW_NO_BET'
            or row.get('sportsbook_wager_eligible') is not False or row.get('model_calibrated') is not False
            or type(row.get('actual_wager')) is not int or row['actual_wager'] != 0
            or not utc(row['source_capture_started_at_utc']) <= utc(row['frozen_at_utc']) < utc(row['event_start_utc'])):
        raise ValueError('Invalid original hitter identity, chronology or no-bet guard')
    team = positive_id(row['hitter_team_id'], 'hitter_team_id')
    opponent = positive_id(row['opponent_team_id'], 'opponent_team_id')
    if team == opponent: raise ValueError('Hitter team/opponent collision')
    receipts = row['source_receipts']; evidence = []; pregame = None; log_seasons = []
    if not isinstance(receipts.get('hitter_game_logs'), list) or len(receipts['hitter_game_logs']) != 2:
        raise ValueError('Original hitter log season receipts missing')
    for kind, receipt in [('pregame_game', receipts['pregame_game']), ('active_roster', receipts['active_roster'])] + [
            ('hitter_game_logs', r) for r in receipts['hitter_game_logs']]:
        uri = urlparse(receipt['source_url']); at = utc(receipt['retrieved_at'])
        if (uri.scheme != 'https' or uri.netloc != 'statsapi.mlb.com' or uri.fragment
                or not utc(row['source_capture_started_at_utc']) <= at <= utc(row['frozen_at_utc'])
                or utc(receipt['data_through']) != at):
            raise ValueError('Invalid original hitter source origin or chronology')
        if kind == 'pregame_game' and (uri.path != '/api/v1.1/game/'+str(game)+'/feed/live' or uri.query):
            raise ValueError('Hitter game source differs from frozen official ID')
        query = parse_qs(uri.query)
        if kind == 'active_roster':
            expected_query = {'rosterType': ['active'], 'date': [utc(row['event_start_utc']).astimezone(props.EASTERN).date().isoformat()]}
            if uri.path != '/api/v1/teams/'+str(team)+'/roster' or query != expected_query:
                raise ValueError('Hitter roster source differs from frozen team/date')
        elif kind == 'hitter_game_logs':
            year = query.get('season', [''])[0]
            if (uri.path != '/api/v1/people/'+str(hitter)+'/stats'
                    or year not in {str(utc(row['event_start_utc']).year-1), str(utc(row['event_start_utc']).year)}
                    or query != {'stats': ['gameLog'], 'group': ['hitting'], 'gameType': ['R'], 'season': [year]}):
                raise ValueError('Hitter history receipt differs from frozen player/seasons')
            log_seasons.append(year)
        digest = _digest(receipt['response_sha256'])
        status = 'LEGACY_DIGEST_ONLY_UNREPLAYABLE'
        if 'original_response_archive_schema' in receipt:
            data = archives.verify(base/HITTER_ROOT/'source_archives', receipt)
            status = 'ORIGINAL_RESPONSE_BYTES_REPLAYED'
            if kind == 'pregame_game': pregame = data
        evidence.append({'kind': kind, 'source_url': receipt['source_url'],
                         'retrieved_at_utc': at.isoformat(), 'response_sha256': digest,
                         'source_replay_status': status,
                         'original_response_sha256': receipt.get('original_response_sha256'),
                         'source_archive_file': receipt.get('source_archive_file')})
    if len(set(log_seasons)) != 2:
        raise ValueError('Duplicate original hitter log season')
    if pregame is not None:
        gd = pregame.get('gameData', {}); sides = gd.get('teams', {})
        other = 'away' if home_side == 'home' else 'home'
        if (pregame.get('gamePk') != game or gd.get('status', {}).get('abstractGameState') != 'Preview'
                or gd.get('status', {}).get('detailedState') not in ('Scheduled', 'Pre-Game')
                or utc(gd['datetime']['dateTime']) != utc(row['event_start_utc'])
                or sides.get(home_side, {}).get('id') != team or sides.get(other, {}).get('id') != opponent):
            raise ValueError('Original MLB pregame response differs from sealed hitter identity')
    return row, {'file_sha256': hashlib.sha256(raw).hexdigest(), 'record_digest_sha256': saved['record_digest_sha256'],
                 'frozen_at_utc': row['frozen_at_utc'], 'saved_start_utc': row['event_start_utc'],
                 'source_receipts': evidence, 'original_pregame_response_replayed': pregame is not None,
                 'all_original_responses_replayed': all(e['source_replay_status'] == 'ORIGINAL_RESPONSE_BYTES_REPLAYED' for e in evidence),
                 'independent_publication_time_attested': False}


def build(base=Path('.')):
    base = Path(base)
    teams = {}; hitters = defaultdict(list)
    team_paths = sorted((base/TEAM_ROOT/'predictions').glob('*.json'))
    hitter_paths = sorted((base/HITTER_ROOT/'predictions').glob('*.json'))
    if not team_paths or not hitter_paths or max(len(team_paths), len(hitter_paths)) > 30000:
        raise ValueError('Missing or oversized original MLB cohorts')
    for path in team_paths:
        row, proof = _team(path, base); key = int(row['game_id'])
        if key in teams: raise ValueError('Duplicate original team game')
        teams[key] = (row, proof, path.relative_to(base).as_posix())
    for path in hitter_paths:
        row, proof = _hitter(path, base)
        hitters[row['game_id']].append((row, proof, path.relative_to(base).as_posix()))
    comparisons = []
    for game in sorted(set(teams) & set(hitters)):
        team, team_proof, team_path = teams[game]
        for hitter, hitter_proof, hitter_path in hitters[game]:
            expected = int(team[hitter['hitter_side']+'_id'])
            opposite = 'away' if hitter['hitter_side'] == 'home' else 'home'
            if hitter['hitter_team_id'] != expected or hitter['opponent_team_id'] != int(team[opposite+'_id']):
                raise ValueError('Cross-cohort game ID has inconsistent team identities')
            shift = (utc(hitter['event_start_utc']) - utc(team['kickoff'])).total_seconds()/60
            comparisons.append({'game_id': game, 'hitter_id': hitter['hitter_id'],
                'home_team_id': int(team['home_id']), 'away_team_id': int(team['away_id']),
                'team_forecast_path': team_path, 'hitter_forecast_path': hitter_path,
                'hitter_minus_team_saved_start_minutes': shift,
                'saved_start_differs': shift != 0, 'same_contemporaneous_forecast': False,
                'team_cohort': team_proof, 'hitter_cohort': hitter_proof,
                'original_source_validation_complete': False,
                'unresolved': ['TEAM_REDUCED_SNAPSHOTS_DO_NOT_REPLAY_ORIGINAL_RESPONSES'] + (
                    [] if hitter_proof['all_original_responses_replayed'] else ['HITTER_LEGACY_SOURCE_BYTES_UNAVAILABLE']) +
                    ['INDEPENDENT_PUBLICATION_TIMES_NOT_ATTESTED']})
    return {'schema': 'tyler-mlb-independent-cohort-schedule-audit-v1',
            'overlapping_official_games': len(set(teams) & set(hitters)), 'player_game_comparisons': len(comparisons),
            'saved_start_drift_comparisons': sum(r['saved_start_differs'] for r in comparisons),
            'comparisons': comparisons, 'original_records_modified': False,
            'joint_performance_comparison_enabled': False, 'prediction_scores_combined': False,
            'new_forecasts_created': 0, 'forecasting_enabled': False, 'model_training_enabled': False,
            'historical_evaluation_enabled': False, 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


if __name__ == '__main__':
    print(json.dumps(build(), sort_keys=True, indent=2))
