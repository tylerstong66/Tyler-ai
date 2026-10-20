import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sports_accuracy_readiness as a


def metric(games, correct):
    return {'games': games, 'blocks': 2, 'uncertainty_status': 'insufficient_blocks',
            'mean': {'accuracy': correct / games if games else None,
                     'brier': .4 if games else None, 'log_loss': .6 if games else None}}


def sources():
    review = {}
    for sport, count in (('NFL', 4), ('NHL', 5), ('MLB', 3)):
        model = 'v2' if sport == 'NFL' else 'model'
        paired = count - 1
        review[sport] = {
            'sport': sport, 'input_integrity': 'verified',
            'NO_BET': True, 'actual_wagers': 0,
            'recorded': count + 1, 'settled': count, 'pending': 1,
            'all_decisive': {model: metric(count, count-1)},
            'paired_market': {model: metric(paired, paired-1),
                              'market': metric(paired, paired-2)},
            'review_due': False, 'latest_result_verified_at': '2026-10-20T12:00:00+00:00',
            'first_100_checkpoint': {'status': 'collecting_forecasts'},
            'ties': 0, 'all_settled_three_outcome': (
                {model: metric(count, count-1)} if sport == 'NFL' else None),
        }
    shadow = {
        'NO_BET': True, 'actual_wagers': 0,
        'enrolled': 5, 'scored': 3, 'pending': 2,
        'same_game_priced_count': 3,
        'first_100_enrolled': {'status': 'collecting_forecasts'},
        'same_game_priced': {'candidate': metric(3, 2), 'market': metric(3, 1)},
    }
    hitter = {
        'no_wagers': True,
        'benchmark': {'no_wagers': True, 'frozen_player_game_forecasts': 8,
                      'scored': 4, 'pending': 3, 'ineligible': 1,
                      'distinct_official_game_ids_with_eligible_settlements': 2,
                      'market_odds_available': False,
                      'metrics': {'hit': {'eligible_player_games': 4, 'brier': .23},
                                  'hr': {'eligible_player_games': 4, 'brier': .09}}}
    }
    return review, shadow, hitter


class AccuracyReadinessTests(unittest.TestCase):
    def run_snapshot(self, mutate=None):
        reports, shadow, hitter = sources()
        if mutate:
            mutate(reports, shadow, hitter)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for path, value in ((a.SHADOW, shadow), (a.HITTER, hitter)):
                destination = base/path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(json.dumps(value))
            originals = {str(p): p.read_bytes() for p in base.rglob('*') if p.is_file()}
            with patch.object(a.review, 'review',
                              side_effect=lambda root, sport, models: reports[sport]):
                result = a.snapshot(base)
            self.assertEqual({str(p): p.read_bytes() for p in base.rglob('*') if p.is_file()}, originals)
            return result

    def test_distinct_denominators_no_combined_rate_and_no_writes(self):
        out = self.run_snapshot()
        self.assertIsNone(out['combined_all_sports_win_rate'])
        self.assertIsNone(out['ROI'])
        self.assertEqual(out['actual_wagers'], 0)
        self.assertEqual(out['primary_prospective']['NFL']['all_decisive_model']['correct_picks'], 3)
        self.assertEqual(out['primary_prospective']['NFL']['same_game_priced_market']['games'], 3)
        self.assertEqual(out['nhl_challenger_overlap']['candidate']['correct_picks'], 2)
        self.assertTrue(out['nhl_challenger_overlap']['overlaps_primary_nhl'])
        self.assertIsNone(out['mlb_hitter_conditional_props']['winner_pick_accuracy'])
        rendered = a.render(out)
        self.assertIn('OVERLAPS NHL', rendered)
        self.assertIn('No valid combined sports accuracy or ROI', rendered)

    def test_invalid_market_denominator_rejected(self):
        def change(reports, shadow, hitter):
            reports['NFL']['paired_market']['market'] = metric(1, 1)
        with self.assertRaisesRegex(ValueError, 'Mixed-sample'):
            self.run_snapshot(change)

    def test_challenger_cannot_exceed_primary_scored_sample(self):
        def change(reports, shadow, hitter):
            shadow['scored'] = 6
            shadow['enrolled'] = 8
        with self.assertRaisesRegex(ValueError, 'denominators'):
            self.run_snapshot(change)

    def test_hitter_player_game_accounting_rejected_when_mismatched(self):
        def change(reports, shadow, hitter):
            hitter['benchmark']['scored'] = 5
        with self.assertRaisesRegex(ValueError, 'accounting inconsistent'):
            self.run_snapshot(change)

    def test_no_wager_guard_rejects_false_source_flag(self):
        def change(reports, shadow, hitter):
            shadow['NO_BET'] = False
        with self.assertRaisesRegex(ValueError, 'research-only'):
            self.run_snapshot(change)

    def test_accuracy_must_correspond_to_integer_correct_picks(self):
        with self.assertRaisesRegex(ValueError, 'Noninteger'):
            a._score({'games': 10, 'blocks': 2, 'uncertainty_status': 'insufficient_blocks',
                      'mean': {'accuracy': .555, 'brier': .2, 'log_loss': .3}})

    def test_zero_game_accuracy_remains_unavailable(self):
        out = a._score(metric(0, 0))
        self.assertIsNone(out['accuracy'])
        self.assertIsNone(out['correct_picks'])


if __name__ == '__main__':
    unittest.main()
