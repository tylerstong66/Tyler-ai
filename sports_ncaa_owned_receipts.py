"""Verify immutable NCAA-owned raw source receipts without authorizing grades."""
import hashlib
import json
from pathlib import Path
import sports_ncaa_official_source as ncaa
from sports_expansion_audit import archive_path, bounded_gzip_read, MAX_BLOB_SIZE, strict_json_loads

def verify(folder):
    folder=archive_path(folder, directory=True)
    path=archive_path(folder/'manifest.json')
    if path.stat().st_size > MAX_BLOB_SIZE:
        raise ValueError('Oversized NCAA source manifest')
    saved=strict_json_loads(path.read_bytes())
    if (saved.get("schema")!="ncaa-owned-2026-source-observations-v1"
            or saved.get("NO_BET") is not True or type(saved.get("actual_wagers")) is not int
            or saved["actual_wagers"] != 0
            or saved.get("official_final_scoring_enabled") is not False
            or saved.get("fbs_source_week_completeness_verified") is not False
            or saved.get("college_to_espn_identity_map_verified") is not False):
        raise ValueError("Invalid NCAA-owned research receipt")
    if 'collection_window' in saved:
        at=ncaa.existing.utc(saved['recorded_at_utc'])
        window=ncaa.collection_window.verify(saved['collection_window'],at)
        expected=ncaa.requested_windows(at.date(),window['days_ahead'],window['days_back'])
        if [(s['league'],s['window'],s['source_url']) for s in saved['snapshots']]!=expected:
            raise ValueError('NCAA lookback does not match declared bounded source requests')
    from collections import defaultdict
    observed=defaultdict(list)
    for snap in saved["snapshots"]:
        league=snap["league"]
        if league not in ncaa.SPORTS:
            raise ValueError("Invalid NCAA source league")
        filename=league+"_"+snap["window"]+".json.gz"
        if snap["source_file"]!=filename or "/" in filename or ".." in filename:
            raise ValueError("Invalid NCAA source archive filename")
        path=archive_path(folder/filename)
        if path.stat().st_size > MAX_BLOB_SIZE:
            raise ValueError('Oversized compressed NCAA source archive')
        raw=bounded_gzip_read(path.read_bytes(),limit=ncaa.MAX_BYTES)
        if hashlib.sha256(raw).hexdigest()!=snap["source_sha256"]:
            raise ValueError("NCAA source digest mismatch")
        games=ncaa.official_scoreboard(raw,league)
        if len(games)!=snap["observed_games"] or sum(x["provider_reported_final"] for x in games)!=snap["observed_finals_not_yet_grading_authorized"]:
            raise ValueError("NCAA source counts differ from original receipt")
        for game in games:
            observed[(league,game["ncaa_game_id"])].append((snap["window"],game))
    unambiguous=[];quarantined=[]
    for (league,identifier),entries in sorted(observed.items()):
        first=entries[0][1]
        if any(row!=first for _,row in entries[1:]):
            quarantined.append({"league":league,"ncaa_game_id":identifier,
                "source_observations":[{"window":window,"game":row} for window,row in entries],
                "reason":"DIFFERING_OFFICIAL_NCAA_SOURCE_WINDOWS_NO_GRADE"})
        else:
            unambiguous.append({"league":league,**first})
    if unambiguous!=saved["unambiguous_ncaa_contests"] or quarantined!=saved["quarantined_ncaa_contests"]:
        raise ValueError("Saved NCAA source reconciliation differs from replay")
    return {"schema":"tyler-ncaa-owned-source-receipt-v1",
            "ncaa_owned_source_sha256_verified":True,
            "reconciled_contests":len(unambiguous),
            "quarantined_contests":len(quarantined),
            "independent_official_final_verified":False,
            "identity_crosswalk_verified":False,
            "source_scope_complete":False,
            "eligible_for_historical_evaluation":False,
            "forecasting_enabled":False,"NO_BET":True,"actual_wagers":0}
