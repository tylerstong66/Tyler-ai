"""Chronological recalibration role isolation; all fixtures are synthetic."""
import copy
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest

import sports_nfl_calibration_development as calibration
import sports_historical_benchmark as b
import sports_benchmark_review as review


def rows():
    result = []
    for season in (2014, 2018, 2019, 2021, 2022, 2024):
        for i in range(24):
            value = ((i*7)%19-9)/10
            home = (i*5+season)%11 < 6
            tie = i == 0
            game = b.Game(str(season)+'_'+str(i), season, i%8+1, 'REG',
                datetime(season, 9, i+1, 17, tzinfo=timezone.utc),
                'AAA', 'BBB', False, 17 if tie else 24 if home else 14,
                17 if tie else 14 if home else 24, -110, -110)
            result.append({'game': game, 'x': [1.0, value, value**2,
                value**3, (i%3-1)/10, (i%5-2)/10, (i%7-3)/10]})
    return result


class CalibrationDevelopmentTests(unittest.TestCase):
    def test_evaluation_labels_cannot_change_fitted_parameters(self):
        original = rows()
        fitted = calibration.experiment(original)
        altered = copy.deepcopy(original)
        for row in altered:
            if row['game'].season >= 2022:
                game = row['game']
                row['game'] = replace(game, home_score=game.away_score, away_score=game.home_score)
        second = calibration.experiment(altered)
        self.assertEqual(fitted['fitted_parameters'], second['fitted_parameters'])
        self.assertEqual(fitted['parameters_sha256_before_evaluation'], second['parameters_sha256_before_evaluation'])
        self.assertNotEqual(fitted['evaluation']['evaluation_rows_sha256'], second['evaluation']['evaluation_rows_sha256'])
        self.assertFalse(fitted['fresh_confirmatory_holdout'])
        self.assertFalse(fitted['promotion_allowed'])

    def test_inputs_are_unchanged_and_ties_are_not_conditional_targets(self):
        source = rows(); before = copy.deepcopy(source)
        report = calibration.experiment(source)
        self.assertEqual(source, before)
        fitted = report['fitted_parameters']
        self.assertEqual(fitted['conditional_calibration_games'], 46)
        self.assertAlmostEqual(fitted['tie_probability'], 2.5/49)
        self.assertEqual(report['evaluation']['evaluation_games'], 48)
        self.assertEqual(report['evaluation']['all_decisive']['calibrated']['games'], 46)
        self.assertEqual(report['prospective_predictions'], 0)
        self.assertEqual(report['actual_wagers'], 0)

    def test_2025_and_live_2026_cannot_enter_any_role(self):
        original = rows(); extras = copy.deepcopy(original[:2])
        for row, season in zip(extras, (2025, 2026)):
            row['game'] = replace(row['game'], season=season, identifier=str(season)+'_unused')
            row['x'] = [float('nan')]
        self.assertEqual(calibration.experiment(original), calibration.experiment(original+extras))

    def test_role_ids_and_clocks_cannot_overlap(self):
        source = rows()
        source[-1]['game'] = replace(source[-1]['game'], identifier=source[0]['game'].identifier)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            calibration.experiment(source)
        source = rows()
        source[48]['game'] = replace(source[48]['game'], kickoff=datetime(2010, 1, 1, tzinfo=timezone.utc))
        with self.assertRaisesRegex(ValueError, 'clocks overlap'):
            calibration.experiment(source)

    def test_heldout_games_cannot_be_passed_to_fit_or_fitting_games_to_evaluate(self):
        training, fitting, heldout = calibration.partition(rows())
        with self.assertRaises(ValueError): calibration.fit_parameters(training, heldout)
        with self.assertRaises(ValueError): calibration.fit_parameters(heldout, fitting)
        frozen = calibration.fit_parameters(training, fitting)
        with self.assertRaises(ValueError): calibration.evaluate(training, frozen)

    def test_calibration_retains_tie_mass_and_normalizes_all_probabilities(self):
        training, fitting, heldout = calibration.partition(rows())
        frozen = calibration.fit_parameters(training, fitting)
        for row in heldout:
            for calibrated in (False, True):
                p = calibration.probabilities(row, frozen, calibrated)
                review.distribution(p, ('home', 'away', 'tie'))
                self.assertEqual(p['tie'], frozen['tie_probability'])

    def test_empty_role_boolean_nonfinite_and_wrong_dimension_rejected(self):
        with self.assertRaises(ValueError): calibration.experiment([])
        for bad in ([True]*7, [float('nan')]*7, [1.0]):
            source = rows(); source[0]['x'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                calibration.experiment(source)

    def test_pinned_source_mismatch_precedes_feature_reconstruction(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path = base/'benchmarks/nfl_independent_v1/games_2010_2025.csv'
            path.parent.mkdir(parents=True); path.write_text('changed')
            with patch.object(calibration.efficiency, 'features') as features:
                with self.assertRaises(ValueError): calibration.run(base)
                features.assert_not_called()


if __name__ == '__main__': unittest.main()
