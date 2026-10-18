"""Dual-source final research never grants prediction or grading privileges."""
import unittest
from datetime import datetime,timezone
from test_sports_ncaa_espn_identity import KICKOFF,KICKOFF_EPOCH
import sports_college_dual_source_finals as finals

def rows(nfinal=True,efinal=True,nscore=28,escore=28):
    nc={"league":"NCAAF_FBS","ncaa_game_id":"654321",
        "home_name":"Tulsa","away_name":"Rice",
        "source_start_time_epoch":str(KICKOFF_EPOCH),
        "provider_reported_final":nfinal,
        "ncaa_home_score":nscore if nfinal else None,
        "ncaa_away_score":21 if nfinal else None}
    es={"league":"NCAAF_FBS","espn_game_id":"401100001",
        "game_id":"401100001","home_name":"Tulsa Golden Hurricane",
        "away_name":"Rice Owls","scheduled_start_utc":KICKOFF,
        "home_score":escore if efinal else None,
        "away_score":21 if efinal else None,
        "provider_completed":efinal,
        "school_names":{"home":"tulsa","away":"rice"}}
    return nc,es

class DualSourceFinalTests(unittest.TestCase):
    def test_equal_final_research_only(self):
        nc,es=rows()
        out=finals.classify([nc],[es])
        self.assertEqual(out["two_source_final_agreements"],1)
        self.assertEqual(out["corroborated_research_only"][0]["home_score"],28)
        self.assertFalse(out["historical_evaluation_enabled"])
        self.assertFalse(out["corroborated_research_only"][0]["independently_certified_official_final"])
        self.assertTrue(out["NO_BET"])

    def test_one_provider_pending_never_corroborated(self):
        nc,es=rows(efinal=False)
        out=finals.classify([nc],[es])
        self.assertEqual(out["two_source_final_agreements"],0)
        self.assertEqual(out["pending"][0]["reason"],"BOTH_SOURCES_NOT_FINAL")

    def test_disagreement_quarantined(self):
        nc,es=rows(escore=31)
        out=finals.classify([nc],[es])
        self.assertEqual(out["two_source_final_agreements"],0)
        self.assertEqual(out["pending"][0]["reason"],"CONFLICTING_FINAL_SCORES_NO_GRADE")

    def test_duplicate_ncaa_game_identity_rejected(self):
        nc,es=rows()
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            finals.classify([nc,nc],[es])

    def test_ambiguous_school_identity_unverified(self):
        nc,es=rows()
        es["school_names"]["home"]="unrelated"
        out=finals.classify([nc],[es])
        self.assertEqual(out["two_source_final_agreements"],0)

if __name__=="__main__":
    unittest.main()
