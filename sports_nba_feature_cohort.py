"""Read-only lifecycle of frozen NBA features and later source observations."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

import sports_expansion_observer as source
import sports_expansion_audit as provider_audit
import sports_nba_official_schedule_audit as nba
import sports_nba_pregame_features as features
import sports_nba_final_receipts as finals


def classify(records, official, provider, *, nba_observed_at, espn_observed_at, now):
    if now.tzinfo is None:
        raise ValueError('Aware cohort audit clock required')
    nt, et = source.utc(nba_observed_at), source.utc(espn_observed_at)
    if max(nt, et) > now:
        raise ValueError('Future-dated current cohort source')
    by_id = {row['nba_game_id']: row for row in official}
    if len(by_id) != len(official):
        raise ValueError('Duplicate current official game ID')
    if (any(key != row['nba_game_id'] for key, row in records.items())
            or len({row['espn_game_id'] for row in records.values()}) != len(records)
            or any(key != row['espn_game_id'] for key, row in provider.items())):
        raise ValueError('Non-bijective cohort or provider identity')
    final_report = finals.classify(official, provider, nba_observed_at=nt.isoformat(),
                                   espn_observed_at=et.isoformat())
    agreeing = {(r['nba_game_id'], r['espn_game_id']): r
                for r in final_report['corroborated_research_only']}
    crosswalk = nba.compare(official, provider)
    matched = {r['espn_game_id']: r['nba_official_game_id'] for r in crosswalk['matched']}
    pending = {r['espn_game_id']: r['reason'] for r in final_report['pending']}
    rows = []
    for game_id, frozen in sorted(records.items()):
        n, e = by_id.get(game_id), provider.get(frozen['espn_game_id'])
        freeze = source.utc(frozen['frozen_at_utc'])
        if freeze > now:
            raise ValueError('Future-dated frozen feature')
        starts = [source.utc(frozen[k]) for k in ('nba_saved_start_utc', 'espn_saved_start_utc')]
        row = {'nba_game_id': game_id, 'espn_game_id': frozen['espn_game_id'],
               'feature_record_sha256': features.digest(frozen),
               'frozen_at_utc': frozen['frozen_at_utc'],
               'original_nba_saved_start_utc': frozen['nba_saved_start_utc'],
               'original_espn_saved_start_utc': frozen['espn_saved_start_utc'],
               'original_saved_start_reached': now >= min(starts),
               'nba_present_in_latest_source': n is not None,
               'espn_present_in_latest_source': e is not None,
               'result_observation': None, 'reason': None}
        reason = None
        if n is None:
            reason = 'NBA_GAME_NOT_PRESENT_IN_LATEST_SOURCE'
        elif e is None:
            reason = 'ESPN_GAME_NOT_PRESENT_IN_LATEST_SOURCE'
        else:
            row.update(nba_source_row_sha256=features.digest(n), espn_source_row_sha256=features.digest(e),
                       current_nba_saved_start_utc=n['tipoff_utc'],
                       current_espn_saved_start_utc=e['scheduled_start_utc'],
                       nba_saved_start_drift_minutes=(source.utc(n['tipoff_utc']) - starts[0]).total_seconds()/60,
                       espn_saved_start_drift_minutes=(source.utc(e['scheduled_start_utc']) - starts[1]).total_seconds()/60,
                       nba_observed_status=n['nba_status'], espn_observed_state=e['state'])
            expected = tuple(frozen['reference_features'][side]['team_tricode'] for side in ('home', 'away'))
            if (tuple(n[side+'_tricode'] for side in ('home', 'away')) != expected
                    or tuple(e[side+'_tricode'] for side in ('home', 'away')) != expected
                    or any(e[side+'_team_id'] != frozen[side+'_team_id'] for side in ('home', 'away'))):
                reason = 'SOURCE_IDENTITY_DIFFERS_FROM_FROZEN_TEAMS'
            elif n['kind'] != 'regular' or e['season_stage'] != 2:
                reason = 'SOURCE_COMPETITION_DIFFERS_FROM_FROZEN_SCOPE'
            elif n['nba_postponed_status'] not in (None, '', 'N'):
                reason = 'POSTPONED_OR_UNKNOWN_NBA_STATUS'
            elif (source.utc(n['tipoff_utc']) != starts[0]
                  or source.utc(e['scheduled_start_utc']) != starts[1]):
                reason = 'CURRENT_START_DIFFERS_FROM_FROZEN_START'
            elif matched.get(e['espn_game_id']) != game_id:
                reason = 'CURRENT_CROSSWALK_NOT_UNIQUE_FROZEN_IDENTITY'
            elif (game_id, e['espn_game_id']) in agreeing:
                current_starts = [source.utc(n['tipoff_utc']), source.utc(e['scheduled_start_utc'])]
                if min(nt, et) <= max(*starts, *current_starts, freeze):
                    reason = 'FINAL_NOT_OBSERVED_AFTER_ORIGINAL_AND_LATEST_STARTS'
                else:
                    row['result_observation'] = agreeing[(game_id, e['espn_game_id'])]
            else:
                reason = pending.get(e['espn_game_id'], 'NO_CORROBORATED_RESULT')
        row['reason'] = reason
        row['status'] = ('CORROBORATED_RESULT_OBSERVATION_ONLY' if row['result_observation'] is not None
                         else 'SAVED_START_REACHED_WITHOUT_CORROBORATED_RESULT' if row['original_saved_start_reached']
                         else 'AWAITING_SAVED_START_WITHOUT_CORROBORATED_RESULT')
        row['identity_quarantined'] = reason in (
            'SOURCE_IDENTITY_DIFFERS_FROM_FROZEN_TEAMS', 'SOURCE_COMPETITION_DIFFERS_FROM_FROZEN_SCOPE',
            'CURRENT_CROSSWALK_NOT_UNIQUE_FROZEN_IDENTITY', 'NON_BIJECTIVE_GAME_IDENTITY',
            'CURRENT_START_DIFFERS_FROM_FROZEN_START')
        rows.append(row)
    counts = Counter(row['status'] for row in rows)
    ages = {'nba': (now-nt).total_seconds()/3600, 'espn': (now-et).total_seconds()/3600}
    return {'schema': 'tyler-nba-frozen-feature-cohort-lifecycle-v1',
            'checked_at_utc': now.isoformat(), 'frozen_feature_observations': len(rows),
            'corroborated_result_observations': counts['CORROBORATED_RESULT_OBSERVATION_ONLY'],
            'pending_feature_observations': sum(row['result_observation'] is None for row in rows),
            'identity_quarantined': sum(row['identity_quarantined'] for row in rows),
            'schedule_drift_observed': sum(any(row.get(side+'_saved_start_drift_minutes', 0) != 0
                                             for side in ('nba', 'espn')) for row in rows),
            'source_observed_at_utc': {'nba': nt.isoformat(), 'espn': et.isoformat()},
            'source_age_hours': ages, 'source_older_than_12_hours': {k: v > 12 for k, v in ages.items()},
            'rows': rows, 'not_a_prediction': True, 'prediction_accuracy_computed': False,
            'actual_tipoff_time_attested': False, 'publication_chronology_checked': False,
            'source_scope_complete': False, 'model_training_enabled': False,
            'historical_evaluation_enabled': False, 'forecasting_enabled': False,
            'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


def _provider(base, path, now):
    if path.parent.is_symlink() or path.is_symlink() or not path.is_file() or path.stat().st_size > provider_audit.MAX_BLOB_SIZE:
        raise ValueError('Invalid current provider receipt')
    original = path.read_bytes()
    manifest, _, _ = provider_audit.audit_capture(path)
    if source.canonical(json.loads(original)) != source.canonical(manifest) or path.read_bytes() != original:
        raise ValueError('Current provider receipt changed during replay')
    for snap in manifest['snapshots']:
        blob = path.parent/snap['compressed_file']
        if blob.is_symlink() or not blob.is_file():
            raise ValueError('Current provider response must be a regular file')
    at = source.utc(manifest['recorded_at_utc'])
    if at > now:
        raise ValueError('Future-dated provider source')
    if not any(s['league'] == 'NBA' for s in manifest['snapshots']):
        raise ValueError('Latest provider capture has no NBA snapshot')
    return manifest, nba.espn_games(manifest, path.parent), hashlib.sha256(original).hexdigest()


def build(base=Path('.'), *, now=None):
    base = Path(base); now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware cohort audit clock required')
    snapshots = {}
    records = features._existing(base, now, features._reference(base, now), snapshots)
    captures = sorted((base/nba.ROOT/'captures').glob('*/manifest.json'))
    provider_captures = sorted((base/source.ROOT/'captures').glob('*/manifest.json'))
    if not captures or not provider_captures:
        raise ValueError('Missing retained cohort observation sources')
    stamp = captures[-1].parent.name
    snapshot = snapshots.get(stamp) or features._snapshot(base, stamp)
    ep = provider_captures[-1]; manifest, provider, provider_hash = _provider(base, ep, now)
    result = classify(records, list(snapshot['official'].values()), provider,
                      nba_observed_at=snapshot['manifest']['created_at_utc'],
                      espn_observed_at=manifest['recorded_at_utc'], now=now)
    result['source_provenance'] = {
        'nba_capture': stamp, 'nba_manifest_sha256': snapshot['manifest_sha256'],
        'nba_response_sha256': snapshot['manifest']['nba_raw_sha256'],
        'espn_capture': ep.parent.name, 'espn_manifest_sha256': provider_hash,
        'espn_raw_response_sha256': sorted(s['original_response_sha256'] for s in manifest['snapshots'] if s['league'] == 'NBA'),
        'provider_independent_of_nba_linked_snapshot': ep.parent.name != snapshot['manifest']['espn_capture']}
    return result


if __name__ == '__main__':
    print(json.dumps(build(), sort_keys=True, indent=2))
