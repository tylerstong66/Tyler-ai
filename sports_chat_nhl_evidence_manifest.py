"""Read-only, bounded retrieval of explicitly named NHL prospective evidence.

A manifest is a caller-provided list of archive paths, not proof of authenticity.
The existing original-source and model verifiers remain mandatory.
"""
import json

from sports_profitability_v1 import read_archive_bytes
from sports_chat_nhl_verified_adapter import nhl_verified_chat_comparison


def compare_nhl_manifest(manifest, archive_root, now=None):
    """Read exact bounded local JSON records; never scan or fetch remote sources."""
    if not isinstance(manifest, dict) or set(manifest) != {"prediction", "entry_quote"}:
        return {"status": "unavailable", "reason": "Explicit prediction and entry quote paths required", "NO_BET": True}
    try:
        records = {}
        for name in ("prediction", "entry_quote"):
            path = manifest[name]
            if not isinstance(path, str) or not path.endswith(".json") or len(path) > 300:
                raise ValueError("Bounded JSON evidence path required")
            raw = read_archive_bytes(archive_root, path, limit=1_000_000)
            record = json.loads(raw)
            if not isinstance(record, dict):
                raise ValueError("Original evidence must be a JSON record")
            records[name] = record
        return nhl_verified_chat_comparison(
            records["prediction"], records["entry_quote"], archive_root, now=now)
    except (ValueError, TypeError, KeyError, OSError, UnicodeError, OverflowError, RecursionError):
        return {"status": "unavailable", "reason": "Archived NHL evidence missing or failed verification", "NO_BET": True}
