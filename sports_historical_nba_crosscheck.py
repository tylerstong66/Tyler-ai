"""Replay NBA-owned and ESPN historical finals with per-game provenance."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import json
import hashlib

import sports_expansion_historical_capture as history
import sports_historical_identity_audit as audit
import sports_nba_historical_owned as owned
import sports_nba_official_schedule_audit as nba
import sports_nba_final_receipts as finals
import sports_expansion_observer as source
from sports_expansion_audit import bounded_gzip_read, strict_json_loads


def _provider_events(raw):
    """Recheck raw ESPN identities at the historical NBA join boundary."""
    payload = strict_json_loads(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get('events'), list):
        raise ValueError('Missing historical NBA provider event slate')
    events = {}
    for event in payload['events']:
        game_id = source._numeric_identity(event['id'], 'provider game')
        if game_id in events:
            raise ValueError('Repeated NBA provider event in historical crosscheck')
        events[game_id] = event
    return events


def build(base=Path('.'),*,split='train',now=None,exact_tipoff_identity=False):
    if split not in owned.YEARS: raise ValueError('Unsupported NBA historical split')
    if type(exact_tipoff_identity) is not bool: raise ValueError('Explicit NBA identity policy required')
    schema=('tyler-historical-nba-exact-tipoff-crosscheck-v2' if exact_tipoff_identity
            else 'tyler-historical-nba-source-crosscheck-v1')
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError('Aware historical NBA audit clock required')
    base=Path(base);integrity=audit.audit(base,now=now)
    excluded={row['game_id'] for row in integrity['quarantined'] if row['league']=='NBA'}
    evidence=defaultdict(list);rows=defaultdict(list);unsupported=set()
    for day in history.dates_by_league()['NBA'][split]:
        if not history.verify_existing(base,'NBA',split,day,as_of=now): continue
        folder=base/history.ROOT/'sources'/'NBA'/split
        path=folder/(day+'.receipt.json');receipt_bytes=path.read_bytes();saved=json.loads(receipt_bytes)
        raw=bounded_gzip_read((folder/(day+'.json.gz')).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=saved['original_response_sha256']:
            raise ValueError('NBA provider response changed during source replay')
        events=_provider_events(raw)
        ref={'source_date':day,'receipt_sha256':hashlib.sha256(receipt_bytes).hexdigest(),
             'response_sha256':saved['original_response_sha256'],'observed_at_utc':saved['recorded_at_utc']}
        for game in saved['parsed_provider_scoreboard']['games']:
            game_id=game['game_id']
            if game_id in excluded: continue
            sides={}
            for team in events[game_id]['competitions'][0]['competitors']:
                side=team['homeAway']
                if side in sides: raise ValueError('Duplicate NBA provider opponent side')
                try:
                    sides[side]=nba.tricode(team['team'].get('abbreviation'))
                except ValueError:
                    unsupported.add(game_id)
                    break
            if game_id in unsupported: continue
            if set(sides)!={'home','away'} or sides['home']==sides['away']:
                raise ValueError('Missing or identical NBA provider opponent codes')
            rows[game_id].append({**game,'espn_game_id':game_id,
                                 'home_tricode':sides['home'],'away_tricode':sides['away']})
            evidence[game_id].append(ref)
    conflicts={game_id for game_id,items in rows.items() if any(row!=items[0] for row in items[1:])}
    provider={game_id:items[0] for game_id,items in rows.items() if game_id not in conflicts and game_id not in unsupported}
    official=owned.verify(base,split,now=now)
    guards={'source_scope_complete':False,'independent_official_final_certification_complete':False,
            'historical_evaluation_enabled':False,'model_training_enabled':False,'training_allowed':False,
            'forecasting_enabled':False,'promotion_allowed':False,'NO_BET':True,'actual_wagers':0}
    unsupported_pending=[{'espn_game_id':game_id,'reason':'UNSUPPORTED_NBA_TEAM_CODES'}
                         for game_id in sorted(unsupported)]
    if exact_tipoff_identity:
        guards['game_identity_policy']='EXACT_UTC_TIPOFF_UNIQUE_WITHIN_30_MINUTES'
    if official is None:
        return {'schema':schema,'league':'NBA','split':split,
                'independent_nba_source_available':False,'two_source_final_agreements':0,
                'corroborated_research_only':[],'pending_or_quarantined':len(provider)+len(unsupported),
                'pending':[{'espn_game_id':game_id,'reason':'NO_ARCHIVED_INDEPENDENT_NBA_SEASON'}
                           for game_id in sorted(provider)]+unsupported_pending,**guards}
    times={game_id:min(source.utc(ref['observed_at_utc']) for ref in evidence[game_id]).isoformat()
           for game_id in provider}
    report=finals.classify(official['parsed_nba_games'],provider,
                          nba_observed_at=official['recorded_at_utc'],espn_observed_by_game=times,
                          exact_tipoff_identity=exact_tipoff_identity)
    if exact_tipoff_identity:
        report['game_identity_policy']=guards['game_identity_policy']
    report['pending'].extend(unsupported_pending)
    report['pending_or_quarantined']=len(report['pending'])
    path=base/owned.ROOT/split/(owned.season(split)+'.receipt.json')
    receipt_digest=hashlib.sha256(path.read_bytes()).hexdigest()
    for row in report['corroborated_research_only']:
        row['nba_receipt_sha256']=receipt_digest
        row['nba_response_sha256']=official['original_response_sha256']
        row['espn_receipts']=evidence[row['espn_game_id']]
    return {**report,'schema':schema,'league':'NBA','split':split,
            'independent_nba_source_available':True,'nba_source_game_ids':len(official['parsed_nba_games']),
            'espn_source_game_ids':len(provider)+len(unsupported),'conflicting_provider_game_ids':sorted(conflicts),
            'excluded_provider_game_ids':sorted(excluded),'training_allowed':False}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split',choices=tuple(owned.YEARS),default='train')
    parser.add_argument('--exact-tipoff-identity',action='store_true',
                        help='Separate historical repeat-fixture identity policy; preserves v1 replay')
    args=parser.parse_args()
    print(json.dumps(build(split=args.split,exact_tipoff_identity=args.exact_tipoff_identity),sort_keys=True,indent=2))
