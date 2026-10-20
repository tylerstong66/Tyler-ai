"""Read-only native v2 coverage diagnostics and original replay guardrails."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sports_nba_receipt_coverage as coverage


def pregame(day='2026-10-21', nba='0022600085', espn='401909834', tipoff='2026-10-21T23:00:00+00:00'):
    return {
        'schema': coverage.pregame.PROTOCOL.schema,
        'NO_BET': True, 'actual_wagers': 0,
        'forecasting_enabled': False, 'model_training_enabled': False,
        'promotion_allowed': False, 'source_scope_complete': False,
        'requested_date': day,
        'strict_pregame_correlated': 1, 'withheld': [],
        'parsed_daily_page': {'requested_date': day, 'daily_game_count': 1},
        'matched': [{'nba_official_game_id': nba, 'espn_game_id': espn,
                     'nba_tipoff_utc': tipoff, 'espn_saved_tipoff_utc': tipoff}],
    }


def postgame(day='2026-10-19', game_ids=()):
    games = [{'nba_game_id': id} for id in game_ids]
    return {
        'schema': coverage.postgame.PROTOCOL.schema,
        'NO_BET': True, 'actual_wagers': 0,
        'forecasting_enabled': False, 'model_training_enabled': False,
        'promotion_allowed': False, 'source_scope_complete': False,
        'requested_date': day, 'supported_final_game_count': len(games),
        'parsed_final_page': {'games': games} if games else None,
        'page_status': ('SUPPORTED_REGULATION_FINAL_PAGE_SOURCE_ONLY'
                        if games else 'EMPTY_DAY_NO_FINAL_EVIDENCE'),
    }


class CoverageTests(unittest.TestCase):
    def run_case(self, pre, post, pre_ok=True, post_ok=True):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for root, rows in ((coverage.pregame.ROOT, pre), (coverage.postgame.ROOT, post)):
                for i, record in enumerate(rows):
                    file = base/root/f'20261020T{i:012d}Z'/'manifest.json'
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.write_text(json.dumps(record, sort_keys=True))
            before = {str(p.relative_to(base)): p.read_bytes()
                      for p in base.rglob('manifest.json')}
            with patch.object(coverage.pregame, 'replay_all', return_value={
                    'receipts_replayed': len(pre),
                    'reports': [{'source_replay_verified': pre_ok} for _ in pre]}), patch.object(
                        coverage.postgame, 'replay_all', return_value={
                    'receipts_replayed': len(post),
                    'reports': [{'source_bytes_replayed': post_ok} for _ in post]}):
                result = coverage.audit(base)
            self.assertEqual(before, {str(p.relative_to(base)): p.read_bytes()
                                      for p in base.rglob('manifest.json')})
            return result

    def test_repeated_sources_are_one_distinct_game_not_three_wins(self):
        report = self.run_case([pregame() for _ in range(3)], [postgame(), postgame()])
        self.assertEqual(report['pregame_receipts_replayed'], 3)
        self.assertEqual(report['pregame_game_observations'], 3)
        self.assertEqual(report['pregame_distinct_game_ids'], 1)
        self.assertEqual(report['pregame_repeat_observations'], 2)
        self.assertEqual(report['pregame_days']['2026-10-21']['capture_count'], 3)
        self.assertEqual(report['postgame_distinct_game_ids'], 0)
        self.assertEqual(report['postgame_days']['2026-10-19']['empty_or_unsupported_captures'], 2)
        self.assertIs(report['prediction_accuracy_computed'], False)
        self.assertIs(report['promotion_allowed'], False)
        self.assertEqual(report['actual_wagers'], 0)

    def test_conflicting_pregame_id_or_start_is_exposed_not_resolved(self):
        original = pregame()
        other = pregame(espn='401909835')
        report = self.run_case([original, other], [])
        self.assertEqual(report['pregame_distinct_game_ids'], 1)
        self.assertEqual(report['pregame_game_id_schedule_or_provider_conflicts'], ['0022600085'])
        later = pregame(tipoff='2026-10-22T00:00:00+00:00')
        report = self.run_case([original, later], [])
        self.assertEqual(report['pregame_game_id_schedule_or_provider_conflicts'], ['0022600085'])

    def test_different_dates_are_not_implicitly_a_full_schedule(self):
        a = pregame()
        b = pregame(day='2026-10-22', nba='0022600100', espn='401909900')
        out = self.run_case([a, b], [postgame(game_ids=('0022600001',)), postgame(game_ids=('0022600001',))])
        self.assertEqual(out['pregame_distinct_game_ids'], 2)
        self.assertEqual(out['postgame_source_game_claims'], 2)
        self.assertEqual(out['postgame_distinct_game_ids'], 1)
        self.assertIs(out['not_proof_of_complete_schedule'], True)
        self.assertEqual(out['independently_corroborated_final_results'], 0)

    def test_postgame_same_game_conflicting_scores_are_flagged_not_graded(self):
        a = postgame(day='2026-10-21', game_ids=('0022600085',))
        a['parsed_final_page']['games'][0].update(
            kind='regular', home_team_id=1, away_team_id=2,
            tipoff_utc='2026-10-21T23:00:00+00:00',
            nba_home_score=101, nba_away_score=99, nba_status=3)
        b = json.loads(json.dumps(a))
        same = self.run_case([], [a, b])
        self.assertEqual(same['postgame_source_game_claims'], 2)
        self.assertEqual(same['postgame_distinct_game_ids'], 1)
        self.assertEqual(same['postgame_repeat_claims_not_new_games'], 1)
        for key in ('postgame_conflicting_identity_game_ids',
                    'postgame_conflicting_schedule_game_ids',
                    'postgame_conflicting_result_game_ids'):
            self.assertEqual(same[key], [])
        b['parsed_final_page']['games'][0]['nba_home_score'] = 102
        scored = self.run_case([], [a, b])
        self.assertEqual(scored['postgame_conflicting_result_game_ids'], ['0022600085'])
        self.assertEqual(scored['postgame_conflicting_schedule_game_ids'], [])
        self.assertFalse(scored['prediction_accuracy_computed'])
        self.assertEqual(scored['independently_corroborated_final_results'], 0)

    def test_postgame_team_start_and_source_date_conflicts_are_separate(self):
        a = postgame(day='2026-10-21', game_ids=('0022600085',))
        a['parsed_final_page']['games'][0].update(
            kind='regular', home_team_id=1, away_team_id=2,
            tipoff_utc='2026-10-21T23:00:00+00:00',
            nba_home_score=101, nba_away_score=99, nba_status=3)
        identity = json.loads(json.dumps(a))
        identity['parsed_final_page']['games'][0]['home_team_id'] = 3
        result = self.run_case([], [a, identity])
        self.assertEqual(result['postgame_conflicting_identity_game_ids'], ['0022600085'])
        self.assertEqual(result['postgame_conflicting_result_game_ids'], [])
        shifted = json.loads(json.dumps(a))
        shifted['parsed_final_page']['games'][0]['tipoff_utc'] = '2026-10-21T23:30:00+00:00'
        result = self.run_case([], [a, shifted])
        self.assertEqual(result['postgame_conflicting_schedule_game_ids'], ['0022600085'])
        different_date = json.loads(json.dumps(a))
        different_date['requested_date'] = '2026-10-22'
        result = self.run_case([], [a, different_date])
        self.assertEqual(result['postgame_conflicting_schedule_game_ids'], ['0022600085'])
        self.assertEqual(result['postgame_conflicting_identity_game_ids'], [])
        self.assertIs(result['promotion_allowed'], False)

    def test_unsafe_flags_inconsistent_counts_and_duplicate_ids_fail_closed(self):
        altered = pregame(); altered['NO_BET'] = False
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            self.run_case([altered], [])
        altered = pregame(); altered['strict_pregame_correlated'] = 2
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            self.run_case([altered], [])
        altered = postgame(game_ids=('123', '123'))
        with self.assertRaisesRegex(ValueError, 'Repeated'):
            self.run_case([], [altered])

    def test_invalid_replay_blocks_reporting_even_if_manifest_claims_valid(self):
        with self.assertRaisesRegex(ValueError, 'replay count'):
            self.run_case([pregame()], [], pre_ok=False)
        with self.assertRaisesRegex(ValueError, 'replay count'):
            self.run_case([], [postgame()], post_ok=False)

    def test_actual_saved_v2_archive_replays_read_only(self):
        # Run end to end against retained real bytes in CI, without network
        # or new settlement files. Absence of saved dates remains a valid zero.
        root = Path(__file__).parent
        before = {str(p): p.read_bytes() for folder in
                  (root/coverage.pregame.ROOT, root/coverage.postgame.ROOT)
                  for p in folder.glob('*/manifest.json')}
        report = coverage.audit(root)
        self.assertEqual(before, {str(p): p.read_bytes() for folder in
                                 (root/coverage.pregame.ROOT, root/coverage.postgame.ROOT)
                                 for p in folder.glob('*/manifest.json')})
        self.assertIs(report['prediction_accuracy_computed'], False)
        self.assertIs(report['NO_BET'], True)


if __name__ == '__main__':
    unittest.main()
