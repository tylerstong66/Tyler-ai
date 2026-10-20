"""Original NBA-owned closed-season receipts, research only and no model use."""
from pathlib import Path
from datetime import datetime, timezone, date, timedelta
from urllib.parse import urlencode
import gzip
import hashlib
import json

import sports_expansion_historical_capture as history
import sports_expansion_observer as source
import sports_nba_official_schedule_audit as nba
from sports_expansion_audit import archive_path, bounded_gzip_read, MAX_BLOB_SIZE

ROOT = history.ROOT/'nba_owned'
YEARS = {'train':2024,'validation':2025}
ENDPOINT = 'https://stats.nba.com/stats/scheduleleaguev2'
# Published nba_api 1.11.4 public-request profile; no cookies or credentials.
# https://github.com/swar/nba_api/blob/master/src/nba_api/stats/library/http.py
HEADERS = {
 'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
 'Accept':'application/json, text/plain, */*','Accept-Language':'en-US,en;q=0.5',
 'Referer':'https://www.nba.com/','Pragma':'no-cache','Cache-Control':'no-cache',
 'Sec-Ch-Ua':'"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
 'Sec-Ch-Ua-Mobile':'?0','Sec-Fetch-Dest':'empty'}


def season(split):
    if split not in YEARS:
        raise ValueError('Unsupported NBA historical split')
    year=YEARS[split]
    return f'{year}-{str(year+1)[-2:]}'


def url(split):
    return ENDPOINT+'?'+urlencode({'LeagueID':'00','Season':season(split)})


def parse(raw,split,observed):
    payload=json.loads(raw);schedule=payload.get('leagueSchedule')
    if not isinstance(schedule,dict) or schedule.get('leagueId')!='00' or schedule.get('seasonYear')!=season(split):
        raise ValueError('NBA original league or season identity mismatch')
    rows=nba.official_games(raw)
    low,high=history.SEASONS['NBA'][split]
    for row in rows:
        at=source.utc(row['tipoff_utc'])
        if int(row['nba_game_id'][3:5])!=YEARS[split]%100:
            raise ValueError('NBA historical game ID outside pinned season')
        if not date.fromisoformat(low)<=at.date()<=date.fromisoformat(high)+timedelta(days=1):
            raise ValueError('NBA historical game outside declared date split')
        if row['nba_status']==3 and observed<=at:
            raise ValueError('NBA historical final observed before scheduled start')
    return rows


def verify(base,split,*,now=None):
    selected=season(split);now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware NBA historical audit clock required')
    folder=Path(base)/ROOT/split
    blob=folder/(selected+'.json.gz');path=folder/(selected+'.receipt.json')
    archive_path(blob, allow_missing=True)
    archive_path(path, allow_missing=True)
    if not blob.exists() and not path.exists(): return None
    if not blob.exists() or not path.exists():
        raise ValueError('Missing NBA historical original source component')
    if blob.is_symlink() or path.is_symlink() or not blob.is_file() or not path.is_file():
        raise ValueError('NBA historical receipt must be a regular file')
    if path.stat().st_size > MAX_BLOB_SIZE:
        raise ValueError('Oversized NBA historical receipt')
    saved=json.loads(path.read_bytes())
    if (saved.get('schema')!='tyler-nba-owned-historical-season-v1'
            or saved.get('league')!='NBA' or saved.get('split')!=split
            or saved.get('season')!=selected or saved.get('source_url')!=url(split)
            or saved.get('NO_BET') is not True or type(saved.get('actual_wagers')) is not int
            or saved.get('actual_wagers')!=0
            or any(saved.get(k) is not False for k in ('model_training_enabled',
                   'forecasting_enabled','promotion_allowed','official_result_grading_enabled'))):
        raise ValueError('NBA historical source scope or research guard changed')
    at=source.utc(saved['recorded_at_utc'])
    if at>now: raise ValueError('NBA historical source observation is future-dated')
    if blob.stat().st_size>MAX_BLOB_SIZE: raise ValueError('Oversized NBA historical archive')
    raw=bounded_gzip_read(blob.read_bytes(),limit=nba.MAX_BYTES)
    if hashlib.sha256(raw).hexdigest()!=saved['original_response_sha256']:
        raise ValueError('NBA historical original response digest mismatch')
    if parse(raw,split,at)!=saved['parsed_nba_games']:
        raise ValueError('NBA historical normalization differs from raw source')
    return saved


def capture(fetch,*,base=Path('.'),split='auto',now=None):
    if split not in (*YEARS,'auto'): raise ValueError('Invalid NBA source acquisition split')
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError('Aware NBA source observation clock required')
    base=Path(base)
    known={(part,season(part)+suffix) for part in YEARS for suffix in ('.json.gz','.receipt.json')}
    for path in (base/ROOT).rglob('*'):
        if path.is_file() and path.relative_to(base/ROOT).parts not in known:
            raise ValueError('Unplanned NBA historical source file')
    old={part:verify(base,part,now=now) for part in YEARS}
    if split=='auto': split=next((part for part in YEARS if old[part] is None),'validation')
    if old[split] is not None:
        return {'split':split,'new_source_seasons':0,'model_training_enabled':False,
                'forecasting_enabled':False,'promotion_allowed':False,'NO_BET':True,'actual_wagers':0}
    if date.fromisoformat(history.SEASONS['NBA'][split][1])>=now.astimezone(timezone.utc).date():
        raise ValueError('NBA historical season is not closed')
    raw=fetch(url(split))
    if not isinstance(raw,bytes) or not raw or len(raw)>nba.MAX_BYTES:
        raise ValueError('Missing or oversized original NBA season response')
    rows=parse(raw,split,now)
    saved={'schema':'tyler-nba-owned-historical-season-v1','league':'NBA','split':split,
           'season':season(split),'source_url':url(split),'recorded_at_utc':now.astimezone(timezone.utc).isoformat(),
           'original_response_sha256':hashlib.sha256(raw).hexdigest(),'parsed_nba_games':rows,
           'transport_profile':'nba_api_1_11_4_public_request_headers',
           'model_training_enabled':False,'forecasting_enabled':False,'promotion_allowed':False,
           'official_result_grading_enabled':False,'NO_BET':True,'actual_wagers':0}
    folder=base/ROOT/split;folder.mkdir(parents=True,exist_ok=True)
    with (folder/(season(split)+'.json.gz')).open('xb') as stream: stream.write(gzip.compress(raw,mtime=0))
    with (folder/(season(split)+'.receipt.json')).open('xb') as stream: stream.write(source.canonical(saved))
    return {'split':split,'new_source_seasons':1,'official_source_games_observed':len(rows),
            'model_training_enabled':False,'forecasting_enabled':False,'promotion_allowed':False,
            'independent_result_crosscheck_complete':False,'NO_BET':True,'actual_wagers':0}


def fetch_bytes(target):
    import requests
    with requests.get(target,headers=HEADERS,timeout=30,allow_redirects=False,stream=True) as response:
        response.raise_for_status();raw=bytearray()
        for chunk in response.iter_content(65536):
            raw.extend(chunk)
            if len(raw)>nba.MAX_BYTES: raise ValueError('NBA HTTP response exceeds original 8 MB budget')
        return bytes(raw)


if __name__=='__main__':
    print(json.dumps(capture(fetch_bytes),sort_keys=True))
