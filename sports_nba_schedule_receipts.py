import re
"""Replay NBA-owned schedule and linked ESPN source receipts; research only."""
import hashlib
import json
from pathlib import Path
import sports_nba_official_schedule_audit as nba
import sports_expansion_observer as espn
from sports_expansion_audit import bounded_gzip_read,MAX_BLOB_SIZE

def read_official_games(raw,saved):
    if saved.get('schema')=='nba-espn-independent-schedule-corroboration-v2':
        import sports_nba_schedule_slots as slots
        games,quarantined=slots.parse(raw,observed_at=saved['created_at_utc'])
        if (saved.get('nba_quarantine_policy')!=slots.POLICY
                or saved.get('nba_source_season')!=json.loads(raw)['leagueSchedule']['seasonYear']
                or saved.get('nba_known_game_count')!=len(games)
                or quarantined!=saved.get('quarantined_future_cup_slots')):
            raise ValueError('NBA future-slot quarantine differs from original source')
        return games
    if saved.get('schema')!='nba-espn-independent-schedule-corroboration-v1':
        raise ValueError('Unsupported NBA source receipt schema')
    return nba.official_games(raw)

def verify(root, stamp):
    if not isinstance(stamp,str) or not re.fullmatch(r"[0-9]{8}T[0-9]{12}Z",stamp):
        raise ValueError("Invalid NBA capture identifier")
    folder=Path(root)/nba.ROOT/"captures"/stamp
    saved=json.loads((folder/"manifest.json").read_bytes())
    if (saved.get("schema") not in ("nba-espn-independent-schedule-corroboration-v1",
                                    "nba-espn-independent-schedule-corroboration-v2")
            or saved.get("NO_BET") is not True or saved.get("actual_wagers")!=0
            or saved.get("not_an_independently_verified_final_result") is not True
            or saved.get("nba_raw_file")!="nba_schedule.json.gz"):
        raise ValueError("Invalid NBA schedule receipt")
    if saved['schema'].endswith('-v2'):
        at=espn.utc(saved['created_at_utc'])
        if (at.strftime('%Y%m%dT%H%M%S%fZ')!=stamp
                or saved.get('nba_official_source_url')!=nba.NBA_URL
                or type(saved.get('actual_wagers')) is not int
                or any(saved.get(k) is not False for k in ('promotion_allowed','forecasting_enabled',
                       'model_training_enabled','official_final_scoring_enabled'))):
            raise ValueError('NBA v2 source chronology or research guards changed')
        for path in (folder/'manifest.json',folder/'nba_schedule.json.gz'):
            if path.is_symlink() or not path.is_file() or path.stat().st_size>MAX_BLOB_SIZE:
                raise ValueError('NBA v2 source must be bounded regular files')
        if saved.get('source_scope_complete') is not False:
            raise ValueError('NBA v2 source scope is not certified complete')
    raw=bounded_gzip_read((folder/"nba_schedule.json.gz").read_bytes(),limit=nba.MAX_BYTES)
    if hashlib.sha256(raw).hexdigest()!=saved["nba_raw_sha256"]:
        raise ValueError("NBA original schedule digest mismatch")
    official=read_official_games(raw,saved)
    linked=saved["espn_capture"]
    if not isinstance(linked,str) or not re.fullmatch(r"[0-9]{8}T[0-9]{12}Z",linked):
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
    result={"schema":"tyler-nba-independent-schedule-receipt-v1",
            "nba_schedule_sha256_verified":True,"espn_manifest_sha256_verified":True,
            "schedule_crosswalk_replayed":True,
            "strict_schedule_correlated":replay["strict_schedule_correlated"],
            "independent_official_final_verified":False,
            "eligible_for_historical_evaluation":False,
            "forecasting_enabled":False,"NO_BET":True,"actual_wagers":0}
    if saved['schema'].endswith('-v2'):
        result.update(schema='tyler-nba-independent-schedule-receipt-v2',
                      quarantined_future_cup_slots=len(saved['quarantined_future_cup_slots']),
                      source_scope_complete=False)
    return result
