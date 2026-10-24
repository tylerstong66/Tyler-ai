"""Original MLB response retention for future research receipts; no forecasts."""
from pathlib import Path
from urllib.parse import urlparse
import gzip
import hashlib
import json
import re
import subprocess

from sports_expansion_audit import archive_path, bounded_gzip_read, strict_json_loads

MAX_BYTES = 3_000_000
MAX_COMPRESSED = 3_500_000
FILENAME = re.compile(r'([0-9a-f]{64})\.json\.gz\Z')
ARCHIVE_DIR = 'benchmarks/mlb_hitter_props_shadow_v1/source_archives/'


def canonical_digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def _decode(blob, filename):
    match = FILENAME.fullmatch(filename)
    if not match or len(blob) > MAX_COMPRESSED:
        raise ValueError('Invalid or oversized MLB original source archive')
    raw = bounded_gzip_read(blob, limit=MAX_BYTES)
    if hashlib.sha256(raw).hexdigest() != match.group(1):
        raise ValueError('MLB original source response digest mismatch')
    data = strict_json_loads(raw)
    if not isinstance(data, dict):
        raise ValueError('MLB original source JSON is not an object')
    canonical_digest(data) # reject nonfinite values under the original reader policy
    return raw, data


def audit_directory(root):
    root = archive_path(root, directory=True, allow_missing=True)
    files = list(root.iterdir()) if root.exists() else []
    for path in files:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_COMPRESSED:
            raise ValueError('Unexpected MLB source archive entry')
        _decode(path.read_bytes(), path.name)
    return len(files)


def retain(root, raw, expected_canonical_sha256):
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise ValueError('Invalid MLB original response bytes')
    data = strict_json_loads(raw)
    if not isinstance(data, dict) or canonical_digest(data) != expected_canonical_sha256:
        raise ValueError('MLB response JSON differs from original reader normalization')
    digest = hashlib.sha256(raw).hexdigest(); filename = digest + '.json.gz'
    root = archive_path(root, directory=True, allow_missing=True)
    root.mkdir(parents=True, exist_ok=True)
    path = root / filename
    try:
        with path.open('xb') as stream:
            stream.write(gzip.compress(raw, mtime=0))
    except FileExistsError:
        if path.is_symlink() or path.stat().st_size > MAX_COMPRESSED:
            raise ValueError('Invalid retained MLB response archive')
        previous, _ = _decode(path.read_bytes(), filename)
        if previous != raw:
            raise ValueError('Existing MLB original response differs')
    return {'original_response_archive_schema': 'mlb-original-response-archive-v1',
            'original_response_sha256': digest, 'source_archive_file': filename}


def verify(root, evidence):
    if evidence.get('original_response_archive_schema') != 'mlb-original-response-archive-v1':
        raise ValueError('Legacy digest-only MLB receipt has no replayable original archive')
    filename = evidence.get('source_archive_file')
    match = FILENAME.fullmatch(filename) if isinstance(filename, str) else None
    if not match or match.group(1) != evidence.get('original_response_sha256'):
        raise ValueError('Invalid MLB original archive filename or digest')
    uri = urlparse(evidence['source_url'])
    if uri.scheme != 'https' or uri.netloc != 'statsapi.mlb.com' or not uri.path.startswith('/api/'):
        raise ValueError('Unexpected MLB source archive origin')
    path = archive_path(Path(root) / filename)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_COMPRESSED:
        raise ValueError('Missing or oversized MLB original response archive')
    _, data = _decode(path.read_bytes(), filename)
    if canonical_digest(data) != evidence['response_sha256']:
        raise ValueError('MLB original source normalization digest mismatch')
    return data


def inspect_staged_additions(repo='.'):
    # This guard is separate from the unchanged prediction publication guard.
    raw = subprocess.check_output(['git','diff','--cached','--name-status','-z'], cwd=repo)
    fields = raw.split(b'\0')
    if fields[-1:] == [b'']:
        fields.pop()
    if not fields or len(fields) % 2:
        raise ValueError('No complete MLB original source additions staged')
    for i in range(0, len(fields), 2):
        status, name = fields[i].decode('ascii'), fields[i+1].decode('utf-8')
        if status != 'A' or not name.startswith(ARCHIVE_DIR):
            raise ValueError('Only new MLB original response archives may be staged')
        filename = name[len(ARCHIVE_DIR):]
        if not FILENAME.fullmatch(filename):
            raise ValueError('Unexpected staged MLB source filename')
        mode = subprocess.check_output(['git','ls-files','--stage','--',name], cwd=repo).split()[0]
        if mode != b'100644':
            raise ValueError('Staged MLB original source must be a regular file')
        blob = subprocess.check_output(['git','show',':'+name], cwd=repo)
        _decode(blob, filename)
    return len(fields)//2


if __name__ == '__main__':
    print(json.dumps({'new_original_source_archives': inspect_staged_additions(),
                      'NO_BET': True, 'actual_wagers': 0}))
