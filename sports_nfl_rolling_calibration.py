"""Fixed annual NFL recalibration development; no prospective or production writes."""
from pathlib import Path
import argparse
import json
import math

import sports_nfl_calibration_development as fixed

b = fixed.b
review = fixed.review
POLICY = {
    'schema': 'nfl-annual-chronological-calibration-development-v1',
    'evaluation_seasons': [2022, 2023, 2024],
    'base_fit_first_season': 2014,
    'base_fit_last_season': 'evaluation season minus four',
    'calibration_fit_seasons': 'three complete seasons immediately before evaluation',
    'base_l2_penalty': 0.01, 'calibration_l2_penalty': 0.01,
    'candidate': 'sigmoid(intercept + slope * annually refitted base logit)',
    'tie_policy': 'Preserve each annual base-training-only smoothed tie prior.',
    'selection_grid': False, '2025_evaluated': False, '2026_prospective_used': False,
    'forecast_changes': 0, 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0,
}


def roles(rows, year):
    if type(year) is not int or year not in POLICY['evaluation_seasons']:
        raise ValueError('Unsupported fixed annual evaluation year')
    # Reuse the pinned experiment's regular-season identity, numeric, clock,
    # dimension and 2014-2024 boundary checks. Never admit 2025/live 2026.
    allowed = [row for group in fixed.partition(rows) for row in group]
    training = [r for r in allowed if 2014 <= r['game'].season <= year-4]
    calibration = [r for r in allowed if year-3 <= r['game'].season < year]
    evaluation = [r for r in allowed if r['game'].season == year]
    if (not all((training, calibration, evaluation))
            or max(r['game'].kickoff for r in training) >= min(r['game'].kickoff for r in calibration)
            or max(r['game'].kickoff for r in calibration) >= min(r['game'].kickoff for r in evaluation)):
        raise ValueError('Annual chronological roles overlap or are empty')
    return training, calibration, evaluation


def fit_parameters(training, calibration, *, year):
    """Evaluation rows are absent from this fitting interface."""
    if (type(year) is not int or year not in POLICY['evaluation_seasons']
            or not training or not calibration
            or any(r['game'].game_type != 'REG' or not 2014 <= r['game'].season <= year-4 for r in training)
            or any(r['game'].game_type != 'REG' or not year-3 <= r['game'].season < year for r in calibration)):
        raise ValueError('Invalid annual fitting roles')
    selected = training + calibration
    if (len({r['game'].identifier for r in selected}) != len(selected)
            or any(len(r['x']) != len(fixed.efficiency.FEATURES)
                or not all(type(x) in (int, float) and math.isfinite(x) for x in r['x'])
                or r['game'].kickoff.tzinfo is None for r in selected)
            or max(r['game'].kickoff for r in training) >= min(r['game'].kickoff for r in calibration)):
        raise ValueError('Invalid annual fitting identity, features or clocks')
    base = b.fit(training, POLICY['base_l2_penalty'], dimension=len(fixed.efficiency.FEATURES))
    fitting = [{'game': r['game'], 'x': [1.0, b.dot(base['weights'], r['x'])]}
               for r in calibration if r['game'].outcome != 'tie']
    calibrator = b.fit(fitting, POLICY['calibration_l2_penalty'], dimension=2)
    return {'evaluation_year': year, 'base_weights': base['weights'],
            'calibrator_weights': calibrator['weights'], 'tie_probability': b.tie_rate(training),
            'training_games': len(training), 'calibration_games': len(calibration),
            'conditional_calibration_games': len(fitting),
            'base_game_ids_sha256': review.digest([r['game'].identifier for r in training]),
            'calibration_game_ids_sha256': review.digest([r['game'].identifier for r in calibration]),
            'latest_base_kickoff_utc': max(r['game'].kickoff for r in training).isoformat(),
            'latest_calibration_kickoff_utc': max(r['game'].kickoff for r in calibration).isoformat(),
            'policy_sha256': review.digest(POLICY)}


def experiment(rows):
    yearly = []; scored = []; full = {key: [] for key in ('uncalibrated', 'calibrated')}
    decisive = {key: [] for key in full}; differences = []
    for year in POLICY['evaluation_seasons']:
        training, calibration, evaluation = roles(rows, year)
        fitted = fit_parameters(training, calibration, year=year)
        digest = review.digest(fitted)
        metrics = fixed.evaluate(evaluation, fitted)
        if review.digest(fitted) != digest:
            raise ValueError('Annual evaluation changed frozen fitted parameters')
        yearly.append({'year': year, 'parameters_sha256_before_evaluation': digest,
                       'fitted_parameters': fitted, 'evaluation': metrics})
        for row in evaluation:
            game = row['game']; block = str(year)+'/'+str(game.week); values = {}
            probabilities = {}
            for name in full:
                p = fixed.probabilities(row, fitted, name == 'calibrated')
                review.distribution(p, ('home', 'away', 'tie')); probabilities[name] = p
                full[name].append({'block': block, **review.full_scores(p, game.outcome)})
                if game.outcome != 'tie':
                    score = review.binary_scores(p['home']/(1-p['tie']), game.outcome)
                    values[name] = score; decisive[name].append({'block': block, **score})
            if game.outcome != 'tie':
                differences.append({'block': block, **{key: values['calibrated'][key]-values['uncalibrated'][key]
                    for key in ('brier', 'log_loss', 'accuracy')}})
            scored.append({'game_id': game.identifier, 'block': block,
                           'outcome': game.outcome, 'probabilities': probabilities})
    return {'policy': POLICY, 'annual_fits': yearly,
            'evaluation_games': len(scored), 'evaluation_rows_sha256': review.digest(scored),
            'all_games_three_outcome': {k: review.estimates(v) for k, v in full.items()},
            'all_decisive': {k: review.estimates(v) for k, v in decisive.items()},
            'paired_calibrated_minus_uncalibrated': review.estimates(differences),
            'independent_chronological_fitting_roles': True,
            'fresh_confirmatory_holdout': False, 'prospective_predictions': 0,
            'forecast_changes': 0, 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0,
            'limitation': fixed.LIMITATION + ' Annual refits use only completed earlier seasons; '
                'an earlier evaluation season can enter a later year fitting role. '
                'This fixed recipe is not selected by evaluation losses and does not replace the retained fixed-fit experiment.'}


def run(base=Path('.')):
    base = Path(base)
    schedule = base/'benchmarks/nfl_independent_v1/games_2010_2025.csv'
    stats = base/'benchmarks/nfl_efficiency_v2/team_stats_2010_2024.csv'
    if b.sha256(schedule.read_bytes()) != fixed.SCHEDULE_SHA256 or b.sha256(stats.read_bytes()) != fixed.STATS_SHA256:
        raise ValueError('Pinned NFL annual recalibration source bytes changed')
    games = b.read_games(schedule, last=2024)
    return experiment(fixed.efficiency.features(games, fixed.efficiency.read_stats(stats, games)))


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--base', type=Path, default=Path('.'))
    args = cli.parse_args()
    print(json.dumps(run(args.base), indent=2, sort_keys=True, allow_nan=False))
