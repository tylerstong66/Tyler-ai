"""Read-only pending hitter/final-source identity diagnostic; never settlement."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json

import requests
from sports_expansion_audit import archive_path
from sports_mlb_prop_prospective import _verify, SPORTS_VERSION, MODEL_NAME
from sports_mlb_sources import OfficialMlbReader, positive_id, utc

DEFAULT_ROOT = Path('benchmarks/mlb_hitter_props_shadow_v1')


def _read(path):
    path = archive_path(path)
    if not path.is_file() or path.stat().st_size > 3_000_000:
        raise ValueError('Invalid bounded MLB diagnostic input')
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def audit(root=DEFAULT_ROOT, *, reader=None, max_games=12):
    """Preflight all originals, then observe at most twelve unique pending games.

    New source observations cannot certify the original forecast's identity or
    historical source availability. Conflicts are diagnostic rows, never labels.
    Existing predictions and settlements are read but never changed.
    """
    if type(max_games) is not int or not 1 <= max_games <= 12:
        raise ValueError('One to twelve official game observations required')
    root = archive_path(root, directory=True)
    predictions = archive_path(root/'predictions', directory=True, allow_missing=True)
    settlements = archive_path(root/'settlements', directory=True, allow_missing=True)
    paths = sorted(predictions.glob('*.json')) if predictions.exists() else []
    if len(paths) > 30000:
        raise ValueError('Unbounded frozen MLB inventory')
    pending = []
    for path in paths:
        record, digest = _read(path); core = _verify(record)
        game = positive_id(core.get('game_id'), 'game_id')
        hitter = positive_id(core.get('hitter_id'), 'hitter_id')
        side = core.get('hitter_side')
        if (path.name != f'{game}_{hitter}.json' or side not in ('home', 'away')
                or core.get('schema') != SPORTS_VERSION or core.get('model') != MODEL_NAME
                or core.get('status') != 'IMMUTABLE_PREGAME_SHADOW_NO_BET'
                or core.get('model_calibrated') is not False
                or core.get('sportsbook_wager_eligible') is not False
                or type(core.get('actual_wager')) is not int or core['actual_wager'] != 0
                or not utc(core['source_capture_started_at_utc']) <= utc(core['frozen_at_utc']) < utc(core['event_start_utc'])):
            raise ValueError('Invalid frozen MLB diagnostic scope')
        team = positive_id(core.get('hitter_team_id'), 'team')
        opponent = positive_id(core.get('opponent_team_id'), 'opponent')
        if team == opponent:
            raise ValueError('Duplicate frozen MLB teams')
        target = archive_path(settlements/path.name, allow_missing=True)
        if target.exists():
            previous, _ = _read(target); sealed = _verify(previous)
            if (sealed.get('game_id') != game or sealed.get('hitter_id') != hitter
                    or sealed.get('prediction_digest_sha256') != record['record_digest_sha256']):
                raise ValueError('Invalid existing MLB settlement link')
            continue
        pending.append((path, core, digest, record['record_digest_sha256']))
    reader = reader or OfficialMlbReader()
    now = utc(reader.clock())
    games = sorted({core['game_id'] for _, core, _, _ in pending
                    if utc(core['event_start_utc']) < now})
    observations = {}
    for game in games[:max_games]:
        try:
            data, receipt = reader.load(f'game/{game}/feed/live', api_version='v1.1')
            gd = data.get('gameData', {})
            observations[game] = {'game_id': positive_id(data.get('gamePk'), 'official game'),
                'home_id': positive_id(gd.get('teams', {}).get('home', {}).get('id'), 'official home'),
                'away_id': positive_id(gd.get('teams', {}).get('away', {}).get('id'), 'official away'),
                'start_utc': utc(gd.get('datetime', {}).get('dateTime')).isoformat(),
                'strict_final_state': gd.get('status', {}).get('abstractGameState') == 'Final'
                    and gd.get('status', {}).get('detailedState') == 'Final',
                'source_receipt': receipt}
        except (requests.RequestException, RuntimeError) as error:
            observations[game] = {'error_type': type(error).__name__}
    rows = []
    for path, core, digest, seal in pending:
        game = core['game_id']; observed = observations.get(game)
        row = {'file': path.name, 'file_sha256': digest, 'record_digest_sha256': seal,
               'game_id': game, 'hitter_id': core['hitter_id'],
               'frozen_start_utc': core['event_start_utc'],
               'frozen_home_id': core['hitter_team_id'] if core['hitter_side'] == 'home' else core['opponent_team_id'],
               'frozen_away_id': core['hitter_team_id'] if core['hitter_side'] == 'away' else core['opponent_team_id'],
               'conflicts': [], 'official_observation': observed}
        if utc(core['event_start_utc']) >= now:
            row['status'] = 'FUTURE_SAVED_START_NOT_OBSERVED'
        elif observed is None:
            row['status'] = 'DEFERRED_GAME_BUDGET'
        elif 'error_type' in observed:
            row['status'] = 'SOURCE_UNAVAILABLE'
        else:
            for field, expected in [('game_id', game), ('home_id', row['frozen_home_id']),
                                    ('away_id', row['frozen_away_id'])]:
                if observed[field] != expected:
                    row['conflicts'].append(field)
            row['start_difference_seconds'] = (utc(observed['start_utc']) - utc(core['event_start_utc'])).total_seconds()
            if row['start_difference_seconds'] != 0:
                row['conflicts'].append('scheduled_start')
            row['status'] = ('SOURCE_IDENTITY_OR_START_CONFLICT' if row['conflicts'] else
                             'IDENTITY_MATCH_ONLY_NOT_SETTLEMENT' if observed['strict_final_state'] else
                             'NOT_STRICT_FINAL')
        rows.append(row)
    return {'schema': 'tyler-mlb-pending-final-source-audit-v1',
            'audit_started_at_utc': now.isoformat(),
            'observed_at_utc': utc(reader.clock()).isoformat(), 'pending_records': len(rows),
            'unique_eligible_games': len(games), 'attempted_unique_games': len(observations),
            'deferred_unique_games': max(0, len(games)-max_games),
            'conflicting_records': sum(bool(r['conflicts']) for r in rows), 'records': rows,
            'read_only_diagnostic': True, 'original_source_availability_verified': False,
            'settlement_enabled': False, 'forecast_rewrite_allowed': False,
            'model_training_enabled': False, 'NO_BET': True, 'actual_wagers': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observe', action='store_true')
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--output-dir', type=Path, default=Path('mlb-final-source-audit'))
    args = parser.parse_args()
    if not args.observe:
        print(json.dumps({'observation_requested': False, 'settlement_enabled': False, 'NO_BET': True}))
        return
    output = archive_path(args.output_dir, directory=True, allow_missing=True)
    output.mkdir(parents=True, exist_ok=False)
    reader = OfficialMlbReader(archive_dir=output/'source_archives')
    report = audit(args.root, reader=reader)
    (output/'report.json').write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'records'}, sort_keys=True))


if __name__ == '__main__': main()
