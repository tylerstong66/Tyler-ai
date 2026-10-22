"""Read-only v3 native/ESPN final-source comparison to original frozen features.

Uses the separate canonical v3 receipts, never reinterprets v1/v2 receipts,
enrolls outcomes, grades forecasts, trains a model or collects new source data.
"""
from pathlib import Path
import json

import sports_nba_native_feature_cohort as native
import sports_nba_postgame_observation_v3 as post


def build(base=Path('.'), *, now=None, capture=None, provider_capture=None):
    report = native.build(base, now=now, _post=post,
                          _capture=capture, _provider_capture=provider_capture)
    report.update(schema='tyler-nba-native-final-break-frozen-feature-source-audit-v3',
                  native_receipt_schema=post.PROTOCOL.schema,
                  source_comparison_only=True,
                  original_v1_v2_v3_receipts_unchanged=True)
    return report


if __name__ == '__main__':
    print(json.dumps(build(), indent=2, sort_keys=True, allow_nan=False))
