"""Read-only scoring reviews of saved prospective forecasts; never enroll or settle."""
import hashlib
import json
import math
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

VERSION = 'prospective-review-v1'
MILESTONE = 100
BOOTSTRAP_DRAWS = 2000
MIN_BLOCKS = 5
BINS = 5
COHORTS = {
    'NFL': ('benchmarks/nfl_prospective_v2', ('v2', 'v1')),
    'NHL': ('benchmarks/two_way_prospective/nhl', ('model', 'fixed_elo')),
    'MLB': ('benchmarks/two_way_prospective/mlb', ('model', 'fixed_elo')),
}
LIMITATION = ('Experimental descriptive results. NFL uncertainty uses season/week blocks; '
              'NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. '
              'Intervals require at least five blocks and are unavailable below that; '
              'five blocks or 100 settled games does not establish a betting edge. '
              'Repeated monitoring intervals are not sequential significance tests. '
              'No model promotion, forecast changes, wagers, or profits are inferred.')


class IntegrityError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def utc(value):
    date = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if date.tzinfo is None:
        raise IntegrityError('Timezone-aware timestamps required')
    return date.astimezone(timezone.utc)


def probability(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise IntegrityError('Invalid probability')
    return value


def distribution(value, labels):
    if set(value) != set(labels):
        raise IntegrityError('Unexpected probability outcomes')
    for p in value.values():
        probability(p)
    if not math.isclose(sum(value.values()), 1, abs_tol=1e-10):
        raise IntegrityError('Probabilities do not sum to one')
    return value


def binary_scores(p, outcome):
    y = outcome == 'home'
    clipped = min(1 - 1e-12, max(1e-12, p))
    return {'brier': 2 * (p - y) ** 2,
            'log_loss': -math.log(clipped if y else 1 - clipped),
            'accuracy': float(('home' if p >= .5 else 'away') == outcome)}


def full_scores(probs, outcome):
    if probs[outcome] <= 0:
        raise IntegrityError('Observed outcome has zero probability; finite log loss unavailable')
    chosen = max(('home', 'away', 'tie'), key=lambda k: probs[k])
    return {'brier': sum((p - (label == outcome)) ** 2 for label, p in probs.items()),
            'log_loss': -math.log(probs[outcome]), 'accuracy': float(chosen == outcome)}


def verify_scores(stored, expected):
    for field, value in expected.items():
        actual = stored.get(field)
        if value is None:
            if actual is not None:
                raise IntegrityError('Stored score disagrees with recomputed result')
        elif not isinstance(actual, (int, float)) or not math.isfinite(actual) or not math.isclose(actual, value, abs_tol=1e-10):
            raise IntegrityError('Stored score disagrees with recomputed result')


def load_rows(root, sport, models):
    if not (root / 'predictions').is_dir() or not (root / 'results').is_dir():
        raise IntegrityError('Prediction or result directory missing')
    predictions = {}
    for path in sorted((root / 'predictions').glob('*.json')):
        pred = json.loads(path.read_text())
        saved = pred.get('sha256')
        if saved != digest({k: v for k, v in pred.items() if k != 'sha256'}):
            raise IntegrityError(f'{path.name}: forecast hash mismatch')
        if pred['game_id'] in predictions or path.stem != pred['game_id']:
            raise IntegrityError('Duplicate or mismatched forecast ID')
        if pred.get('NO_BET') is not True or pred.get('actual_wagers') != 0:
            raise IntegrityError('Paper-only forecast required')
        if not utc(pred['generated_at']) <= utc(pred['recorded_at']) < utc(pred['kickoff']):
            raise IntegrityError('Forecast timestamps are not pregame')
        if any(utc(source['retrieved_at']) > utc(pred['generated_at']) for source in pred.get('source_snapshots', [])):
            raise IntegrityError('Source snapshot was retrieved after forecast generation')
        for model in models:
            distribution(pred[model], ('home', 'away', 'tie') if sport == 'NFL' else ('home', 'away'))
        if pred.get('market') is not None:
            probability(pred['market']['conditional_home_probability'])
            if utc(pred['market_observed_at']) > utc(pred['generated_at']):
                raise IntegrityError('Market probability observed after forecast generation')
        predictions[pred['game_id']] = pred
    rows = []
    seen = set()
    for path in sorted((root / 'results').glob('*.json')):
        result = json.loads(path.read_text())
        identifier = result['game_id']
        if identifier in seen or path.stem != identifier or identifier not in predictions:
            raise IntegrityError('Duplicate, orphan, or mismatched result ID')
        seen.add(identifier)
        pred = predictions[identifier]
        if any(result.get(key, pred.get(key)) != pred.get(key) for key in ('event_id', 'season', 'week', 'sport')):
            raise IntegrityError('Result metadata disagrees with saved forecast')
        if result.get('prediction_sha256') != pred['sha256']:
            raise IntegrityError('Result does not reference the saved forecast hash')
        if utc(result['verified_at']) < utc(pred['kickoff']):
            raise IntegrityError('Result verification predates scheduled start')
        for side in ('home', 'away'):
            score = result[side + '_score']
            if isinstance(score, bool) or not isinstance(score, int) or score < 0:
                raise IntegrityError('Invalid final score')
        outcome = ('home' if result['home_score'] > result['away_score'] else
                   'away' if result['home_score'] < result['away_score'] else 'tie')
        if result['outcome'] != outcome or (sport != 'NFL' and outcome == 'tie'):
            raise IntegrityError('Outcome disagrees with final scores')
        block = (f"{pred['season']}/{pred['week']}" if sport == 'NFL' else
                 utc(pred['kickoff']).astimezone(ZoneInfo('America/New_York')).date().isoformat())
        row = {'game_id': identifier, 'block': block, 'outcome': outcome,
               'binary': {}, 'full': {}, 'probabilities': {}, 'verified_at': result['verified_at']}
        for model in models:
            probs = pred[model]
            if sport == 'NFL':
                full = full_scores(probs, outcome)
                row['full'][model] = full
                if probs['home'] + probs['away'] <= 0:
                    raise IntegrityError('Conditional home probability undefined')
                conditional = probs['home'] / (1 - probs['tie'])
                expected = {'full_brier': full['brier'], 'full_log_loss': full['log_loss'],
                            'binary_brier': None, 'conditional_log_loss': None, 'correct': None}
            else:
                conditional = probs['home']
                expected = {}
            probability(conditional)
            row['probabilities'][model] = {'conditional_home': conditional, **probs}
            if outcome != 'tie':
                binary = binary_scores(conditional, outcome)
                row['binary'][model] = binary
                expected.update({'binary_brier' if sport == 'NFL' else 'brier': binary['brier'],
                                 'conditional_log_loss' if sport == 'NFL' else 'log_loss': binary['log_loss'],
                                 'correct': binary['accuracy']})
            verify_scores(result['scores'][model], expected)
        market = pred.get('market')
        if market is not None and outcome != 'tie':
            p = market['conditional_home_probability']
            binary = binary_scores(p, outcome)
            row['binary']['market'] = binary
            row['probabilities']['market'] = {'conditional_home': p}
            verify_scores(result['scores'].get('market', {}), {
                'binary_brier' if sport == 'NFL' else 'brier': binary['brier'],
                'conditional_log_loss' if sport == 'NFL' else 'log_loss': binary['log_loss'],
                'correct': binary['accuracy']})
        elif 'market' in result['scores']:
            raise IntegrityError('Market score lacks an eligible saved market forecast')
        rows.append(row)
    return predictions, rows


def percentile(values, q):
    values = sorted(values)
    index = (len(values) - 1) * q
    low = int(index)
    return values[low] + (values[math.ceil(index)] - values[low]) * (index - low)


def estimates(records, draws=BOOTSTRAP_DRAWS):
    """Game-weighted means and percentile CIs from shared block resampling."""
    fields = ('brier', 'log_loss', 'accuracy')
    grouped = defaultdict(list)
    for record in records:
        grouped[record['block']].append(record)
    mean = {field: sum(r[field] for r in records) / len(records) if records else None for field in fields}
    intervals = {field: None for field in fields}
    if len(grouped) >= MIN_BLOCKS:
        groups = [grouped[key] for key in sorted(grouped)]
        totals = [(len(group), [sum(r[field] for r in group) for field in fields]) for group in groups]
        samples = {field: [] for field in fields}
        rng = random.Random(20261014)
        for _ in range(draws):
            selected = [totals[rng.randrange(len(totals))] for _ in totals]
            size = sum(count for count, _ in selected)
            for i, field in enumerate(fields):
                samples[field].append(sum(sums[i] for _, sums in selected) / size)
        intervals = {field: [percentile(values, .025), percentile(values, .975)] for field, values in samples.items()}
    return {'games': len(records), 'blocks': len(grouped), 'mean': mean, 'ci95': intervals,
            'uncertainty_status': 'available_descriptive' if len(grouped) >= MIN_BLOCKS else 'insufficient_blocks',
            'interval_method': 'percentile block bootstrap', 'bootstrap_draws': draws,
            'minimum_blocks': MIN_BLOCKS}


def wilson(successes, total):
    if not total:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z*z / total
    center = (p + z*z / (2*total)) / denominator
    width = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / denominator
    return [max(0, center-width), min(1, center+width)]


def calibration(observations):
    bins = []
    for index in range(BINS):
        selected = [(p, y) for p, y in observations if min(int(p * BINS), BINS-1) == index]
        count = len(selected)
        bins.append({'lower': index/BINS, 'upper': (index+1)/BINS, 'games': count,
                     'mean_probability': sum(p for p, _ in selected)/count if count else None,
                     'observed_rate': sum(y for _, y in selected)/count if count else None,
                     'observed_rate_wilson95': wilson(sum(y for _, y in selected), count)})
    return {'games': len(observations), 'bins': bins,
            'limitation': 'Fixed five bins. Wilson bin intervals assume independent observations; descriptive only.'}


def subset_metrics(rows, models, kind):
    return {model: estimates([{'block': r['block'], **r[kind][model]} for r in rows]) for model in models}


def comparisons(rows, model, baselines):
    output = {}
    for baseline in baselines:
        paired = [r for r in rows if model in r['binary'] and baseline in r['binary']]
        records = [{'block': r['block'], **{f: r['binary'][model][f] - r['binary'][baseline][f]
                                          for f in ('brier', 'log_loss', 'accuracy')}} for r in paired]
        output[baseline] = estimates(records)
        output[baseline]['direction'] = 'model minus baseline; negative Brier/log loss favors model; positive accuracy favors model'
    return output


def collection_evidence(root, sport):
    manifests = sorted((root / 'captures').glob('*/manifest.json'))
    if not manifests:
        return {'latest_manifest': None, 'collection_completed': None, 'errors': None, 'excluded': None}
    path = manifests[-1]
    manifest = json.loads(path.read_text())
    enrollment_path = path.parent/'enrollment.json'
    enrollment = json.loads(enrollment_path.read_text()) if sport == 'NFL' and enrollment_path.exists() else {}
    failures = sorted((root/'errors').glob('*.json'))
    newer_failure = failures[-1] if failures and failures[-1].stem > path.parent.name else None
    return {'latest_manifest': str(path), 'collection_completed': manifest.get('collection_completed'),
            'errors': manifest.get('errors', []), 'excluded': manifest.get('excluded', enrollment.get('excluded', [])),
            'optional_availability_errors': manifest.get('optional_availability_errors', []),
            'newer_saved_collection_failure': json.loads(newer_failure.read_text()) if newer_failure else None,
            'completion_note': 'NFL completion must be corroborated with the successful workflow run.' if sport == 'NFL' else
                               'Manifest completion alone does not imply absence of per-game errors.'}


def review(root, sport, models):
    predictions, rows = load_rows(root, sport, models)
    decisive = [r for r in rows if r['outcome'] != 'tie']
    paired = [r for r in decisive if 'market' in r['binary']]
    model_calibration = {model: calibration([(r['probabilities'][model]['conditional_home'], r['outcome'] == 'home') for r in decisive]) for model in models}
    full_calibration = {model: {label: calibration([(r['probabilities'][model][label], r['outcome'] == label) for r in rows])
                                for label in ('home', 'away', 'tie')} for model in models} if sport == 'NFL' else None
    return {'sport': sport, 'input_integrity': 'verified', 'recorded': len(predictions), 'settled': len(rows),
            'pending': len(predictions)-len(rows), 'ties': len(rows)-len(decisive),
            'review_milestone': MILESTONE, 'review_due': len(rows) >= MILESTONE,
            'review_status': 'ready_for_human_review' if len(rows) >= MILESTONE else 'collecting',
            'latest_result_verified_at': max((r['verified_at'] for r in rows), key=utc, default=None),
            'input_sha256': digest({'predictions': predictions, 'results': [json.loads(p.read_text()) for p in sorted((root/'results').glob('*.json'))]}),
            'all_settled_three_outcome': subset_metrics(rows, models, 'full') if sport == 'NFL' else None,
            'all_decisive': subset_metrics(decisive, models, 'binary'),
            'paired_market': subset_metrics(paired, (*models, 'market'), 'binary'),
            'paired_differences': comparisons(decisive, models[0], (models[1], 'market')),
            'conditional_home_calibration': model_calibration,
            'paired_market_calibration': calibration([(r['probabilities']['market']['conditional_home'], r['outcome'] == 'home') for r in paired]),
            'full_outcome_calibration': full_calibration, 'collection_evidence': collection_evidence(root, sport),
            'block_unit': 'season/week' if sport == 'NFL' else 'Eastern scheduled game date',
            'brier_scale': 'sum over outcomes; two-way Brier = 2*(p-y)^2, range 0 to 2',
            'probability_policy': 'Saved pregame probabilities only; NFL binary metrics condition on no tie.',
            'limitation': LIMITATION, 'NO_BET': True, 'actual_wagers': 0}


def fmt(value, percent=False):
    return 'Unavailable' if value is None else f'{value:.1%}' if percent else f'{value:.4f}'


def render(data):
    lines = [f"# {data['sport']} prospective benchmark review", '', '**NO BET — actual wagers $0.**', '']
    if data.get('input_integrity') != 'verified':
        return '\n'.join(lines + ['Input integrity error: ' + data['error'], '', 'Metrics withheld pending verification.', ''])
    lines += [f"Recorded: **{data['recorded']}** · Settled: **{data['settled']}** · Pending: **{data['pending']}**",
              '', f"100-settlement milestone: **{data['review_status']}**. This flag requests human review; it does not authorize model promotion or wagering.",
              '', f"Latest result verified: {data['latest_result_verified_at'] or 'Unavailable'} (UTC).",
              '', 'Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.',
              'Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.',
              '', f"Uncertainty unit: {data['block_unit']}. CIs require at least {MIN_BLOCKS} blocks."]
    sections = [('All settled games — three outcomes, including NFL ties', 'all_settled_three_outcome'),
                ('All decisive games — conditional two-way scores', 'all_decisive'),
                ('Same-game comparisons with saved market odds — decisive games only', 'paired_market')]
    for title, key in sections:
        metrics = data[key]
        if metrics is None:
            continue
        lines += ['', '## '+title, '', '| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |',
                  '|---|---:|---:|---:|---:|---:|---|---|---|']
        for model, m in metrics.items():
            intervals = ['Unavailable' if m['ci95'][field] is None else ' to '.join(fmt(v, field == 'accuracy') for v in m['ci95'][field]) for field in ('brier', 'log_loss', 'accuracy')]
            lines.append(f"| {model} | {m['games']} | {m['blocks']} | {fmt(m['mean']['brier'])} | {fmt(m['mean']['log_loss'])} | {fmt(m['mean']['accuracy'], True)} | {' | '.join(intervals)} |")
    lines += ['', 'NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.',
              '', '## Paired differences', '', 'Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.',
              '', '| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |',
              '|---|---:|---:|---:|---|---:|---|---:|---|']
    for baseline, m in data['paired_differences'].items():
        cells = []
        for field in ('brier', 'log_loss', 'accuracy'):
            ci = m['ci95'][field]
            display = lambda value: fmt(value, field == 'accuracy').replace('%', ' pp')
            cells += [display(m['mean'][field]), 'Unavailable' if ci is None else ' to '.join(display(v) for v in ci)]
        lines.append(f"| {baseline} | {m['games']} | {m['blocks']} | {' | '.join(cells)} |")
    calibrations = dict(data['conditional_home_calibration'])
    calibrations['market (paired only)'] = data['paired_market_calibration']
    if data['full_outcome_calibration']:
        for model, outcomes in data['full_outcome_calibration'].items():
            for label, value in outcomes.items():
                calibrations[model+' full '+label] = value
    lines += ['', '## Calibration', '', 'Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.',
              'Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.',
              '', '| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |',
              '|---|---|---:|---:|---:|---|']
    for model, value in calibrations.items():
        for item in value['bins']:
            ci = item['observed_rate_wilson95']
            lines.append(f"| {model} | {item['lower']:.0%}–{item['upper']:.0%} | {item['games']} | {fmt(item['mean_probability'], True)} | {fmt(item['observed_rate'], True)} | {'Unavailable' if ci is None else ' to '.join(fmt(v, True) for v in ci)} |")
    evidence = data['collection_evidence']
    lines += ['', '## Collection evidence', '', f"Latest saved manifest: {evidence['latest_manifest'] or 'Unavailable'}.",
              f"Manifest completion field: {evidence['collection_completed']}. Errors: {json.dumps(evidence['errors'])}. Exclusions: {json.dumps(evidence['excluded'])}.",
              f"Optional availability errors: {json.dumps(evidence.get('optional_availability_errors', []))}.",
              f"Newer saved collection failure: {json.dumps(evidence.get('newer_saved_collection_failure'))}.",
              evidence.get('completion_note', ''), '', LIMITATION, '']
    return '\n'.join(lines)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def run(base=Path('.')):
    base = Path(base)
    reports = []
    for sport, (folder, models) in COHORTS.items():
        root = base / folder
        try:
            data = review(root, sport, models)
        except (ValueError, KeyError, TypeError, OSError) as error:
            data = {'sport': sport, 'input_integrity': 'error', 'error': str(error), 'review_due': None,
                    'NO_BET': True, 'actual_wagers': 0}
        data['report_version'] = VERSION
        write(root/'REVIEW.json', data)
        (root/'REVIEW.md').write_text(render(data))
        reports.append(data)
    index_rows = []
    for data in reports:
        keys = ('sport', 'input_integrity', 'recorded', 'settled', 'pending', 'review_milestone', 'review_due', 'review_status', 'latest_result_verified_at', 'error')
        item = {key: data[key] for key in keys if key in data}
        item['review_path'] = COHORTS[data['sport']][0]+'/REVIEW.json'
        if data['input_integrity'] == 'verified':
            item['market_paired_games'] = next(iter(data['paired_market'].values()))['games']
        index_rows.append(item)
    index = {'report_version': VERSION, 'leagues': index_rows, 'NO_BET': True, 'actual_wagers': 0,
             'limitation': LIMITATION}
    write(base/'benchmarks/two_way_prospective/REVIEW_ALL.json', index)
    lines = ['# Prospective benchmark reviews', '', '**NO BET — actual wagers $0.**', '',
             '| Sport | Settled | Recorded | Pending | Market-paired | 100-game review | Report |',
             '|---|---:|---:|---:|---:|---|---|']
    links = {'NFL': '../nfl_prospective_v2/REVIEW.md', 'NHL': 'nhl/REVIEW.md', 'MLB': 'mlb/REVIEW.md'}
    for data in reports:
        sport = data['sport']
        if data['input_integrity'] != 'verified':
            lines.append(f"| {sport} | Unavailable | Unavailable | Unavailable | Unavailable | Integrity error | [Review]({links[sport]}) |")
        else:
            paired = next(iter(data['paired_market'].values()))['games']
            lines.append(f"| {sport} | {data['settled']} | {data['recorded']} | {data['pending']} | {paired} | {data['review_status']} | [Review]({links[sport]}) |")
    lines += ['', 'Each sport is a separate prospective cohort. Counts are games, not the number of model scores. These cohorts are not pooled or described as unique games across cohorts.', '', LIMITATION, '']
    (base/'benchmarks/two_way_prospective/REVIEW_ALL.md').write_text('\n'.join(lines))
    return index


if __name__ == '__main__':
    result = run()
    print(json.dumps([{'sport': d['sport'], 'input_integrity': d['input_integrity'],
                       'settled': d.get('settled'), 'review_due': d['review_due']} for d in result['leagues']]))
    raise SystemExit(0 if all(d['input_integrity'] == 'verified' for d in result['leagues']) else 1)
