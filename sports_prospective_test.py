"""Append-only NFL shadow test. Public GETs only; frozen models; no wagers."""
import csv
import heapq
import io
import json
import math
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from zoneinfo import ZoneInfo
import sports_historical_benchmark as b
import sports_efficiency_candidate as c
import sports_market_evidence as m

ROOT = Path('benchmarks/nfl_prospective_v2')
FIELDS = ['game_id','season','week','game_type','gameday','gametime','home_team','away_team','location','home_score','away_score','home_moneyline','away_moneyline']
STAT_FIELDS = ['game_id','season','week','team','opponent_team','attempts','sacks_suffered','carries','passing_epa','rushing_epa']
TEAM_NAMES = {'EAGLES':'PHI','JAGUARS':'JAX','BENGALS':'CIN','DOLPHINS':'MIA','RAIDERS':'LV','PATRIOTS':'NE','VIKINGS':'MIN','SAINTS':'NO','BROWNS':'CLE','JETS':'NYJ','COLTS':'IND','STEELERS':'PIT','TEXANS':'HOU','TITANS':'TEN','GIANTS':'NYG','COMMANDERS':'WAS','BEARS':'CHI','PACKERS':'GB','BRONCOS':'DEN','CHARGERS':'LAC','LIONS':'DET','CARDINALS':'ARI','49ERS':'SF','SEAHAWKS':'SEA','RAVENS':'BAL','FALCONS':'ATL','BILLS':'BUF','RAMS':'LA','BUCCANEERS':'TB','COWBOYS':'DAL'}


def now():
    return datetime.now(timezone.utc)


def write_json(path, data, exclusive=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w') as stream:
        stream.write(json.dumps(data, sort_keys=True, indent=2, allow_nan=False)+'\n')


class Capture:
    def __init__(self, folder, source_cache=None, snapshot_dir=None):
        self.folder = Path(folder); self.folder.mkdir(parents=True, exist_ok=False)
        self.evidence = []
        self.source_cache=Path(source_cache) if source_cache else None
        self.snapshot_dir=Path(snapshot_dir) if snapshot_dir else self.folder

    def get(self, url):
        if not url.startswith('https://'):
            raise ValueError('HTTPS required')
        if self.source_cache:
            index=json.loads((self.source_cache/'index.json').read_text())
            cached=index.get(url)
            if cached and timedelta(0)<=now()-b.utc(cached['retrieved_at'])<=timedelta(minutes=30):
                content=(self.source_cache/cached['file']).read_bytes()
                if b.sha256(content)!=cached['sha256']:raise ValueError('Cached capture hash mismatch')
                return content,{'source_url':url,'retrieved_at':cached['retrieved_at'],'response_sha256':cached['sha256'],'reused_verified_capture':True}
        import requests
        headers={}
        token=os.environ.get('GH_PUBLIC_READ_TOKEN')
        if token and url.startswith('https://api.github.com/'):
            headers['Authorization']='Bearer '+token
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.content
        retrieved = now().isoformat()
        return content, {'source_url':url, 'retrieved_at':retrieved, 'response_sha256':b.sha256(content)}

    def retain(self, name, content, evidence):
        # Retain factual reduced snapshots rather than article text or commentary.
        data = content if isinstance(content, bytes) else b.canonical(content)+b'\n'
        self.snapshot_dir.mkdir(parents=True,exist_ok=True)
        path = self.snapshot_dir/(b.sha256(data)+Path(name).suffix) if self.snapshot_dir!=self.folder else self.folder/name
        if path.exists():
            if path.read_bytes()!=data:raise ValueError('Existing snapshot content mismatch')
        else:path.write_bytes(data)
        record = {**evidence, 'sha256':b.sha256(data), 'path':str(path)}
        self.evidence.append(record)
        return record


def game_from_row(r):
    kickoff = datetime.fromisoformat(r['gameday']+'T'+r['gametime']).replace(tzinfo=ZoneInfo('America/New_York')).astimezone(timezone.utc)
    if r['location'] not in {'Home','Neutral'}:
        raise ValueError('Unknown venue')
    home, away = [b.TEAM_ALIASES.get(r[k], r[k]) for k in ('home_team','away_team')]
    if home == away:
        raise ValueError('Team identity mismatch')
    return b.Game(r['game_id'],int(r['season']),int(r['week']),r['game_type'],kickoff,home,away,r['location']=='Neutral',int(r['home_score'] or 0),int(r['away_score'] or 0),None,None)


def normalized_events(data):
    events = []
    for e in data.get('events',[]):
        co = e['competitions'][0]
        sides = {x['homeAway']:x for x in co['competitors']}
        alias = lambda t: {'WSH':'WAS','LAR':'LA'}.get(t,t)
        home, away = [alias(sides[s]['team']['abbreviation']) for s in ('home','away')]
        odds, diagnostics = m.parse_odds(co.get('odds', []))
        events.append({'event_id':e['id'],'kickoff':b.utc(e['date']).isoformat(),'home':home,'away':away,'state':e['status']['type']['state'],'completed':e['status']['type'].get('completed',False),'home_score':int(sides['home'].get('score',0)),'away_score':int(sides['away'].get('score',0)),'neutral':co.get('neutralSite'), 'odds':odds, 'odds_diagnostics':diagnostics})
    return events


def match_event(game, events):
    matches = [e for e in events if e['home']==game.home and e['away']==game.away and b.utc(e['kickoff'])==game.kickoff]
    if len(matches) != 1:
        raise ValueError('Exact schedule/ESPN team and kickoff match required')
    e = matches[0]
    if e['neutral'] is not None and bool(e['neutral']) != game.neutral:
        raise ValueError('Venue disagreement')
    return e


def pregame_features(history, stats, target, cutoff):
    """Replay prior state; never read an unplayed target result or later final."""
    cutoff = b.utc(cutoff)
    if cutoff >= target.kickoff:
        raise ValueError('Pregame cutoff required')
    state, efficiency, pending, stats_pending = b.PriorState(), c.EfficiencyState(), [], []
    eligible = [g for g in history if g.kickoff < cutoff]
    for game in sorted(eligible, key=lambda g:(g.kickoff,g.identifier)):
        historical_cutoff = min(cutoff,game.kickoff-timedelta(seconds=1))
        while pending and pending[0][0] <= historical_cutoff:
            available, _, prior = heapq.heappop(pending);state.apply(prior, available)
        while stats_pending and stats_pending[0][0] <= historical_cutoff:
            _, _, prior = heapq.heappop(stats_pending);efficiency.apply(prior,stats)
        state.new_season(game.season)
        heapq.heappush(pending,(game.kickoff+timedelta(hours=24),game.identifier,game))
        heapq.heappush(stats_pending,(game.kickoff+timedelta(hours=48),game.identifier,game))
    while pending and pending[0][0] <= cutoff:
        available, _, prior = heapq.heappop(pending);state.apply(prior,available)
    while stats_pending and stats_pending[0][0] <= cutoff:
        _, _, prior = heapq.heappop(stats_pending);efficiency.apply(prior,stats)
    state.new_season(target.season)
    ho,hd = efficiency.ratings(target.home);ao,ad = efficiency.ratings(target.away)
    return {'game':target, 'x':state.features(target)+[ho-ao,ad-hd], 'cutoff':cutoff.isoformat(),'prior_results_used':state.used_results,'latest_result_available_at':state.latest_available.isoformat() if state.latest_available else None, 'efficiency_prior_games':[len(efficiency.offense[target.home]),len(efficiency.offense[target.away])]}


def extract_injuries(html, source, game):
    """Official factual designations; absence is unknown; QB is not inferred starter."""
    articles = []
    for raw in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',html,re.S|re.I):
        try:
            d=json.loads(raw)
            if d.get('@type')=='NewsArticle':articles.append(d)
        except (ValueError,AttributeError):pass
    if len(articles)!=1:
        return {'coverage':'unknown','observations':[],'reason':'official publication metadata unavailable','injury_effect_enabled':False}
    article=articles[0]
    if f'Week {game.week}' not in article.get('headline',''):
        return {'coverage':'unknown','observations':[],'reason':'report week mismatch','injury_effect_enabled':False}
    published=article.get('dateModified') or article.get('datePublished')
    if not published or b.utc(published).year!=game.season or b.utc(published)>b.utc(source['retrieved_at']):
        return {'coverage':'unknown','observations':[],'reason':'publication not verified for season','injury_effect_enabled':False}
    observations=[];team=None
    for line in unescape(article.get('articleBody','')).splitlines():
        line=line.strip()
        if line in TEAM_NAMES:
            team=TEAM_NAMES[line];continue
        if team not in {game.home,game.away} or not re.match(r'^(OUT|QUESTIONABLE|DOUBTFUL):',line):continue
        status,players=line.split(':',1)
        for player in players.split(','):
            m=re.match(r'\s*(?:(QB|RB|WR|TE|FB|OT|OL|G|C|DE|DT|DL|EDGE|OLB|LB|CB|DB|S)\s+)?(.+?)(?:\s*\((.*?)\))?\s*$',player)
            if not m:continue
            position,name,injury=m.groups();name=name.strip()
            observations.append({'game_id':game.identifier,'team':team,'player_id':'nfl-report:'+team+':'+re.sub(r'[^a-z0-9]','',name.lower()),'player_identity_kind':'source_team_and_name_not_league_player_id','player_name':name,'position':position,'injury':injury,'kind':'game_designation','status':status.lower(),'published_at':published,'retrieved_at':source['retrieved_at'],'publication_time_verified':True,'source_url':source['source_url'],'source_sha256':source['sha256']})
    checked=[]
    for team in (game.home,game.away):
        checked.extend(c.availability([r for r in observations if r['team']==team],game.identifier,team,source['retrieved_at'])['observations'])
    return {'coverage':'verified_game_designations' if checked else 'unknown','observations':checked,'confirmed_starting_qb':{'home':'unknown','away':'unknown'},'official_inactives':'not_captured','injury_effect_enabled':False}


def binary_market(odds):
    if not odds:return None
    o=odds[0]
    def implied(p):return -p/(100-p) if p<0 else 100/(p+100)
    h,a=implied(o['home_moneyline']),implied(o['away_moneyline'])
    return {**o,'conditional_home_probability':h/(h+a)}


def forecast(root, capture, history, stats, targets, events, v2, v1, availability_data):
    folder=root/'predictions';folder.mkdir(parents=True,exist_ok=True)
    exclusions=[];new=[];decisions=[]
    count=len(list(folder.glob('*.json')))
    for g in sorted(targets,key=lambda g:(g.kickoff,g.identifier)):
        path=folder/(g.identifier+'.json')
        if path.exists():
            decisions.append({'game_id':g.identifier,'decision':'already_enrolled'});continue
        generated=now()
        if g.kickoff <= generated:
            exclusions.append({'game_id':g.identifier,'reason':'already_started'})
            decisions.append({'game_id':g.identifier,'decision':'already_started','checked_at':generated.isoformat()});continue
        if count>=100:
            decisions.append({'game_id':g.identifier,'decision':'frozen_100_forecast_cap','checked_at':generated.isoformat()});continue
        try:
            e=match_event(g,events)
            if e['state']!='pre' or e['completed']:raise ValueError('ESPN does not confirm scheduled/unstarted')
            row=pregame_features(history,stats,g,generated.isoformat())
            if min(row['efficiency_prior_games'])<8:raise ValueError('Insufficient recent efficiency history')
            row['source_snapshots']=capture.evidence
            # Metadata and both models are committed as ONE immutable artifact.
            base=b.probabilities(v1['weights'],{'x':row['x'][:5]},v1['tie_probability'])
            market=binary_market(e['odds'])
            payload={'game_id':g.identifier,'event_id':e['event_id'],'home':g.home,'away':g.away,'season':g.season,'week':g.week,'kickoff':g.kickoff.isoformat(),'generated_at':generated.isoformat(),'cutoff':generated.isoformat(),'v2_model_sha256':b.sha256(b.canonical(v2)),'v1_model_sha256':b.sha256(b.canonical(v1)),'features':row['x'],'v2':b.probabilities(v2['weights'],row,v2['tie_probability']),'v1':base,'market':market,'market_observed_at':e.get('market_observed_at') or next(x['retrieved_at'] for x in capture.evidence if 'scoreboard' in x['source_url']),'source_snapshots':capture.evidence,'availability':availability_data.get(g.identifier,{'coverage':'unknown','observations':[],'injury_effect_enabled':False}),'prior_results_used':row['prior_results_used'],'latest_result_available_at':row['latest_result_available_at'],'efficiency_prior_games':row['efficiency_prior_games'],'NO_BET':True,'actual_wagers':0}
            if generated<b.utc(v2['frozen_at']):raise ValueError('Model not frozen')
            if any(b.utc(s['retrieved_at'])>generated for s in capture.evidence):raise ValueError('Source retrieved after generation')
            recorded=now()
            if recorded>=g.kickoff:raise ValueError('Kickoff reached before recording')
            payload['recorded_at']=recorded.isoformat()
            payload['sha256']=b.sha256(b.canonical(payload))
            write_json(path,payload,exclusive=True);new.append(g.identifier);count+=1
            decisions.append({'game_id':g.identifier,'decision':'enrolled','checked_at':generated.isoformat(),'priced':market is not None})
        except ValueError as error:
            exclusions.append({'game_id':g.identifier,'reason':str(error)})
            decisions.append({'game_id':g.identifier,'decision':'excluded','reason':str(error),'checked_at':generated.isoformat()})
    write_json(capture.folder/'enrollment.json',{'new_predictions':new,'excluded':exclusions,'decisions':decisions})
    return new


def settle(root,capture,events,schedule):
    outcomes=[];errors=[]
    for path in sorted((root/'predictions').glob('*.json')):
        p=json.loads(path.read_text());result_path=root/'results'/(p['game_id']+'.json')
        if result_path.exists():continue
        candidates=[e for e in events if e['event_id']==p['event_id']]
        if not candidates:continue
        e=candidates[0]
        if not e['completed'] or e['state']!='post':continue
        g=next((g for g in schedule if g.identifier==p['game_id']),None)
        if not g:errors.append({'game_id':p['game_id'],'reason':'final schedule missing'});continue
        try:
            if (g.home,g.away,g.kickoff)!=(p['home'],p['away'],b.utc(p['kickoff'])):
                raise ValueError('Final identity disagrees with saved prediction')
            match_event(g,[e])
            if (g.home_score,g.away_score)!=(e['home_score'],e['away_score']):raise ValueError('Final score sources disagree')
            if b.utc(p['generated_at'])>=g.kickoff:raise ValueError('Late prediction')
            stored=p.pop('sha256')
            if stored!=b.sha256(b.canonical(p)):raise ValueError('Prediction hash mismatch')
            outcome=g.outcome
            record={'game_id':g.identifier,'event_id':e['event_id'],'season':g.season,'week':g.week,'outcome':outcome,'home_score':g.home_score,'away_score':g.away_score,'verified_at':now().isoformat(),'prediction_sha256':stored,'source_snapshots':capture.evidence,'scores':{}}
            for name in ['v2','v1']:
                probs=p[name];conditional=probs['home']/(1-probs['tie'])
                record['scores'][name]={'full_brier':sum((probs[s]-(s==outcome))**2 for s in probs),'full_log_loss':-math.log(probs[outcome]),'binary_brier':None if outcome=='tie' else 2*(conditional-(outcome=='home'))**2,'conditional_log_loss':None if outcome=='tie' else b.conditional_loss(conditional,outcome),'correct':None if outcome=='tie' else ('home' if conditional>=.5 else 'away')==outcome}
            if p['market'] and outcome!='tie':
                conditional=p['market']['conditional_home_probability']
                record['scores']['market']={'binary_brier':2*(conditional-(outcome=='home'))**2,'conditional_log_loss':b.conditional_loss(conditional,outcome),'correct':('home' if conditional>=.5 else 'away')==outcome}
            write_json(result_path,record,exclusive=True);outcomes.append(g.identifier)
        except ValueError as error:errors.append({'game_id':g.identifier,'reason':str(error)})
    return outcomes,errors


def report(root):
    predictions=[json.loads(p.read_text()) for p in (root/'predictions').glob('*.json')]
    results=[json.loads(p.read_text()) for p in (root/'results').glob('*.json')]
    paired=[r for r in results if 'market' in r['scores']]
    mean=lambda values:sum(values)/len(values) if values else None
    metrics={name:{metric:mean([r['scores'][name][metric] for r in paired]) for metric in ['binary_brier','conditional_log_loss','correct']} for name in ['v2','v1','market']}
    value={'recorded':len(predictions),'settled':len(results),'pending':len(predictions)-len(results),'target':100,'paired_priced_decisive_games':len(paired),'paired_metrics':metrics,'availability_records':sum(len(p['availability']['observations']) for p in predictions),'injury_effect_enabled':False,'NO_BET':True,'actual_wagers':0}
    value['state']='completed_100_game_test' if len(results)>=100 else 'collecting'
    value['full_three_outcome_metrics']={name:{metric:mean([r['scores'][name][metric] for r in results]) for metric in ['full_brier','full_log_loss']} for name in ['v2','v1']}
    value['week_block_brier_difference']=b.week_bootstrap([{'week':str(r['season'])+'/'+str(r['week']),'model_brier':r['scores']['v2']['binary_brier'],'market_brier':r['scores']['market']['binary_brier']} for r in paired]) if paired else None
    if value['week_block_brier_difference']:
        value['week_block_brier_difference']['limitation']='Approximate season/week-block uncertainty for the prospective sample; not proof of future profitability.'
    write_json(root/'summary.json',value)
    lines=['# Tyler NFL prospective paper test','',f"Recorded: **{len(predictions)}/100** · Settled: **{len(results)}** · Pending: **{len(predictions)-len(results)}**",'', '**NO BET — actual wagers $0.**', '', 'Frozen experimental v2 compared with frozen v1 and market odds observed before kickoff. QB/injury reports are evidence only; model effects remain disabled. Confirmed starters and final inactive lists are unknown unless explicitly captured.','', '| Model | Paired games | Brier (lower is better) | Log loss (lower is better) | Accuracy |','|---|---:|---:|---:|---:|']
    for name in ['v2','v1','market']:
        m=metrics[name];fmt=lambda x:'Pending' if x is None else f'{x:.4f}'
        accuracy='Pending' if m['correct'] is None else f"{m['correct']:.1%}"
        lines.append(f"| {name} | {len(paired)} | {fmt(m['binary_brier'])} | {fmt(m['conditional_log_loss'])} | {accuracy} |")
    lines+=['','| Game | Kickoff (Eastern) | V2 pick | V2 win probability | Saved (Eastern) |','|---|---|---|---:|---|']
    for pred in sorted(predictions,key=lambda x:(x['kickoff'],x['game_id'])):
        chosen='home' if pred['v2']['home']>=pred['v2']['away'] else 'away'
        eastern=lambda x:b.utc(x).astimezone(ZoneInfo('America/New_York')).strftime('%b %d %I:%M %p')
        lines.append(f"| {pred['away']} at {pred['home']} | {eastern(pred['kickoff'])} | {pred[chosen]} | {pred['v2'][chosen]:.1%} | {eastern(pred['generated_at'])} |")
    lines+=['','Probabilities include a small tie allowance. These picks are experimental model outputs, not wagering recommendations. Source timing and scheduling delays can leave coverage gaps; missed games are logged rather than backfilled after kickoff.','', '[Machine-readable summary](summary.json) · [Predictions](predictions) · [Result records](results) · [Source captures](captures)','']
    lines+=['', '[Full benchmark review, calibration and uncertainty](REVIEW.md)', '']
    (root/'RESULTS.md').write_text('\n'.join(lines))
    return value


def run(root=ROOT,source_cache=None):
    root=Path(root)
    config=json.loads((ROOT/'config.json').read_text())
    for name,digest in config['models_and_warmup_sha256'].items():
        if b.sha256(Path(name).read_bytes())!=digest:raise ValueError('Frozen model or warmup snapshot changed')
    if len(list((root/'results').glob('*.json')))>=100:
        return report(root)
    stamp=now().strftime('%Y%m%dT%H%M%S%fZ');capture=Capture(root/'captures'/stamp,source_cache,root/'snapshots')
    # Every run pins the current public schedule revision and release digests.
    raw,e=capture.get('https://api.github.com/repos/nflverse/nfldata/commits?path=data/games.csv&per_page=1')
    commit=json.loads(raw)[0]['sha']
    raw,e=capture.get(f'https://raw.githubusercontent.com/nflverse/nfldata/{commit}/data/games.csv')
    rows=[r for r in csv.DictReader(io.StringIO(raw.decode())) if int(r['season'])>=2025]
    reduced=[{k:r[k] for k in FIELDS} for r in rows]
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=FIELDS);writer.writeheader();writer.writerows(reduced)
    capture.retain('schedule.csv',stream.getvalue().encode(),{**e,'commit':commit})
    historical=b.read_games('benchmarks/nfl_independent_v1/games_2010_2025.csv',last=2024)
    finals=[game_from_row(r) for r in rows if r['home_score']!='' and r['away_score']!='']
    historical+=finals
    raw,e=capture.get('https://api.github.com/repos/nflverse/nflverse-data/releases/tags/stats_team')
    assets={a['name']:a for a in json.loads(raw)['assets']}
    stats_rows=[]
    for year in sorted({g.season for g in finals}):
        asset=assets[f'stats_team_week_{year}.csv'];raw,e=capture.get(asset['browser_download_url'])
        if asset['digest']!='sha256:'+b.sha256(raw):raise ValueError('Release digest mismatch')
        stats_rows.extend({k:r[k] for k in STAT_FIELDS} for r in csv.DictReader(io.StringIO(raw.decode())))
        capture.retain(f'stats_team_week_{year}.csv',raw,{**e,'release_digest':asset['digest'],'updated_at':asset['updated_at']})
    # Filter only finals; live or unverified totals never become history.
    eligible_history=[g for g in historical if g.kickoff+timedelta(hours=48)<=now()]
    final_ids={g.identifier for g in eligible_history}
    stats_rows=[r for r in stats_rows if r['game_id'] in final_ids]
    with Path('benchmarks/nfl_efficiency_v2/team_stats_2010_2024.csv').open(newline='') as stream:stats_rows=list(csv.DictReader(stream))+stats_rows
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=STAT_FIELDS);writer.writeheader();writer.writerows(stats_rows)
    forecast_error=None
    with tempfile.TemporaryDirectory() as temporary:
        stats_file=Path(temporary)/'combined_stats.csv';stats_file.write_text(stream.getvalue())
        try:stats=c.read_stats(stats_file,eligible_history)
        except ValueError as error:
            stats={};forecast_error={'stage':'forecast_history','error':str(error)}
    current=now()
    targets=[game_from_row(r) for r in rows if r['game_type']=='REG' and current-timedelta(hours=24)<game_from_row(r).kickoff<=current+timedelta(hours=24)]
    dates=sorted({g.kickoff.astimezone(ZoneInfo('America/New_York')).strftime('%Y%m%d') for g in targets}|{b.utc(json.loads(p.read_text())['kickoff']).astimezone(ZoneInfo('America/New_York')).strftime('%Y%m%d') for p in (root/'predictions').glob('*.json') if not (root/'results'/p.name).exists()})
    events=[]
    for day in dates:
        raw,e=capture.get(f'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={day}')
        normalized=normalized_events(json.loads(raw))
        for event in normalized:event['market_observed_at']=e['retrieved_at']
        events.extend(normalized);capture.retain('espn_'+day+'.json',normalized,e)
    availability_data={}
    for week in sorted({g.week for g in targets if g.kickoff>now()}):
        # URL format may change: report failure stays explicit unknown evidence.
        games=[g for g in targets if g.week==week and g.kickoff>now()]
        url=f'https://www.nfl.com/news/nfl-week-{week}-injury-report-player-statuses-for-all-15-games'
        try:
            raw,e=capture.get(url)
            source={**e,'sha256':e['response_sha256']}
            parsed={g.identifier:extract_injuries(raw.decode(),source,g) for g in games}
            capture.retain(f'availability_week_{week}.json',parsed,e);availability_data.update(parsed)
        except Exception as error:
            capture.retain(f'availability_week_{week}.json',{'coverage':'unknown','error':str(error)},{'source_url':url,'retrieved_at':now().isoformat()})
    v2=json.loads(Path('benchmarks/nfl_efficiency_v2/run_2026_10_11/model.json').read_text())
    v1=json.loads(Path('benchmarks/nfl_independent_v1/run_2026_10_11/model.json').read_text())
    if forecast_error:
        new=[]
        write_json(capture.folder/'enrollment.json',{'new_predictions':[],'excluded':[{'game_id':g.identifier,'reason':'incomplete_eligible_stats_history'} for g in targets if g.kickoff>now()]})
    else:new=forecast(root,capture,historical,stats,targets,events,v2,v1,availability_data)
    followups,quote_errors=m.collect_followups(root,capture,events,now)
    outcomes,errors=settle(root,capture,events,finals)
    errors.extend(quote_errors)
    if forecast_error:errors.append(forecast_error)
    write_json(capture.folder/'manifest.json',{'sources':capture.evidence,'new_predictions':new,'new_results':outcomes,'errors':errors,'new_market_followups':followups,'collection_completed':True})
    summary=report(root)
    print(json.dumps(summary,indent=2))
    return summary


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--root',default=str(ROOT));parser.add_argument('--source-cache');args=parser.parse_args()
    try:
        run(args.root,args.source_cache)
    except Exception as error:
        write_json(Path(args.root)/'errors'/(now().strftime('%Y%m%dT%H%M%S%fZ')+'.json'),{'observed_at':now().isoformat(),'error':str(error),'collection_completed':False})
        raise
