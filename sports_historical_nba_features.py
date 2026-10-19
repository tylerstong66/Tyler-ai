"""NBA-only source-backed chronological feature diagnostics; no fit or forecast.

Receipt availability is observed, whereas kickoff + 24 hours is an explicitly
unverified retrospective reconstruction. The two states never share results.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import heapq
import json

import sports_expansion_observer as source
import sports_historical_nba_crosscheck as crosscheck
import sports_historical_content_seal as original_seal
import sports_historical_extension_seal as independent_seal

WINDOW=10
RECONSTRUCTION_DELAY=timedelta(hours=24)
PROTOCOL={
    'league':'NBA','history_window':WINDOW,
    'features':['prior_games','mean_points_for','mean_points_against','mean_margin','days_since_prior_start'],
    'cutoff':'ONE_SECOND_BEFORE_EARLIEST_SOURCE_SCHEDULED_START',
    'reconstruction_result_delay_hours':24,'season_state':'ISOLATED_BY_SPLIT_AND_SEASON',
    'history_scope':'CORROBORATED_SOURCE_SUBSET_NOT_CERTIFIED_FULL_SCHEDULE',
    'missing_values':'NULL_NO_IMPUTED_AVERAGE_OR_REST',
    'reconstructed_publication_time_attested':False,
}


def digest(value):return hashlib.sha256(source.canonical(value)).hexdigest()


def _times(row,season):
    identifier=row['nba_game_id']
    if (row.get('league')!='NBA' or not isinstance(identifier,str) or len(identifier)!=10
            or not identifier.isdigit() or identifier[:3] not in ('002','004')
            or int(identifier[3:5])!=season%100):
        raise ValueError('NBA feature season/game identity mismatch')
    starts=[source.utc(row[k]) for k in ('nba_scheduled_start_utc','espn_scheduled_start_utc')]
    for start in starts:
        if (start.year if start.month>=7 else start.year-1)!=season:
            raise ValueError('NBA feature event outside isolated season')
    observed=[source.utc(row[k]) for k in ('nba_source_observed_at_utc','espn_source_observed_at_utc')]
    if min(observed)<=max(starts) or source.utc(row['corroboration_available_at_utc'])!=max(observed):
        raise ValueError('NBA feature result observation chronology mismatch')
    scores=[row[k] for k in ('home_score','away_score')]
    if any(type(n) is not int or n<0 for n in scores) or scores[0]==scores[1]:
        raise ValueError('Invalid NBA feature source final')
    if (not row.get('home_tricode') or not row.get('away_tricode') or
            row['home_tricode']==row['away_tricode']):
        raise ValueError('Invalid NBA feature opponent identity')
    return min(starts),max(starts),max(observed)


def chronological_features(rows,*,season):
    """Pure diagnostic engine. Only build() supplies verified receipt rows."""
    prepared=[];ids=set();espn_ids=set()
    for row in rows:
        start,latest,observed=_times(row,season)
        if row['nba_game_id'] in ids or row['espn_game_id'] in espn_ids:
            raise ValueError('Duplicate NBA feature identity')
        ids.add(row['nba_game_id']);espn_ids.add(row['espn_game_id'])
        prepared.append((start,row['nba_game_id'],latest,observed,row))
    states={mode:defaultdict(list)
            for mode in ('observed_receipt_time','reconstructed_24h')}
    queues={mode:[] for mode in states};out=[]
    for start,identifier,latest,observed,row in sorted(prepared):
        cutoff=start-timedelta(seconds=1);views={}
        for mode,state in states.items():
            pending=queues[mode]
            while pending and pending[0][0]<=cutoff:
                available,prior_id,prior_start,prior=heapq.heappop(pending)
                for side,opponent in (('home','away'),('away','home')):
                    team=prior[side+'_tricode']
                    state[team].append({
                        'nba_game_id':prior_id,'source_row_sha256':digest(prior),
                        'available_at_utc':available.isoformat(),'start':prior_start,
                        'points_for':prior[side+'_score'],'points_against':prior[opponent+'_score']})
                    state[team]=sorted(state[team],key=lambda x:(x['start'],x['nba_game_id']))[-WINDOW:]
            sides={}
            for side in ('home','away'):
                history=list(state[row[side+'_tricode']])
                # Availability order can differ from event order in later
                # receipt captures. Select the last ten eligible event times.
                history=sorted(history,key=lambda x:(x['start'],x['nba_game_id']))[-WINDOW:]
                count=len(history)
                sides[side]={'prior_games':count,
                    'mean_points_for':sum(x['points_for'] for x in history)/count if count else None,
                    'mean_points_against':sum(x['points_against'] for x in history)/count if count else None,
                    'mean_margin':sum(x['points_for']-x['points_against'] for x in history)/count if count else None,
                    'days_since_prior_start':(start-history[-1]['start']).total_seconds()/86400 if count else None,
                    'source_history':[{k:v for k,v in x.items() if k not in
                                      ('start','points_for','points_against')} for x in history]}
            views[mode]=sides
            available=observed if mode=='observed_receipt_time' else latest+RECONSTRUCTION_DELAY
            heapq.heappush(pending,(available,identifier,start,row))
        out.append({'nba_game_id':identifier,'espn_game_id':row['espn_game_id'],
                    'scheduled_start_utc':start.isoformat(),'feature_cutoff_utc':cutoff.isoformat(),
                    'target_source_row_sha256':digest(row),'views':views,
                    'historical_pregame_availability_attested':False,
                    'eligible_for_model_training':False})
    return out


def build(base=Path('.'),*,split='train',now=None):
    if split not in ('train','validation'):raise ValueError('Unsupported NBA feature split')
    now=now or datetime.now(timezone.utc)
    original_seal.verify(base);independent_seal.verify(base)
    report=crosscheck.build(base,split=split,now=now,exact_tipoff_identity=True)
    rows=report['corroborated_research_only']
    features=chronological_features(rows,season=2024 if split=='train' else 2025)
    return {'schema':'tyler-nba-source-backed-feature-diagnostics-v1','league':'NBA','split':split,
        'protocol':PROTOCOL,'protocol_sha256':digest(PROTOCOL),
        'crosscheck_report_sha256':digest(report),
        'source_game_index':{r['nba_game_id']:{'source_row_sha256':digest(r),'source_row':r} for r in rows},
        'feature_rows':features,'corroborated_target_games':len(features),
        'other_pending_games':report['pending_or_quarantined'],
        'targets_with_both_team_histories':{mode:sum(all(r['views'][mode][side]['prior_games']>0
            for side in ('home','away')) for r in features) for mode in
            ('observed_receipt_time','reconstructed_24h')},
        'historical_pregame_features_verified':False,'source_scope_complete':False,
        'model_training_enabled':False,'historical_evaluation_enabled':False,
        'forecasting_enabled':False,'promotion_allowed':False,'NO_BET':True,'actual_wagers':0}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split',choices=('train','validation'),default='train')
    args=parser.parse_args()
    print(json.dumps(build(split=args.split),sort_keys=True,indent=2))
