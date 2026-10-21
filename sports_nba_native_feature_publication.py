"""Separate live GitHub publication replay for native-daily NBA feature bytes."""
from datetime import datetime, timezone
import json
from pathlib import Path

import sports_nba_native_pregame_features as features
import sports_nba_feature_publication as shared
from sports_expansion_audit import archive_path

WORKFLOW = '.github/workflows/sports_research_integration.yml'
SCHEMA = 'tyler-nba-native-daily-feature-github-server-observation-v2'


def audit(run_id, *, base=Path('.'), now=None, fetch=shared.fetch_json, cohort_ids=None):
    base = Path(base); now = features._clock(now or datetime.now(timezone.utc))
    records = features._existing(base, now, features._reference(base, now), {})
    if cohort_ids is not None:
        ids = list(cohort_ids)
        if not ids or len(ids) != len(set(ids)) or not set(ids) <= set(records):
            raise ValueError('Invalid native NBA feature publication cohort')
        records = {key: records[key] for key in ids}
    originals = {}
    for key, row in records.items():
        path = archive_path(base/features.ROOT/(key+'.json'))
        if path.stat().st_size > 1_000_000: raise ValueError('Oversized native feature publication input')
        raw = path.read_bytes()
        if raw != features.source.canonical({'record': row, 'record_sha256': features.digest(row)}):
            raise ValueError('Original native feature changed during publication audit')
        originals[key] = raw
    report = shared._attest(records, originals, run_id, now, fetch, root=features.ROOT,
                            workflow=WORKFLOW, schema=SCHEMA)
    report.update(feature_protocol_sha256=features.PROTOCOL_SHA256,
                  source_scope='NATIVE_DAILY_FEATURE_PROTOCOL_ONLY',
                  original_v1_publication_evidence_unchanged=True,
                  cross_version_counts_must_not_be_pooled=True)
    return report


def replay(path, *, base=Path('.'), now=None, fetch=shared.fetch_json):
    path = archive_path(Path(path))
    if not path.is_file() or path.stat().st_size > 1_000_000:
        raise ValueError('Invalid bounded native publication recipe')
    saved = json.loads(path.read_bytes())
    actual = audit(saved['run_id'], base=base, now=now, fetch=fetch,
                   cohort_ids=[item['nba_game_id'] for item in saved['evidence']])
    old = {key: value for key, value in saved.items() if key != 'checked_at_utc'}
    new = {key: value for key, value in actual.items() if key != 'checked_at_utc'}
    if features.source.canonical(old) != features.source.canonical(new):
        raise ValueError('Native publication recipe differs from fresh server replay')
    return actual


if __name__ == '__main__':
    import argparse
    cli = argparse.ArgumentParser(description=__doc__)
    group = cli.add_mutually_exclusive_group(required=True)
    group.add_argument('--run-id', type=int); group.add_argument('--replay', type=Path)
    cli.add_argument('--base', type=Path, default=Path('.')); args = cli.parse_args()
    report = replay(args.replay, base=args.base) if args.replay else audit(args.run_id, base=args.base)
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
