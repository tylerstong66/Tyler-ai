"""Read-only original-source casebook for historical college score disputes.

Both providers' claims are retained. No source is selected as the correct
result, and disputed games never become labels, forecasts or wagers.
"""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

import sports_historical_fbs_crosscheck as crosscheck
import sports_expansion_historical_capture as history
import sports_expansion_observer as source


def build(base=Path('.'), *, league='NCAAM_D1', split='validation', now=None,verified_school_aliases=False):
    base=Path(base); now=now or datetime.now(timezone.utc)
    report=crosscheck.build(base,league=league,split=split,now=now,
                            verified_school_aliases=verified_school_aliases)
    disputes=[row for row in report['pending']
              if row['reason']=='CONFLICTING_FINAL_SCORES_NO_GRADE']
    ncaa_ids={row['ncaa_game_id'] for row in disputes}
    espn_ids={row['espn_game_id'] for row in disputes}
    ncaa=defaultdict(list);espn=defaultdict(list)
    for saved,path,period in crosscheck._owned_sources(base,league,split,now):
        for row in saved['parsed_ncaa_games']:
            if row['ncaa_game_id'] in ncaa_ids:
                ncaa[row['ncaa_game_id']].append({
                    'source_receipt':path.relative_to(base).as_posix(),
                    'receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'response_sha256':saved['original_response_sha256'],
                    'observed_at_utc':saved['recorded_at_utc'],
                    'source_period':period,'original_normalized_claim':row})
    for day in history.dates_by_league()[league][split]:
        if not history.verify_existing(base,league,split,day,as_of=now):continue
        path=base/history.ROOT/'sources'/league/split/(day+'.receipt.json')
        receipt_bytes=path.read_bytes();saved=json.loads(receipt_bytes)
        for row in saved['parsed_provider_scoreboard']['games']:
            if row['game_id'] in espn_ids:
                espn[row['game_id']].append({
                    'source_receipt':path.relative_to(base).as_posix(),
                    'receipt_sha256':hashlib.sha256(receipt_bytes).hexdigest(),
                    'response_sha256':saved['original_response_sha256'],
                    'observed_at_utc':saved['recorded_at_utc'],
                    'source_date':day,'original_normalized_claim':row})
    cases=[]
    for row in sorted(disputes,key=lambda x:(x['espn_game_id'],x['ncaa_game_id'])):
        ns=ncaa[row['ncaa_game_id']];es=espn[row['espn_game_id']]
        if not ns or not es:raise ValueError('Missing original score dispute evidence')
        # Recheck after the second replay rather than trusting the earlier
        # classifier if inputs change while this diagnostic is being built.
        for n in ns:
            n=n['original_normalized_claim']
            for e in es:
                e=e['original_normalized_claim']
                if (not n['provider_reported_final'] or not e['provider_completed'] or
                    (n['ncaa_home_score'],n['ncaa_away_score'])==(e['home_score'],e['away_score'])):
                    raise ValueError('Source dispute changed during diagnostic replay')
        cases.append({**row,'ncaa_observations':ns,'espn_observations':es,
                      'resolution':'UNRESOLVED_NO_SOURCE_PREFERRED',
                      'eligible_for_result_agreement':False})
    result={'schema':'tyler-historical-college-score-dispute-casebook-v1',
        'league':league,'split':split,'disputed_games':len(cases),'cases':cases,
        'selection_policy':'ALL_EXACT_IDENTITY_FINAL_SCORE_DISAGREEMENTS',
        'crosscheck_report_sha256':hashlib.sha256(source.canonical(report)).hexdigest(),
        'other_pending_games':len(report['pending'])-len(cases),
        'source_scope_complete':False,'training_allowed':False,
        'historical_evaluation_enabled':False,'forecasting_enabled':False,
        'official_result_grading_enabled':False,'promotion_allowed':False,
        'NO_BET':True,'actual_wagers':0}
    if verified_school_aliases:
        result.update(schema='tyler-historical-college-reviewed-score-dispute-casebook-v2',
                      school_identity_policy=report['school_identity_policy'],
                      school_identity_manifest_sha256=report['school_identity_manifest_sha256'])
    return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--league',choices=('NCAAF_FBS','NCAAM_D1'),default='NCAAM_D1')
    parser.add_argument('--split',choices=('train','validation'),default='validation')
    parser.add_argument('--verified-school-aliases',action='store_true')
    args=parser.parse_args()
    print(json.dumps(build(league=args.league,split=args.split,
                          verified_school_aliases=args.verified_school_aliases),sort_keys=True,indent=2))
