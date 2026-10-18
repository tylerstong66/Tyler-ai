"""Replay NBA-owned schedule and linked ESPN source receipts; research only."""
import hashlib
import json
from pathlib import Path
import sports_nba_official_schedule_audit as nba
import sports_expansion_observer as espn
from sports_expansion_audit import bounded_gzip_read

def verify(root, stamp):
    if not isinstance(stamp,str) or len(stamp)!=22 or not stamp.endswith("Z") or not stamp[:-1].isdigit():
        raise ValueError("Invalid NBA capture identifier")
    folder=Path(root)/nba.ROOT/"captures"/stamp
    saved=json.loads((folder/"manifest.json").read_bytes())
    if (saved.get("schema")!="nba-espn-independent-schedule-corroboration-v1"
            or saved.get("NO_BET") is not True or saved.get("actual_wagers")!=0
            or saved.get("not_an_independently_verified_final_result") is not True
            or saved.get("nba_raw_file")!="nba_schedule.json.gz"):
        raise ValueError("Invalid NBA schedule receipt")
    raw=bounded_gzip_read((folder/"nba_schedule.json.gz").read_bytes(),limit=nba.MAX_BYTES)
    if hashlib.sha256(raw).hexdigest()!=saved["nba_raw_sha256"]:
        raise ValueError("NBA original schedule digest mismatch")
    official=nba.official_games(raw)
    linked=saved["espn_capture"]
    if not isinstance(linked,str) or len(linked)!=22 or not linked.endswith("Z") or not linked[:-1].isdigit():
        raise ValueError("Invalid linked ESPN capture")
    espn_folder=Path(root)/espn.ROOT/"captures"/linked
    original=(espn_folder/"manifest.json").read_bytes()
    if hashlib.sha256(original).hexdigest()!=saved["espn_manifest_sha256"]:
        raise ValueError("Linked ESPN manifest digest mismatch")
    manifest=json.loads(original)
    if (manifest.get("schema")!="tyler-college-nba-provider-observation-v1"
            or manifest.get("NO_BET") is not True or manifest.get("actual_wagers")!=0):
        raise ValueError("Invalid linked ESPN receipt")
    replay=nba.compare(official,nba.espn_games(manifest,espn_folder))
    if replay!=saved["report"]:
        raise ValueError("Saved independent schedule crosswalk differs from replay")
    return {"schema":"tyler-nba-independent-schedule-receipt-v1",
            "nba_schedule_sha256_verified":True,"espn_manifest_sha256_verified":True,
            "schedule_crosswalk_replayed":True,
            "strict_schedule_correlated":replay["strict_schedule_correlated"],
            "independent_official_final_verified":False,
            "eligible_for_historical_evaluation":False,
            "forecasting_enabled":False,"NO_BET":True,"actual_wagers":0}
