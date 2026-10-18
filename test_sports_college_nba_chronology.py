"""Adversarial tests for prospective NCAA/NBA chronology guard."""
import unittest
from sports_college_nba_chronology import verify_pregame_candidate

def candidate():
    return {
        "NO_BET": True, "actual_wagers": 0, "forecasting_enabled": False,
        "independent_official_final_verified": True,
        "identity_crosswalk_verified": True,
        "scheduled_start_utc": "2026-10-20T20:00:00Z",
        "frozen_at_utc": "2026-10-20T19:45:00Z",
        "feature_observed_at_utc": ["2026-10-20T18:00:00Z", "2026-10-20T19:40:00Z"],
        "official_final_observed_at_utc": "2026-10-20T23:00:00Z",
    }

class ChronologyTests(unittest.TestCase):
    def test_valid_research_candidate_stays_no_bet(self):
        out=verify_pregame_candidate(candidate())
        self.assertTrue(out["chronology_preflight_passed"])
        self.assertFalse(out["forecasting_enabled"])
        self.assertFalse(out["promotion_allowed"])

    def test_future_feature_and_post_kickoff_feature_rejected(self):
        for stamp in ("2026-10-20T19:50:00Z","2026-10-20T20:01:00Z"):
            with self.subTest(stamp=stamp):
                c=candidate();c["feature_observed_at_utc"].append(stamp)
                with self.assertRaisesRegex(ValueError,"Feature observed"):
                    verify_pregame_candidate(c)

    def test_late_freeze_and_backdated_final_rejected(self):
        c=candidate();c["frozen_at_utc"]="2026-10-20T20:00:00Z"
        with self.assertRaisesRegex(ValueError,"Freeze"):
            verify_pregame_candidate(c)
        c=candidate();c["official_final_observed_at_utc"]="2026-10-20T19:00:00Z"
        with self.assertRaisesRegex(ValueError,"Official final timestamp"):
            verify_pregame_candidate(c)

    def test_unverified_identity_or_final_fails_closed(self):
        for key in ("identity_crosswalk_verified","independent_official_final_verified"):
            c=candidate();c[key]=False
            with self.assertRaises(ValueError):
                verify_pregame_candidate(c)

    def test_research_only_flags_mandatory(self):
        for key,value in (("NO_BET",False),("actual_wagers",1),("forecasting_enabled",True)):
            c=candidate();c[key]=value
            with self.assertRaises(ValueError):
                verify_pregame_candidate(c)

    def test_empty_or_timezone_free_feature_provenance_rejected(self):
        c=candidate();c["feature_observed_at_utc"]=[]
        with self.assertRaisesRegex(ValueError,"Missing feature"):
            verify_pregame_candidate(c)
        c=candidate();c["feature_observed_at_utc"]=["2026-10-20T19:00:00"]
        with self.assertRaisesRegex(ValueError,"Timezone-free"):
            verify_pregame_candidate(c)

if __name__=="__main__":
    unittest.main()
