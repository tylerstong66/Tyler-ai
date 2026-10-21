"""Explicit native-daily NBA feature protocol; append-only observations, no model use."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re

import sports_nba_pregame_features as reference_features
import sports_nba_feature_cohort as provider_reader
import sports_nba_owned_daily_observation_v2 as receipts
from sports_expansion_audit import archive_path

ROOT = Path('benchmarks/nba_native_pregame_features_v2/records')
PROTOCOL = {
    'schema': 'nba-native-daily-reference-feature-protocol-v2',
    'target_season': '2026-27', 'reference_season': '2025-26',
    'source_receipt_schema': receipts.PROTOCOL.schema,
    'reference_feature_protocol_sha256': reference_features.PROTOCOL_SHA256,
    'reference_games_per_team': 10, 'maximum_source_age_hours': 12,
    'source_scope': 'ONE_REQUESTED_EASTERN_DATE_ONLY_EXACT_COMPLETE_PREGAME_AGREEMENT',
    'reference_scope': 'LAST_TEN_CORROBORATED_PREVIOUS_SEASON_RESULTS_AVAILABLE_AT_FREEZE',
    'not_a_prediction': True, 'prior_season_roster_changes_not_modeled': True,
    'original_v1_features_unchanged': True,
}
PROTOCOL_SHA256 = 'a265a5ab457318d7bcee4304698c3238c6fa0af8e9fec10506b0daf3ee7e7746'
source = reference_features.source
digest = reference_features.digest


def _clock(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Aware native NBA feature clock required')
    return value.astimezone(timezone.utc)


def _reference(base, now):
    path = archive_path(base/ROOT.parent/'protocol.json')
    if (not path.is_file() or path.stat().st_size > 1_000_000
            or digest(PROTOCOL) != PROTOCOL_SHA256
            or hashlib.sha256(path.read_bytes()).hexdigest() != PROTOCOL_SHA256):
        raise ValueError('Native NBA feature protocol differs from frozen recipe')
    return reference_features._reference(base, now)


def _snapshot(base, stamp, now):
    receipts.replay(base, stamp, now=now)
    path = archive_path(base/receipts.ROOT/stamp/'manifest.json')
    if not path.is_file() or path.stat().st_size > 512_000:
        raise ValueError('Oversized native NBA feature source manifest')
    raw = path.read_bytes(); manifest = json.loads(raw)
    if manifest['season'] != PROTOCOL['target_season']:
        raise ValueError('Unsupported native NBA feature target season')
    provider_path = archive_path(base/provider_reader.source.ROOT/'captures'/
                                 manifest['espn_capture']/'manifest.json')
    provider_manifest, provider, provider_hash = provider_reader._provider(base, provider_path, now)
    if provider_hash != manifest['espn_manifest_sha256']:
        raise ValueError('Native NBA feature linked provider digest mismatch')
    receipts.replay(base, stamp, now=now)
    if path.read_bytes() != raw:
        raise ValueError('Native NBA feature source changed during replay')
    return {'stamp': stamp, 'manifest': manifest, 'manifest_sha256': hashlib.sha256(raw).hexdigest(),
            'provider_manifest': provider_manifest, 'provider': provider,
            'official': {r['nba_game_id']: r for r in manifest['parsed_daily_page']['games']}}


def _record(snapshot, matched, reference, freeze):
    m = snapshot['manifest']; n = snapshot['official'][matched['nba_official_game_id']]
    e = snapshot['provider'][matched['espn_game_id']]
    nt = source.utc(m['recorded_at_utc']); et = source.utc(snapshot['provider_manifest']['recorded_at_utc'])
    starts = [source.utc(n['tipoff_utc']), source.utc(e['scheduled_start_utc'])]
    if (len([r for r in m['matched'] if r['nba_official_game_id'] == n['nba_game_id']]) != 1
            or starts[0] != starts[1]
            or any(n[side+'_tricode'] != e[side+'_tricode'] for side in ('home', 'away'))):
        raise ValueError('Native NBA feature target lacks unique exact source agreement')
    if (n['kind'] != 'regular' or type(n['nba_status']) is not int or n['nba_status'] != 1 or e['season_stage'] != 2
            or e['provider_completed'] is not False or e['state'] != 'pre'):
        raise reference_features.IneligibleSourceGame('BOTH_NATIVE_SOURCES_NOT_REGULAR_PREGAME')
    if freeze >= min(starts):
        raise reference_features.IneligibleSourceGame('NATIVE_SAVED_START_ALREADY_REACHED')
    if max(nt, et) > freeze or min(starts) <= max(nt, et):
        raise ValueError('Native feature source/freeze chronology mismatch')
    if any(freeze-at > timedelta(hours=PROTOCOL['maximum_source_age_hours']) for at in (nt, et)):
        raise reference_features.IneligibleSourceGame('NATIVE_SCHEDULE_SOURCE_TOO_OLD_AT_FREEZE')
    summaries = {}
    for side in ('home', 'away'):
        team = n[side+'_tricode']; eligible = []
        for row in reference['corroborated_research_only']:
            if team not in (row['home_tricode'], row['away_tricode']): continue
            at = source.utc(row['corroboration_available_at_utc'])
            latest = max(source.utc(row[k]) for k in ('nba_scheduled_start_utc', 'espn_scheduled_start_utc'))
            if at > freeze or latest >= freeze: continue
            if not re.fullmatch(r'00225\d{5}', row['nba_game_id']):
                raise ValueError('Native NBA feature reference crossed fixed prior season')
            eligible.append((latest, row['nba_game_id'], row))
        selected = sorted(eligible)[-PROTOCOL['reference_games_per_team']:]
        if len(selected) != PROTOCOL['reference_games_per_team']:
            raise reference_features.IneligibleSourceGame('INSUFFICIENT_NATIVE_REFERENCE_HISTORY')
        if len({r['nba_game_id'] for _, _, r in selected}) != len(selected):
            raise ValueError('Duplicate native NBA feature reference result')
        scored = []
        for _, _, row in selected:
            own = 'home' if row['home_tricode'] == team else 'away'
            opposite = 'away' if own == 'home' else 'home'
            scored.append((row[own+'_score'], row[opposite+'_score']))
        count = len(selected)
        summaries[side] = {'team_tricode': team, 'prior_games': count,
            'mean_points_for': sum(r[0] for r in scored)/count,
            'mean_points_against': sum(r[1] for r in scored)/count,
            'mean_margin': sum(r[0]-r[1] for r in scored)/count,
            'days_since_latest_prior_start': (min(starts)-selected[-1][0]).total_seconds()/86400,
            'reference_source_rows': [{'source_row_sha256': digest(r), 'source_row': r} for _, _, r in selected]}
    return {'schema': 'tyler-nba-native-daily-pregame-reference-feature-v2',
        'nba_game_id': n['nba_game_id'], 'espn_game_id': e['espn_game_id'],
        'home_team_id': e['home_team_id'], 'away_team_id': e['away_team_id'],
        'frozen_at_utc': freeze.isoformat(), 'scheduled_start_utc': min(starts).isoformat(),
        'nba_saved_start_utc': n['tipoff_utc'], 'espn_saved_start_utc': e['scheduled_start_utc'],
        'requested_daily_source_date': m['requested_date'],
        'nba_native_daily_capture': snapshot['stamp'], 'nba_manifest_sha256': snapshot['manifest_sha256'],
        'nba_response_sha256': m['nba_raw_sha256'], 'espn_capture': m['espn_capture'],
        'espn_manifest_sha256': m['espn_manifest_sha256'], 'protocol_sha256': PROTOCOL_SHA256,
        'reference_report_sha256': digest(reference), 'reference_features': summaries,
        'source_scope_complete': False, 'full_season_schedule_verified': False,
        'original_v1_features_unchanged': True, 'not_a_prediction': True,
        'independent_publication_time_attested': False, 'actual_tipoff_time_attested': False,
        'source_origin_independently_attested': False, 'model_training_enabled': False,
        'historical_evaluation_enabled': False, 'forecasting_enabled': False,
        'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


def _existing(base, now, reference, snapshots):
    root = archive_path(base/ROOT, directory=True, allow_missing=True)
    paths = sorted(root.iterdir()) if root.exists() else []
    if len(paths) > 5000: raise ValueError('Unbounded native NBA feature inventory')
    records = {}
    for file in paths:
        path = archive_path(file)
        if (not re.fullmatch(r'00226\d{5}\.json', path.name) or not path.is_file()
                or path.stat().st_size > 1_000_000):
            raise ValueError('Invalid bounded native NBA feature file')
        raw = path.read_bytes(); saved = json.loads(raw); row = saved['record']
        if raw != source.canonical(saved) or saved.get('record_sha256') != digest(row):
            raise ValueError('Native NBA feature digest/encoding mismatch')
        freeze = source.utc(row['frozen_at_utc'])
        if freeze > now or path.stem != row['nba_game_id']:
            raise ValueError('Native NBA feature filename or freeze mismatch')
        stamp = row['nba_native_daily_capture']
        if stamp not in snapshots: snapshots[stamp] = _snapshot(base, stamp, now)
        snap = snapshots[stamp]
        matches = [r for r in snap['manifest']['matched'] if r['nba_official_game_id'] == path.stem
                   and r['espn_game_id'] == row['espn_game_id']]
        if len(matches) != 1 or source.canonical(_record(snap, matches[0], reference, freeze)) != source.canonical(row):
            raise ValueError('Native NBA feature differs from original source replay')
        records[path.stem] = row
    return records


def audit(base=Path('.'), *, now=None):
    base = Path(base); now = _clock(now or datetime.now(timezone.utc))
    records = _existing(base, now, _reference(base, now), {})
    return {'schema': 'tyler-nba-native-daily-feature-audit-v2',
            'verified_feature_observations': len(records), 'not_a_prediction': True,
            'forecasting_enabled': False, 'model_training_enabled': False,
            'historical_evaluation_enabled': False, 'promotion_allowed': False,
            'NO_BET': True, 'actual_wagers': 0}


def collect(base=Path('.'), *, clock=None):
    base = Path(base); clock = clock or (lambda: datetime.now(timezone.utc))
    started = _clock(clock()); reference = _reference(base, started); snapshots = {}
    existing = _existing(base, started, reference, snapshots)
    root = archive_path(base/receipts.ROOT, directory=True, allow_missing=True)
    folders = sorted(root.iterdir()) if root.exists() else []
    if len(folders) > 1024: raise ValueError('Unbounded native NBA feature source inventory')
    receipts.replay_all(base, now=started)
    snapshot = _snapshot(base, folders[-1].name, started) if folders else None
    freeze = _clock(clock())
    if not started <= freeze <= started+timedelta(minutes=5):
        raise ValueError('Invalid native feature audit/creation interval')
    prepared = []; pending = []
    for matched in snapshot['manifest']['matched'] if snapshot else []:
        if matched['nba_official_game_id'] in existing: continue
        try: prepared.append(_record(snapshot, matched, reference, freeze))
        except reference_features.IneligibleSourceGame as error:
            pending.append({'nba_game_id': matched['nba_official_game_id'], 'reason': str(error)})
    destination = archive_path(base/ROOT, directory=True, allow_missing=True)
    for row in prepared:
        destination.mkdir(parents=True, exist_ok=True)
        with (destination/(row['nba_game_id']+'.json')).open('xb') as stream:
            stream.write(source.canonical({'record': row, 'record_sha256': digest(row)}))
    return {'schema': 'tyler-nba-native-daily-feature-collection-v2',
            'verified_existing': len(existing), 'new_feature_observations': len(prepared),
            'source_capture': snapshot['stamp'] if snapshot else None, 'not_enrolled': pending,
            'not_a_prediction': True, 'historical_backfilled_forecasts': 0,
            'original_v1_features_unchanged': True, 'model_training_enabled': False,
            'forecasting_enabled': False, 'historical_evaluation_enabled': False,
            'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


if __name__ == '__main__':
    import argparse
    cli = argparse.ArgumentParser(description=__doc__)
    actions = cli.add_mutually_exclusive_group()
    actions.add_argument('--collect', action='store_true'); actions.add_argument('--audit', action='store_true')
    cli.add_argument('--base', type=Path, default=Path('.')); args = cli.parse_args()
    result = collect(args.base) if args.collect else audit(args.base) if args.audit else {
        'collection_requested': False, 'forecasting_enabled': False, 'NO_BET': True, 'actual_wagers': 0}
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
