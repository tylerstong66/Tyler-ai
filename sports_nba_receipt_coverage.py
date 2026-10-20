"""Read-only NBA v2 receipt inventory: distinct games, not repeated predictions.

Strictly replays archived original NBA/ESPN observations before counting
sources. Neither a captured schedule nor a final-page card constitutes a
prospectively enrolled model prediction or an independently attested result.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import sports_nba_owned_daily_observation_v2 as pregame
import sports_nba_postgame_observation_v2 as postgame
from sports_expansion_audit import archive_path, MAX_BLOB_SIZE

VERSION = 'nba-distinct-native-v2-receipt-coverage-v1'
MAX_RECEIPTS = 256


def _manifests(base, root):
    folder = base / root
    archive_path(folder, directory=True, allow_missing=True)
    if not folder.exists():
        return []
    children = sorted(folder.iterdir())
    if len(children) > MAX_RECEIPTS:
        raise ValueError('Unbounded native NBA receipt inventory')
    output = []
    for child in children:
        archive_path(child, directory=True)
        file = archive_path(child / 'manifest.json')
        if file.stat().st_size > MAX_BLOB_SIZE:
            raise ValueError('Oversized native NBA receipt')
        raw = file.read_bytes()
        obj = json.loads(raw)
        if (not isinstance(obj, dict) or obj.get('NO_BET') is not True
                or type(obj.get('actual_wagers')) is not int or obj['actual_wagers'] != 0
                or obj.get('forecasting_enabled') is not False
                or obj.get('model_training_enabled') is not False
                or obj.get('promotion_allowed') is not False
                or (obj.get('source_scope_complete') is not False if root == pregame.ROOT
                    else obj.get('source_scope_complete', False) is not False)):
            raise ValueError('Unsafe or malformed native NBA receipt')
        output.append((child.name, hashlib.sha256(raw).hexdigest(), obj))
    return output


def audit(base=Path('.')):
    """Replay original archived pages, then count game identities by source day."""
    base = Path(base)
    before = pregame.replay_all(base)
    after = postgame.replay_all(base)
    starts = _manifests(base, pregame.ROOT)
    finals = _manifests(base, postgame.ROOT)
    if (before['receipts_replayed'] != len(starts) or
            after['receipts_replayed'] != len(finals) or
            any(row.get('source_replay_verified') is not True for row in before['reports']) or
            any(row.get('source_bytes_replayed') is not True for row in after['reports'])):
        raise ValueError('Archived native NBA source replay count disagrees with inventory')

    by_day = defaultdict(lambda: {'captures': 0, 'observations': 0, 'game_ids': set()})
    game_claims = defaultdict(set)
    # Keep original team identity and scheduled-start claims for a separate
    # pregame-versus-postgame source comparison. These are not predictions.
    pregame_native_claims = defaultdict(set)
    pregame_observations = 0
    for stamp, digest, source in starts:
        if source.get('schema') != pregame.PROTOCOL.schema:
            raise ValueError('Unexpected native NBA pregame schema')
        rows = source['matched']
        parsed = source['parsed_daily_page']
        if (not isinstance(rows, list) or
                source['strict_pregame_correlated'] != len(rows) or
                source['withheld'] != [] or
                parsed['daily_game_count'] != len(rows) or
                parsed['requested_date'] != source['requested_date']):
            raise ValueError('Incomplete or inconsistent native pregame receipt')
        day = source['requested_date']
        native_games = parsed.get('games')
        if (not isinstance(native_games, list) or len(native_games) != len(rows)
                or len({g['nba_game_id'] for g in native_games}) != len(rows)
                or {g['nba_game_id'] for g in native_games}
                   != {r['nba_official_game_id'] for r in rows}):
            raise ValueError('Pregame matched IDs disagree with replayed native page')
        native_by_id = {g['nba_game_id']: g for g in native_games}
        seen = set()
        for row in rows:
            game = row['nba_official_game_id']
            provider = row['espn_game_id']
            if (not isinstance(game, str) or not game.isdigit() or
                    not isinstance(provider, str) or not provider.isdigit() or game in seen):
                raise ValueError('Invalid or repeated game within one pregame receipt')
            seen.add(game)
            native = native_by_id[game]
            if native['tipoff_utc'] != row['nba_tipoff_utc']:
                raise ValueError('Native game start differs from matched source claim')
            game_claims[game].add((day, provider, row['nba_tipoff_utc'], row['espn_saved_tipoff_utc']))
            pregame_native_claims[game].add((
                native['home_team_id'], native['away_team_id'],
                native['home_tricode'], native['away_tricode'], native['kind'],
                native['tipoff_utc'], day))
            by_day[day]['game_ids'].add(game)
        by_day[day]['captures'] += 1
        by_day[day]['observations'] += len(rows)
        pregame_observations += len(rows)

    post_days = defaultdict(lambda: {'captures': 0, 'supported_final_page_game_claims': 0, 'game_ids': set(), 'empty_or_unsupported': 0})
    postgame_observations = 0
    # Repeated postgame captures are observations of source claims, not
    # separate outcomes. Record contradictory original page claims for review
    # instead of silently choosing the last or most favorable score.
    post_claims = defaultdict(lambda: {'identity': set(), 'schedule': set(), 'result': set(), 'dates': set()})
    for stamp, digest, source in finals:
        if source.get('schema') != postgame.PROTOCOL.schema:
            raise ValueError('Unexpected native NBA postgame schema')
        day = source['requested_date']
        parsed = source.get('parsed_final_page')
        games = parsed['games'] if parsed is not None else []
        if (not isinstance(games, list) or
                type(source.get('supported_final_game_count')) is not int or
                source['supported_final_game_count'] != len(games)):
            raise ValueError('Inconsistent native postgame source counts')
        if len({g['nba_game_id'] for g in games}) != len(games):
            raise ValueError('Repeated native NBA postgame game ID')
        for game in games:
            claim = post_claims[game['nba_game_id']]
            claim['identity'].add(tuple(game.get(field) for field in (
                'home_team_id', 'away_team_id', 'home_tricode', 'away_tricode', 'kind')))
            claim['schedule'].add(tuple(game.get(field) for field in (
                'tipoff_utc', 'source_reported_actual_start_utc',
                'source_reported_actual_end_utc')))
            claim['result'].add(tuple(game.get(field) for field in (
                'nba_home_score', 'nba_away_score', 'nba_status')))
            claim['dates'].add(day)
        post_days[day]['captures'] += 1
        post_days[day]['supported_final_page_game_claims'] += len(games)
        post_days[day]['game_ids'].update(g['nba_game_id'] for g in games)
        if not games:
            post_days[day]['empty_or_unsupported'] += 1
        postgame_observations += len(games)

    def pack(items, observation_key):
        return {date: {'capture_count': row['captures'],
                       'captured_game_observations': row[observation_key],
                       'distinct_game_ids': len(row['game_ids']),
                       'repeat_observations_not_new_games': row[observation_key] - len(row['game_ids']),
                       **({'empty_or_unsupported_captures': row['empty_or_unsupported']}
                          if 'empty_or_unsupported' in row else {})}
                for date, row in sorted(items.items())}

    identity_conflicts = sorted(game for game, claims in game_claims.items()
                                if len({(claim[1], claim[2], claim[3]) for claim in claims}) != 1
                                or len({claim[0] for claim in claims}) != 1)
    unique_pregame = len(game_claims)
    unique_post = len(set.union(*(row['game_ids'] for row in post_days.values()))
                      if post_days else set())
    # A shared NBA game ID is only a source-level observation. Compare exact
    # identities and starts without automatically resolving schedule revisions
    # or asserting independently corroborated outcomes.
    shared = sorted(set(pregame_native_claims) & set(post_claims))
    cross_identity_conflicts = sorted(
        game for game in shared
        if {row[:5] for row in pregame_native_claims[game]}
           != post_claims[game]['identity'])
    cross_start_drifts = sorted(
        game for game in shared
        if {row[5] for row in pregame_native_claims[game]}
           != {row[0] for row in post_claims[game]['schedule']})
    cross_date_drifts = sorted(
        game for game in shared
        if {row[6] for row in pregame_native_claims[game]}
           != post_claims[game]['dates'])
    unresolved = (set(identity_conflicts) | set(cross_identity_conflicts) |
                  set(cross_start_drifts) | set(cross_date_drifts) |
                  {game for game in shared if
                   len(post_claims[game]['identity']) != 1 or
                   len(post_claims[game]['schedule']) != 1 or
                   len(post_claims[game]['result']) != 1 or
                   len(post_claims[game]['dates']) != 1})
    return {'schema': VERSION, 'NO_BET': True, 'actual_wagers': 0,
            'pregame_receipts_replayed': len(starts),
            'pregame_distinct_game_ids': unique_pregame,
            'pregame_game_observations': pregame_observations,
            'pregame_repeat_observations': pregame_observations - unique_pregame,
            'pregame_days': pack(by_day, 'observations'),
            'pregame_game_id_schedule_or_provider_conflicts': identity_conflicts,
            'postgame_receipts_replayed': len(finals),
            'postgame_source_game_claims': postgame_observations,
            'postgame_distinct_game_ids': unique_post,
            'postgame_repeat_claims_not_new_games': postgame_observations - unique_post,
            'postgame_days': pack(post_days, 'supported_final_page_game_claims'),
            'postgame_conflicting_identity_game_ids': sorted(
                game for game, claim in post_claims.items() if len(claim['identity']) > 1),
            'postgame_conflicting_schedule_game_ids': sorted(
                game for game, claim in post_claims.items()
                if len(claim['schedule']) > 1 or len(claim['dates']) > 1),
            'postgame_conflicting_result_game_ids': sorted(
                game for game, claim in post_claims.items() if len(claim['result']) > 1),
            'cross_phase_shared_source_game_ids': shared,
            'cross_phase_shared_source_games': len(shared),
            'cross_phase_conflicting_team_identity_game_ids': cross_identity_conflicts,
            'cross_phase_changed_scheduled_start_game_ids': cross_start_drifts,
            'cross_phase_changed_requested_date_game_ids': cross_date_drifts,
            'cross_phase_source_only_consistent_game_ids': sorted(set(shared) - unresolved),
            'cross_phase_source_only_consistency_is_not_verified_result': True,
            'prospective_winner_predictions_enrolled_by_this_audit': 0,
            'independently_corroborated_final_results': 0,
            'prediction_accuracy_computed': False, 'forecasting_enabled': False,
            'model_training_enabled': False, 'promotion_allowed': False,
            'not_proof_of_complete_schedule': True,
            'limitation': 'Retained native v2 receipt dates only. Repeated observations are not new games. '
                          'Reported conflicts require source review, never automatic forecast edits. '
                          'Disagreeing repeated final-source claims are flagged without resolution or enrollment. '
                          'Cross-phase matching is source-only; schedule drift is flagged, not adjudicated. '
                          'Postgame page claims are not independently verified finals. '
                          'No model selection, retrospective grade, promotion or wagers.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path('.'))
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    report = audit(args.base)
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
