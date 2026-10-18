"""Research-only eligibility exclusion and guard tests."""
import unittest
from sports_college_nba_eligibility import classify, classify_batch

def record():
    return dict(
        league="NCAAF_FBS", NO_BET=True, actual_wagers=0,
        source_archive_sha256_verified=True,
        identity_crosswalk_verified=True,
        independent_official_final_verified=True,
        source_conflict=False,
        chronology_preflight_passed=True,
        source_scope_complete=True,
    )

class EligibilityTests(unittest.TestCase):
    def test_fully_correlated_record_is_evaluation_only(self):
        result=classify(record())
        self.assertTrue(result["eligible_for_historical_evaluation"])
        self.assertFalse(result["eligible_for_model_training"])
        self.assertFalse(result["forecasting_enabled"])
        self.assertFalse(result["promotion_allowed"])

    def test_each_missing_provenance_excludes_record(self):
        for key in (
            "source_archive_sha256_verified", "identity_crosswalk_verified",
            "independent_official_final_verified", "source_conflict",
            "chronology_preflight_passed", "source_scope_complete"
        ):
            with self.subTest(key=key):
                r=record();r.pop(key)
                out=classify(r)
                self.assertFalse(out["eligible_for_historical_evaluation"])
                self.assertTrue(out["exclusion_reasons"])

    def test_source_conflict_excluded(self):
        r=record();r["source_conflict"]=True
        self.assertIn("SOURCE_CONFLICT_OR_UNKNOWN",classify(r)["exclusion_reasons"])

    def test_source_only_current_cohorts_remain_excluded(self):
        for league in ("NCAAF_FBS","NCAAM_D1","NBA"):
            r={"league":league,"NO_BET":True,"actual_wagers":0}
            self.assertFalse(classify(r)["eligible_for_historical_evaluation"])

    def test_invalid_sport_and_betting_guards_raise(self):
        for key,value in (("league","NFL"),("NO_BET",False),("actual_wagers",1)):
            r=record();r[key]=value
            with self.assertRaises(ValueError):
                classify(r)

    def test_batch_counts_do_not_enable_training(self):
        incomplete=record();incomplete["source_scope_complete"]=False
        out=classify_batch([record(),incomplete])
        self.assertEqual((out["examined"],out["eligible_for_historical_evaluation"],out["excluded"]),(2,1,1))
        self.assertFalse(out["model_training_enabled"])

if __name__=="__main__":
    unittest.main()
