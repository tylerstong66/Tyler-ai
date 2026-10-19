"""Source-backed college team-form diagnostics with separate sport protocols.

No NBA/NFL coefficients, fitting, prediction freezes or outcome grading.
Receipt availability and an unverified 24-hour reconstruction remain distinct.
"""
from collections import defaultdict
from datetime import datetime,timedelta,timezone,date
from pathlib import Path
import hashlib
import heapq
import json

import sports_expansion_historical_capture as history
import sports_expansion_observer as source
import sports_historical_content_seal as original_seal
import sports_historical_extension_seal as independent_seal
import sports_historical_fbs_crosscheck as crosscheck

PROTOCOLS={league:{'league':league,'prior_game_window':window,
    'feature_fields':['prior_games','mean_points_for','mean_points_against','mean_margin','days_since_prior_start'],
    'cutoff':'ONE_SECOND_BEFORE_EARLIEST_SOURCE_SCHEDULED_START',
    'reconstruction_delay_hours':24,'reconstruction_publication_time_attested':False,
    'season_state':'SEPARATE_SPORT_AND_SEASON_SPLIT',
    'history_scope':'CORROBORATED_SOURCE_SUBSET_NOT_CERTIFIED_COMPLETE_SCHEDULE',
    'missing_values':'NULL_NO_IMPUTED_AVERAGES_OR_REST'}
    for league,window in (('NCAAF_FBS',4),('NCAAM_D1',8))}


def digest(value):return hashlib.sha256(source.canonical(value)).hexdigest()


def _event(row,league,split):
    if row['league']!=league or row['split']!=split:
        raise ValueError('College feature record crossed sport or season split')
    starts=[source.utc(row[k]) for k in ('ncaa_start_utc','espn_start_utc')]
    low,high=history.SEASONS[league][split]
    if any(not date.fromisoformat(low)<=s.date()<=date.fromisoformat(high)+timedelta(days=1) for s in starts):
        raise ValueError('College feature game outside declared source season')
    available=source.utc(row['observed_available_at_utc'])
    if available<=max(starts):raise ValueError('College feature final predates source kickoff')
    scores=[row[k] for k in ('home_score','away_score')]
    if any(type(v) is not int or v<0 for v in scores) or scores[0]==scores[1]:
        raise ValueError('Invalid college feature final score')
    teams=[row[k] for k in ('home_team_id','away_team_id')]
    if (any(not isinstance(v,str) or not v.isdigit() or int(v)<=0 for v in teams)
            or teams[0]==teams[1]):raise ValueError('Invalid college feature team identity')
    return min(starts),max(starts),available


def chronological_features(records,*,league,split):
    if league not in PROTOCOLS or split not in ('train','validation'):
        raise ValueError('Unsupported college feature scope')
    games=[];nids=set();eids=set()
    for row in records:
        early,late,observed=_event(row,league,split)
        if row['ncaa_game_id'] in nids or row['espn_game_id'] in eids:
            raise ValueError('Duplicate college feature game identity')
        nids.add(row['ncaa_game_id']);eids.add(row['espn_game_id'])
        games.append((early,row['espn_game_id'],late,observed,row))
    window=PROTOCOLS[league]['prior_game_window']
    states={mode:defaultdict(list) for mode in ('observed_receipt_time','reconstructed_24h')}
    queues={mode:[] for mode in states};result=[]
    for start,game_id,late,observed,row in sorted(games):
        cutoff=start-timedelta(seconds=1);views={}
        for mode,state in states.items():
            queue=queues[mode]
            while queue and queue[0][0]<=cutoff:
                at,prior_id,prior_start,prior=heapq.heappop(queue)
                for side,opposite in (('home','away'),('away','home')):
                    team=prior[side+'_team_id']
                    state[team].append({'espn_game_id':prior_id,'source_record_sha256':digest(prior),
                        'available_at_utc':at.isoformat(),'start':prior_start,
                        'for':prior[side+'_score'],'against':prior[opposite+'_score']})
                    state[team]=sorted(state[team],key=lambda x:(x['start'],x['espn_game_id']))[-window:]
            sides={}
            for side in ('home','away'):
                previous=state[row[side+'_team_id']];count=len(previous)
                sides[side]={'prior_games':count,
                    'mean_points_for':sum(p['for'] for p in previous)/count if count else None,
                    'mean_points_against':sum(p['against'] for p in previous)/count if count else None,
                    'mean_margin':sum(p['for']-p['against'] for p in previous)/count if count else None,
                    'days_since_prior_start':(start-previous[-1]['start']).total_seconds()/86400 if count else None,
                    'source_history':[{k:v for k,v in p.items() if k not in ('start','for','against')}
                                      for p in previous]}
            views[mode]=sides
            at=observed if mode=='observed_receipt_time' else late+timedelta(hours=24)
            heapq.heappush(queue,(at,game_id,start,row))
        result.append({'league':league,'split':split,'espn_game_id':game_id,
            'ncaa_game_id':row['ncaa_game_id'],'feature_cutoff_utc':cutoff.isoformat(),
            'target_source_record_sha256':digest(row),'views':views,
            'historical_pregame_availability_attested':False,'eligible_for_model_training':False})
    return result


def _records(base,league,split,now,report):
    wanted_n={r['ncaa_game_id'] for r in report['corroborated_research_only']}
    wanted_e={r['espn_game_id'] for r in report['corroborated_research_only']}
    ncaa={};espn={}
    expected_n={r['ncaa_game_id']:{(ref.get('week',ref.get('source_date')),
                     ref['receipt_sha256'],ref['response_sha256']) for ref in r['ncaa_receipts']}
                for r in report['corroborated_research_only']}
    expected_e={r['espn_game_id']:{(ref['source_date'],ref['receipt_sha256'],ref['response_sha256'])
                                 for ref in r['espn_receipts']}
                for r in report['corroborated_research_only']}
    def retain(target,key,row):
        if key in target and target[key]!=row:
            raise ValueError('College feature source identity changed during replay')
        target[key]=row
    for saved,path,period in crosscheck._owned_sources(base,league,split,now):
        ref=(period.get('week',period.get('source_date')),
             hashlib.sha256(path.read_bytes()).hexdigest(),saved['original_response_sha256'])
        for row in saved['parsed_ncaa_games']:
            if row['ncaa_game_id'] in wanted_n:
                if ref not in expected_n[row['ncaa_game_id']]:
                    raise ValueError('College feature NCAA receipt changed during replay')
                retain(ncaa,row['ncaa_game_id'],row)
    for day in history.dates_by_league()[league][split]:
        if not history.verify_existing(base,league,split,day,as_of=now):continue
        path=base/history.ROOT/'sources'/league/split/(day+'.receipt.json')
        saved=json.loads(path.read_bytes())
        ref=(day,hashlib.sha256(path.read_bytes()).hexdigest(),saved['original_response_sha256'])
        for row in saved['parsed_provider_scoreboard']['games']:
            if row['game_id'] in wanted_e:
                if ref not in expected_e[row['game_id']]:
                    raise ValueError('College feature ESPN receipt changed during replay')
                retain(espn,row['game_id'],row)
    records=[]
    for agreement in report['corroborated_research_only']:
        n=ncaa.get(agreement['ncaa_game_id']);e=espn.get(agreement['espn_game_id'])
        if n is None or e is None:raise ValueError('Missing original college feature source game')
        if ((n['ncaa_home_score'],n['ncaa_away_score'])!=(agreement['home_score'],agreement['away_score'])
                or (e['home_score'],e['away_score'])!=(agreement['home_score'],agreement['away_score'])):
            raise ValueError('College source scores changed during feature replay')
        records.append({'league':league,'split':split,
            'ncaa_game_id':agreement['ncaa_game_id'],'espn_game_id':agreement['espn_game_id'],
            'home_team_id':e['home_team_id'],'away_team_id':e['away_team_id'],
            'home_score':agreement['home_score'],'away_score':agreement['away_score'],
            'ncaa_start_utc':datetime.fromtimestamp(int(n['source_start_time_epoch']),timezone.utc).isoformat(),
            'espn_start_utc':e['scheduled_start_utc'],
            'observed_available_at_utc':agreement['corroboration_available_at_utc'],
            'source_agreement':agreement,'ncaa_claim_sha256':digest(n),'espn_claim_sha256':digest(e)})
    return records


def build(base=Path('.'),*,league='NCAAF_FBS',split='train',now=None):
    if league not in PROTOCOLS or split not in ('train','validation'):
        raise ValueError('Unsupported college source feature scope')
    base=Path(base);now=now or datetime.now(timezone.utc)
    original_seal.verify(base);independent_seal.verify(base)
    report=crosscheck.build(base,league=league,split=split,now=now,verified_school_aliases=True)
    records=_records(base,league,split,now,report)
    features=chronological_features(records,league=league,split=split)
    return {'schema':'tyler-college-source-backed-feature-diagnostics-v1','league':league,'split':split,
        'protocol':PROTOCOLS[league],'protocol_sha256':digest(PROTOCOLS[league]),
        'crosscheck_report_sha256':digest(report),
        'school_identity_manifest_sha256':report['school_identity_manifest_sha256'],
        'source_game_index':{r['espn_game_id']:{'source_record_sha256':digest(r),'source_record':r} for r in records},
        'feature_rows':features,'corroborated_target_games':len(features),
        'other_pending_games':report['pending_or_quarantined'],
        'targets_with_both_team_histories':{mode:sum(all(r['views'][mode][side]['prior_games']>0
            for side in ('home','away')) for r in features) for mode in
            ('observed_receipt_time','reconstructed_24h')},
        'institutional_membership_verified':False,'source_scope_complete':False,
        'historical_pregame_features_verified':False,'model_training_enabled':False,
        'historical_evaluation_enabled':False,'forecasting_enabled':False,
        'promotion_allowed':False,'NO_BET':True,'actual_wagers':0}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--league',choices=tuple(PROTOCOLS),default='NCAAF_FBS')
    parser.add_argument('--split',choices=('train','validation'),default='train')
    args=parser.parse_args()
    print(json.dumps(build(league=args.league,split=args.split),sort_keys=True,indent=2))
