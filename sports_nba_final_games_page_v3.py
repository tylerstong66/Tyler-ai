"""Read-only diagnostic for native regulation finals with explicit Final break status.

No collector uses this parser. Existing v1/v2 receipts retain their contracts.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import sports_nba_final_games_page as v1
import sports_nba_games_page_v2 as envelope
import sports_nba_postgame_observation_v2 as receipts
from sports_expansion_audit import archive_path, bounded_gzip_read


def parse(raw, *, requested_date, season, observed_at):
    result = v1._parse(raw, requested_date=requested_date, season=season,
                       observed_at=observed_at, document_reader=envelope.document,
                       break_status='Final')
    result.update(schema='tyler-nba-owned-daily-final-break-status-page-v3',
                  date_override_field_state='EXPLICIT_NULL',
                  date_override_active_attested=False,
                  game_break_status='Final', reader_scope='OPT_IN_DIAGNOSTIC_ONLY')
    return result


def inspect(base, capture, *, now=None):
    """Reinterpret verified original bytes without modifying a retained receipt."""
    base = Path(base)
    now = now or datetime.now(timezone.utc)
    replay = receipts.replay(base, capture, now=now)
    folder = base / receipts.ROOT / capture
    manifest_path = archive_path(folder / 'manifest.json')
    original = manifest_path.read_bytes()
    manifest = json.loads(original)
    # Replay already enforces the fixed archive filename, original schema,
    # clocks, canonical manifest and bounded source bytes.
    blob = archive_path(folder / 'nba_games.html.gz')
    if blob.stat().st_size > envelope.v1.MAX_BYTES:
        raise ValueError('Oversized native final diagnostic archive')
    raw = bounded_gzip_read(blob.read_bytes(), envelope.v1.MAX_BYTES)
    if len(raw) != manifest['raw_bytes'] or hashlib.sha256(raw).hexdigest() != manifest['raw_sha256']:
        raise ValueError('Native final diagnostic source digest mismatch')
    parsed = parse(raw, requested_date=manifest['requested_date'], season=manifest['season'],
                   observed_at=datetime.fromisoformat(manifest['recorded_at_utc']))
    if receipts.replay(base, capture, now=now) != replay or manifest_path.read_bytes() != original:
        raise ValueError('Native final diagnostic receipt changed during inspection')
    return {**parsed, 'capture': capture, 'original_receipt_page_status': replay['page_status'],
            'original_receipt_manifest_sha256': hashlib.sha256(original).hexdigest(),
            'source_bytes_replayed': True, 'fresh_source_observation': False,
            'receipt_rewritten': False, 'outcomes_enrolled': 0,
            'independent_final_agreement_verified': False,
            'prediction_accuracy_computed': False}


if __name__ == '__main__':
    import argparse
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--base', type=Path, default=Path('.'))
    cli.add_argument('--capture', required=True)
    args = cli.parse_args()
    print(json.dumps(inspect(args.base, args.capture), indent=2, sort_keys=True, allow_nan=False))
