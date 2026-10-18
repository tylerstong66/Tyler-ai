"""Archived finals require real receipt replay and postgame chronology."""
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

import sports_college_final_receipts as receipts
import sports_expansion_observer as espn
import sports_expansion_audit as audit
import sports_ncaa_espn_identity as identity
import sports_ncaa_official_source as ncaa
from test_sports_ncaa_espn_identity import AT, official_game, espn_game


class FinalReceiptTests(unittest.TestCase):
    def seed(self, root, *, at=None, completed=True, conflict=False, score=28, game_id="401100001"):

        at = at or AT + timedelta(hours=8)
        def official(url):
            game = official_game(final=completed)
            if completed:
                game['teams'][0]['score'] = str(score)
            return json.dumps({'data': {'contests': [game]}}).encode()
        ncaa.run(official, base=root, now=at)
        def fetch(url):
            if "football/college-football" in url and "dates=20261017" in url:
                game = espn_game(completed=completed)
                game['id'] = game_id
                if completed:
                    game['competitions'][0]['competitors'][0]['score'] = str(score)
                if conflict:
                    game["competitions"][0]["competitors"][0]["score"] = "31"
                return json.dumps({"count": 1, "events": [game]}).encode()
            return b'{"count":0,"events":[]}'
        espn.capture(fetch, base=root, now=at, days_ahead=0)
        cross = identity.run(base=root, now=at + timedelta(minutes=1))
        return (at + timedelta(minutes=1)).strftime("%Y%m%dT%H%M%S%fZ"), cross

    def test_original_finals_replay_with_hashes_and_no_model_authorization(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); stamp, _ = self.seed(root)
            out = receipts.publish(root, stamp)
            self.assertEqual(out["two_source_final_agreements"], 1)
            row = out["corroborated_research_only"][0]
            self.assertEqual((row["home_score"], row["away_score"]), (28, 21))
            self.assertTrue(row["result_observation_chronology_verified"])
            self.assertFalse(row["pregame_feature_chronology_verified"])
            self.assertEqual(len(out["ncaa_manifest_sha256"]), 64)
            self.assertEqual(receipts.publish(root, stamp), out)
            for key in ("model_training_enabled", "historical_evaluation_enabled",
                        "forecasting_enabled", "promotion_allowed", "source_scope_complete"):
                self.assertIs(out[key], False)
            self.assertIs(out["NO_BET"], True)
            self.assertEqual(out["actual_wagers"], 0)

    def test_final_observed_before_or_at_kickoff_is_quarantined(self):
        for at in (AT, AT + timedelta(hours=3)):
            with self.subTest(at=at), tempfile.TemporaryDirectory() as td:
                stamp, _ = self.seed(Path(td), at=at)
                out = receipts.build(td, stamp)
                self.assertEqual(out["two_source_final_agreements"], 0)
                self.assertEqual(out["pending"][0]["reason"],
                                 "FINAL_OBSERVED_AT_OR_BEFORE_SAVED_START")

    def test_pending_and_disagreement_are_not_labels(self):
        for kwargs, reason in (({"completed": False}, "BOTH_SOURCES_NOT_FINAL"),
                               ({"conflict": True}, "CONFLICTING_FINAL_SCORES_NO_GRADE")):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as td:
                stamp, _ = self.seed(Path(td), **kwargs)
                out = receipts.build(td, stamp)
                self.assertEqual(out["two_source_final_agreements"], 0)
                self.assertEqual(out["pending"][0]["reason"], reason)

    def test_crosswalk_timestamp_cannot_precede_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); stamp, _ = self.seed(root)
            folder = root / identity.ROOT / 'captures' / stamp
            obj = json.loads((folder / 'manifest.json').read_bytes())
            obj['recorded_at_utc'] = AT.isoformat()
            new = AT.strftime('%Y%m%dT%H%M%S%fZ')
            folder.rename(folder.parent / new)
            (folder.parent / new / 'manifest.json').write_bytes(espn.canonical(obj))
            with self.assertRaisesRegex(ValueError, 'after crosswalk'):
                receipts.build(root, new)

    def test_moved_capture_and_raw_mutation_fail_closed(self):
        for mode in ('timestamp', 'raw'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as td:
                root = Path(td); stamp, _ = self.seed(root)
                if mode == 'timestamp':
                    path = root / identity.ROOT / 'captures' / stamp / 'manifest.json'
                    obj = json.loads(path.read_bytes()); obj['recorded_at_utc'] = AT.isoformat()
                    path.write_bytes(espn.canonical(obj))
                else:
                    path = next((root / ncaa.ROOT / 'captures').glob('*/*.gz'))
                    path.write_bytes(b'corrupt')
                with self.assertRaises(ValueError):
                    receipts.build(root, stamp)
                self.assertFalse((root / receipts.ROOT).exists())

    def test_existing_derived_dataset_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); stamp, _ = self.seed(root)
            receipts.publish(root, stamp)
            path = root / receipts.ROOT / 'captures_v2' / stamp / 'manifest.json'
            path.write_bytes(b'altered')
            with self.assertRaisesRegex(ValueError, 'differs from replay'):
                receipts.publish(root, stamp)
            self.assertEqual(path.read_bytes(), b'altered')

    def test_v1_derived_bytes_remain_untouched_by_v2_publication(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); stamp, _ = self.seed(root)
            legacy = root / receipts.ROOT / 'captures' / stamp / 'manifest.json'
            legacy.parent.mkdir(parents=True)
            legacy.write_bytes(b'original v1 bytes')
            out = receipts.publish(root, stamp)
            self.assertEqual(out['schema'], 'tyler-college-archived-final-research-v2')
            self.assertEqual(legacy.read_bytes(), b'original v1 bytes')

    def test_linked_receipt_isolated_from_unrelated_corrupt_capture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); stamp, _ = self.seed(root)
            # This unrelated ESPN capture is not linked by the chosen receipt.
            later = AT + timedelta(hours=10)
            espn.capture(lambda _: b'{"count":0,"events":[]}', base=root,
                         now=later, days_ahead=0)
            folder = root / espn.ROOT / 'captures' / later.strftime('%Y%m%dT%H%M%S%fZ')
            next(folder.glob('*.gz')).write_bytes(b'corrupt')
            out = receipts.build(root, stamp)
            self.assertEqual(out['two_source_final_agreements'], 1)
            with self.assertRaises(ValueError):
                audit.audit(root)

    def test_traversal_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'identifier'):
            receipts.build('.', '../../outside')


if __name__ == '__main__':
    unittest.main()
