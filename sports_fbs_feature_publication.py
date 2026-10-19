"""Separate GitHub server chronology for original FBS reference-feature records."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

import sports_fbs_pregame_features as features
import sports_github_server_evidence as server

WORKFLOW = '.github/workflows/college_final_receipts.yml'


def audit(run_id, *, base=Path('.'), now=None, fetch=server.fetch_json, cohort_ids=None):
    base = Path(base); now = now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError('Aware FBS publication audit clock required')
    records = features._existing(base, now, features._reference(base, now), {})
    if cohort_ids is not None:
        ids = list(cohort_ids)
        if not ids or len(ids) != len(set(ids)) or not set(ids) <= set(records):
            raise ValueError('Invalid original FBS publication cohort')
        records = {key: records[key] for key in ids}
    if not records: raise ValueError('No original FBS features to attest')
    run = server.run_observation(run_id, now=now, workflow=WORKFLOW,
                                 events=('pull_request', 'push'), fetch=fetch)
    observed = features.source.utc(run['server_created_at_utc']); evidence = []
    for key, row in sorted(records.items()):
        start = min(features.source.utc(row[k]) for k in ('ncaa_saved_start_utc', 'espn_saved_start_utc'))
        if not features.source.utc(row['frozen_at_utc']) <= observed < start:
            raise ValueError('FBS server observation does not follow freeze and precede both saved starts')
        path = features.ROOT/(key+'.json'); raw = features._read(base/path, 1_000_000)
        if raw != features.source.canonical({'record': row, 'record_sha256': features.digest(row)}):
            raise ValueError('Original FBS feature changed during publication audit')
        blob = server.verify_blob(path.as_posix(), raw, run['head_sha'], fetch=fetch)
        evidence.append({'espn_game_id': key, 'ncaa_game_id': row['ncaa_game_id'],
            'path': path.as_posix(), 'git_blob_sha1': blob, 'file_sha256': hashlib.sha256(raw).hexdigest(),
            'record_sha256': features.digest(row), 'frozen_at_utc': row['frozen_at_utc'],
            'ncaa_saved_start_utc': row['ncaa_saved_start_utc'], 'espn_saved_start_utc': row['espn_saved_start_utc'],
            'earliest_saved_start_utc': start.isoformat()})
    return {'schema': 'tyler-fbs-feature-github-server-observation-v1',
            'repository': server.REPOSITORY, **run, 'checked_at_utc': now.isoformat(),
            'feature_observations_verified': len(evidence), 'protocol_sha256': features.PROTOCOL_SHA256,
            'evidence': evidence, 'saved_report_requires_fresh_api_replay': True,
            'claim_scope': 'GITHUB_SERVER_OBSERVED_EXACT_ORIGINAL_FBS_FEATURE_BYTES_BEFORE_BOTH_SAVED_STARTS',
            'cohort_scope': 'EXPLICIT_ORIGINAL_FEATURE_IDS', 'source_origin_certified': False,
            'public_repository_visibility_attested': False, 'actual_kickoff_time_attested': False,
            'not_a_prediction': True, 'model_training_enabled': False, 'forecasting_enabled': False,
            'historical_evaluation_enabled': False, 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


def replay(path, *, base=Path('.'), now=None, fetch=server.fetch_json):
    saved = json.loads(features._read(Path(path), 1_000_000))
    ids = [r['espn_game_id'] for r in saved['evidence']]
    actual = audit(saved['run_id'], base=base, now=now, fetch=fetch, cohort_ids=ids)
    old = {k: v for k, v in saved.items() if k != 'checked_at_utc'}
    new = {k: v for k, v in actual.items() if k != 'checked_at_utc'}
    if features.source.canonical(old) != features.source.canonical(new):
        raise ValueError('Saved FBS publication report differs from fresh API replay')
    return actual


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--run-id', type=int); group.add_argument('--replay', type=Path)
    args = parser.parse_args(); report = replay(args.replay) if args.replay else audit(args.run_id)
    print(json.dumps(report, sort_keys=True, indent=2))
