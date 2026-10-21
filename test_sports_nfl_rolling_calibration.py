"""Synthetic annual fitting isolation; never fit on the live NFL cohort."""
import copy
import json
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sports_nfl_rolling_calibration as rolling
import test_sports_nfl_calibration_development as fixtures


def rows():
    seed = fixtures.rows()[:24]; output = []
    for year in range(2014, 2025):
        for index, row in enumerate(seed):
            game = row['game']
            output.append({'game': replace(game, season=year, identifier=f'{year}_{index}',
                kickoff=game.kickoff.replace(year=year)), 'x': list(row['x'])})
    return output


class AnnualCalibrationTests(unittest.TestCase):
    def test_retained_actual_report_replays_exactly_and_does_not_support_adoption(self):
        retained = json.loads((Path(__file__).parent/
            'benchmarks/nfl_annual_calibration_development_v1/DEVELOPMENT_RESULT.json').read_text())
        report = rolling.run(Path(__file__).parent)
        self.assertEqual(report, retained['report'])
        self.assertEqual(retained['decision'], 'NO_ADOPTION_SUPPORTED_BY_PROPER_LOSSES')
        for loss in ('brier', 'log_loss'):
            self.assertGreater(report['paired_calibrated_minus_uncalibrated']['mean'][loss], 0)
        self.assertFalse(report['promotion_allowed'])

    def test_each_year_has_disjoint_prior_only_fitting_roles(self):
        for year in (2022, 2023, 2024):
            train, fit, evaluation = rolling.roles(rows(), year)
            self.assertEqual(max(r['game'].season for r in train), year-4)
            self.assertEqual({r['game'].season for r in fit}, set(range(year-3, year)))
            self.assertEqual({r['game'].season for r in evaluation}, {year})
            self.assertFalse({r['game'].identifier for r in train+fit} &
                             {r['game'].identifier for r in evaluation})
            with self.assertRaises(ValueError): rolling.fit_parameters(train, evaluation, year=year)

    def test_last_evaluation_labels_cannot_change_any_fitted_parameters(self):
        source = rows(); altered = copy.deepcopy(source)
        for row in altered:
            if row['game'].season == 2024:
                game = row['game']; row['game'] = replace(game,
                    home_score=game.away_score, away_score=game.home_score)
        first = rolling.experiment(source); second = rolling.experiment(altered)
        self.assertEqual([r['fitted_parameters'] for r in first['annual_fits']],
                         [r['fitted_parameters'] for r in second['annual_fits']])
        self.assertNotEqual(first['evaluation_rows_sha256'], second['evaluation_rows_sha256'])
        self.assertEqual(first['evaluation_games'], 72)
        self.assertEqual(first['prospective_predictions'], 0)
        self.assertFalse(first['fresh_confirmatory_holdout']); self.assertFalse(first['promotion_allowed'])

    def test_earlier_evaluation_enters_only_later_calibration_and_tie_prior_is_preserved(self):
        source = rows(); altered = copy.deepcopy(source)
        for row in altered:
            if row['game'].season == 2022:
                game = row['game']; row['game'] = replace(game,
                    home_score=game.away_score, away_score=game.home_score)
        parameters = []
        for dataset in (source, altered):
            annual = []
            for year in (2022, 2023, 2024):
                train, fit, evaluation = rolling.roles(dataset, year)
                p = rolling.fit_parameters(train, fit, year=year)
                for row in evaluation:
                    for calibrated in (True, False):
                        self.assertEqual(rolling.fixed.probabilities(row, p, calibrated)['tie'], p['tie_probability'])
                annual.append(p)
            parameters.append(annual)
        self.assertEqual(parameters[0][0], parameters[1][0])
        self.assertNotEqual(parameters[0][1]['calibrator_weights'], parameters[1][1]['calibrator_weights'])

    def test_2025_live_2026_inputs_and_nonregular_games_are_excluded(self):
        original = rows(); extras = copy.deepcopy(original[:3])
        for row, year in zip(extras, (2025, 2026, 2024)):
            row['game'] = replace(row['game'], season=year, identifier=f'excluded_{year}',
                                   game_type='POST' if year == 2024 else 'REG')
            row['x'] = [float('nan')]
        for year in (2022, 2023, 2024):
            self.assertEqual(rolling.roles(original, year), rolling.roles(original+extras, year))

    def test_bad_features_ids_clocks_and_years_fail(self):
        for value in (True, 2021, 2025):
            with self.assertRaises(ValueError): rolling.roles(rows(), value)
        for bad in ([True]*7, [float('inf')]*7, [1.0]):
            source = rows(); source[0]['x'] = bad
            with self.assertRaises(ValueError): rolling.roles(source, 2022)
        train, fit, _ = rolling.roles(rows(), 2022)
        with self.assertRaises(ValueError): rolling.fit_parameters(train+train[:1], fit, year=2022)
        fit[0]['game'] = replace(fit[0]['game'], kickoff=fit[0]['game'].kickoff.replace(year=2010))
        with self.assertRaises(ValueError): rolling.fit_parameters(train, fit, year=2022)

    def test_source_hash_mismatch_precedes_reconstruction(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'benchmarks/nfl_independent_v1/games_2010_2025.csv'
            path.parent.mkdir(parents=True); path.write_text('changed')
            with patch.object(rolling.fixed.efficiency, 'features') as features:
                with self.assertRaises(ValueError): rolling.run(Path(directory))
                features.assert_not_called()


if __name__ == '__main__': unittest.main()
