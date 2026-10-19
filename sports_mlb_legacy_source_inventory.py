"""Read-only current archive matches for explicitly selected sealed MLB receipts.

A normalized JSON match is a present content observation, not evidence of
original wire bytes, source URL, publication time, or availability at freeze.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import re

import sports_mlb_cross_cohort_audit as cohorts
import sports_mlb_source_archives as archives

PATH = re.compile(re.escape(cohorts.HITTER_ROOT.as_posix()) + r'/predictions/[1-9][0-9]*_[1-9][0-9]*\.json\Z')


def _local(base, relative):
    current = base
    for part in Path(relative).parts:
        current = current/part
        if current.is_symlink():
            raise ValueError('Symlink in current inventory path')
    return current


def build(selection, *, base=Path('.')):
    """Selection maps literal original record paths to expected file SHA256s."""
    base = Path(base)
    if not isinstance(selection, dict) or not 0 < len(selection) <= 30000:
        raise ValueError('Explicit bounded hitter record selection required')
    for path, digest in selection.items():
        if not isinstance(path, str) or not PATH.fullmatch(path):
            raise ValueError('Selection contains an unexpected hitter path')
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('Selection requires exact original file digests')
    directory = _local(base, cohorts.HITTER_ROOT/'source_archives')
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        raise ValueError('Invalid current archive directory')
    paths = sorted(directory.iterdir()) if directory.exists() else []
    if len(paths) > 10000:
        raise ValueError('Oversized current source archive inventory')
    index = {}; archive_inventory = []
    for path in paths:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > archives.MAX_COMPRESSED:
            raise ValueError('Unexpected current source archive entry')
        raw, data = archives._decode(path.read_bytes(), path.name)
        digest = archives.canonical_digest(data)
        entry = {
            'path': path.relative_to(base).as_posix(),
            'archive_uncompressed_sha256': hashlib.sha256(raw).hexdigest(),
            'uncompressed_bytes': len(raw)}
        index.setdefault(digest, []).append(entry)
        archive_inventory.append({**entry, 'response_canonical_sha256': digest})
    rows = []; counts = Counter()
    for path, expected in sorted(selection.items()):
        _, proof = cohorts._hitter(_local(base, path), base)
        if proof['file_sha256'] != expected:
            raise ValueError('Selected original hitter bytes changed')
        for receipt in proof['source_receipts']:
            matches = index.get(receipt['response_sha256'], [])
            declared = receipt['source_replay_status'] == 'ORIGINAL_RESPONSE_BYTES_REPLAYED'
            status = ('DECLARED_ORIGINAL_ARCHIVE_REPLAYED' if declared else
                      'CURRENT_CANONICAL_JSON_MATCH_ONLY' if matches else
                      'NO_CURRENT_ARCHIVE_CONTENT_MATCH')
            counts[(receipt['kind'], status)] += 1
            rows.append({'record_path': path, 'record_file_sha256': expected,
                'kind': receipt['kind'], 'source_url': receipt['source_url'],
                'receipt_retrieved_at_utc': receipt['retrieved_at_utc'],
                'response_canonical_sha256': receipt['response_sha256'],
                'declared_original_archive_replayed': declared,
                'inventory_status': status, 'current_archive_candidates': matches,
                'candidate_original_wire_bytes_attested': False,
                'candidate_source_url_attested': False,
                'candidate_availability_at_freeze_attested': False})
    return {'schema': 'tyler-mlb-legacy-source-content-inventory-v1',
        'selection': dict(sorted(selection.items())), 'selected_hitter_records': len(selection),
        'current_archives_verified': len(paths), 'receipt_observations': len(rows),
        'current_archive_inventory': archive_inventory,
        'counts': [{'kind': kind, 'status': status, 'count': count}
                   for (kind, status), count in sorted(counts.items())], 'rows': rows,
        'archive_inventory_scope': 'CURRENT_LOCAL_FILES_WITHOUT_ORIGINAL_PUBLICATION_TIMING',
        'original_records_modified': False, 'original_source_validation_complete': False,
        'publication_chronology_checked': False, 'prediction_scores_computed': False,
        'new_forecasts_created': 0, 'forecasting_enabled': False, 'model_training_enabled': False,
        'historical_evaluation_enabled': False, 'promotion_allowed': False,
        'NO_BET': True, 'actual_wagers': 0}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cohort-report', type=Path, required=True,
                        help='Existing publication report used only to select exact hitter files')
    args = parser.parse_args()
    _, report = cohorts._read(args.cohort_report, limit=1_000_000)
    records = report['records']
    selection = {}
    for record in records:
        if record['cohort'] != 'hitter':
            continue
        if record['path'] in selection:
            raise ValueError('Duplicate hitter path in cohort selection')
        selection[record['path']] = record['file_sha256']
    print(json.dumps(build(selection), sort_keys=True, indent=2))
