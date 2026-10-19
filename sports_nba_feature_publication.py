"""Replay GitHub server observation of exact pregame feature bytes; no forecasts."""
from datetime import datetime, timezone
from pathlib import Path
import base64
import hashlib
import json
import os
import re

import requests
import sports_expansion_observer as source
import sports_nba_pregame_features as features

REPOSITORY = 'tylerstong66/Tyler-ai'
API = 'https://api.github.com/repos/' + REPOSITORY
WORKFLOW = '.github/workflows/college_final_receipts.yml'


def fetch_json(url):
    if not url.startswith(API + '/'):
        raise ValueError('Unapproved publication evidence URL')
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Tyler-AI-feature-chronology'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    with requests.get(url, headers=headers, timeout=(10, 30), stream=True,
                      allow_redirects=False) as response:
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError('GitHub evidence did not return HTTP 200')
        parts = []
        size = 0
        for part in response.iter_content(65536):
            size += len(part)
            if size > 1_000_000:
                raise ValueError('Oversized GitHub publication evidence')
            parts.append(part)
    return json.loads(b''.join(parts))


def _attest(records, raw_files, run_id, now, fetch):
    if type(run_id) is not int or run_id <= 0:
        raise ValueError('Positive integer GitHub run ID required')
    run = fetch(API + '/actions/runs/' + str(run_id))
    sha = run.get('head_sha', '')
    if (type(run.get('id')) is not int or run['id'] != run_id
            or run.get('repository', {}).get('full_name') != REPOSITORY
            or run.get('head_repository', {}).get('full_name') != REPOSITORY
            or run.get('path') != WORKFLOW
            or run.get('event') not in ('pull_request', 'push')
            or not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{40}', sha)):
        raise ValueError('Wrong GitHub repository, workflow, run, event or commit')
    observed = source.utc(run['created_at'])
    if observed > now:
        raise ValueError('Future GitHub server timestamp')
    evidence = []
    if not records or set(records) != set(raw_files):
        raise ValueError('Missing or inconsistent feature cohort')
    for game_id, record in sorted(records.items()):
        if not re.fullmatch(r'00226\d{5}', game_id) or record['nba_game_id'] != game_id:
            raise ValueError('Invalid feature game identity')
        start = min(source.utc(record[k]) for k in ('nba_saved_start_utc', 'espn_saved_start_utc'))
        if not source.utc(record['frozen_at_utc']) <= observed < start:
            raise ValueError('GitHub observation not between feature freeze and both saved starts')
        path = (features.ROOT / (game_id + '.json')).as_posix()
        raw = raw_files[game_id]
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        item = fetch(API + '/contents/' + path + '?ref=' + sha)
        if (item.get('type') != 'file' or item.get('path') != path
                or item.get('sha') != blob or type(item.get('size')) is not int
                or item['size'] != len(raw) or item.get('encoding') != 'base64'):
            raise ValueError('GitHub immutable commit does not contain expected feature blob')
        content = item.get('content')
        if not isinstance(content, str) or base64.b64decode(''.join(content.split()), validate=True) != raw:
            raise ValueError('GitHub immutable feature bytes differ')
        evidence.append({'nba_game_id': game_id, 'path': path, 'git_blob_sha1': blob,
                         'file_sha256': hashlib.sha256(raw).hexdigest(),
                         'frozen_at_utc': record['frozen_at_utc'],
                         'earliest_saved_start_utc': start.isoformat()})
    return {'schema': 'tyler-nba-feature-github-server-observation-v1',
            'repository': REPOSITORY, 'run_id': run_id, 'head_sha': sha,
            'workflow_path': WORKFLOW, 'event': run['event'],
            'github_server_created_at_utc': run['created_at'],
            'checked_at_utc': now.isoformat(), 'feature_observations_verified': len(evidence),
            'evidence': evidence,
            'claim_scope': 'GITHUB_SERVER_OBSERVED_EXACT_COMMIT_FEATURE_BYTES_BEFORE_SAVED_STARTS',
            'saved_report_requires_fresh_api_replay': True,
            'public_repository_visibility_attested': False, 'actual_tipoff_time_attested': False,
            'source_origin_certified': False, 'not_a_prediction': True,
            'model_training_enabled': False, 'forecasting_enabled': False,
            'historical_evaluation_enabled': False, 'promotion_allowed': False,
            'NO_BET': True, 'actual_wagers': 0}


def audit(run_id, *, base=Path('.'), now=None, fetch=fetch_json, cohort_ids=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware publication audit clock required')
    base = Path(base)
    records = features._existing(base, now, features._reference(base, now), {})
    if cohort_ids is not None:
        ids = list(cohort_ids)
        if not ids or len(ids) != len(set(ids)) or not set(ids) <= set(records):
            raise ValueError('Invalid or missing original publication cohort')
        records = {game_id: records[game_id] for game_id in ids}
    raw_files = {game_id: (base / features.ROOT / (game_id + '.json')).read_bytes()
                 for game_id in records}
    # Bind re-read bytes to the source-replayed records, even if files change during audit.
    for game_id, record in records.items():
        expected = source.canonical({'record': record, 'record_sha256': features.digest(record)})
        if raw_files[game_id] != expected:
            raise ValueError('Feature record changed during publication audit')
    return _attest(records, raw_files, run_id, now, fetch)


def replay(path, *, base=Path('.'), now=None, fetch=fetch_json):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
        raise ValueError('Invalid saved publication report')
    saved = json.loads(path.read_bytes())
    ids = [item['nba_game_id'] for item in saved['evidence']]
    actual = audit(saved['run_id'], base=base, now=now, fetch=fetch, cohort_ids=ids)
    # A saved report is a replay recipe, never a substitute for live API verification.
    old = {k: v for k, v in saved.items() if k != 'checked_at_utc'}
    new = {k: v for k, v in actual.items() if k != 'checked_at_utc'}
    if source.canonical(old) != source.canonical(new):
        raise ValueError('Saved publication report differs from fresh API replay')
    return actual


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--run-id', type=int)
    group.add_argument('--replay', type=Path)
    args = parser.parse_args()
    result = replay(args.replay) if args.replay else audit(args.run_id)
    print(json.dumps(result, sort_keys=True, indent=2))
