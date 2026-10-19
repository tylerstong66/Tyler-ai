"""Exact publication chronology for explicit MLB records with declared archives.

No fitting, forecast creation, prediction grading, or changes to sealed records.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

import sports_github_server_evidence as server
import sports_mlb_cross_cohort_audit as cohorts
import sports_mlb_legacy_source_inventory as inventory

WORKFLOW = '.github/workflows/college_nba_source_observation.yml'


def audit(selection, run_id, *, base=Path('.'), now=None, fetch=server.fetch_json):
    base = Path(base); now = now or datetime.now(timezone.utc)
    if not isinstance(selection, dict) or not 0 < len(selection) <= 100:
        raise ValueError('Explicit bounded archived-source cohort required')
    for path, digest in selection.items():
        if not isinstance(path, str) or not inventory.PATH.fullmatch(path):
            raise ValueError('Invalid archived-source cohort record path')
        cohorts._digest(digest)
    inventory._local(base, cohorts.HITTER_ROOT/'source_archives')
    run = server.run_observation(run_id, now=now, workflow=WORKFLOW, events=('push',), fetch=fetch)
    observed = cohorts.utc(run['server_created_at_utc'])
    blobs = {}; records = []
    for path, expected in sorted(selection.items()):
        if not isinstance(path, str) or not inventory.PATH.fullmatch(path):
            raise ValueError('Invalid archived-source cohort record path')
        record = inventory._local(base, path)
        row, proof = cohorts._hitter(record, base)
        if proof['file_sha256'] != expected:
            raise ValueError('Selected archived-source record bytes changed')
        if not proof['all_original_responses_replayed']:
            raise ValueError('Every selected original response must declare and replay its archive')
        if not cohorts.utc(proof['frozen_at_utc']) <= observed < cohorts.utc(proof['saved_start_utc']):
            raise ValueError('Server observation must follow freeze and precede saved start')
        raw, _ = cohorts._read(record)
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Original record changed during publication audit')
        blobs[path] = raw; sources = []
        for receipt in proof['source_receipts']:
            archive = cohorts.HITTER_ROOT/'source_archives'/receipt['source_archive_file']
            archive_path = inventory._local(base, archive)
            if not archive_path.is_file() or archive_path.stat().st_size > 700000:
                raise ValueError('Missing or oversized server-verifiable source archive')
            compressed = archive_path.read_bytes()
            original, data = cohorts.archives._decode(compressed, archive_path.name)
            if (hashlib.sha256(original).hexdigest() != receipt['original_response_sha256']
                    or cohorts.archives.canonical_digest(data) != receipt['response_sha256']):
                raise ValueError('Declared original source archive changed during publication audit')
            name = archive.as_posix()
            if name in blobs and blobs[name] != compressed:
                raise ValueError('Conflicting original source archive bytes')
            blobs[name] = compressed
            sources.append({'kind': receipt['kind'], 'source_url': receipt['source_url'],
                'receipt_retrieved_at_utc': receipt['retrieved_at_utc'], 'archive_path': name,
                'original_response_sha256': receipt['original_response_sha256'],
                'response_canonical_sha256': receipt['response_sha256']})
        records.append({'path': path, 'file_sha256': expected, 'game_id': row['game_id'],
            'record_digest_sha256': proof['record_digest_sha256'], 'frozen_at_utc': proof['frozen_at_utc'],
            'saved_start_utc': proof['saved_start_utc'], 'source_receipts': sources,
            'server_observed_after_freeze_before_saved_start': True})
    def verify(path):
        raw = blobs[path]
        digest = server.verify_blob(path, raw, run['head_sha'], fetch=fetch)
        return {'path': path, 'git_blob_sha1': digest, 'file_sha256': hashlib.sha256(raw).hexdigest(),
                'bytes': len(raw)}
    with ThreadPoolExecutor(max_workers=4) as pool:
        verified = list(pool.map(verify, sorted(blobs)))
    return {'schema': 'tyler-mlb-declared-source-publication-v1', 'repository': server.REPOSITORY,
        'checked_at_utc': now.isoformat(), 'selection': dict(sorted(selection.items())), 'run': run,
        'records': records, 'immutable_blobs': verified, 'hitter_records_verified': len(records),
        'distinct_source_archives_verified': len(blobs)-len(records),
        'claim_scope': 'EXACT_RECORD_AND_DECLARED_ARCHIVE_BLOBS_OBSERVED_BEFORE_EACH_SAVED_START',
        'all_declared_original_response_bytes_replayed': True,
        'saved_report_requires_fresh_server_and_blob_replay': True,
        'source_origin_certified': False, 'receipt_clock_independently_attested': False,
        'actual_first_pitch_attested': False, 'public_visibility_attested': False,
        'model_input_semantics_fully_recomputed': False, 'original_records_modified': False,
        'prediction_scores_computed': False, 'new_forecasts_created': 0,
        'forecasting_enabled': False, 'model_training_enabled': False,
        'historical_evaluation_enabled': False, 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


def replay(path, *, base=Path('.'), now=None, fetch=server.fetch_json):
    _, saved = cohorts._read(Path(path), limit=1_000_000)
    actual = audit(saved['selection'], saved['run']['run_id'], base=base, now=now, fetch=fetch)
    if ({k: v for k, v in actual.items() if k != 'checked_at_utc'} !=
            {k: v for k, v in saved.items() if k != 'checked_at_utc'}):
        raise ValueError('Saved source publication report differs from fresh replay')
    return actual


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--recipe', type=Path)
    group.add_argument('--replay', type=Path)
    args = parser.parse_args()
    if args.replay:
        report = replay(args.replay)
    else:
        _, recipe = cohorts._read(args.recipe, limit=1_000_000)
        report = audit(recipe['selection'], recipe['run_id'])
    print(json.dumps(report, sort_keys=True, indent=2))
