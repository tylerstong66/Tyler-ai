"""Offline chronological NFL recalibration development; no prospective writes."""
from pathlib import Path
import argparse
import json
import math

import sports_historical_benchmark as b
import sports_efficiency_candidate as efficiency
import sports_benchmark_review as review

SCHEDULE_SHA256 = '630be0adec995aa16c29f6cb863099220613e3394e5a9b8f206150e6a2974850'
STATS_SHA256 = 'b9614fd519f5c05f0b4c4257c5e295ff8de4f800ce3aad34292bc95f5c31f871'
POLICY = {
    'schema': 'nfl-chronological-recalibration-development-v1',
    'base_fit_seasons': [2014, 2018],
    'calibration_fit_seasons': [2019, 2021],
    'evaluation_seasons': [2022, 2024],
    'base_l2_penalty': 0.01, 'calibration_l2_penalty': 0.01,
    'conditional_calibrator': 'sigmoid(intercept + slope * base_logit)',
    'tie_policy': 'Preserve base-training-only tie prior; exclude ties from conditional calibration fit.',
    'historical_result_delay_hours': 24, 'historical_stats_delay_hours': 48,
    '2025_evaluated': False, '2026_prospective_used': False,
    'selection_grid': False, 'promotion_allowed': False,
    'NO_BET': True, 'actual_wagers': 0,
}
LIMITATION = (
    'Retrospective development with disjoint chronological parameter-fitting and evaluation games; '
    'the split and fixed recipe were designed after historical aggregate and early prospective '
    'results were seen. This is not a fresh confirmatory holdout or prospective evidence. '
    'Historical publication delays are assumed and source revisions are not independently timed. '
    'Market prices are untimestamped evaluation references only. No live recipe, forecasts, '
    'outcomes, model promotion or wagers are changed.'
)


def partition(rows):
    groups = []
    seen = set()
    for key in ('base_fit_seasons', 'calibration_fit_seasons', 'evaluation_seasons'):
        low, high = POLICY[key]
        selected = sorted([r for r in rows if r['game'].game_type == 'REG'
                           and low <= r['game'].season <= high],
                          key=lambda r: (r['game'].kickoff, r['game'].identifier))
        if not selected:
            raise ValueError('Each chronological role requires nonempty games')
        for row in selected:
            game = row['game']
            if game.identifier in seen or len(row['x']) != len(efficiency.FEATURES):
                raise ValueError('Duplicate game or incompatible historical feature vector')
            if (not all(type(x) in (int, float) and math.isfinite(x) for x in row['x'])
                    or game.outcome not in ('home', 'away', 'tie')
                    or game.kickoff.tzinfo is None):
                raise ValueError('Invalid historical calibration input')
            seen.add(game.identifier)
        groups.append(selected)
    if not all(max(r['game'].kickoff for r in earlier) < min(r['game'].kickoff for r in later)
               for earlier, later in zip(groups, groups[1:])):
        raise ValueError('Training, calibration and evaluation clocks overlap')
    return groups


def fit_parameters(training, calibration):
    """The evaluation role is deliberately absent from this fitting interface."""
    if (not training or not calibration
            or any(not 2014 <= r['game'].season <= 2018 for r in training)
            or any(not 2019 <= r['game'].season <= 2021 for r in calibration)
            or max(r['game'].kickoff for r in training) >= min(r['game'].kickoff for r in calibration)):
        raise ValueError('Invalid chronological calibration fitting roles')
    base = b.fit(training, POLICY['base_l2_penalty'], dimension=len(efficiency.FEATURES))
    tie = b.tie_rate(training)
    calibration_rows = [{'game': r['game'], 'x': [1.0, b.dot(base['weights'], r['x'])]}
                        for r in calibration if r['game'].outcome != 'tie']
    if not calibration_rows:
        raise ValueError('No decisive games for conditional calibration')
    fitted = b.fit(calibration_rows, POLICY['calibration_l2_penalty'], dimension=2)
    return {'base_weights': base['weights'], 'calibrator_weights': fitted['weights'],
            'tie_probability': tie,
            'base_game_ids_sha256': review.digest([r['game'].identifier for r in training]),
            'calibration_game_ids_sha256': review.digest([r['game'].identifier for r in calibration]),
            'training_games': len(training), 'calibration_games': len(calibration),
            'conditional_calibration_games': len(calibration_rows),
            'policy_sha256': review.digest(POLICY)}


def probabilities(row, fitted, calibrated):
    logit = b.dot(fitted['base_weights'], row['x'])
    if calibrated:
        intercept, slope = fitted['calibrator_weights']
        logit = intercept + slope * logit
    conditional = b.sigmoid(logit)
    tie = fitted['tie_probability']
    return {'home': (1-tie)*conditional, 'away': (1-tie)*(1-conditional), 'tie': tie}


def evaluate(rows, fitted):
    """Score unchanged frozen parameters on the evaluation role only."""
    if not rows or any(not 2022 <= r['game'].season <= 2024 for r in rows):
        raise ValueError('Evaluation must be confined to the fixed 2022-2024 role')
    full = {key: [] for key in ('uncalibrated', 'calibrated')}
    decisive = {key: [] for key in ('uncalibrated', 'calibrated', 'market')}
    reliability = {key: [] for key in ('uncalibrated', 'calibrated')}
    differences = []
    paired = {key: [] for key in ('uncalibrated', 'calibrated', 'market')}
    evaluation_rows = []
    for row in rows:
        game = row['game']; block = str(game.season)+'/'+str(game.week)
        values = {}
        for name in ('uncalibrated', 'calibrated'):
            p = probabilities(row, fitted, name == 'calibrated')
            review.distribution(p, ('home', 'away', 'tie'))
            full[name].append({'block': block, **review.full_scores(p, game.outcome)})
            if game.outcome != 'tie':
                conditional = p['home']/(1-p['tie'])
                score = review.binary_scores(conditional, game.outcome)
                values[name] = score
                decisive[name].append({'block': block, **score})
                reliability[name].append((conditional, game.outcome == 'home'))
        if game.outcome != 'tie':
            differences.append({'block': block, **{
                key: values['calibrated'][key]-values['uncalibrated'][key]
                for key in ('brier', 'log_loss', 'accuracy')}})
            market = b.market_probability(game)
            if market is not None:
                review.probability(market)
                for name in ('uncalibrated', 'calibrated'):
                    paired[name].append({'block': block, **values[name]})
                paired['market'].append({'block': block, **review.binary_scores(market, game.outcome)})
        evaluation_rows.append({'game_id': game.identifier, 'block': block,
                                'outcome': game.outcome,
                                'uncalibrated': probabilities(row, fitted, False),
                                'calibrated': probabilities(row, fitted, True)})
    return {'evaluation_games': len(rows),
            'evaluation_rows_sha256': review.digest(evaluation_rows),
            'all_games_three_outcome': {k: review.estimates(v) for k, v in full.items()},
            'all_decisive': {k: review.estimates(v) for k, v in decisive.items() if k != 'market'},
            'same_priced_decisive_games': {k: review.estimates(v) for k, v in paired.items()},
            'conditional_home_calibration': {k: review.calibration(v) for k, v in reliability.items()},
            'paired_calibrated_minus_uncalibrated': review.estimates(differences),
            'coefficient_selection_from_evaluation_allowed': False}


def experiment(rows):
    training, calibration, validation = partition(rows)
    fitted = fit_parameters(training, calibration)
    frozen_digest = review.digest(fitted)
    metrics = evaluate(validation, fitted)
    if review.digest(fitted) != frozen_digest:
        raise ValueError('Evaluation changed frozen calibration parameters')
    return {'policy': POLICY, 'fitted_parameters': fitted,
            'parameters_sha256_before_evaluation': frozen_digest,
            'evaluation': metrics, 'limitation': LIMITATION,
            'independent_parameter_fitting_roles': True,
            'fresh_confirmatory_holdout': False, 'prospective_predictions': 0,
            'promotion_allowed': False, 'forecast_changes': 0,
            'NO_BET': True, 'actual_wagers': 0}


def run(base=Path('.')):
    base = Path(base)
    schedule = base/'benchmarks/nfl_independent_v1/games_2010_2025.csv'
    stats = base/'benchmarks/nfl_efficiency_v2/team_stats_2010_2024.csv'
    if b.sha256(schedule.read_bytes()) != SCHEDULE_SHA256 or b.sha256(stats.read_bytes()) != STATS_SHA256:
        raise ValueError('Pinned NFL recalibration source bytes changed')
    games = b.read_games(schedule, last=2024) # 2025 and live 2026 never enter this experiment.
    rows = efficiency.features(games, efficiency.read_stats(stats, games))
    return experiment(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path('.'))
    args = parser.parse_args()
    print(json.dumps(run(args.base), sort_keys=True, indent=2, allow_nan=False))
