"""Read-only frozen NBA feature lifecycle under one recent native daily source."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import sports_nba_feature_cohort as cohort
import sports_nba_postgame_observation_v2 as post
from sports_expansion_audit import archive_path


def classify(records, manifest, provider, *, provider_observed_at, now):
    """Normalized, already audited inputs; no prediction grading or label writes."""
    parsed = manifest['parsed_final_page']
    official = parsed['games'] if parsed is not None else []
    native_at = cohort.source.utc(manifest['recorded_at_utc'])
    provider_at = cohort.source.utc(provider_observed_at)
    result = cohort.classify(records, official, provider,
        nba_observed_at=native_at.isoformat(), espn_observed_at=provider_at.isoformat(), now=now)
    by_id = {game['nba_game_id']: game for game in official}
    for row in result['rows']:
        frozen = records[row['nba_game_id']]
        original_dates = [cohort.source.utc(frozen[key]).astimezone(post.shared.page.EASTERN).date().isoformat()
                          for key in ('nba_saved_start_utc', 'espn_saved_start_utc')]
        row['requested_daily_source_date'] = manifest['requested_date']
        row['original_saved_date_covered_by_daily_source'] = manifest['requested_date'] in original_dates
        n, e = by_id.get(row['nba_game_id']), provider.get(row['espn_game_id'])
        reason = None
        if n is None and not row['original_saved_date_covered_by_daily_source']:
            reason = 'OUTSIDE_REQUESTED_DAILY_SOURCE_DATE'
        elif n is not None and e is not None:
            if cohort.source.utc(n['tipoff_utc']) != cohort.source.utc(e['scheduled_start_utc']):
                reason = 'NATIVE_DAILY_FINAL_STARTS_NOT_EXACT'
            elif min(native_at, provider_at) < cohort.source.utc(n['source_reported_actual_end_utc']):
                reason = 'FINAL_SOURCE_OBSERVED_BEFORE_NATIVE_REPORTED_END'
        if reason is not None:
            row['result_observation'] = None
            row['reason'] = reason
            if reason == 'NATIVE_DAILY_FINAL_STARTS_NOT_EXACT':
                row['identity_quarantined'] = True
            row['status'] = ('SAVED_START_REACHED_WITHOUT_CORROBORATED_RESULT'
                             if row['original_saved_start_reached']
                             else 'AWAITING_SAVED_START_WITHOUT_CORROBORATED_RESULT')
    result.update(
        schema='tyler-nba-native-daily-frozen-feature-lifecycle-v2',
        requested_daily_source_date=manifest['requested_date'],
        native_page_status=manifest['page_status'],
        native_supported_final_game_count=manifest['supported_final_game_count'],
        native_original_body_sha256=manifest['raw_sha256'],
        frozen_games_outside_daily_source_date=sum(
            not row['original_saved_date_covered_by_daily_source'] and row['nba_game_id'] not in by_id
            for row in result['rows']),
        corroborated_result_observations=sum(row['result_observation'] is not None for row in result['rows']),
        pending_feature_observations=sum(row['result_observation'] is None for row in result['rows']),
        identity_quarantined=sum(row['identity_quarantined'] for row in result['rows']),
        source_scope='ONE_RECENT_EASTERN_DATE_ONLY_NO_FULL_COHORT_COVERAGE_CLAIM',
        independent_final_source_observation_only=True,
        outcomes_enrolled=0, settlement_enabled=False, feature_backfill_allowed=False,
        official_final_results_verified=False, independent_final_agreement_verified=False,
        source_origin_independently_attested=False, receipt_clock_independently_attested=False)
    return result


def build(base=Path('.'), *, now=None):
    base = Path(base); now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError('Aware native NBA cohort clock required')
    now = now.astimezone(timezone.utc)
    # Replay all original feature bytes, source receipts and both historical
    # seals; no daily source can replace a frozen record's original dependency.
    snapshots = {}
    records = cohort.features._existing(base, now, cohort.features._reference(base, now), snapshots)
    post.replay_all(base, now=now)
    folders = sorted((base/post.ROOT).glob('*/manifest.json'))
    if not folders:
        return {'schema': 'tyler-nba-native-daily-frozen-feature-lifecycle-v2',
            'source_status': 'NO_RETAINED_NATIVE_POSTGAME_RECEIPT',
            'frozen_feature_observations': len(records), 'corroborated_result_observations': 0,
            'outcomes_enrolled': 0, 'prediction_accuracy_computed': False,
            'source_scope_complete': False, 'settlement_enabled': False,
            'official_final_results_verified': False, 'feature_backfill_allowed': False,
            'forecasting_enabled': False, 'model_training_enabled': False,
            'historical_evaluation_enabled': False, 'promotion_allowed': False,
            'NO_BET': True, 'actual_wagers': 0}
    path = archive_path(folders[-1]); raw = path.read_bytes()
    post.replay(base, path.parent.name, now=now)
    if path.read_bytes() != raw:
        raise ValueError('Native postgame manifest changed during cohort audit')
    manifest = json.loads(raw)
    providers = sorted((base/cohort.source.ROOT/'captures').glob('*/manifest.json'))
    if not providers: raise ValueError('Missing independently retained NBA provider source')
    provider_manifest, provider, provider_hash = cohort._provider(base, providers[-1], now)
    result = classify(records, manifest, provider,
        provider_observed_at=provider_manifest['recorded_at_utc'], now=now)
    result['source_provenance'] = {
        'native_postgame_capture': path.parent.name,
        'native_manifest_sha256': hashlib.sha256(raw).hexdigest(),
        'provider_capture': providers[-1].parent.name,
        'provider_manifest_sha256': provider_hash,
        'provider_independent_of_native_postgame_receipt': True}
    return result


if __name__ == '__main__':
    print(json.dumps(build(), sort_keys=True, indent=2, allow_nan=False))
