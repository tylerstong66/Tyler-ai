"""Verify the separate completed D1/NBA original-byte index; no model use."""
from pathlib import Path
import hashlib
import json

import sports_ncaa_d1_historical_owned as d1
import sports_nba_historical_owned as nba
from sports_historical_content_seal import MAX_FILE_BYTES

MANIFEST=d1.history.ROOT/'INDEPENDENT_SOURCE_COMPLETION_2026_10_19.json'
MANIFEST_SHA256='e5e04fa5f776e767be47651410144b926b71ba29b18de3a9d6c90cb018d9819b'
GUARDS=('training_allowed','historical_evaluation_enabled','forecasting_enabled',
        'promotion_allowed','official_schedule_completeness_certified')


def expected_paths():
    paths=[]
    for split,days in d1.DATES.items():
        for day in days:
            paths.extend(d1.ROOT/split/(day+suffix) for suffix in ('.json.gz','.receipt.json'))
    for split in nba.YEARS:
        paths.extend(nba.ROOT/split/(nba.season(split)+suffix)
                     for suffix in ('.json.gz','.receipt.json'))
    return sorted(paths)


def content_index(base=Path('.')):
    base=Path(base);index=[]
    for relative in expected_paths():
        path=base/relative
        if (any((base/p).is_symlink() for p in (relative,*relative.parents)) or
                not path.is_file() or path.stat().st_size>MAX_FILE_BYTES):
            raise ValueError('Missing, oversized or nonregular frozen independent source')
        index.append({'path':relative.as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    return len(index),hashlib.sha256(json.dumps(index,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def verify(base=Path('.')):
    path=Path(base)/MANIFEST
    if path.is_symlink() or not path.is_file() or path.stat().st_size>1_000_000:
        raise ValueError('Missing or invalid independent-source completion manifest')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA256:
        raise ValueError('Independent-source completion manifest digest changed')
    saved=json.loads(raw)
    if (saved.get('schema')!='tyler-completed-independent-historical-sources-v1'
            or saved.get('NO_BET') is not True or type(saved.get('actual_wagers')) is not int
            or saved['actual_wagers']!=0 or any(saved.get(k) is not False for k in GUARDS)):
        raise ValueError('Independent-source completion research guards changed')
    count,digest=content_index(base)
    if count!=saved.get('source_files') or digest!=saved.get('source_file_index_sha256'):
        raise ValueError('Frozen independent-source index differs from completion snapshot')
    return {'schema':'tyler-frozen-independent-historical-content-seal-v1',
        'indexed_source_files_verified':count,'original_index_digest_verified':True,
        'source_origin_or_publication_time_attested':False,
        'source_semantics_verified_by_this_seal':False,
        **{k:False for k in GUARDS},'NO_BET':True,'actual_wagers':0}


if __name__=='__main__':print(json.dumps(verify(),sort_keys=True))
