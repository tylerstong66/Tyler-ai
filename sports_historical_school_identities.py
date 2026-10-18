"""Replay explicitly reviewed school spellings from both historical source splits.

This is identity metadata, never pregame feature availability or final grading.
No fuzzy matching, suffix rules, scores, winners or future-season aliases.
"""
from pathlib import Path
import hashlib
import json

import sports_expansion_historical_capture as history
import sports_ncaa_historical_owned as owned
import sports_ncaa_espn_identity as identity
from sports_expansion_audit import bounded_gzip_read

MANIFEST=history.ROOT/'school_identity_v1/NCAAF_FBS.json'
MANIFEST_SHA256='7163214bcb687b43baffbcbd36a57d3d5653564789250c0981b6f843774b34cd'


def load(base=Path('.'),*,league='NCAAF_FBS',split='train',now=None):
    if league!='NCAAF_FBS' or split not in owned.YEARS:
        raise ValueError('No reviewed historical school policy for requested scope')
    base=Path(base);path=base/MANIFEST
    if path.is_symlink() or not path.is_file() or path.stat().st_size>1_000_000:
        raise ValueError('Missing or invalid reviewed historical identity manifest')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA256:
        raise ValueError('Reviewed historical identity manifest digest mismatch')
    saved=json.loads(raw)
    if (saved.get('schema')!='tyler-historical-fbs-school-identities-v1'
            or saved.get('league')!=league or saved.get('NO_BET') is not True
            or type(saved.get('actual_wagers')) is not int or saved['actual_wagers']!=0
            or any(saved.get(k) is not False for k in ('score_or_outcome_used_for_identity',
                    'historical_pregame_availability_attested','training_allowed',
                    'forecasting_enabled','promotion_allowed'))):
        raise ValueError('Historical identity source scope or research guards changed')
    ncaa_cache={};espn_cache={};aliases={};targets=set()
    for entry in saved['entries']:
        original=identity.name(entry['ncaa_school']);target=identity.name(entry['espn_school'])
        if original in aliases or target in targets or original==target:
            raise ValueError('Ambiguous historical school alias mapping')
        seonames=set();team_ids=set()
        # Both original source seasons attest the spelling independently. The
        # requested split never borrows an unobserved spelling from 2026.
        if set(entry['evidence'])!=set(owned.YEARS):
            raise ValueError('Both historical identity evidence splits required')
        for part in owned.YEARS:
            nr=entry['evidence'][part]['ncaa'];er=entry['evidence'][part]['espn']
            week=nr['week'];day=er['source_date']
            if type(week) is not int or week not in owned.WEEKS:
                raise ValueError('Invalid historical school NCAA source week')
            if day not in history.dates_by_league()[league][part]:
                raise ValueError('Invalid historical school provider source date')
            if (part,week) not in ncaa_cache:
                record=owned.verify(base,part,week,now=now)
                if record is None:raise ValueError('Missing original NCAA identity evidence')
                folder=base/owned.ROOT/part
                receipt=folder/f'week-{week:02d}.receipt.json'
                original_bytes=bounded_gzip_read((folder/f'week-{week:02d}.json.gz').read_bytes())
                ncaa_cache[(part,week)]=(record,hashlib.sha256(receipt.read_bytes()).hexdigest(),
                    {str(g['contestId']):g for g in json.loads(original_bytes)['data']['contests']})
            record,digest,contests=ncaa_cache[(part,week)]
            if nr['receipt_sha256']!=digest or nr['response_sha256']!=record['original_response_sha256']:
                raise ValueError('NCAA identity evidence digest mismatch')
            game=contests.get(nr['contest_id'])
            if game is None:raise ValueError('Missing original NCAA identity contest')
            teams=[t for t in game['teams'] if t['isHome'] is nr['is_home']]
            if (len(teams)!=1 or teams[0]['nameShort']!=entry['ncaa_school']
                    or nr['school']!=entry['ncaa_school'] or teams[0]['seoname']!=nr['seoname']):
                raise ValueError('NCAA institutional spelling differs from original source')
            seonames.add(nr['seoname'])
            if (part,day) not in espn_cache:
                if not history.verify_existing(base,league,part,day,as_of=now):
                    raise ValueError('Missing original ESPN identity evidence')
                folder=base/history.ROOT/'sources'/league/part
                receipt=folder/(day+'.receipt.json');record_bytes=receipt.read_bytes()
                record=json.loads(record_bytes)
                original_bytes=bounded_gzip_read((folder/(day+'.json.gz')).read_bytes())
                espn_cache[(part,day)]=(record,hashlib.sha256(record_bytes).hexdigest(),
                    {str(g['id']):g for g in json.loads(original_bytes)['events']})
            record,digest,events=espn_cache[(part,day)]
            if er['receipt_sha256']!=digest or er['response_sha256']!=record['original_response_sha256']:
                raise ValueError('ESPN identity evidence digest mismatch')
            event=events.get(er['game_id'])
            if event is None:raise ValueError('Missing original ESPN identity event')
            teams=[t['team'] for t in event['competitions'][0]['competitors']
                   if t['homeAway']==er['home_away']]
            if (len(teams)!=1 or teams[0]['location']!=entry['espn_school']
                    or er['school']!=entry['espn_school'] or str(teams[0]['id'])!=er['team_id']):
                raise ValueError('ESPN institutional spelling differs from original source')
            team_ids.add(er['team_id'])
        if len(seonames)!=1 or len(team_ids)!=1:
            raise ValueError('Historical institutional identity changes between splits')
        aliases[original]=entry['espn_school'];targets.add(target)
    return {'aliases':aliases,'manifest_sha256':MANIFEST_SHA256,
            'policy':saved['review_policy'],'reviewed_school_spellings':len(aliases)}


if __name__=='__main__':
    result=load();print(json.dumps({k:v for k,v in result.items() if k!='aliases'},sort_keys=True))
