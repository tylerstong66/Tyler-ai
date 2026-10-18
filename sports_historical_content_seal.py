"""Verify the frozen v1 source-byte index without certifying data/model use."""
from pathlib import Path
import hashlib
import json

import sports_expansion_historical_capture as history
import sports_ncaa_historical_owned as fbs

MANIFEST = history.ROOT / 'SOURCE_COMPLETION_2026_10_18.json'
MAX_FILE_BYTES = 8_500_000


def expected_paths():
    """The original v1 scope is fixed; later D1/NBA originals may append."""
    paths = []
    for league, splits in history.dates_by_league().items():
        for split, days in splits.items():
            for day in days:
                paths.extend(history.ROOT/'sources'/league/split/(day+suffix)
                             for suffix in ('.json.gz','.receipt.json'))
    for split in fbs.YEARS:
        for week in fbs.WEEKS:
            paths.extend(fbs.ROOT/split/(f'week-{week:02d}'+suffix)
                         for suffix in ('.json.gz','.receipt.json'))
    return sorted(paths)


def content_index(base=Path('.')):
    base = Path(base); index = []
    for relative in expected_paths():
        path = base/relative
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError('Missing, oversized or nonregular frozen historical input')
        index.append({'path':str(relative),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    raw = json.dumps(index,sort_keys=True,separators=(',',':')).encode()
    return len(index), hashlib.sha256(raw).hexdigest()


def verify(base=Path('.')):
    saved = json.loads((Path(base)/MANIFEST).read_bytes())
    if (saved.get('schema')!='tyler-completed-historical-source-acquisition-v1'
            or saved.get('NO_BET') is not True or type(saved.get('actual_wagers')) is not int
            or saved.get('actual_wagers')!=0
            or any(saved.get(key) is not False for key in (
                'training_allowed','historical_evaluation_enabled','forecasting_enabled',
                'promotion_allowed','official_schedule_completeness_certified'))):
        raise ValueError('Frozen historical manifest research guards changed')
    count,digest = content_index(base)
    if count!=saved.get('source_files') or digest!=saved.get('source_file_index_sha256'):
        raise ValueError('Frozen historical content index differs from completion snapshot')
    return {'schema':'tyler-frozen-historical-content-seal-v1',
            'indexed_source_files_verified':count,'original_index_digest_verified':True,
            'source_origin_or_publication_time_attested':False,
            'source_semantics_verified_by_this_seal':False,
            'training_allowed':False,'historical_evaluation_enabled':False,
            'forecasting_enabled':False,'promotion_allowed':False,
            'NO_BET':True,'actual_wagers':0}


if __name__=='__main__':
    print(json.dumps(verify(),sort_keys=True))
