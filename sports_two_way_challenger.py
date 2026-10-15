"""Offline 2024-fit / 2025-validation development comparison. Never promotes models."""
import argparse
import gzip
import json
import math
from copy import deepcopy
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import sports_benchmark_review as review
import sports_historical_benchmark as b
import sports_two_way_test as live

ROOT = Path('benchmarks/two_way_challenger_v1')
CANDIDATES = ['fixed_elo', 'ridge_recipe', 'elo_prior_calibration']


def elo_logit(row, config):
    venue = 0 if row['data']['neutral'] is True else config['home_offset']
    return (row['x'][1]*200 + venue)*math.log(10)/400


def calibration_objective(rows, weights, penalty):
    loss = 0.0
    for row in rows:
        z = b.dot(weights, row['calibration_x'])
        y = float(row['game'].outcome == 'home')
        loss += max(z, 0)+math.log1p(math.exp(-abs(z)))-y*z
    # Shrink slope toward one (fixed Elo), with an unpenalized intercept.
    return loss/len(rows)+penalty*(weights[1]-1)**2/2


def fit_calibration(rows, penalty):
    if not rows or not math.isfinite(penalty) or penalty <= 0:
        raise ValueError('Positive penalty and nonempty training rows required')
    if any(len(r['calibration_x']) != 2 or r['calibration_x'][0] != 1 or
           not all(math.isfinite(v) for v in r['calibration_x']) or
           r['game'].outcome not in ('home','away') for r in rows):
        raise ValueError('Malformed decisive calibration training row')
    weights = [0.0, 1.0]
    for iteration in range(60):
        gradient = [0.0, penalty*(weights[1]-1)]
        hessian = [[0.0, 0.0], [0.0, penalty]]
        for row in rows:
            x = row['calibration_x']; p = b.sigmoid(b.dot(weights,x))
            y = float(row['game'].outcome == 'home')
            for j in range(2):
                gradient[j] += (p-y)*x[j]/len(rows)
                for k in range(2):
                    hessian[j][k] += p*(1-p)*x[j]*x[k]/len(rows)
        if max(abs(g) for g in gradient) < 1e-8:
            return {'weights':weights,'penalty':penalty,'slope_prior':1,
                    'iterations':iteration,'converged':True}
        step = b.solve(hessian,gradient)
        previous = calibration_objective(rows,weights,penalty)
        for backtrack in range(25):
            candidate = [w-s*(.5**backtrack) for w,s in zip(weights,step)]
            if calibration_objective(rows,candidate,penalty) <= previous+1e-12:
                weights = candidate
                break
        else:
            raise RuntimeError('Calibration descent failed')
    raise RuntimeError('Calibration did not converge')


def partition(history, config, train_season=2024, validation_season=2025):
    if validation_season <= train_season or not history:
        raise ValueError('Nonempty chronological seasons required')
    if any(g['season'] not in (train_season,validation_season) or not g.get('completed') for g in history):
        raise ValueError('Only completed training/validation-season history permitted')
    delay = timedelta(hours=config['result_delay_hours'])
    cutoff = max(b.utc(g['kickoff']) for g in history)+delay+timedelta(seconds=1)
    # unique_finals marks ambiguous resumptions in place; preserve the source archive.
    games = live.unique_finals(deepcopy(history),cutoff)
    train_games = [g for g in games if g['season']==train_season]
    validation_games = [g for g in games if g['season']==validation_season]
    if not train_games or not validation_games or max(b.utc(g['kickoff'])+delay for g in train_games) >= min(b.utc(g['kickoff']) for g in validation_games):
        raise ValueError('All training results must be eligible before validation starts')
    rows = live.feature_rows(games,config)
    for row in rows:
        row['calibration_x'] = [1.0,elo_logit(row,config)]
    eligible = lambda r: r['data']['regular'] and not r['data'].get('historical_resumption_ambiguous')
    training = [r for r in rows if r['data']['season']==train_season and eligible(r)]
    validation = [r for r in rows if r['data']['season']==validation_season and eligible(r)]
    if not training or not validation:
        raise ValueError('Nonempty regular-season training and validation required')
    excluded = [{'game_id':g['game_id'],'season':g['season'],'reason':'ambiguous_resumption'}
                for g in games if g['regular'] and g.get('historical_resumption_ambiguous')]
    return training, validation, excluded


def compare(history, config, protocol):
    training,validation,excluded = partition(history,config,protocol['training_season'],protocol['validation_season'])
    penalty = protocol['l2_penalty']
    models = {'ridge_recipe':b.fit(training,penalty,dimension=2),
              'elo_prior_calibration':fit_calibration(training,penalty)}
    scores = []
    for row in validation:
        game = row['data']; outcome = row['game'].outcome
        probabilities = {'fixed_elo':b.sigmoid(elo_logit(row,config)),
                         'ridge_recipe':b.sigmoid(b.dot(models['ridge_recipe']['weights'],row['x'])),
                         'elo_prior_calibration':b.sigmoid(b.dot(models['elo_prior_calibration']['weights'],row['calibration_x']))}
        scores.append({'game_id':game['game_id'],'kickoff':game['kickoff'],
                       'simulated_cutoff':(b.utc(game['kickoff'])-timedelta(seconds=1)).isoformat(),
                       'block':b.utc(game['kickoff']).astimezone(ZoneInfo('America/New_York')).date().isoformat(),
                       'features':row['x'],'calibration_features':row['calibration_x'],'outcome':outcome,
                       'home_probability':probabilities,
                       'scores':{name:review.binary_scores(p,outcome) for name,p in probabilities.items()}})
    metrics = {name:review.estimates([{'block':r['block'],**r['scores'][name]} for r in scores]) for name in CANDIDATES}
    paired = {name:review.estimates([{'block':r['block'],**{
        field:r['scores'][name][field]-r['scores']['fixed_elo'][field]
        for field in ('brier','log_loss','accuracy')}} for r in scores]) for name in CANDIDATES[1:]}
    selected = min(CANDIDATES,key=lambda name:metrics[name]['mean']['log_loss'])
    bounds = lambda rows: {'games':len(rows),'first_start':rows[0]['data']['kickoff'],'last_start':rows[-1]['data']['kickoff']}
    return {'sport':config['sport'],'training':bounds(training),'validation':bounds(validation),
            'training_season':protocol['training_season'],'validation_season':protocol['validation_season'],
            'models_fit_on_training_only':models,'metrics':metrics,'candidate_minus_fixed_elo':paired,
            'selected_development_candidate':selected,'promotion_allowed':False,
            'calibration':{name:review.calibration([(r['home_probability'][name],r['outcome']=='home') for r in scores]) for name in CANDIDATES},
            'excluded':excluded,'result_delay_hours':config['result_delay_hours'],
            'brier_scale':'sum over two outcomes; range 0 to 2',
            'block_unit':'Eastern scheduled game date','score_rows_sha256':b.sha256(b.canonical(scores)),
            'limitations':protocol['limitations'],'NO_BET':True,'actual_wagers':0}, scores


def evaluate(base=Path('.')):
    base = Path(base)
    protocol = json.loads((base/ROOT/'protocol.json').read_text())
    if (protocol['training_season'],protocol['validation_season'],protocol['candidate_order'],protocol['l2_penalty'],protocol['calibration_prior'],protocol['promotion_allowed']) != (2024,2025,CANDIDATES,.01,[0.0,1.0],False):
        raise ValueError('Unsupported experiment protocol')
    expected_paths = {str(live.ROOT/'protocol.json'),str(live.ROOT/'nhl/history.json'),str(live.ROOT/'mlb/history.json')}
    if set(protocol['files_sha256']) != expected_paths:
        raise ValueError('Only pinned historical inputs permitted')
    for path, expected in protocol['files_sha256'].items():
        if b.sha256((base/path).read_bytes()) != expected:
            raise ValueError('Pinned development input hash mismatch: '+path)
    live_protocol = json.loads((base/live.ROOT/'protocol.json').read_text())
    reports,scores = [],{}
    for sport in ('NHL','MLB'):
        history = json.loads((base/live.ROOT/sport.lower()/'history.json').read_text())
        report,rows = compare(history,live_protocol[sport],protocol)
        report['protocol_sha256'] = b.sha256(b.canonical(protocol))
        reports.append(report);scores[sport]=rows
    return reports,scores


def render(reports):
    lines = ['# NHL/MLB challenger development comparison','','**NO BET / actual wagers $0. No model promotion.**','',
             'Fit only on 2024-season regular games; evaluate on 2025-season regular games with delayed rolling Elo. '
             'No 2026-season replay input or live fitted weights are read. Candidate family was fixed before this run, after inspecting the 2026 replay; this is not preregistered or blind.','',
             '| Sport | Candidate | Training games | Validation games | Brier | Log loss | Accuracy |',
             '|---|---|---:|---:|---:|---:|---:|']
    for data in reports:
        for name in CANDIDATES:
            m=data['metrics'][name]['mean']
            lines.append(f"| {data['sport']} | {name} | {data['training']['games']} | {data['validation']['games']} | {m['brier']:.6f} | {m['log_loss']:.6f} | {m['accuracy']:.1%} |")
    lines += ['','Brier (two-outcome sum) and log loss: lower is better. '
              'The existing ridge recipe is re-fitted on 2024 here; these scores do not evaluate the live 2025-fitted model.','',
              '## Paired log-loss differences versus fixed Elo','',
              'Same validation games, Eastern-date block bootstrap; negative favors the candidate. '
              'Intervals are descriptive and unadjusted for candidate selection.','',
              '| Sport | Candidate | Mean difference | 95% interval |','|---|---|---:|---|']
    for data in reports:
        for name,diff in data['candidate_minus_fixed_elo'].items():
            ci=diff['ci95']['log_loss']
            interval=f'{ci[0]:.6f} to {ci[1]:.6f}' if ci else 'Unavailable'
            lines.append(f"| {data['sport']} | {name} | {diff['mean']['log_loss']:.6f} | {interval} |")
    lines += ['','## Development selection and scope','',
              'Selection minimizes 2025 mean log loss across the three fixed candidates, with listed order breaking exact ties. '
              'This selects on validation and does not create a new independent test. No refitting on 2025, future enrollment, deployment, or changes to live assets occur.','']
    for data in reports:
        lines.append(f"- {data['sport']}: selected `{data['selected_development_candidate']}`; fit {data['training']['first_start']} through {data['training']['last_start']}; validate {data['validation']['first_start']} through {data['validation']['last_start']}; {len(data['excluded'])} ambiguous regular-season resumptions excluded across both seasons.")
    lines += ['','## Methods and reproduction','',
              '`fixed_elo` retains the frozen league K, home offset, and offseason regression. '
              '`ridge_recipe` uses the existing intercept + rating-difference/200 logistic fit, L2=0.01 with slope prior zero. '
              '`elo_prior_calibration` fits intercept + fixed-Elo logit with the same penalty, shrinking the slope toward one; the intercept is unpenalized. '
              'No hyperparameter grid or probability clipping is selected. Equal initial ratings of 1500 mean early 2024 has no earlier-season warmup. '
              'All finals, including playoffs and ambiguous resumptions, may update Elo only after their retained start plus 12 hours; ambiguous resumptions are never fitting/scoring examples.','',
              'Run `python sports_two_way_challenger.py --output /tmp/two-way-challenger`. '
              '[protocol.json](protocol.json) pins all historical inputs and rules. JSON reports retain fitted parameters, calibration bins, paired Brier/log-loss/accuracy estimates and per-game score hashes; compressed score files retain reconstructed probabilities and features. '
              'The command is offline and never writes to live model, forecast, or result paths.','']
    lines += [f'- {item}' for item in reports[0]['limitations']]
    return '\n'.join(lines)+'\n'


def run(output, base=Path('.')):
    reports,scores=evaluate(base);output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    for report in reports:
        name=report['sport'].lower()
        review.write(output/(name+'_report.json'),report)
        (output/(name+'_scores.json.gz')).write_bytes(gzip.compress(b.canonical(scores[report['sport']])+b'\n',mtime=0))
    (output/'README.md').write_text(render(reports))
    return reports


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True);parser.add_argument('--base',default='.')
    args=parser.parse_args()
    print(json.dumps([{'sport':d['sport'],'selected':d['selected_development_candidate']} for d in run(args.output,Path(args.base))]))
