"""Revalidate saved NCAA/ESPN strict identity matches against original archives."""
import hashlib
import json
import re
from pathlib import Path
import sports_expansion_observer as espn
import sports_ncaa_official_source as ncaa
import sports_ncaa_espn_identity as identity
import sports_ncaa_owned_receipts as ncaa_receipts

STAMP=re.compile(r"[0-9]{8}T[0-9]{12}Z\Z")

def verify(root,stamp):
    if not isinstance(stamp,str) or not STAMP.fullmatch(stamp):
        raise ValueError("Invalid college crosswalk capture identifier")
    root=Path(root)
    folder=root/identity.ROOT/"captures"/stamp
    saved=json.loads((folder/"manifest.json").read_bytes())
    if (saved.get("schema")!="ncaa-espn-strict-college-game-identity-v1"
            or saved.get("NO_BET") is not True or saved.get("actual_wagers")!=0
            or saved.get("promotion_allowed") is not False):
        raise ValueError("Invalid college crosswalk receipt")
    sources=[]
    for key,base in (("ncaa",ncaa.ROOT),("espn",espn.ROOT)):
        linked=saved[key+"_capture"]
        if not isinstance(linked,str) or not STAMP.fullmatch(linked):
            raise ValueError("Invalid linked source capture identifier")
        source=root/base/"captures"/linked
        raw=(source/"manifest.json").read_bytes()
        if hashlib.sha256(raw).hexdigest()!=saved[key+"_manifest_sha256"]:
            raise ValueError("Linked source manifest digest mismatch")
        sources.append((source,json.loads(raw)))
    (ncaa_folder,ncaa_manifest),(espn_folder,espn_manifest)=sources
    ncaa_receipts.verify(ncaa_folder)
    official=identity.verify_ncaa(ncaa_folder,ncaa_manifest)
    provider=identity.verify_espn(espn_folder,espn_manifest)
    report=identity.reconcile(official,provider)
    if report!=saved["report"]:
        raise ValueError("Saved college identity crosswalk differs from replay")
    return {"schema":"tyler-ncaa-espn-crosswalk-replay-v1",
            "linked_source_manifests_verified":True,
            "identity_crosswalk_replayed":True,
            "strict_identity_matches":report["unique_source_game_identity_matches"],
            "independent_official_final_verified":False,
            "source_scope_complete":False,
            "eligible_for_historical_evaluation":False,
            "forecasting_enabled":False,"NO_BET":True,"actual_wagers":0}
