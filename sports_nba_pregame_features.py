"""Append-only NBA pregame feature observations; no predictions or model use."""
from datetime import datetime,timedelta,timezone
from pathlib import Path
import hashlib
import json
import re

import sports_expansion_observer as source
import sports_expansion_audit as source_audit
import sports_nba_official_schedule_audit as nba
import sports_nba_schedule_receipts as receipts
import sports_historical_nba_crosscheck as history
import sports_historical_content_seal as original_seal
import sports_historical_extension_seal as independent_seal

ROOT=Path('benchmarks/nba_pregame_features_v1/records')
PROTOCOL={'schema':'nba-pregame-reference-features-protocol-v1','target_season':'2026-27',
    'reference_season':'2025-26','reference_split':'validation','reference_games_per_team':10,
    'reference_scope':'LAST_TEN_CORROBORATED_PREVIOUS_SEASON_RESULTS_AVAILABLE_AT_FREEZE',
    'maximum_schedule_source_age_hours':12,'target_kind':'regular',
    'feature_fields':['prior_games','mean_points_for','mean_points_against','mean_margin','days_since_latest_prior_start'],
    'not_a_prediction':True,'prior_season_roster_changes_not_modeled':True}
PROTOCOL_SHA256='bdd146edfa1be2718330324c13318979a78a4f990c4353c88ce2c89c27c983d8'


class IneligibleSourceGame(ValueError):pass


def digest(value):return hashlib.sha256(source.canonical(value)).hexdigest()


def _reference(base,now):
    path=base/ROOT.parent/'protocol.json'
    if (path.is_symlink() or not path.is_file() or path.stat().st_size>1_000_000
            or digest(PROTOCOL)!=PROTOCOL_SHA256
            or hashlib.sha256(path.read_bytes()).hexdigest()!=PROTOCOL_SHA256):
        raise ValueError('NBA pregame feature protocol differs from frozen experiment')
    original_seal.verify(base);independent_seal.verify(base)
    return history.build(base,split='validation',now=now,exact_tipoff_identity=True)


def _snapshot(base,stamp):
    receipts.verify(base,stamp)
    folder=base/nba.ROOT/'captures'/stamp
    original=(folder/'manifest.json').read_bytes();saved=json.loads(original)
    if (saved['schema']!='nba-espn-independent-schedule-corroboration-v2'
            or saved['nba_source_season']!=PROTOCOL['target_season']):
        raise ValueError('Unsupported NBA pregame source season or receipt version')
    raw=source_audit.bounded_gzip_read((folder/'nba_schedule.json.gz').read_bytes(),limit=nba.MAX_BYTES)
    if hashlib.sha256(raw).hexdigest()!=saved['nba_raw_sha256']:
        raise ValueError('NBA pregame source changed during replay')
    official={r['nba_game_id']:r for r in receipts.read_official_games(raw,saved)}
    ef=base/source.ROOT/'captures'/saved['espn_capture']
    ebytes=(ef/'manifest.json').read_bytes();em=json.loads(ebytes)
    if hashlib.sha256(ebytes).hexdigest()!=saved['espn_manifest_sha256']:
        raise ValueError('NBA pregame linked provider changed during replay')
    source_audit.audit_capture(ef/'manifest.json')
    if source.utc(em['recorded_at_utc'])>source.utc(saved['created_at_utc']):
        raise ValueError('Linked NBA provider capture follows original schedule capture')
    return {'stamp':stamp,'manifest':saved,'manifest_sha256':hashlib.sha256(original).hexdigest(),
        'provider_manifest':em,'official':official,'provider':nba.espn_games(em,ef)}


def _record(snapshot,matched,reference,freeze):
    m=snapshot['manifest'];nt=source.utc(m['created_at_utc'])
    et=source.utc(snapshot['provider_manifest']['recorded_at_utc'])
    n=snapshot['official'][matched['nba_official_game_id']]
    e=snapshot['provider'][matched['espn_game_id']]
    if sum(r['nba_official_game_id']==n['nba_game_id'] for r in m['report']['matched'])!=1:
        raise IneligibleSourceGame('NON_BIJECTIVE_SOURCE_GAME_IDENTITY')
    starts=[source.utc(n['tipoff_utc']),source.utc(e['scheduled_start_utc'])]
    if n['kind']!=PROTOCOL['target_kind'] or e['season_stage']!=2:
        raise IneligibleSourceGame('NOT_REGULAR_SEASON_TARGET')
    if n['nba_status']!=1 or e['provider_completed'] is not False or e['state']!='pre':
        raise IneligibleSourceGame('BOTH_SOURCES_NOT_PREGAME')
    if n['nba_postponed_status'] not in (None,'','N'):
        raise IneligibleSourceGame('POSTPONED_OR_UNKNOWN_SOURCE_STATUS')
    if freeze>=min(starts):raise IneligibleSourceGame('SOURCE_SAVED_START_ALREADY_REACHED')
    if max(nt,et)>freeze:raise ValueError('Schedule source observed after feature freeze')
    if min(starts)<=max(nt,et):raise ValueError('Schedule source not observed before saved starts')
    if any(freeze-at>timedelta(hours=PROTOCOL['maximum_schedule_source_age_hours']) for at in (nt,et)):
        raise IneligibleSourceGame('SCHEDULE_SOURCE_TOO_OLD_AT_FREEZE')
    summaries={}
    for side in ('home','away'):
        team=n[side+'_tricode'];eligible=[]
        for row in reference['corroborated_research_only']:
            if team not in (row['home_tricode'],row['away_tricode']):continue
            at=source.utc(row['corroboration_available_at_utc'])
            latest=max(source.utc(row[k]) for k in ('nba_scheduled_start_utc','espn_scheduled_start_utc'))
            if at>freeze or latest>=freeze:continue
            season=int(row['nba_game_id'][3:5])
            if season!=25:raise ValueError('NBA pregame reference crossed fixed source season')
            eligible.append((latest,row['nba_game_id'],row))
        selected=sorted(eligible)[-PROTOCOL['reference_games_per_team']:]
        if len(selected)!=PROTOCOL['reference_games_per_team']:
            raise IneligibleSourceGame('INSUFFICIENT_CORROBORATED_REFERENCE_HISTORY')
        if len({r['nba_game_id'] for _,_,r in selected})!=len(selected):
            raise ValueError('Duplicate NBA pregame reference result identity')
        scored=[]
        for _,_,row in selected:
            own='home' if row['home_tricode']==team else 'away';opposite='away' if own=='home' else 'home'
            scored.append((row[own+'_score'],row[opposite+'_score']))
        count=len(selected)
        summaries[side]={'team_tricode':team,'prior_games':count,
            'mean_points_for':sum(s[0] for s in scored)/count,
            'mean_points_against':sum(s[1] for s in scored)/count,
            'mean_margin':sum(s[0]-s[1] for s in scored)/count,
            'days_since_latest_prior_start':(min(starts)-selected[-1][0]).total_seconds()/86400,
            'reference_source_rows':[{'source_row_sha256':digest(r),'source_row':r} for _,_,r in selected]}
    return {'schema':'tyler-nba-pregame-reference-feature-observation-v1',
        'nba_game_id':n['nba_game_id'],'espn_game_id':e['espn_game_id'],
        'frozen_at_utc':freeze.isoformat(),'scheduled_start_utc':min(starts).isoformat(),
        'nba_saved_start_utc':n['tipoff_utc'],'espn_saved_start_utc':e['scheduled_start_utc'],
        'home_team_id':e['home_team_id'],'away_team_id':e['away_team_id'],
        'nba_capture':snapshot['stamp'],'nba_manifest_sha256':snapshot['manifest_sha256'],
        'nba_response_sha256':m['nba_raw_sha256'],'espn_capture':m['espn_capture'],
        'espn_manifest_sha256':m['espn_manifest_sha256'],
        'protocol_sha256':digest(PROTOCOL),'reference_report_sha256':digest(reference),
        'reference_features':summaries,'not_a_prediction':True,
        'independent_publication_time_attested':False,'institutional_membership_certified':False,
        'model_training_enabled':False,'forecasting_enabled':False,'historical_evaluation_enabled':False,
        'promotion_allowed':False,'NO_BET':True,'actual_wagers':0}


def _verify(path,base,now,reference,snapshots):
    if (not re.fullmatch(r'00226\d{5}\.json',path.name) or path.is_symlink()
            or not path.is_file() or path.stat().st_size>1_000_000):
        raise ValueError('Invalid NBA pregame feature record path')
    raw=path.read_bytes();saved=json.loads(raw);record=saved['record']
    if raw!=source.canonical(saved) or saved.get('record_sha256')!=digest(record):
        raise ValueError('NBA pregame feature content digest or encoding changed')
    if path.stem!=record['nba_game_id']:raise ValueError('NBA feature file differs from source game ID')
    freeze=source.utc(record['frozen_at_utc'])
    if freeze>now:raise ValueError('NBA pregame feature freeze is future-dated')
    stamp=record['nba_capture']
    if stamp not in snapshots:snapshots[stamp]=_snapshot(base,stamp)
    snapshot=snapshots[stamp]
    matches=[m for m in snapshot['manifest']['report']['matched']
             if m['nba_official_game_id']==record['nba_game_id'] and m['espn_game_id']==record['espn_game_id']]
    if len(matches)!=1:raise ValueError('NBA feature lacks a unique original source crosswalk')
    expected=_record(snapshot,matches[0],reference,freeze)
    if source.canonical(record)!=source.canonical(expected):
        raise ValueError('NBA pregame feature differs from original-source replay')
    return record


def verify(path,*,base=Path('.'),now=None):
    base=Path(base);now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError('Aware NBA feature audit clock required')
    return _verify(Path(path),base,now,_reference(base,now),{})


def _existing(base,now,reference,snapshots):
    existing={}
    root=base/ROOT
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or (path.is_file() and path.parent!=root):
            raise ValueError('Unplanned NBA pregame feature input')
        if path.is_file():
            record=_verify(path,base,now,reference,snapshots);existing[record['nba_game_id']]=record
    return existing


def audit(base=Path('.'),*,now=None):
    base=Path(base);now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError('Aware NBA feature audit clock required')
    existing=_existing(base,now,_reference(base,now),{})
    return {'schema':'tyler-nba-pregame-feature-audit-v1','verified_feature_observations':len(existing),
            'not_a_prediction':True,'forecasting_enabled':False,'promotion_allowed':False,
            'model_training_enabled':False,'historical_evaluation_enabled':False,
            'NO_BET':True,'actual_wagers':0}


def collect(base=Path('.'),*,now=None):
    base=Path(base);now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError('Aware NBA feature collection clock required')
    reference=_reference(base,now);snapshots={};existing=_existing(base,now,reference,snapshots)
    root=base/ROOT
    captures=sorted((base/nba.ROOT/'captures').glob('*/manifest.json'))
    prepared=[];pending=[]
    if captures:
        stamp=captures[-1].parent.name
        if stamp not in snapshots:snapshots[stamp]=_snapshot(base,stamp)
        snapshot=snapshots[stamp]
        for matched in snapshot['manifest']['report']['matched']:
            game_id=matched['nba_official_game_id']
            if game_id in existing:continue
            try:record=_record(snapshot,matched,reference,now)
            except IneligibleSourceGame as error:
                pending.append({'nba_game_id':game_id,'espn_game_id':matched['espn_game_id'],'reason':str(error)})
                continue
            prepared.append(record)
    for record in prepared:
        envelope={'record':record,'record_sha256':digest(record)}
        root.mkdir(parents=True,exist_ok=True)
        with (root/(record['nba_game_id']+'.json')).open('xb') as stream:stream.write(source.canonical(envelope))
    return {'schema':'tyler-nba-pregame-feature-collection-status-v1',
        'verified_existing':len(existing),'new_feature_observations':len(prepared),
        'not_enrolled':pending,'source_available':bool(captures),
        'not_a_prediction':True,'historical_backfilled_forecasts':0,
        'model_training_enabled':False,'forecasting_enabled':False,
        'historical_evaluation_enabled':False,
        'promotion_allowed':False,'NO_BET':True,'actual_wagers':0}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-only',action='store_true')
    args=parser.parse_args()
    print(json.dumps(audit() if args.audit_only else collect(),sort_keys=True,indent=2))
