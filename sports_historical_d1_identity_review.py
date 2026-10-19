"""Propose D1 school identity evidence for review; never activate aliases.

Candidates require exact UTC time, home/away orientation and an independently
exact-named opponent. No fuzzy names, scores or outcomes select an institution.
"""
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import json

import sports_expansion_observer as source
import sports_expansion_historical_capture as history
import sports_historical_identity_audit as audit
import sports_historical_content_seal as original_seal
import sports_historical_extension_seal as independent_seal
import sports_ncaa_d1_historical_owned as owned
from sports_expansion_audit import bounded_gzip_read
from sports_ncaa_espn_identity import name


def propose(ncaa,espn):
    """Pure metadata review, requiring repeated anchors in both source splits."""
    splits=('train','validation')
    if set(ncaa)!=set(splits) or set(espn)!=set(splits):
        raise ValueError('Both D1 source identity splits required')
    for observations in (ncaa,espn):
        if ({r['game_id'] for r in observations['train']} &
                {r['game_id'] for r in observations['validation']}):
            raise ValueError('D1 source game identity crosses season splits')
    groups=defaultdict(lambda:defaultdict(list));uses=defaultdict(set)
    for split in splits:
        lookup=defaultdict(list)
        for game in ncaa[split]:
            for side in ('home','away'):
                lookup[(side,name(game[side]['school']),source.utc(game['start_utc']))].append(game)
        for event in espn[split]:
            at=source.utc(event['start_utc'])
            for side,opposite in (('home','away'),('away','home')):
                candidates=lookup[(opposite,name(event[opposite]['school']),at)]
                if len(candidates)!=1:continue
                contest=candidates[0];n=contest[side];e=event[side]
                if name(n['school'])==name(e['school']):continue
                if (not isinstance(n.get('seoname'),str) or not n['seoname'] or
                        not isinstance(e.get('team_id'),str) or
                        not e['team_id'].isdigit() or int(e['team_id'])<=0):continue
                key=(name(n['school']),name(e['school']),n['seoname'],e['team_id'])
                row={'ncaa_school':n['school'],'espn_school':e['school'],
                    'ncaa_game_id':contest['game_id'],'espn_game_id':event['game_id'],
                    'side':side,'exact_start_utc':at.isoformat(),
                    'exact_opponent':name(event[opposite]['school']),
                    'ncaa_receipts':contest['receipts'],'espn_receipts':event['receipts']}
                groups[key][split].append(row)
                uses[(split,'ncaa',contest['game_id'])].add(event['game_id'])
                uses[(split,'espn',event['game_id'])].add(contest['game_id'])
    original=defaultdict(set);targets=defaultdict(set);slugs=defaultdict(set);ids=defaultdict(set)
    for n,e,slug,team in groups:
        original[n].add((e,slug,team));targets[e].add((n,slug,team))
        slugs[slug].add(team);ids[team].add(slug)
    proposals=[];excluded=[]
    for key,parts in sorted(groups.items()):
        n,e,slug,team=key;reasons=[];evidence={}
        if len(original[n])!=1 or len(targets[e])!=1 or len(slugs[slug])!=1 or len(ids[team])!=1:
            reasons.append('AMBIGUOUS_OR_CHANGED_INSTITUTIONAL_IDENTITY')
        for split in splits:
            unique={(r['ncaa_game_id'],r['espn_game_id'],r['side']):r for r in parts[split]}
            rows=[unique[k] for k in sorted(unique)]
            if any(len(uses[(split,'ncaa',r['ncaa_game_id'])])!=1 or
                   len(uses[(split,'espn',r['espn_game_id'])])!=1 for r in rows):
                reasons.append('NON_BIJECTIVE_ANCHOR_GAME_IDENTITY')
            if len(rows)<2 or len({r['exact_opponent'] for r in rows})<2:
                reasons.append('INSUFFICIENT_DISTINCT_GAMES_AND_OPPONENTS_'+split.upper())
            evidence[split]=rows
        entry={'ncaa_normalized_school':n,'espn_normalized_school':e,
               'ncaa_seoname':slug,'espn_team_id':team,'evidence':evidence,
               'alias_activation_allowed':False,'institutional_identity_certified':False,
               'division_one_membership_verified':False}
        if reasons:excluded.append({**entry,'exclusion_reasons':sorted(set(reasons))})
        else:proposals.append({**entry,'review_required':True})
    return {'schema':'tyler-historical-d1-school-identity-review-v1',
        'candidate_proposals':proposals,'candidate_institutions':len(proposals),
        'excluded_candidates':excluded,'excluded_candidate_institutions':len(excluded),
        'score_or_outcome_used_for_identity':False,'runtime_aliases_added':0,
        'training_allowed':False,'historical_evaluation_enabled':False,
        'forecasting_enabled':False,'promotion_allowed':False,'NO_BET':True,'actual_wagers':0}


def _read(base,split,now,excluded):
    ns=defaultdict(list);es=defaultdict(list);quarantined=set()
    for day in owned.DATES[split]:
        saved=owned.verify(base,split,day,now=now)
        if saved is None:raise ValueError('Missing completed D1 identity source day')
        quarantined.update(q['ncaa_game_id'] for q in saved.get('quarantined_ncaa_contests',[]))
        folder=base/owned.ROOT/split;receipt=folder/(day+'.receipt.json')
        raw=bounded_gzip_read((folder/(day+'.json.gz')).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=saved['original_response_sha256']:
            raise ValueError('D1 identity source changed during replay')
        ref={'source_date':day,'receipt_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),
             'response_sha256':saved['original_response_sha256'],'observed_at_utc':saved['recorded_at_utc']}
        for game in json.loads(raw)['data']['contests']:
            teams={('home' if t['isHome'] else 'away'):{'school':t['nameShort'],
                    'seoname':t.get('seoname')} for t in game['teams']}
            if game.get('startTimeEpoch') is None:continue
            row={'game_id':str(game['contestId']),**teams,
                 'start_utc':datetime.fromtimestamp(int(game['startTimeEpoch']),timezone.utc).isoformat()}
            ns[row['game_id']].append((row,ref))
    for day in history.dates_by_league()['NCAAM_D1'][split]:
        if not history.verify_existing(base,'NCAAM_D1',split,day,as_of=now):
            raise ValueError('Missing completed D1 provider identity day')
        folder=base/history.ROOT/'sources'/'NCAAM_D1'/split
        receipt=folder/(day+'.receipt.json');receipt_bytes=receipt.read_bytes();saved=json.loads(receipt_bytes)
        raw=bounded_gzip_read((folder/(day+'.json.gz')).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=saved['original_response_sha256']:
            raise ValueError('D1 provider identity source changed during replay')
        ref={'source_date':day,'receipt_sha256':hashlib.sha256(receipt_bytes).hexdigest(),
             'response_sha256':saved['original_response_sha256'],'observed_at_utc':saved['recorded_at_utc']}
        for game in json.loads(raw)['events']:
            teams={t['homeAway']:{'school':t['team'].get('location'),
                   'team_id':str(t['team']['id'])} for t in game['competitions'][0]['competitors']}
            if any(not t['school'] for t in teams.values()):continue
            row={'game_id':str(game['id']),**teams,'start_utc':source.utc(game['date']).isoformat()}
            es[row['game_id']].append((row,ref))
    def collapse(observations,excluded_ids):
        result=[]
        for game_id,items in sorted(observations.items()):
            if game_id in excluded_ids or any(r!=items[0][0] for r,_ in items[1:]):continue
            result.append({**items[0][0],'receipts':[ref for _,ref in items]})
        return result
    return collapse(ns,quarantined),collapse(es,excluded)


def build(base=Path('.'),*,now=None):
    base=Path(base);now=now or datetime.now(timezone.utc)
    original_seal.verify(base);independent_seal.verify(base)
    integrity=audit.audit(base,now=now)
    excluded={r['game_id'] for r in integrity['quarantined'] if r['league']=='NCAAM_D1'}
    ncaa={};espn={}
    for split in ('train','validation'):ncaa[split],espn[split]=_read(base,split,now,excluded)
    return propose(ncaa,espn)


if __name__=='__main__':print(json.dumps(build(),sort_keys=True,indent=2))
