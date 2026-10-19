"""Verify GitHub server observation of exact independently frozen MLB forecasts."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

import sports_expansion_observer as canonical_json
import sports_mlb_cross_cohort_audit as cohorts
from sports_mlb_sources import utc
import sports_github_server_evidence as server
from sports_github_server_evidence import API, REPOSITORY, fetch_json

WORKFLOW = '.github/workflows/mlb_shadow_scoreboard_publisher.yml'
SCHEMA = 'tyler-mlb-cohort-github-server-observation-v1'


def _inputs(base):
    report = cohorts.build(base); inputs = {}
    for row in report['comparisons']:
        for side in ('team', 'hitter'):
            path = row[side+'_forecast_path']; proof = row[side+'_cohort']
            item = {'file_sha256': proof['file_sha256'], 'record_digest_sha256': proof['record_digest_sha256'],
                    'frozen_at_utc': proof['frozen_at_utc'], 'saved_start_utc': proof['saved_start_utc'],
                    'cohort': side, 'game_id': row['game_id']}
            if path in inputs and canonical_json.canonical(inputs[path]) != canonical_json.canonical(item):
                raise ValueError('Conflicting original cohort input identity')
            inputs[path] = item
    return inputs


def _run(run_id, now, fetch):
    return server.run_observation(run_id, now=now, workflow=WORKFLOW, events=('schedule',), fetch=fetch)


def _file(path, proof, raw, run, fetch):
    observed = utc(run['server_created_at_utc'])
    if not utc(proof['frozen_at_utc']) <= observed < utc(proof['saved_start_utc']):
        raise ValueError('Server observation does not follow freeze and precede original saved start')
    if hashlib.sha256(raw).hexdigest() != proof['file_sha256']:
        raise ValueError('Original forecast changed during server audit')
    blob = server.verify_blob(path, raw, run['head_sha'], fetch=fetch)
    return {'path': path, **proof, 'git_blob_sha1': blob, 'run_id': run['run_id'],
            'head_sha': run['head_sha'], 'server_created_at_utc': run['server_created_at_utc'],
            'server_observed_before_original_saved_start': True}


def audit(assignments, *, base=Path('.'), now=None, fetch=fetch_json):
    base = Path(base); now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware MLB publication audit clock required')
    if not isinstance(assignments, dict) or not 0 < len(assignments) <= 500:
        raise ValueError('Explicit bounded original forecast cohort required')
    inputs = _inputs(base)
    if not set(assignments) <= set(inputs):
        raise ValueError('Publication recipe contains a path outside verified original overlapping cohorts')
    if any(type(value) is not int or value <= 0 for value in assignments.values()):
        raise ValueError('Positive integer server run IDs required')
    runs = {run_id: _run(run_id, now, fetch) for run_id in sorted(set(assignments.values()))}
    raw_files = {path: cohorts._read(base/path)[0] for path in assignments}
    def verify(path):
        return _file(path, inputs[path], raw_files[path], runs[assignments[path]], fetch)
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(verify, sorted(assignments)))
    return {'schema': SCHEMA, 'repository': REPOSITORY, 'checked_at_utc': now.isoformat(),
            'assignments': dict(sorted(assignments.items())), 'runs': [runs[k] for k in sorted(runs)],
            'records': records, 'forecast_files_verified': len(records),
            'winner_records_verified': sum(r['cohort'] == 'team' for r in records),
            'hitter_records_verified': sum(r['cohort'] == 'hitter' for r in records),
            'distinct_games': len({r['game_id'] for r in records}),
            'claim_scope': 'GITHUB_SERVER_OBSERVED_EXACT_ORIGINAL_FORECAST_BYTES_BEFORE_EACH_SAVED_START',
            'cohort_scope': 'EXPLICIT_ORIGINAL_PATHS_ONLY', 'saved_report_requires_fresh_api_replay': True,
            'original_source_validation_complete': False, 'source_origin_certified': False,
            'public_repository_visibility_attested': False, 'actual_tipoff_time_attested': False,
            'joint_performance_comparison_enabled': False, 'new_forecasts_created': 0,
            'forecasting_enabled': False, 'model_training_enabled': False,
            'historical_evaluation_enabled': False, 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


def replay(path, *, base=Path('.'), now=None, fetch=fetch_json):
    _, saved = cohorts._read(Path(path), limit=1_000_000)
    actual = audit(saved['assignments'], base=base, now=now, fetch=fetch)
    old = {k: v for k, v in saved.items() if k != 'checked_at_utc'}
    new = {k: v for k, v in actual.items() if k != 'checked_at_utc'}
    if canonical_json.canonical(old) != canonical_json.canonical(new):
        raise ValueError('Saved MLB server report differs from fresh API replay')
    return actual


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--assignments', type=Path)
    group.add_argument('--replay', type=Path)
    args = parser.parse_args()
    result = replay(args.replay) if args.replay else audit(cohorts._read(args.assignments)[1])
    print(json.dumps(result, sort_keys=True, indent=2))
