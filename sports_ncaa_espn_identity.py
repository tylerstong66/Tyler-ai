"""Conservative NCAA-controlled vs ESPN college game identity crosswalk.

Only identical school names AND unique kickoff within 30 minutes are linked.
Both source manifests and all raw ESPN/NCAA SHA receipts are reread; unknown
aliases, reschedules, different scores or duplicates remain unverified.
No scoring, training, frozen prediction, betting or market odds operations.
"""
import gzip
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path

import sports_expansion_observer as espn
from sports_expansion_audit import archive_path, bounded_gzip_read, MAX_BLOB_SIZE
import sports_ncaa_official_source as ncaa

ROOT=espn.ROOT/"college_identity"


def name(value):
    if not isinstance(value,str) or not value.strip():
        raise ValueError("Missing immutable school identity")
    # No fuzzy school aliases, mascot-stripping, edit distance or team IDs
    # borrowed from the other provider. Unmatched schools stay unverified.
    ascii_value=unicodedata.normalize("NFKD",value)
    ascii_value="".join(c for c in ascii_value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+","",ascii_value.lower())

# Human-reviewed exact NCAA `nameShort` spellings observed in the 2026-10-17
# frozen FBS source, with the corresponding ESPN `team.location` university
# names. No edit-distance matching, mascots, scores or result-based lookup.
# Every matched game still needs both sides and a unique kickoff within 30m.
FBS_NCAA_TO_ESPN_SCHOOL={
    "mississippist":"mississippistate",
    "arizonast":"arizonastate",
    "kansasst":"kansasstate",
    "oklahomast":"oklahomastate",
    "charlestonso":"charlestonsouthern",
    "floridast":"floridastate",
    "ohiost":"ohiostate",
    "pennst":"pennstate",
    "michiganst":"michiganstate",
    "oregonst":"oregonstate",
    "washingtonst":"washingtonstate",
    "sandiegost":"sandiegostate",
    "fresnost":"fresnostate",
    "armywestpoint":"army",
    "flaatlantic":"floridaatlantic",
    "southfla":"southflorida",
    "kentst":"kentstate",
    "northdakotast":"northdakotastate",
    "niu":"northernillinois",
    "sanjosest":"sanjosestate",
    "ballst":"ballstate",
    "centralmich":"centralmichigan",
    "westernmich":"westernmichigan",
    "easternmich":"easternmichigan",
    "sacramentost":"sacramentostate",
    "southernmiss":"southernmiss",
    "arkansasst":"arkansasstate",
    "georgiast":"georgiastate",
    "fiu":"floridainternational",
    "middletenn":"middletennessee",
    "missourist":"missouristate",
    "ulm":"ulmonroe",
}


def official_school_name(sport,school):
    """An exact, curated 2026 FBS spelling; no NCAA D1 hoops assumptions."""
    original=name(school)
    return FBS_NCAA_TO_ESPN_SCHOOL.get(original,original) if sport=="NCAAF_FBS" else original



def verify_ncaa(folder, manifest):
    folder=archive_path(folder, directory=True)
    if (manifest.get("schema")!="ncaa-owned-2026-source-observations-v1"
            or manifest.get("official_final_scoring_enabled") is not False
            or manifest.get("forecasting_enabled") is not False
            or manifest.get("NO_BET") is not True):
        raise ValueError("NCAA original source provenance invalid")
    observed=defaultdict(list)
    for snap in manifest["snapshots"]:
        league=snap["league"]
        if league not in ncaa.SPORTS:
            raise ValueError("Unexpected NCAA sport in original archive")
        filename=league+'_'+snap['window']+'.json.gz'
        if snap['source_file'] != filename or '/' in filename or '..' in filename:
            raise ValueError('Invalid NCAA identity archive filename')
        compressed=archive_path(folder/filename)
        if not compressed.is_file() or compressed.stat().st_size>ncaa.MAX_BYTES+1_000_000:
            raise ValueError("Missing NCAA archived source")
        raw=bounded_gzip_read(compressed.read_bytes(),limit=ncaa.MAX_BYTES)
        if hashlib.sha256(raw).hexdigest()!=snap["source_sha256"]:
            raise ValueError("NCAA original archived source SHA mismatch")
        rows=ncaa.official_scoreboard(raw,league)
        if len(rows)!=snap["observed_games"]:
            raise ValueError("NCAA normalized source count differs from original")
        for row in rows:
            observed[(league,row["ncaa_game_id"])].append(row)
    accepted=[]
    conflicted=set()
    for key,rows in sorted(observed.items()):
        if any(row!=rows[0] for row in rows[1:]):
            conflicted.add(key)
        else:
            accepted.append({"league":key[0],**rows[0]})
    saved=manifest["unambiguous_ncaa_contests"]
    if accepted!=saved:
        raise ValueError("Archived NCAA original normalized games differ")
    if { (x["league"],x["ncaa_game_id"]) for x in manifest["quarantined_ncaa_contests"] }!=conflicted:
        raise ValueError("NCAA original quarantine list differs from raw source")
    return accepted


def verify_espn(folder,manifest):
    folder=archive_path(folder, directory=True)
    if (manifest.get("schema")!="tyler-college-nba-provider-observation-v1"
            or manifest.get("source_trust")!="ESPN_ONLY_NOT_INDEPENDENT_OFFICIAL_VERIFICATION"
            or manifest.get("NO_BET") is not True
            or manifest.get("forecasting_enabled") is not False):
        raise ValueError("ESPN original source provenance invalid")
    by_identity=defaultdict(list)
    normalized=[]
    for snap in manifest["snapshots"]:
        sport=snap["league"]
        if sport not in ncaa.SPORTS:
            continue
        filename=sport+'_'+snap['day']+'.json.gz'
        if snap['compressed_file'] != filename or '/' in filename or '..' in filename:
            raise ValueError('Invalid ESPN college identity archive filename')
        path=archive_path(folder/filename)
        if path.stat().st_size > MAX_BLOB_SIZE:
            raise ValueError('Oversized saved ESPN college source file')
        raw=bounded_gzip_read(path.read_bytes())
        if hashlib.sha256(raw).hexdigest()!=snap["original_response_sha256"]:
            raise ValueError("ESPN college source raw digest mismatch")
        payload=json.loads(raw)
        parsed=espn.parse_scoreboard(payload,sport)
        if parsed!=snap["parsed"]:
            raise ValueError("ESPN college parsed source differs from archived receipt")
        normalized.append(snap)
        for event in payload["events"]:
            eid=str(event["id"])
            sides={}
            for team in event["competitions"][0]["competitors"]:
                side=team["homeAway"]
                if side in sides:
                    raise ValueError("Duplicated ESPN home/away side")
                school=team["team"].get("location")
                sides[side]=name(school) if school else None
            if set(sides)!={"home","away"}:
                raise ValueError("Missing ESPN home/away identity")
            by_identity[(sport,eid)].append(sides)
    unique,conflicts=espn.reconcile_for_manifest(manifest,normalized)
    valid=[x for x in manifest["undisputed_provider_games"] if x["league"] in ncaa.SPORTS]
    quarantined={(x["league"],x["game_id"]) for x in manifest["quarantined_provider_games"]
                 if x["league"] in ncaa.SPORTS}
    if unique!=valid or {(x["league"],x["game_id"]) for x in conflicts}!=quarantined:
        raise ValueError("ESPN original saved college cohort differs from raw scoreboard")
    output=[]
    for game in valid:
        ident=(game["league"],game["game_id"])
        rows=by_identity[ident]
        if not rows or any(x!=rows[0] for x in rows[1:]):
            raise ValueError("ESPN school identity changed across same-game saved source dates")
        output.append({**game,
                       "school_names":rows[0],
                       "espn_game_id":game["game_id"]})
    return output


def reconcile(source_rows,espn_rows,*,use_curated_fbs_aliases=True):
    # Historical source cohorts must explicitly opt out of the 2026-only
    # curated spelling policy; default preserves all existing receipt bytes.
    resolve = official_school_name if use_curated_fbs_aliases else lambda sport, school: name(school)
    ncaa_keys=defaultdict(list)
    for row in source_rows:
        ncaa_keys[(row["league"],resolve(row["league"],row["home_name"]),
                   resolve(row["league"],row["away_name"]))].append(row)
    matched=[];unverified=[]
    for item in sorted(espn_rows,key=lambda x:(x["league"],x["espn_game_id"])):
        names=item["school_names"]
        base={"league":item["league"],"espn_game_id":item["espn_game_id"],
              "espn_scheduled_start_utc":item["scheduled_start_utc"],
              "espn_home":item["home_name"],"espn_away":item["away_name"]}
        if names["home"] is None or names["away"] is None:
            unverified.append({**base,"reason":"ESPN_SCHOOL_LOCATION_UNAVAILABLE"})
            continue
        candidate=ncaa_keys[(item["league"],names["home"],names["away"])]
        start=espn.utc(item["scheduled_start_utc"])
        nearby=[row for row in candidate
                if row["source_start_time_epoch"] is not None
                and abs((datetime.fromtimestamp(
                    int(row["source_start_time_epoch"]),tz=timezone.utc)-start
                         ).total_seconds())<=72*3600]
        close=[row for row in nearby
               if abs((datetime.fromtimestamp(
                    int(row["source_start_time_epoch"]),tz=timezone.utc)-start
                        ).total_seconds())<=30*60]
        if len(close)!=1 or len(nearby)!=1:
            reason=("MULTIPLE_NCAA_IDENTITIES" if len(nearby)>1 else
                    "NC AA_START_CHANGED" if nearby else
                    "NO_UNAMBIGUOUS_NCAA_GAME_ID").replace("NC AA","NCAA")
            unverified.append({**base,"reason":reason,
                               "observed_ncaa_ids":[g["ncaa_game_id"] for g in nearby]})
            continue
        nc=close[0]
        if item["provider_completed"] and nc["provider_reported_final"]:
            if (item["home_score"]!=nc["ncaa_home_score"]
                    or item["away_score"]!=nc["ncaa_away_score"]):
                unverified.append({**base,"reason":"CONFLICTING_FINAL_SCORES_NO_GRADE",
                                   "ncaa_game_id":nc["ncaa_game_id"]})
                continue
        at=datetime.fromtimestamp(int(nc["source_start_time_epoch"]),tz=timezone.utc)
        matched.append({**base,
                        "ncaa_game_id":nc["ncaa_game_id"],
                        "ncaa_home_school_as_recorded":nc["home_name"],
                        "ncaa_away_school_as_recorded":nc["away_name"],
                        "curated_fbs_home_alias":(name(nc["home_name"])!=
                                                  resolve(item["league"],nc["home_name"])),
                        "curated_fbs_away_alias":(name(nc["away_name"])!=
                                                  resolve(item["league"],nc["away_name"])),
                        "ncaa_source_start_utc":at.isoformat(),
                        "start_difference_minutes":(at-start).total_seconds()/60,
                        "espn_provider_completed":item["provider_completed"],
                        "ncaa_provider_reported_final":nc["provider_reported_final"],
                        "identity_status":"EXACT_SCHOOL_AND_SCHEDULE_MATCH_ONLY",
                        "independent_result_grading_enabled":False})
    return {
        "espn_games_examined":len(espn_rows),
        "unique_source_game_identity_matches":len(matched),
        "unverified_game_identifiers":len(unverified),
        "matched":matched,"unverified":unverified,
        "official_final_scoring_enabled":False,"forecasting_enabled":False,
        "NO_BET":True,"actual_wagers":0,"promotion_allowed":False,
    }


def run(*,base=Path("."),now=None):
    base=Path(base);now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Aware source audit timestamp required")
    espn_files=sorted((base/espn.ROOT/"captures").glob("*/manifest.json"))
    ncaa_files=sorted((base/ncaa.ROOT/"captures").glob("*/manifest.json"))
    if not espn_files or not ncaa_files:
        raise ValueError("Missing NCAA/ESPN independent sources")
    ef=espn_files[-1]; nf=ncaa_files[-1]
    es=json.loads(ef.read_text());ns=json.loads(nf.read_text())
    for src in (es,ns):
        elapsed=now-espn.utc(src["recorded_at_utc"])
        if elapsed<timedelta(seconds=-60) or elapsed>timedelta(hours=12):
            raise ValueError("One independent source stale or future-dated")
    official=verify_ncaa(nf.parent,ns)
    news=verify_espn(ef.parent,es)
    report=reconcile(official,news)
    stamp=now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path=base/ROOT/"captures"/stamp
    if path.exists():
        raise ValueError("Source crosswalk archive collision")
    snapshot={
        "schema":"ncaa-espn-strict-college-game-identity-v1",
        "recorded_at_utc":now.astimezone(timezone.utc).isoformat(),
        "ncaa_capture":nf.parent.name,
        "ncaa_manifest_sha256":hashlib.sha256(nf.read_bytes()).hexdigest(),
        "espn_capture":ef.parent.name,
        "espn_manifest_sha256":hashlib.sha256(ef.read_bytes()).hexdigest(),
        "report":report,"NO_BET":True,"actual_wagers":0,
        "promotion_allowed":False,
    }
    path.mkdir(parents=True)
    (path/"manifest.json").write_bytes(espn.canonical(snapshot))
    return snapshot


def main():
    result=run()
    r=result["report"]
    print(json.dumps({"at":result["recorded_at_utc"],
                      "examined":r["espn_games_examined"],
                      "exact_identity_matches":r["unique_source_game_identity_matches"],
                      "unverified":r["unverified_game_identifiers"],
                      "NO_BET":True}))


if __name__=="__main__":
    main()
