"""Classify two-source college finals for research without enabling grading.

This module deliberately never consumes odds, predictions, or betting records.
A matching score is evidence of corroboration, not certification of an
independent official final or eligibility for model evaluation.
"""
from collections import Counter
import sports_ncaa_espn_identity as identity

def classify(ncaa_rows,espn_rows):
    crosswalk=identity.reconcile(ncaa_rows,espn_rows)
    official_by_id={(r["league"],r["ncaa_game_id"]):r for r in ncaa_rows}
    provider_by_id={(r["league"],r["espn_game_id"]):r for r in espn_rows}
    if len(official_by_id)!=len(ncaa_rows) or len(provider_by_id)!=len(espn_rows):
        raise ValueError("Duplicate source game identity")
    identity_uses=Counter((r["league"],r["ncaa_game_id"]) for r in crosswalk["matched"])
    corroborated=[]
    pending=[]
    for matched in crosswalk["matched"]:
        key=(matched["league"],matched["ncaa_game_id"])
        ek=(matched["league"],matched["espn_game_id"])
        nc=official_by_id[key]
        es=provider_by_id[ek]
        base={"league":matched["league"],"ncaa_game_id":matched["ncaa_game_id"],
              "espn_game_id":matched["espn_game_id"],
              "scheduled_start_utc":matched["espn_scheduled_start_utc"]}
        if identity_uses[key] != 1:
            pending.append({**base,"reason":"NON_BIJECTIVE_GAME_IDENTITY"})
            continue
        if not (nc["provider_reported_final"] and es["provider_completed"]):
            pending.append({**base,"reason":"BOTH_SOURCES_NOT_FINAL"})
            continue
        home,away=nc["ncaa_home_score"],nc["ncaa_away_score"]
        if (not isinstance(home,int) or isinstance(home,bool)
                or not isinstance(away,int) or isinstance(away,bool)
                or home<0 or away<0 or home==away
                or es["home_score"]!=home or es["away_score"]!=away):
            raise ValueError("Invalid or contradictory final in matched identity")
        corroborated.append({**base,"home_score":home,"away_score":away,
                             "source_agreement":"NCAA_AND_ESPN_REPORTED_SAME_FINAL",
                             "independently_certified_official_final":False,
                             "eligible_for_historical_evaluation":False})
    pending.extend({"league":r["league"],"espn_game_id":r["espn_game_id"],
                    "reason":r["reason"],
                    **({"ncaa_game_id":r["ncaa_game_id"]} if "ncaa_game_id" in r else {})}
                   for r in crosswalk["unverified"])
    return {"schema":"tyler-college-dual-source-final-research-v1",
            "two_source_final_agreements":len(corroborated),
            "pending_or_quarantined":len(pending),
            "corroborated_research_only":corroborated,
            "pending":pending,
            "independent_official_final_certification_complete":False,
            "historical_evaluation_enabled":False,
            "forecasting_enabled":False,"promotion_allowed":False,
            "NO_BET":True,"actual_wagers":0}
