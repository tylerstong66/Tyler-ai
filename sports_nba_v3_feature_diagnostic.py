"""Opt-in v3 source comparison against frozen features; no result enrollment."""
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path

import sports_nba_final_games_page_v3 as reader
import sports_nba_native_feature_cohort as native
from sports_expansion_audit import archive_path


def build(base=Path('.'), *, capture, provider_capture=None, now=None):
    base = Path(base); now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError('Aware v3 feature diagnostic clock required')
    now = now.astimezone(timezone.utc)
    parsed = reader.inspect(base, capture, now=now)
    path = archive_path(base/reader.receipts.ROOT/capture/'manifest.json')
    raw = path.read_bytes(); original = json.loads(raw)
    if hashlib.sha256(raw).hexdigest() != parsed['original_receipt_manifest_sha256']:
        raise ValueError('Original v3 diagnostic dependency changed')
    cohort = native.cohort
    records = cohort.features._existing(base, now, cohort.features._reference(base, now), {})
    if provider_capture is not None:
        if not isinstance(provider_capture, str) or not re.fullmatch(r'\d{8}T\d{12}Z', provider_capture):
            raise ValueError('Invalid v3 diagnostic provider capture')
        providers = [archive_path(base/cohort.source.ROOT/'captures'/provider_capture/'manifest.json')]
    else:
        providers = sorted((base/cohort.source.ROOT/'captures').glob('*/manifest.json'))
    if not providers: raise ValueError('Missing independent v3 diagnostic provider')
    provider_manifest, provider, provider_hash = cohort._provider(base, providers[-1], now)
    # An in-memory comparison input only. Never serialize it as a canonical
    # source receipt or pass it to an enrollment/settlement collector.
    view = {**original, 'parsed_final_page': parsed,
            'supported_final_game_count': parsed['daily_game_count'],
            'page_status': 'V3_DIAGNOSTIC_ONLY_NOT_AN_ENROLLED_RECEIPT'}
    report = native.classify(records, view, provider,
        provider_observed_at=provider_manifest['recorded_at_utc'], now=now)
    if (reader.receipts.replay(base, capture, now=now)['source_bytes_replayed'] is not True
            or path.read_bytes() != raw):
        raise ValueError('Original v3 diagnostic receipt changed during feature comparison')
    report.update(schema='tyler-nba-v3-frozen-feature-source-diagnostic-v1',
        diagnostic_only=True, existing_native_v2_lifecycle_changed=False,
        original_receipt_page_status=original['page_status'],
        source_provenance={
            'native_postgame_capture': capture,
            'native_manifest_sha256': parsed['original_receipt_manifest_sha256'],
            'native_original_body_sha256': parsed['original_body_sha256'],
            'provider_capture': providers[-1].parent.name,
            'provider_manifest_sha256': provider_hash,
            'provider_original_response_sha256': sorted(
                row['original_response_sha256'] for row in provider_manifest['snapshots']
                if row['league'] == 'NBA')})
    return report


if __name__ == '__main__':
    import argparse
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--base', type=Path, default=Path('.'))
    cli.add_argument('--capture', required=True)
    cli.add_argument('--provider-capture')
    args = cli.parse_args()
    print(json.dumps(build(args.base, capture=args.capture, provider_capture=args.provider_capture),
                     indent=2, sort_keys=True, allow_nan=False))
