"""Separate native-v2 frozen-feature / v3 final-source lifecycle; research only."""
import json
from pathlib import Path

import sports_nba_native_feature_cohort as lifecycle
import sports_nba_native_pregame_features as features
import sports_nba_postgame_observation_v3 as post


def build(base=Path('.'), *, now=None, capture=None, provider_capture=None):
    # The legacy v3 lifecycle defaults to v1 frozen features. Pin the newer
    # feature reader here, including its own protocol and original-byte replay.
    report = lifecycle.build(base, now=now, _post=post, _capture=capture,
                             _provider_capture=provider_capture, _features=features)
    report.update(schema='tyler-nba-native-v2-feature-final-v3-lifecycle-v1',
                  feature_cohort='NATIVE_DAILY_V2_ONLY',
                  feature_protocol_sha256=features.PROTOCOL_SHA256,
                  frozen_feature_root=features.ROOT.as_posix(),
                  native_receipt_schema=post.PROTOCOL.schema,
                  original_v1_feature_cohort_unchanged=True,
                  cross_version_counts_must_not_be_pooled=True,
                  not_a_prediction=True,
                  source_comparison_only=True)
    return report


if __name__ == '__main__':
    print(json.dumps(build(), indent=2, sort_keys=True, allow_nan=False))
