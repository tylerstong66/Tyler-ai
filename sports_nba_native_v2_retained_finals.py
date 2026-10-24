"""Read-only native-v2 feature lifecycle across retained NBA/ESPN final sources."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
from itertools import islice
import json
from pathlib import Path
import re

import sports_nba_native_v2_final_v3_cohort as daily
from sports_expansion_audit import archive_path, strict_json_loads, MAX_BLOB_SIZE

MAX_CAPTURES = 1024
NATIVE_FIELDS = ('nba_game_id', 'kind', 'home_team_id', 'away_team_id',
    'home_tricode', 'away_tricode', 'tipoff_utc', 'nba_status',
    'nba_home_score', 'nba_away_score', 'source_reported_actual_start_utc',
    'source_reported_actual_end_utc')
PROVIDER_FIELDS = ('espn_game_id', 'home_team_id', 'away_team_id',
    'home_tricode', 'away_tricode', 'scheduled_start_utc', 'season_stage',
    'provider_completed', 'home_score', 'away_score')


def _inventory(base, root):
    folder = archive_path(base/root, directory=True, allow_missing=True)
    children = list(islice(folder.iterdir(), MAX_CAPTURES+1)) if folder.exists() else []
    if len(children) > MAX_CAPTURES:
        raise ValueError('Unbounded retained NBA source inventory')
    result = []
    for child in sorted(children):
        archive_path(child, directory=True)
        if not re.fullmatch(r'[0-9]{8}T[0-9]{12}Z', child.name):
            raise ValueError('Invalid retained NBA source capture identifier')
        path = archive_path(child/'manifest.json')
        if path.stat().st_size > MAX_BLOB_SIZE:
            raise ValueError('Oversized retained NBA source manifest')
        result.append(path)
    return result


def _fingerprint(row, fields):
    # Type-preserving canonical JSON avoids false/float equality hiding drift.
    return daily.features.source.canonical({key: row.get(key) for key in fields})


def _provenance(item, *, native):
    manifest = item['manifest']
    result = {'capture': item['capture'], 'manifest_sha256': item['manifest_sha256'],
              'observed_at_utc': manifest['recorded_at_utc']}
    if native:
        result.update(requested_date=manifest['requested_date'],
                      original_response_sha256=manifest['raw_sha256'])
    else:
        result['original_response_sha256'] = sorted(s['original_response_sha256']
            for s in manifest['snapshots'] if s['league'] == 'NBA')
    return result


def classify(records, native_sources, provider_sources, *, now):
    """Already replayed source inputs; no score-dependent receipt selection."""
    now = daily.features._clock(now)
    utc = daily.features.source.utc
    if (any(key != row['nba_game_id'] for key, row in records.items())
            or len({row['espn_game_id'] for row in records.values()}) != len(records)):
        raise ValueError('Non-bijective frozen NBA feature identities')
    native_claims = defaultdict(list); provider_claims = defaultdict(list)
    native_matchups = defaultdict(list); provider_matchups = defaultdict(list)
    provider_quarantines = defaultdict(list)
    for item in native_sources:
        at = utc(item['manifest']['recorded_at_utc'])
        if at > now: raise ValueError('Future-dated retained NBA final source')
        for row in (item['manifest'].get('parsed_final_page') or {}).get('games', []):
            claim = (at, item['capture'], item, row)
            native_claims[row['nba_game_id']].append(claim)
            native_matchups[tuple(sorted((row['home_tricode'], row['away_tricode'])))].append(claim)
    for item in provider_sources:
        at = utc(item['manifest']['recorded_at_utc'])
        if at > now: raise ValueError('Future-dated retained provider final source')
        for row in item['manifest'].get('quarantined_provider_games', []):
            if row['league'] == 'NBA':
                provider_quarantines[row['game_id']].append(_provenance(item, native=False))
        for key, row in item['games'].items():
            if key != row['espn_game_id']: raise ValueError('Retained provider identity differs from lookup key')
            claim = (at, item['capture'], item, row)
            provider_matchups[tuple(sorted((row['home_tricode'], row['away_tricode'])))].append(claim)
            if row['provider_completed'] is True:
                provider_claims[key].append(claim)
    rows = []
    for key, frozen in sorted(records.items()):
        if key != frozen['nba_game_id']: raise ValueError('Frozen NBA identity differs from lookup key')
        ns = sorted(native_claims[key], key=lambda x: (x[0], x[1]))
        es = sorted(provider_claims[frozen['espn_game_id']], key=lambda x: (x[0], x[1]))
        starts = [utc(frozen[field]) for field in ('nba_saved_start_utc', 'espn_saved_start_utc')]
        teams = tuple(sorted(frozen['reference_features'][side]['team_tricode'] for side in ('home', 'away')))
        native_aliases = [x for x in native_matchups[teams] if x[3]['nba_game_id'] != key
                          and abs((utc(x[3]['tipoff_utc'])-starts[0]).total_seconds()) <= 30*60]
        provider_aliases = [x for x in provider_matchups[teams] if x[3]['espn_game_id'] != frozen['espn_game_id']
                            and abs((utc(x[3]['scheduled_start_utc'])-starts[1]).total_seconds()) <= 30*60]
        row = {'nba_game_id': key, 'espn_game_id': frozen['espn_game_id'],
               'feature_record_sha256': daily.features.digest(frozen),
               'frozen_at_utc': frozen['frozen_at_utc'],
               'original_saved_start_reached': now >= min(starts),
               'native_final_claims': len(ns), 'provider_final_claims': len(es),
               'result_observation': None, 'source_pair': None, 'quarantined': False}
        reason = None
        if len({_fingerprint(x[3], NATIVE_FIELDS) for x in ns}) > 1:
            reason = 'CONFLICTING_RETAINED_NATIVE_FINAL_CLAIMS'
        elif frozen['espn_game_id'] in provider_quarantines:
            reason = 'RETAINED_PROVIDER_IDENTITY_QUARANTINED'
        elif len({_fingerprint(x[3], PROVIDER_FIELDS) for x in es}) > 1:
            reason = 'CONFLICTING_RETAINED_PROVIDER_FINAL_CLAIMS'
        elif native_aliases:
            reason = 'RETAINED_NATIVE_GAME_ID_REASSIGNMENT_OR_AMBIGUITY'
        elif provider_aliases:
            reason = 'RETAINED_PROVIDER_GAME_ID_REASSIGNMENT_OR_AMBIGUITY'
        if reason:
            row['quarantined'] = True
            row['conflicting_native_sources'] = [dict(_provenance(x[2], native=True),
                claimed_game_id=x[3]['nba_game_id'],
                normalized_game_sha256=hashlib.sha256(_fingerprint(x[3], NATIVE_FIELDS)).hexdigest()) for x in ns+native_aliases]
            row['conflicting_provider_sources'] = [dict(_provenance(x[2], native=False),
                claimed_game_id=x[3]['espn_game_id'],
                normalized_game_sha256=hashlib.sha256(_fingerprint(x[3], PROVIDER_FIELDS)).hexdigest()) for x in es+provider_aliases]
            row['provider_quarantine_sources'] = provider_quarantines.get(frozen['espn_game_id'], [])
        elif not ns:
            reason = 'NO_RETAINED_NATIVE_FINAL_FOR_FROZEN_GAME'
        elif not es:
            reason = 'NO_RETAINED_PROVIDER_FINAL_FOR_FROZEN_GAME'
        else:
            # Consistency is checked over ALL final claims before choosing the
            # earliest native observation and earliest provider observed after
            # its reported end. Never search for a pair with favorable scores.
            native = ns[0]
            ended = utc(native[3]['source_reported_actual_end_utc'])
            eligible = [x for x in es if x[0] >= ended]
            row['provider_final_claims_before_native_reported_end'] = len(es)-len(eligible)
            if not eligible:
                reason = 'NO_PROVIDER_FINAL_OBSERVED_AFTER_NATIVE_REPORTED_END'
            else:
                provider = eligible[0]
                result = daily.lifecycle.classify({key: frozen}, native[2]['manifest'],
                    provider[2]['games'], provider_observed_at=provider[0].isoformat(), now=now)
                actual = result['rows'][0]
                row['result_observation'] = actual['result_observation']
                row['quarantined'] = actual['identity_quarantined'] or actual['reason'] == 'CONFLICTING_FINAL_SCORES_NO_GRADE'
                reason = actual['reason']
                row['source_pair'] = {'native': _provenance(native[2], native=True),
                                      'provider': _provenance(provider[2], native=False)}
        row['reason'] = reason
        row['status'] = ('CORROBORATED_RESULT_OBSERVATION_ONLY' if row['result_observation'] else
                         'QUARANTINED_RETAINED_SOURCE_CLAIMS' if row['quarantined'] else
                         'AWAITING_ORIGINAL_SAVED_START' if not row['original_saved_start_reached'] else
                         'PENDING_RETAINED_FINAL_SOURCE_EVIDENCE')
        rows.append(row)
    matched = sum(row['result_observation'] is not None for row in rows)
    return {'schema': 'tyler-nba-native-v2-retained-final-lifecycle-v1',
        'checked_at_utc': now.isoformat(), 'feature_cohort': 'NATIVE_DAILY_V2_ONLY',
        'feature_protocol_sha256': daily.features.PROTOCOL_SHA256,
        'frozen_feature_root': daily.features.ROOT.as_posix(),
        'frozen_feature_observations': len(rows), 'corroborated_result_observations': matched,
        'pending_feature_observations': len(rows)-matched,
        'awaiting_original_saved_start': sum(not r['original_saved_start_reached'] for r in rows),
        'quarantined_features': sum(r['quarantined'] for r in rows),
        'native_receipts_replayed': len(native_sources), 'provider_receipts_replayed': len(provider_sources),
        'native_receipts_without_supported_finals': sum(not (s['manifest'].get('parsed_final_page') or {}).get('games') for s in native_sources),
        'rows': rows, 'source_scope': 'ALL_RETAINED_ACCEPTED_FINAL_CLAIMS_FOR_NATIVE_V2_FEATURES',
        'receipt_selection': 'ALL_CLAIMS_CONSISTENT_THEN_EARLIEST_NATIVE_AND_PROVIDER_AFTER_REPORTED_END',
        'cross_version_counts_must_not_be_pooled': True, 'not_a_prediction': True,
        'fresh_source_observation': False, 'actual_tipoff_time_attested': False,
        'source_origin_independently_attested': False, 'publication_chronology_checked': False,
        'receipt_clock_independently_attested': False,
        'original_feature_bytes_unchanged': True, 'outcomes_enrolled': 0,
        'source_scope_complete': False, 'official_final_results_verified': False,
        'independent_final_agreement_verified': False, 'prediction_accuracy_computed': False,
        'settlement_enabled': False, 'feature_backfill_allowed': False,
        'historical_evaluation_enabled': False, 'model_training_enabled': False,
        'forecasting_enabled': False, 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


def build(base=Path('.'), *, now=None):
    base = Path(base); now = daily.features._clock(now or datetime.now(timezone.utc))
    native_paths = _inventory(base, daily.post.ROOT)
    provider_paths = _inventory(base, daily.lifecycle.cohort.source.ROOT/'captures')
    records = daily.features._existing(base, now, daily.features._reference(base, now), {})
    native = []; provider = []; without_nba = 0
    for path in native_paths:
        raw = path.read_bytes()
        daily.post.replay(base, path.parent.name, now=now)
        if path.read_bytes() != raw: raise ValueError('Retained native manifest changed during replay')
        native.append({'capture': path.parent.name, 'manifest_sha256': hashlib.sha256(raw).hexdigest(),
                       'manifest': strict_json_loads(raw)})
    for path in provider_paths:
        original = path.read_bytes()
        candidate = strict_json_loads(original)
        if not any(s['league'] == 'NBA' for s in candidate['snapshots']):
            verified, _, _ = daily.lifecycle.cohort.provider_audit.audit_capture(path)
            if path.read_bytes() != original or verified != candidate:
                raise ValueError('Provider manifest changed during no-NBA replay')
            if daily.features.source.utc(verified['recorded_at_utc']) > now:
                raise ValueError('Future-dated provider capture without NBA')
            without_nba += 1
            continue
        manifest, games, digest = daily.lifecycle.cohort._provider(base, path, now)
        # Full capture replay includes every sport. Retain only NBA metadata
        # and the complete NBA game map so a season's history stays bounded
        # without dropping NBA ambiguity or quarantine context.
        context = {'recorded_at_utc': manifest['recorded_at_utc'],
                   'snapshots': [{'league': 'NBA', 'original_response_sha256': s['original_response_sha256']}
                                 for s in manifest['snapshots'] if s['league'] == 'NBA'],
                   'quarantined_provider_games': [s for s in manifest['quarantined_provider_games'] if s['league'] == 'NBA']}
        provider.append({'capture': path.parent.name, 'manifest_sha256': digest,
                         'manifest': context, 'games': games})
    report = classify(records, native, provider, now=now)
    report.update(provider_inventory_receipts_replayed=len(provider_paths),
                  provider_receipts_without_nba=without_nba)
    return report


if __name__ == '__main__':
    print(json.dumps(build(), indent=2, sort_keys=True, allow_nan=False))
