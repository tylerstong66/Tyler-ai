"""Local temporary-Git tests for no-overwrite and publication chronology controls."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from sports_mlb_prop_prospective import _seal
from sports_mlb_prop_publish_guard import inspect_staged_pregame_additions
from sports_mlb_shadow_publication_audit import audit_forecast_publication

REL="benchmarks/mlb_hitter_props_shadow_v1/predictions/849810_683734.json"
GAME="2026-10-16T00:00:00+00:00"
FROZEN="2026-10-15T19:22:00+00:00"
COMMIT="2026-10-15T19:32:00+00:00"


def git(root,*args,commit_time=None):
    env=os.environ.copy()
    if commit_time:
        env.update(GIT_AUTHOR_DATE=commit_time,GIT_COMMITTER_DATE=commit_time)
    return subprocess.check_output(["git",*args],cwd=root,env=env,
                                   stderr=subprocess.PIPE).decode().strip()


def value():
    return _seal({
        "schema":"mlb_hit_prop_shadow_ledger_v1",
        "status":"IMMUTABLE_PREGAME_SHADOW_NO_BET",
        "game_id":849810,"hitter_id":683734,
        "hitter_name":"Synthetic Hitter",
        "frozen_at_utc":FROZEN,"event_start_utc":GAME,
        "model_calibrated":False,"sportsbook_wager_eligible":False,
        "actual_wager":0,
        "conditional_at_bat_probabilities":{"hit":0.60,"hr":0.08},
    })


class GitRepoTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=self.temp.name
        git(self.root,"init","-q")
        git(self.root,"config","user.name","Test Publisher")
        git(self.root,"config","user.email","test-publisher@example.com")
        self.path=Path(self.root)/REL
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def stage(self,obj=None):
        self.path.write_text(json.dumps(obj if obj is not None else value(),indent=2)+"\n")
        git(self.root,"add",REL)

    def commit(self,time=COMMIT):
        git(self.root,"commit","-qm","freeze synthetic pregame record",commit_time=time)

    def test_new_pred_file_passes_guard_and_original_commit_audit(self):
        self.stage()
        check=inspect_staged_pregame_additions(
            repo=self.root,now="2026-10-15T19:35:00Z")
        self.assertEqual(check["publishable_new_immutable_files"],1)
        self.assertEqual(check["records"][0]["game_id"],849810)
        self.commit()
        history=audit_forecast_publication(repo=self.root)
        self.assertEqual(history["status"],"GIT_HISTORY_REVIEW_PASS_NOT_SERVER_ATTESTED")
        self.assertEqual(history["git_metadata_pregame"],1)
        self.assertEqual(history["verified_unchanged_git_blobs"],1)
        self.assertEqual(history["independently_attested_publish_times"],0)
        self.assertFalse(history["prospective_proof_established"])

    def test_modifying_existing_forecast_is_rejected_at_staging(self):
        self.stage()
        self.commit()
        changed=value()
        changed.pop("record_digest_sha256")
        changed["hitter_name"]="Changed after original publication"
        self.stage(_seal(changed))
        with self.assertRaisesRegex(ValueError,"mutation"):
            inspect_staged_pregame_additions(repo=self.root,
                                             now="2026-10-15T19:36:00Z")
        self.commit()
        review=audit_forecast_publication(repo=self.root)
        self.assertEqual(review["status"],"GIT_HISTORY_REVIEW_FOUND_PROBLEMS")
        self.assertIn("MODIFIED_OR_NO_FULL_GIT_HISTORY",review["records"][0]["status"])

    def test_git_commit_second_precision_is_flagged_not_falsely_failed(self):
        special=value()
        special.pop("record_digest_sha256")
        special["frozen_at_utc"]="2026-10-15T19:32:00.500000+00:00"
        self.stage(_seal(special))
        self.commit(time="2026-10-15T19:32:00+00:00")
        history=audit_forecast_publication(repo=self.root)
        self.assertEqual(history["git_metadata_pregame"],1)
        self.assertEqual(history["subsecond_metadata_order_uncertain"],1)
        self.assertEqual(history["records"][0]["status"],
                         "GIT_COMMIT_METADATA_PREGAME_SUBSECOND_ORDER_UNKNOWN")
        self.assertEqual(history["independently_attested_publish_times"],0)

    def test_after_start_original_commit_metadata_is_not_pregame(self):
        self.stage()
        self.commit(time="2026-10-16T00:05:00+00:00")
        review=audit_forecast_publication(repo=self.root)
        self.assertEqual(review["git_metadata_pregame"],0)
        self.assertEqual(review["records"][0]["status"],"GIT_METADATA_NOT_PREGAME")

    def test_refuse_late_publication_even_if_freeze_was_early(self):
        self.stage()
        with self.assertRaisesRegex(ValueError,"Too late"):
            inspect_staged_pregame_additions(repo=self.root,
                now="2026-10-15T23:59:00Z")

    def test_refuse_other_paths_or_staged_deletion(self):
        extra=Path(self.root)/"unrelated.txt"
        extra.write_text("Anything")
        git(self.root,"add","unrelated.txt")
        with self.assertRaisesRegex(ValueError,"outside"):
            inspect_staged_pregame_additions(repo=self.root,
                now="2026-10-15T19:35:00Z")
        git(self.root,"reset","-q")
        self.stage()
        self.commit()
        git(self.root,"rm","-q",REL)
        with self.assertRaisesRegex(ValueError,"mutation"):
            inspect_staged_pregame_additions(repo=self.root,
                now="2026-10-15T19:35:00Z")

    def test_uncommitted_tamper_fails_local_audit(self):
        self.stage()
        self.commit()
        obj=json.loads(self.path.read_text())
        obj["conditional_at_bat_probabilities"]["hit"]=0.98
        self.path.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError,"digest mismatch"):
            audit_forecast_publication(repo=self.root)


if __name__=="__main__":
    unittest.main()
