"""Offline retrospective diagnostics; never fit models, enroll forecasts or fetch data."""
import argparse
import gzip
import json
import math
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import sports_benchmark_review as review
import sports_historical_benchmark as b
import sports_two_way_test as live

ROOT = Path('benchmarks/two_way_retrospective_v1')
LIMITATION = ('Retrospective reconstruction, not a blind holdout or prospective forecast. '
              'These outcomes existed before model freezing and this diagnostic was selected afterward. '
              'Revised historical snapshots cannot establish original publication times; kickoff plus '
              '12 hours is the frozen availability assumption, not an observed final publication time. '
              'No historical market-price comparison, injury/lineup effects, model selection, promotion, '
              'wagers or profits are established. Block intervals are descriptive, not sequential tests.')


def replay(history, games, model, config, evaluation_season):
    freeze = b.utc(model['frozen_at'])
    delay = timedelta(hours=config['result_delay_hours'])
    if evaluation_season <= model['training_season']:
        raise ValueError('Evaluation must follow the training season')
    if any(g['season'] > model['training_season'] for g in history):
        raise ValueError('Warmup contains evaluation-season games')
    if any(g['season'] != evaluation_season or b.utc(g['kickoff'])+delay >= freeze for g in games):
        raise ValueError('Evaluation games must be in the declared season and eligible before freeze')
    if any(not g.get('completed') for g in history+games):
        raise ValueError('Replay requires completed historical games')
    combined = live.unique_finals(history+games, freeze)
    identifiers = {g['game_id'] for g in games}
    if len(identifiers) != len(games):
        raise ValueError('Duplicate evaluation game')
    rows, excluded = [], []
    for row in live.feature_rows(combined, config):
        game = row['data']
        if game['game_id'] not in identifiers:
            continue
        if game.get('historical_resumption_ambiguous'):
            excluded.append({'game_id':game['game_id'], 'reason':'ambiguous_resumption'})
            continue
        x = row['x']
        # The live feature is rating difference / 200. Recover that same
        # difference for the existing fixed-Elo comparator, including its venue rule.
        fixed = b.sigmoid((x[1]*200+(0 if game['neutral'] is True else config['home_offset']))*math.log(10)/400)
        probabilities = {'model':b.sigmoid(b.dot(model['weights'],x)), 'fixed_elo':fixed}
        outcome = 'home' if game['home_score'] > game['away_score'] else 'away'
        rows.append({'game_id':game['game_id'], 'season':game['season'],
                     'kickoff':game['kickoff'], 'simulated_cutoff':(b.utc(game['kickoff'])-timedelta(seconds=1)).isoformat(),
                     'block':b.utc(game['kickoff']).astimezone(ZoneInfo('America/New_York')).date().isoformat(),
                     'features':x, 'outcome':outcome, 'home_probability':probabilities,
                     'scores':{name:review.binary_scores(p,outcome) for name,p in probabilities.items()},
                     'kind':'retrospective_reconstruction_not_recorded_pregame', 'NO_BET':True, 'actual_wagers':0})
    if not rows:
        raise ValueError('No eligible evaluation games')
    metrics = {name:review.estimates([{'block':row['block'], **row['scores'][name]} for row in rows])
               for name in ('model','fixed_elo')}
    difference = review.estimates([{'block':row['block'], **{
        field:row['scores']['model'][field]-row['scores']['fixed_elo'][field]
        for field in ('brier','log_loss','accuracy')}} for row in rows])
    return {'sport':config['sport'], 'evaluation_season':evaluation_season,
            'training_season':model['training_season'], 'evaluation_eligible_before':model['frozen_at'],
            'scored':len(rows), 'excluded':excluded, 'first_start':rows[0]['kickoff'], 'last_start':rows[-1]['kickoff'],
            'metrics':metrics, 'model_minus_fixed_elo':difference,
            'brier_scale':'sum over two outcomes; range 0 to 2; lower is better',
            'block_unit':'Eastern scheduled game date', 'result_delay_hours':config['result_delay_hours'],
            'ambiguous_history_policy':'Do not score ambiguous resumptions; update ratings only after their later retained start plus the frozen delay.',
            'calibration':{name:review.calibration([(row['home_probability'][name],row['outcome']=='home') for row in rows])
                           for name in ('model','fixed_elo')},
            'NO_BET':True, 'actual_wagers':0, 'limitation':LIMITATION}, rows


def evaluate(base=Path('.')):
    base = Path(base); root = base/ROOT
    manifest = json.loads((root/'inputs.json').read_text())
    for path, expected in manifest['files_sha256'].items():
        if b.sha256((base/path).read_bytes()) != expected:
            raise ValueError('Pinned replay input hash mismatch: '+path)
    protocol = json.loads((base/live.ROOT/'protocol.json').read_text())
    reports, scores = [], {}
    for sport in ('NHL','MLB'):
        folder = base/live.ROOT/sport.lower()
        model = json.loads((folder/'model.json').read_text())
        history = json.loads((folder/'history.json').read_text())
        if model['history_sha256'] != b.sha256(b.canonical(history)) or model['protocol_sha256'] != b.sha256(b.canonical(protocol)):
            raise ValueError('Frozen model provenance mismatch')
        inputs = json.loads(gzip.decompress((root/(sport.lower()+'_games.json.gz')).read_bytes()))
        data, rows = replay(history, inputs['games'], model, protocol[sport], manifest['evaluation_season'])
        data['input_manifest_sha256'] = b.sha256((root/'inputs.json').read_bytes())
        data['source_provenance'] = inputs['source_provenance']
        data['score_rows_sha256'] = b.sha256(b.canonical(rows))
        reports.append(data); scores[sport] = rows
    return reports, scores


def render(reports):
    lines = ['# Frozen NHL/MLB retrospective replay', '', '**NO BET / actual wagers $0.**', '',
             'Fixed 2025-fitted model weights, evaluated on retained 2026-season finals eligible before each October 11 freeze. '
             'No fitting or parameter search occurs. Live prospective forecasts and results remain separate.', '',
             '| Sport | Games | Date blocks | Model Brier | Fixed Elo Brier | Model log loss | Fixed Elo log loss | Model accuracy | Fixed Elo accuracy |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for data in reports:
        m,e = [data['metrics'][name] for name in ('model','fixed_elo')]
        lines.append(f"| {data['sport']} | {data['scored']} | {m['blocks']} | {m['mean']['brier']:.6f} | {e['mean']['brier']:.6f} | {m['mean']['log_loss']:.6f} | {e['mean']['log_loss']:.6f} | {m['mean']['accuracy']:.1%} | {e['mean']['accuracy']:.1%} |")
    lines += ['', 'Brier and log loss evaluate probability quality; lower is better. Accuracy alone can favor a model with worse probability losses. '
              'The observed fitted-model mean losses are higher than fixed Elo in both leagues; these point estimates do not establish a statistically reliable difference.', '',
              '## Paired differences and descriptive uncertainty', '',
              'Model minus fixed Elo on the same games. Negative Brier/log loss favors the fitted model.', '',
              '| Sport | Brier difference (95% interval) | Log-loss difference (95% interval) |', '|---|---|---|']
    for data in reports:
        diff = data['model_minus_fixed_elo']; cells=[]
        for metric in ('brier','log_loss'):
            ci = diff['ci95'][metric]
            interval = f'{ci[0]:.6f} to {ci[1]:.6f}' if ci else 'Unavailable'
            cells.append(f"{diff['mean'][metric]:.6f} ({interval})")
        lines.append(f"| {data['sport']} | {' | '.join(cells)} |")
    lines += ['', '## Scope and reproduction', '']
    for data in reports:
        lines.append(f"- {data['sport']}: {data['first_start']} through {data['last_start']} UTC; {len(data['excluded'])} ambiguous resumptions excluded from scoring. Outcome eligibility is before {data['evaluation_eligible_before']}.")
    lines += ['', 'Inputs are pinned by hashes in [inputs.json](inputs.json). Compressed game snapshots retain the source repository commit and original observed-history hash. '
              'Per-game simulated cutoffs, features, probabilities and scores are in the corresponding compressed score files. '
              'These are reconstructions, never artifacts recorded before those historical games.', '',
              'Run `python sports_two_way_replay.py --output /tmp/two-way-replay` from the repository root; compare its files with this directory. '
              'The command makes no network requests and does not write to prospective or private ledgers.', '', LIMITATION, '']
    return '\n'.join(lines)


def run(output, base=Path('.')):
    reports,scores = evaluate(base); output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    for data in reports:
        sport=data['sport'].lower()
        review.write(output/(sport+'_report.json'),data)
        (output/(sport+'_scores.json.gz')).write_bytes(gzip.compress(b.canonical(scores[data['sport']])+b'\n',mtime=0))
    (output/'README.md').write_text(render(reports))
    return reports


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True);parser.add_argument('--base',default='.')
    args=parser.parse_args(); data=run(args.output,Path(args.base))
    print(json.dumps([{'sport':d['sport'],'games':d['scored']} for d in data]))
