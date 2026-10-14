"""Independent NHL/MLB team-Elo paper baselines; no NFL coefficients or wagers."""
import heapq
import json
import math
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
import sports_historical_benchmark as b
import sports_prospective_test as n

ROOT=Path('benchmarks/two_way_prospective')
CLUBS='ANA BOS BUF CAR CBJ CGY CHI COL DAL DET EDM FLA LAK MIN MTL NJD NSH NYI NYR OTT PHI PIT SEA SJS STL TBL TOR UTA VAN VGK WPG WSH'.split()
ESPN_PATH={'NHL':'hockey/nhl','MLB':'baseball/mlb'}
ALIASES={'NHL':{'WSH':'WSH','NJ':'NJD','SJ':'SJS','TB':'TBL','LA':'LAK','UTAH':'UTA'},'MLB':{'WSH':'WSH','WAS':'WSH','CHW':'CWS','AZ':'ARI','ATH':'ATH','OAK':'ATH'}}


def nhl_games(data):
    games=[]
    rows=data.get('games') or [g for d in data.get('gameWeek',[]) for g in d.get('games',[])]
    for g in rows:
        if g['gameType'] not in [2,3]:continue
        finished=g['gameState'] in ['OFF','FINAL'] and g.get('gameScheduleState')=='OK'
        games.append({'game_id':str(g['id']),'season':int(str(g['season'])[:4]),'kickoff':b.utc(g['startTimeUTC']).isoformat(),'home':g['homeTeam']['abbrev'],'away':g['awayTeam']['abbrev'],'home_id':str(g['homeTeam']['id']),'away_id':str(g['awayTeam']['id']),'home_score':g['homeTeam'].get('score'),'away_score':g['awayTeam'].get('score'),'regular':g['gameType']==2,'neutral':g.get('neutralSite'),'completed':finished,'state':'post' if finished else 'pre' if g['gameState'] in ['FUT','PRE'] and g.get('gameScheduleState')=='OK' else 'in'})
    return games


def mlb_games(data):
    games=[]
    for day in data.get('dates',[]):
        for g in day['games']:
            if g['gameType'] not in ['R','D','F','L','W']:continue
            status=g['status'];finished=status.get('abstractGameState')=='Final' and status.get('codedGameState')=='F' and status.get('detailedState')=='Final'
            pre=status.get('abstractGameState')=='Preview' and status.get('detailedState') in ['Scheduled','Pre-Game'] and status.get('startTimeTBD') is not True
            h,a=g['teams']['home'],g['teams']['away']
            games.append({'game_id':str(g['gamePk']),'season':int(g['season']),'kickoff':b.utc(g['gameDate']).isoformat(),'home':h['team'].get('abbreviation',str(h['team']['id'])),'away':a['team'].get('abbreviation',str(a['team']['id'])),'home_name':h['team']['name'],'away_name':a['team']['name'],'home_id':str(h['team']['id']),'away_id':str(a['team']['id']),'home_score':h.get('score'),'away_score':a.get('score'),'regular':g['gameType']=='R','neutral':None,'completed':finished,'state':'post' if finished else 'pre' if pre else 'in','probable_pitchers':{s:g['teams'][s].get('probablePitcher') for s in ['home','away']},'scheduled_innings':g.get('scheduledInnings')})
    return games


def unique_finals(games,cutoff):
    records={}
    for g in games:
        if not g['completed'] or b.utc(g['kickoff'])>=cutoff:continue
        if not all(isinstance(g[s+'_score'],int) and not isinstance(g[s+'_score'],bool) and g[s+'_score']>=0 for s in ['home','away']):raise ValueError('Malformed final scores')
        if g['home_score']==g['away_score']:raise ValueError('Two-way final cannot tie')
        if g['home_id']==g['away_id']:raise ValueError('Team identity mismatch')
        if g['game_id'] in records:
            old=records[g['game_id']]
            if any(old[k]!=g[k] for k in ['home_id','away_id','home_score','away_score']):raise ValueError('Conflicting duplicate final')
            if old['kickoff']!=g['kickoff']:
                old['kickoff']=max(old['kickoff'],g['kickoff'])
                old['historical_resumption_ambiguous']=True
        else:records[g['game_id']]=g
    return sorted(records.values(),key=lambda g:(g['kickoff'],g['game_id']))


class Ratings:
    def __init__(self,config):
        self.config=config;self.elo=defaultdict(lambda:1500.0);self.season=None;self.used=0
    def season_start(self,season):
        if self.season is not None and season!=self.season:
            for team in self.elo:self.elo[team]=1500+(self.elo[team]-1500)*2/3
        self.season=season
    def x(self,g):return [1.0,(self.elo[g['home_id']]-self.elo[g['away_id']])/200]
    def probability(self,g):
        offset=0 if g['neutral'] is True else self.config['home_offset']
        return b.sigmoid((self.elo[g['home_id']]-self.elo[g['away_id']]+offset)*math.log(10)/400)
    def apply(self,g):
        delta=self.config['k']*((g['home_score']>g['away_score'])-self.probability(g))
        self.elo[g['home_id']]+=delta;self.elo[g['away_id']]-=delta;self.used+=1


def feature_rows(history,config):
    state=Ratings(config);pending=[];rows=[]
    for g in history:
        cutoff=b.utc(g['kickoff'])-timedelta(seconds=1)
        while pending and pending[0][0]<=cutoff:
            _,_,prior=heapq.heappop(pending);state.apply(prior)
        state.season_start(g['season'])
        rows.append({'data':g,'x':state.x(g),'game':b.Game(g['game_id'],g['season'],0,'REG',b.utc(g['kickoff']),g['home_id'],g['away_id'],g['neutral'] is True,g['home_score'],g['away_score'],None,None)})
        heapq.heappush(pending,(b.utc(g['kickoff'])+timedelta(hours=config['result_delay_hours']),g['game_id'],g))
    return rows


def pregame(history,target,cutoff,config):
    state=Ratings(config);pending=[]
    if cutoff>=b.utc(target['kickoff']):raise ValueError('Pregame cutoff required')
    for g in history:
        if b.utc(g['kickoff'])>=cutoff:break
        while pending and pending[0][0]<=b.utc(g['kickoff'])-timedelta(seconds=1):
            _,_,prior=heapq.heappop(pending);state.apply(prior)
        state.season_start(g['season'])
        heapq.heappush(pending,(b.utc(g['kickoff'])+timedelta(hours=config['result_delay_hours']),g['game_id'],g))
    while pending and pending[0][0]<=cutoff:
        _,_,prior=heapq.heappop(pending);state.apply(prior)
    state.season_start(target['season'])
    return state.x(target),state.probability(target),state.used


def fit_model(history,config,protocol):
    rows=feature_rows(history,config)
    training=[r for r in rows if r['data']['season']==2025 and r['data']['regular'] and not r['data'].get('historical_resumption_ambiguous')]
    minimum=1200 if config['sport']=='NHL' else 2400
    if len(training)<minimum:raise ValueError('Prior full-season training coverage incomplete')
    model=b.fit(training,protocol['l2_penalty'],dimension=2)
    model.update(version=config['sport'].lower()+'-team-elo-logistic-v1',sport=config['sport'],features=['intercept','elo_difference_200'],frozen_at=n.now().isoformat(),training_season=2025,training_games=len(training),training_only_no_independent_validation=True,availability_effect_enabled=False,protocol_sha256=b.sha256(b.canonical(protocol)),history_sha256=b.sha256(b.canonical(history)))
    return model


def espn_events(data,sport):
    records=[]
    for e in data.get('events',[]):
        co=e['competitions'][0];sides={r['homeAway']:r for r in co['competitors']}
        alias=lambda s:ALIASES[sport].get(sides[s]['team']['abbreviation'],sides[s]['team']['abbreviation'])
        odds=[]
        for o in co.get('odds',[]):
            ml=o.get('moneyline',{});h,a=[ml.get(s,{}).get('close',{}).get('odds') for s in ['home','away']]
            if h is not None and a is not None:odds.append({'provider':o.get('provider',{}).get('name'),'home_moneyline':b.price(str(h)),'away_moneyline':b.price(str(a))})
        records.append({'event_id':e['id'],'kickoff':b.utc(e['date']).isoformat(),'home':alias('home'),'away':alias('away'),'home_name':sides['home']['team']['displayName'],'away_name':sides['away']['team']['displayName'],'home_score':int(sides['home'].get('score',0)),'away_score':int(sides['away'].get('score',0)),'state':e['status']['type']['state'],'completed':e['status']['type'].get('completed',False),'neutral':co.get('neutralSite'),'odds':odds})
    return records


def match(g,events,sport):
    def identity(e):
        return all(e[s]==g[s] for s in ['home','away']) if sport=='NHL' else all(e[s+'_name']==g[s+'_name'] for s in ['home','away'])
    matches=[e for e in events if identity(e) and b.utc(e['kickoff'])==b.utc(g['kickoff'])]
    if len(matches)!=1:raise ValueError('Exact official/ESPN matchup and kickoff match required')
    if isinstance(g.get('neutral'),bool) and isinstance(matches[0].get('neutral'),bool) and g['neutral']!=matches[0]['neutral']:raise ValueError('Official/ESPN venue disagreement')
    return matches[0]


def match_final(g,events,sport,pred):
    """Allow a small NHL provider time revision only for the saved final event.

    Enrollment still uses exact start times. Official identity/time must already
    match the immutable forecast, and settle() separately requires equal scores.
    MLB retains exact times to avoid confusing doubleheaders or resumptions.
    """
    if sport!='NHL':return match(g,events,sport)
    pinned=[e for e in events if e['event_id']==pred['event_id']]
    if len(pinned)!=1:raise ValueError('Unique saved ESPN final event required')
    e=pinned[0]
    difference=abs(b.utc(e['kickoff'])-b.utc(g['kickoff']))
    if difference:
        if not g['completed'] or not e['completed'] or e['state']!='post' or difference>timedelta(minutes=15):
            raise ValueError('NHL final start-time revision exceeds verification policy')
    # Validate the same matchup and venue at the provider's revised timestamp;
    # the original official and saved timestamps remain untouched.
    return match({**g,'kickoff':e['kickoff']},pinned,sport)


def record_forecasts(root,capture,history,games,events,model,config,availability):
    new=[];excluded=[]
    for g in sorted(games,key=lambda g:(g['kickoff'],g['game_id'])):
        path=root/'predictions'/(g['game_id']+'.json')
        if path.exists():continue
        clock=n.now()
        if not clock<b.utc(g['kickoff'])<=clock+timedelta(hours=24):continue
        try:
            e=match(g,events,config['sport'])
            if g['state']!='pre' or e['state']!='pre':raise ValueError('Game has started or is not normally scheduled')
            x,fixed,used=pregame(history,g,clock,config)
            probability=b.sigmoid(b.dot(model['weights'],x))
            observed=e.get('market_observed_at') or next(s['retrieved_at'] for s in capture.evidence if 'scoreboard' in s['source_url'])
            data={'sport':config['sport'],'game_id':g['game_id'],'event_id':e['event_id'],'home':e['home'],'away':e['away'],'home_id':g['home_id'],'away_id':g['away_id'],'season':g['season'],'kickoff':g['kickoff'],'generated_at':clock.isoformat(),'recorded_at':n.now().isoformat(),'model_sha256':b.sha256(b.canonical(model)),'features':x,'prior_results_used':used,'model':{'home':probability,'away':1-probability},'fixed_elo':{'home':fixed,'away':1-fixed},'market':n.binary_market(e['odds']),'market_observed_at':observed,'availability':availability.get(g['game_id'],{'coverage':'unknown','effect_enabled':False}),'source_snapshots':capture.evidence,'NO_BET':True,'actual_wagers':0}
            if b.utc(data['recorded_at'])>=b.utc(g['kickoff']) or clock<b.utc(model['frozen_at']):raise ValueError('Recording outside frozen pregame window')
            if any(b.utc(s['retrieved_at'])>clock for s in capture.evidence):raise ValueError('Future source snapshot')
            data['sha256']=b.sha256(b.canonical(data));n.write_json(path,data,exclusive=True);new.append(g['game_id'])
        except ValueError as error:excluded.append({'game_id':g['game_id'],'reason':str(error)})
    return new,excluded


def settle(root,capture,games,events,sport):
    new=[];errors=[]
    for path in (root/'predictions').glob('*.json'):
        if (root/'results'/path.name).exists():continue
        pred=json.loads(path.read_text());g=next((g for g in games if g['game_id']==pred['game_id']),None)
        if not g or not g['completed']:continue
        try:
            if any(g[s+'_id']!=pred[s+'_id'] for s in ['home','away']) or b.utc(g['kickoff'])!=b.utc(pred['kickoff']):raise ValueError('Final identity differs from saved forecast')
            e=match_final(g,events,sport,pred)
            if e['event_id']!=pred['event_id'] or not e['completed'] or e['state']!='post':continue
            if any(g[s+'_score']!=e[s+'_score'] for s in ['home','away']):raise ValueError('Final scores disagree')
            if not all(isinstance(g[s+'_score'],int) and not isinstance(g[s+'_score'],bool) and g[s+'_score']>=0 for s in ['home','away']):raise ValueError('Malformed final scores')
            if g['home_score']==g['away_score']:raise ValueError('Tied final remains pending')
            digest=pred.pop('sha256')
            if digest!=b.sha256(b.canonical(pred)):raise ValueError('Saved forecast hash mismatch')
            if not b.utc(pred['generated_at'])<=b.utc(pred['recorded_at'])<b.utc(g['kickoff']):raise ValueError('Late or inconsistent forecast timestamps')
            outcome='home' if g['home_score']>g['away_score'] else 'away'
            scores={}
            probs={k:pred[k]['home'] for k in ['model','fixed_elo']}
            if pred['market']:probs['market']=pred['market']['conditional_home_probability']
            for key,probability in probs.items():scores[key]={'brier':2*(probability-(outcome=='home'))**2,'log_loss':b.conditional_loss(probability,outcome),'correct':('home' if probability>=.5 else 'away')==outcome}
            verification={'method':'exact_kickoff' if b.utc(g['kickoff'])==b.utc(e['kickoff']) else 'nhl_saved_event_bounded_start_time','event_id':e['event_id'],'official_kickoff':g['kickoff'],'espn_kickoff':e['kickoff'],'start_time_difference_seconds':abs((b.utc(e['kickoff'])-b.utc(g['kickoff'])).total_seconds())}
            record={'sport':sport,'game_id':g['game_id'],'outcome':outcome,'home_score':g['home_score'],'away_score':g['away_score'],'verified_at':n.now().isoformat(),'prediction_sha256':digest,'scores':scores,'source_snapshots':capture.evidence,'match_verification':verification}
            n.write_json(root/'results'/path.name,record,exclusive=True);new.append(g['game_id'])
        except ValueError as error:errors.append({'game_id':g['game_id'],'reason':str(error)})
    return new,errors


def report(root,sport):
    predictions=[json.loads(p.read_text()) for p in (root/'predictions').glob('*.json')]
    results=[json.loads(p.read_text()) for p in (root/'results').glob('*.json')]
    paired=[r for r in results if 'market' in r['scores']]
    mean=lambda values:sum(values)/len(values) if values else None
    metrics={key:{name:mean([r['scores'][key][name] for r in paired]) for name in ['brier','log_loss','correct']} for key in ['model','fixed_elo','market']}
    summary={'sport':sport,'recorded':len(predictions),'settled':len(results),'pending':len(predictions)-len(results),'paired_games':len(paired),'paired_metrics':metrics,'first_review_milestone':100,'enrollment_cap':None,'availability_effect_enabled':False,'NO_BET':True,'actual_wagers':0}
    n.write_json(root/'summary.json',summary)
    lines=[f'# Tyler {sport} prospective paper test','',f"Recorded: **{len(predictions)}** · Settled: **{len(results)}** · Pending: **{len(predictions)-len(results)}**",'', '**NO BET — actual wagers $0.**','', 'Frozen team-Elo logistic model versus fixed Elo and timestamped market odds. No NFL coefficients, goalie or pitcher model effects. Historical fitting is training only; this is the fresh independent test.','', '| Model | Paired games | Brier | Log loss | Accuracy |','|---|---:|---:|---:|---:|']
    for key,m in metrics.items():
        fmt=lambda x:'Pending' if x is None else f'{x:.4f}'
        accuracy='Pending' if m['correct'] is None else f"{m['correct']:.1%}"
        lines.append(f"| {key} | {len(paired)} | {fmt(m['brier'])} | {fmt(m['log_loss'])} | {accuracy} |")
    lines+=['','| Game | Start (Eastern) | Model pick | Win probability |','|---|---|---|---:|']
    for pred in sorted(predictions,key=lambda p:(p['kickoff'],p['game_id'])):
        side='home' if pred['model']['home']>=.5 else 'away';date=b.utc(pred['kickoff']).astimezone(ZoneInfo('America/New_York')).strftime('%b %d %I:%M %p')
        lines.append(f"| {pred['away']} at {pred['home']} | {date} | {pred[side]} | {pred['model'][side]:.1%} |")
    lines+=['','All eligible regular-season and playoff games are enrolled before start, including games without odds (unpriced games are excluded only from paired market metrics). First review after 100 settled games; enrollment continues. Unknown starters/lineups stay unknown. Delays or source conflicts can leave coverage gaps. These are experimental forecasts, not betting recommendations.','']
    (root/'RESULTS.md').write_text('\n'.join(lines));return summary


def read_capture(capture,url,parser,name):
    raw,e=capture.get(url);data=parser(json.loads(raw));capture.retain(name,data,e);return data


def availability_snapshot(capture,g,sport):
    if sport=='MLB':
        url='https://statsapi.mlb.com/api/v1.1/game/'+g['game_id']+'/feed/live'
        raw,e=capture.get(url);data=json.loads(raw);gd=data['gameData']
        if str(data.get('gamePk'))!=g['game_id'] or b.utc(gd['datetime']['dateTime'])!=b.utc(g['kickoff']) or any(str(gd['teams'][s]['id'])!=g[s+'_id'] for s in ['home','away']):raise ValueError('Official MLB availability identity mismatch')
        lineups={}
        for side in ['home','away']:
            box=data.get('liveData',{}).get('boxscore',{}).get('teams',{}).get(side,{})
            order=box.get('battingOrder',[]);players=box.get('players',{})
            lineups[side]=[players['ID'+str(i)]['person'] for i in order] if len(order)==9 and len(set(order))==9 and all('ID'+str(i) in players for i in order) else None
        value={'probable_pitchers':gd.get('probablePitchers',{}),'published_batting_orders':lineups,'pitcher_status':'probable_not_confirmed','effect_enabled':False}
    else:
        url='https://api-web.nhle.com/v1/gamecenter/'+g['game_id']+'/landing'
        raw,e=capture.get(url);data=json.loads(raw)
        if str(data.get('id'))!=g['game_id'] or b.utc(data['startTimeUTC'])!=b.utc(g['kickoff']) or any(str(data[s+'Team']['id'])!=g[s+'_id'] for s in ['home','away']):raise ValueError('Official NHL availability identity mismatch')
        value={'confirmed_starting_goalies':{'home':None,'away':None},'goalie_comparison_is_not_starter_confirmation':True,'effect_enabled':False}
    value['source_url']=url;value['retrieved_at']=e['retrieved_at'];value['original_response_sha256']=e['response_sha256']
    capture.retain('availability_'+g['game_id']+'.json',value,e);return value


def run_sport(sport,source_cache=None):
    root=ROOT/sport.lower();protocol=json.loads((ROOT/'protocol.json').read_text());config=protocol[sport]
    history=json.loads((root/'history.json').read_text());model=json.loads((root/'model.json').read_text())
    pinned=json.loads((ROOT/'frozen_assets.json').read_text())
    for name,digest in pinned.items():
        if b.sha256((ROOT/name).read_bytes())!=digest:raise ValueError('Frozen asset changed')
    if model['history_sha256']!=b.sha256(b.canonical(history)) or model['protocol_sha256']!=b.sha256(b.canonical(protocol)):raise ValueError('Frozen history/protocol mismatch')
    capture=n.Capture(root/'captures'/n.now().strftime('%Y%m%dT%H%M%S%fZ'),source_cache,root/'snapshots')
    clock=n.now();today=clock.astimezone(ZoneInfo('America/New_York')).date()
    if sport=='NHL':
        start_year=clock.year if clock.month>=7 else clock.year-1;season=str(start_year)+str(start_year+1)
        def fetch_club(club):
            url=f'https://api-web.nhle.com/v1/club-schedule-season/{club}/{season}'
            return read_capture(capture,url,nhl_games,'history_'+club+'.json')
        with ThreadPoolExecutor(max_workers=6) as executor:current=[g for rows in executor.map(fetch_club,CLUBS) for g in rows]
    else:
        url=f'https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={clock.year}-03-01&endDate={today.isoformat()}&hydrate=linescore'
        current=read_capture(capture,url,mlb_games,'current_history.json')
    # Only actual verified finals can enter feature history, at the delay cutoff.
    current_finals=unique_finals(current,clock)
    observed=json.loads((root/'observed_history.json').read_text()) if (root/'observed_history.json').exists() else []
    combined=unique_finals(history+observed+current_finals,clock)
    n.write_json(root/'observed_history.json',unique_finals(observed+current_finals,clock))
    dates={today.isoformat(),(today+timedelta(days=1)).isoformat()}
    dates|={b.utc(json.loads(p.read_text())['kickoff']).astimezone(ZoneInfo('America/New_York')).date().isoformat() for p in (root/'predictions').glob('*.json') if not (root/'results'/p.name).exists()}
    games=[];events=[]
    for day in sorted(dates):
        if sport=='NHL':url='https://api-web.nhle.com/v1/schedule/'+day;parser=nhl_games
        else:url='https://statsapi.mlb.com/api/v1/schedule?sportId=1&date='+day+'&hydrate=probablePitcher,linescore,team';parser=mlb_games
        games+=read_capture(capture,url,parser,'official_'+day+'.json')
        url='https://site.api.espn.com/apis/site/v2/sports/'+ESPN_PATH[sport]+'/scoreboard?dates='+day.replace('-','')
        day_events=read_capture(capture,url,lambda d:espn_events(d,sport),'espn_'+day+'.json')
        for event in day_events:event['market_observed_at']=capture.evidence[-1]['retrieved_at']
        events+=day_events
    # NHL daily endpoints return overlapping weeks; preserve one exact event.
    deduplicated={}
    for g in games:
        if g['game_id'] in deduplicated and any(g[k]!=deduplicated[g['game_id']][k] for k in ['kickoff','home_id','away_id','home_score','away_score','state']):raise ValueError('Daily official snapshots conflict')
        deduplicated[g['game_id']]=g
    games=list(deduplicated.values());availability={};optional_errors=[]
    for g in games:
        if g['state']=='pre' and clock<b.utc(g['kickoff'])<=clock+timedelta(hours=24) and not (root/'predictions'/(g['game_id']+'.json')).exists():
            try:availability[g['game_id']]=availability_snapshot(capture,g,sport)
            except Exception as error:
                availability[g['game_id']]={'coverage':'unknown','effect_enabled':False,'error':str(error)}
                optional_errors.append({'stage':'availability','game_id':g['game_id'],'error':str(error)})
    new,excluded=record_forecasts(root,capture,combined,games,events,model,config,availability)
    settled,errors=settle(root,capture,games,events,sport)
    n.write_json(capture.folder/'manifest.json',{'sources':capture.evidence,'history_games':len(combined),'new_predictions':new,'new_results':settled,'excluded':excluded,'errors':errors,'optional_availability_errors':optional_errors,'collection_completed':True})
    return report(root,sport)


def run(source_cache=None):
    summaries=[];errors=[]
    for sport in ['NHL','MLB']:
        try:summaries.append(run_sport(sport,source_cache))
        except Exception as error:
            n.write_json(ROOT/sport.lower()/'errors'/(n.now().strftime('%Y%m%dT%H%M%S%fZ')+'.json'),{'error':str(error),'collection_completed':False,'observed_at':n.now().isoformat()});errors.append(sport+': '+str(error))
    n.write_json(ROOT/'summary.json',{'leagues':summaries,'errors':errors,'NO_BET':True,'actual_wagers':0})
    print(json.dumps({'leagues':summaries,'errors':errors},indent=2))
    if errors:raise RuntimeError('; '.join(errors))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--source-cache');args=parser.parse_args();run(args.source_cache)
