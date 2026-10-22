"""Shared source-only college feature lifecycle checks; no prediction grading."""
from datetime import datetime, timezone

SCOPES = {
    'NCAAF_FBS': ('FBS', 'tyler-fbs-frozen-reference-feature-cohort-v1', 'actual_kickoff_time_attested'),
    'NCAAM_D1': ('D1', 'tyler-d1-frozen-reference-feature-cohort-v1', 'actual_tipoff_time_attested'),
}


def classify(records, original_snapshots, current, dataset, *, now, features, league):
    if league not in SCOPES or features.PROTOCOL['league'] != league:
        raise ValueError('College cohort reader crossed feature protocol scope')
    label, schema, start_attestation = SCOPES[league]
    if now.tzinfo is None: raise ValueError(f'Aware {label} cohort clock required')
    nt, et = [features.source.utc(current['source_manifests'][kind]['recorded_at_utc']) for kind in ('ncaa', 'espn')]
    if max(nt, et, features.source.utc(current['manifest']['recorded_at_utc'])) > now:
        raise ValueError(f'Future-dated current {label} source pair')
    finals = {}; quarantined = {}
    for row in dataset['rows']:
        if row['league'] != league: continue
        scores = [row.get(side+'_score') for side in ('home', 'away')]
        if (any(type(score) is not int or score < 0 for score in scores) or scores[0] == scores[1]
                or row.get('source_archive_sha256_verified') is not True
                or row.get('source_agreement') != 'NCAA_AND_ESPN_REPORTED_SAME_FINAL'
                or row.get('independently_certified_official_final') is not False
                or row.get('eligible_for_historical_evaluation') is not False):
            raise ValueError(f'Invalid or unreplayed {label} final source evidence')
        if row['espn_game_id'] in finals: raise ValueError(f'Duplicate {label} result dataset identity')
        finals[row['espn_game_id']] = row
    for row in dataset['quarantined']:
        if row['league'] == league: quarantined[row['espn_game_id']] = row['reasons']
    rows = []
    for game_id, frozen in sorted(records.items()):
        if game_id != frozen['espn_game_id']: raise ValueError(f'Frozen {label} cohort ID mismatch')
        freeze = features.source.utc(frozen['frozen_at_utc'])
        if freeze > now: raise ValueError(f'Future-dated frozen {label} feature')
        starts = [features.source.utc(frozen[k]) for k in ('ncaa_saved_start_utc', 'espn_saved_start_utc')]
        original = original_snapshots[frozen['crosswalk_capture']]['rows']['ncaa'][frozen['ncaa_game_id']]
        n = current['rows']['ncaa'].get(frozen['ncaa_game_id']); e = current['rows']['espn'].get(game_id)
        row = {'espn_game_id': game_id, 'ncaa_game_id': frozen['ncaa_game_id'],
            'feature_record_sha256': features.digest(frozen), 'frozen_at_utc': frozen['frozen_at_utc'],
            'original_ncaa_saved_start_utc': frozen['ncaa_saved_start_utc'],
            'original_espn_saved_start_utc': frozen['espn_saved_start_utc'],
            'original_saved_start_reached': now >= min(starts),
            'ncaa_present_in_latest_source_pair': n is not None, 'espn_present_in_latest_source_pair': e is not None,
            'result_observation': None, 'reason': None, 'identity_quarantined': False}
        if n is not None:
            start = datetime.fromtimestamp(int(n['source_start_time_epoch']), timezone.utc)
            row.update(current_ncaa_saved_start_utc=start.isoformat(), ncaa_observed_state=n['source_state'],
                       ncaa_saved_start_drift_minutes=(start-starts[0]).total_seconds()/60)
        if e is not None:
            start = features.source.utc(e['scheduled_start_utc'])
            row.update(current_espn_saved_start_utc=start.isoformat(), espn_observed_state=e['state'],
                       espn_saved_start_drift_minutes=(start-starts[1]).total_seconds()/60,
                       espn_observed_status_names=sorted('UNKNOWN' if value is None else value for value in current['espn_status_names'].get(game_id, set())))
        if ((n is not None and any(features.identity.name(n[side+'_name']) != features.identity.name(original[side+'_name']) for side in ('home', 'away')))
                or (e is not None and any(e[side+'_team_id'] != frozen[side+'_team_id']
                    or features.identity.name(e[side+'_name']) != features.identity.name(frozen['reference_features'][side]['provider_team_name'])
                    for side in ('home', 'away')))):
            row.update(reason='LATEST_SOURCE_IDENTITY_DIFFERS_FROM_ORIGINAL', identity_quarantined=True)
        elif ((n is not None and datetime.fromtimestamp(
                int(n['source_start_time_epoch']), timezone.utc) != starts[0])
              or (e is not None and features.source.utc(e['scheduled_start_utc']) != starts[1])):
            row.update(reason='CURRENT_START_DIFFERS_FROM_FROZEN_START', identity_quarantined=True)
        elif game_id in quarantined:
            row.update(reason='RESULT_DATASET_QUARANTINED', identity_quarantined=True,
                       result_quarantine_reasons=quarantined[game_id])
        elif game_id in finals:
            final = finals[game_id]
            identity_ok = (final['ncaa_game_id'] == frozen['ncaa_game_id']
                and all(final['espn_'+side+'_team_id'] == frozen[side+'_team_id']
                        and features.identity.name(final['ncaa_'+side+'_school']) == features.identity.name(original[side+'_name'])
                        for side in ('home', 'away')))
            if not identity_ok:
                row.update(reason='RESULT_IDENTITY_DIFFERS_FROM_ORIGINAL', identity_quarantined=True)
            else:
                at = [features.source.utc(final[k]) for k in ('ncaa_source_observed_at_utc', 'espn_source_observed_at_utc')]
                final_starts = [features.source.utc(final[k]) for k in ('scheduled_start_utc', 'ncaa_scheduled_start_utc')]
                if max(at) > now: raise ValueError(f'Future-dated {label} result observation')
                if final_starts != [starts[1], starts[0]]:
                    row.update(reason='RESULT_START_DIFFERS_FROM_FROZEN_START', identity_quarantined=True)
                elif (final.get('result_observation_chronology_verified') is not True
                        or min(at) <= max(freeze, *starts, *final_starts)):
                    row['reason'] = 'FINAL_NOT_OBSERVED_AFTER_ORIGINAL_AND_REPORTED_STARTS'
                else:
                    row['result_observation'] = final
        else:
            row['reason'] = ('GAME_NOT_PRESENT_IN_LATEST_SOURCE_PAIR' if n is None or e is None
                             else 'NO_CORROBORATED_RESULT_FOR_ORIGINAL_FEATURE')
        row['status'] = ('CORROBORATED_RESULT_OBSERVATION_ONLY' if row['result_observation'] is not None
            else 'SAVED_START_REACHED_WITHOUT_CORROBORATED_RESULT' if row['original_saved_start_reached']
            else 'AWAITING_SAVED_START_WITHOUT_CORROBORATED_RESULT')
        rows.append(row)
    ages = {'ncaa': (now-nt).total_seconds()/3600, 'espn': (now-et).total_seconds()/3600}
    return {'schema': schema, 'checked_at_utc': now.isoformat(),
            'frozen_feature_observations': len(rows),
            'corroborated_result_observations': sum(r['result_observation'] is not None for r in rows),
            'pending_feature_observations': sum(r['result_observation'] is None for r in rows),
            'identity_quarantined': sum(r['identity_quarantined'] for r in rows),
            'schedule_drift_observed': sum(any(r.get(kind+'_saved_start_drift_minutes', 0) != 0 for kind in ('ncaa', 'espn')) for r in rows),
            'source_age_hours': ages, 'source_older_than_12_hours': {k: v > 12 for k, v in ages.items()},
            'rows': rows, 'not_a_prediction': True, 'prediction_accuracy_computed': False,
            'publication_chronology_checked': False, start_attestation: False,
            'institutional_membership_certified': False,
            'source_scope_complete': False, 'forecasting_enabled': False, 'model_training_enabled': False,
            'historical_evaluation_enabled': False, 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}
