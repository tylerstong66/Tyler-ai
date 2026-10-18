"""Research-only eligibility classification for NCAA/NBA source evidence.

Source status is not a prediction or training authorization. Never infer
independent result verification from a successful collection workflow.
"""
LEAGUES = frozenset(("NCAAF_FBS", "NCAAM_D1", "NBA"))

def classify(record):
    if not isinstance(record, dict) or record.get("league") not in LEAGUES:
        raise ValueError("Unsupported historical research cohort")
    if record.get("NO_BET") is not True or record.get("actual_wagers") != 0:
        raise ValueError("No-bet invariant required")
    reasons=[]
    if record.get("source_archive_sha256_verified") is not True:
        reasons.append("SOURCE_ARCHIVE_NOT_VERIFIED")
    if record.get("identity_crosswalk_verified") is not True:
        reasons.append("INDEPENDENT_IDENTITY_NOT_VERIFIED")
    if record.get("independent_official_final_verified") is not True:
        reasons.append("OFFICIAL_FINAL_NOT_VERIFIED")
    if record.get("source_conflict") is not False:
        reasons.append("SOURCE_CONFLICT_OR_UNKNOWN")
    if record.get("chronology_preflight_passed") is not True:
        reasons.append("PREGAME_CHRONOLOGY_NOT_VERIFIED")
    if record.get("source_scope_complete") is not True:
        reasons.append("SCHEDULE_COVERAGE_NOT_CERTIFIED")
    # These flags are caller assertions, not independently replayed receipts.
    # Do not grant historical evaluation eligibility until a trusted reader
    # derives these fields from immutable, hash-verified source manifests.
    reasons.append("TRUSTED_SOURCE_RECEIPT_READER_NOT_IMPLEMENTED")
    return {
        "schema": "tyler-college-nba-research-eligibility-v1",
        "league": record["league"],
        "eligible_for_historical_evaluation": not reasons,
        "exclusion_reasons": reasons,
        "eligible_for_model_training": False,
        "forecasting_enabled": False,
        "promotion_allowed": False,
        "NO_BET": True,
        "actual_wagers": 0,
    }

def classify_batch(rows):
    if not isinstance(rows, list):
        raise ValueError("Expected research evidence list")
    results=[classify(row) for row in rows]
    return {
        "schema": "tyler-college-nba-eligibility-batch-v1",
        "examined": len(results),
        "eligible_for_historical_evaluation": sum(row["eligible_for_historical_evaluation"] for row in results),
        "excluded": sum(not row["eligible_for_historical_evaluation"] for row in results),
        "rows": results,
        "model_training_enabled": False,
        "NO_BET": True,
        "actual_wagers": 0,
    }
