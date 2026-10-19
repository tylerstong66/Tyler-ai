"""Read-only D1 feature lifecycle and corroborated source result observations."""
from datetime import datetime, timezone
from pathlib import Path
import json

import sports_d1_pregame_features as features
import sports_college_result_dataset as results
import sports_college_feature_cohort_core as core


def classify(records, original_snapshots, current, dataset, *, now):
    return core.classify(records, original_snapshots, current, dataset,
                         now=now, features=features, league='NCAAM_D1')


def build(base=Path('.'), *, now=None):
    base = Path(base); now = now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError('Aware D1 cohort clock required')
    snapshots = {}; original = features._reference(base, now)
    records = features._existing(base, now, original, snapshots, features.digest(original))
    paths = sorted((base/features.identity.ROOT/'captures').glob('*/manifest.json'))
    if not paths: raise ValueError('Missing D1 source crosswalk archive')
    stamp = paths[-1].parent.name
    current = snapshots.get(stamp) or features._snapshot(base, stamp)
    dataset = results.assemble(base, [p.parent.name for p in paths])
    report = classify(records, snapshots, current, dataset, now=now)
    report['source_provenance'] = {'crosswalk_capture': stamp,
        'crosswalk_manifest_sha256': current['manifest_sha256'],
        'ncaa_capture': current['manifest']['ncaa_capture'], 'espn_capture': current['manifest']['espn_capture'],
        'ncaa_manifest_sha256': current['manifest']['ncaa_manifest_sha256'],
        'espn_manifest_sha256': current['manifest']['espn_manifest_sha256'],
        'result_dataset_sha256': features.digest(dataset), 'result_captures_replayed': dataset['captures_replayed'],
        'result_captures_rejected': dataset['captures_rejected']}
    return report


if __name__ == '__main__':
    print(json.dumps(build(), sort_keys=True, indent=2))
