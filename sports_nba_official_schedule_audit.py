"""Read-only ESPN/NBA-owned schedule reconciliation for Tyler AI's NBA cohort.

Both raw feeds are retained. Only games with unambiguous ESPN-to-NBA team
tricode, time and season identity matches are labeled corroborated. The
NBA-controlled schedule is independent of ESPN, but this does NOT freeze
predictions, authorize grading, or prove profitable wagering.
"""
import gzip
import hashlib
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
import sports_expansion_observer as obs
from sports_expansion_audit import archive_path, bounded_gzip_read, MAX_BLOB_SIZE, audit_capture, strict_json_loads

NBA_URL="https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"
ROOT=obs.ROOT/"nba_official"
ABBR_ALIASES={"NY":"NYK","GS":"GSW","SA":"SAS","NO":"NOP","UTAH":"UTA","PHO":"PHX","WSH":"WAS","BKN":"BKN"}
MAX_BYTES=8_000_000
ALLOWED_KINDS={"002":"regular","004":"playoffs"}


def tricode(value):
    if not isinstance(value,str):
        raise ValueError("Team abbreviation missing")
    value=ABBR_ALIASES.get(value.upper(),value.upper())
    if not re.fullmatch(r"[A-Z]{2,3}",value):
        raise ValueError("Unsupported team abbreviation")
    return value


def official_games(raw):
    """Parse NBA-controlled current season schedule with fixed identity checks."""
    payload=strict_json_loads(raw)
    groups=payload["leagueSchedule"]["gameDates"]
    if not isinstance(groups,list) or len(groups)<50:
        raise ValueError("NBA schedule payload missing expected season calendar")
    games=[]
    seen=set()
    for date_block in groups:
        for item in date_block["games"]:
            identifier=str(item["gameId"])
            if not re.fullmatch(r"[0-9]{10}",identifier):
                raise ValueError("Invalid NBA official game ID")
            if identifier in seen:
                raise ValueError("Duplicate official NBA game ID")
            seen.add(identifier)
            kind=ALLOWED_KINDS.get(identifier[:3])
            if kind is None:
                continue # preseason, G-League, NBA Cup exhibition or unknown
            home=item["homeTeam"];away=item["awayTeam"]
            h=tricode(home["teamTricode"]);a=tricode(away["teamTricode"])
            if h==a:
                raise ValueError("NBA home/away team collision")
            tip=obs.utc(item["gameDateTimeUTC"])
            stage=item["gameStatus"]
            if type(stage) is not int or stage not in (1,2,3):
                raise ValueError("Unknown official NBA game status")
            score={}
            if stage==3:
                for side,team in (("home",home),("away",away)):
                    value=team["score"]
                    if type(value) is int and value>=0:
                        score[side]=value
                    elif isinstance(value,str) and value.isascii() and value.isdecimal():
                        score[side]=int(value)
                    else:
                        raise ValueError("Malformed NBA official final score")
                if score["home"]==score["away"]:
                    raise ValueError("NBA official final is tied")
            games.append({
                "nba_game_id":identifier,
                "kind":kind,
                "home_tricode":h,"away_tricode":a,
                "tipoff_utc":tip.isoformat(),
                "nba_status":stage,
                "nba_home_score":score.get("home"),
                "nba_away_score":score.get("away"),
                "nba_postponed_status":item.get("postponedStatus"),
                "nba_original_game_code":item.get("gameCode"),
            })
    if len(games)<100:
        raise ValueError("NBA current season official schedule is unexpectedly incomplete")
    return games


def espn_games(manifest, capture_folder):
    """Reparse signed ESPN NBA source bytes rather than using unlinked names."""
    rows={}
    conflicted={item["game_id"] for item in manifest["quarantined_provider_games"]
                if item["league"]=="NBA"}
    eligible={row["game_id"]:row for row in manifest["undisputed_provider_games"]
              if row["league"]=="NBA"}
    for snap in manifest["snapshots"]:
        if snap["league"]!="NBA":
            continue
        day = snap.get('day')
        if not isinstance(day, str) or not re.fullmatch(r'20\d{2}-\d{2}-\d{2}', day):
            raise ValueError('Invalid NBA provider archive day')
        date.fromisoformat(day)
        if snap.get('compressed_file') != 'NBA_'+day+'.json.gz':
            raise ValueError('Invalid NBA provider archive filename')
        blob = archive_path(capture_folder/snap["compressed_file"])
        if blob.stat().st_size > MAX_BLOB_SIZE:
            raise ValueError('Oversized linked ESPN NBA archive')
        raw=bounded_gzip_read(blob.read_bytes())
        if hashlib.sha256(raw).hexdigest()!=snap["original_response_sha256"]:
            raise ValueError("Archived ESPN NBA response hash disagrees")
        payload=strict_json_loads(raw)
        for event in payload["events"]:
            game_id=str(event["id"])
            if game_id not in eligible or game_id in conflicted:
                continue
            sides={}
            for team in event["competitions"][0]["competitors"]:
                side=team["homeAway"]
                if side in sides:
                    raise ValueError("Duplicate ESPN team side")
                sides[side]=tricode(team["team"]["abbreviation"])
            if set(sides)!={"home","away"} or sides["home"]==sides["away"]:
                raise ValueError("Ambiguous ESPN team abbreviations")
            identity=(sides["home"],sides["away"])
            if game_id in rows and rows[game_id]!=identity:
                raise ValueError("ESPN team abbreviations changed within immutable source")
            rows[game_id]=identity
    if set(rows)!=set(eligible):
        raise ValueError("A retained ESPN NBA game lacks verified raw team abbreviations")
    return {game_id:{**record,
                     "espn_game_id":game_id,
                     "home_tricode":rows[game_id][0],
                     "away_tricode":rows[game_id][1]}
            for game_id,record in eligible.items()}


def compare(official,espn,*,exact_tipoff_identity=False):
    """Select by unique team identity, then validate time; never fuzzy-force."""
    if type(exact_tipoff_identity) is not bool:
        raise ValueError('NBA identity policy must be an explicit boolean')
    # Matching emits row IDs which downstream readers use as mapping keys.
    # Bind the two before any fixture selection so an aliased/reused row ID
    # cannot make a later final lookup consume another game's source fields.
    if any(key != row['espn_game_id'] for key, row in espn.items()):
        raise ValueError('NBA provider game identity differs from lookup key')
    by_teams=defaultdict(list)
    for game in official:
        by_teams[(game["home_tricode"],game["away_tricode"])].append(game)
    matched=[];unverified=[]
    for game in sorted(espn.values(),key=lambda r:r["espn_game_id"]):
        expected=obs.utc(game["scheduled_start_utc"])
        possibilities=[n for n in by_teams[(game["home_tricode"],game["away_tricode"])]
                       if abs((obs.utc(n["tipoff_utc"])-expected).total_seconds())<72*3600]
        close=[n for n in possibilities if abs((obs.utc(n["tipoff_utc"])-expected).total_seconds())<=30*60]
        base={"espn_game_id":game["espn_game_id"],
              "teams":game["away_tricode"]+" at "+game["home_tricode"],
              "espn_saved_tipoff_utc":game["scheduled_start_utc"]}
        # Opt-in historical policy: two distinct repeat fixtures may share a
        # 72-hour window. Require an exact UTC match and no competing fixture
        # within the existing 30-minute tolerance. Never select by score.
        exact=[n for n in close if obs.utc(n['tipoff_utc'])==expected]
        if len(close)==1 and (len(possibilities)==1 or
                             (exact_tipoff_identity and len(exact)==1)):
            chosen=close[0]
            diff=(obs.utc(chosen["tipoff_utc"])-expected).total_seconds()/60
            matched.append({**base,"nba_official_game_id":chosen["nba_game_id"],
                            "nba_tipoff_utc":chosen["tipoff_utc"],
                            "start_offset_minutes":diff,
                            "nba_status":chosen["nba_status"],
                            "espn_provider_completed":game["provider_completed"],
                            "nba_provider_completed":chosen["nba_status"]==3,
                            "source_agreement":"SCHEDULE_AND_TEAM_MATCH_ONLY",
                            "official_final_scoring_enabled":False})
        else:
            reason=("AMBIGUOUS_NBA_IDENTITY" if len(close)>1 or len(possibilities)>1
                    else "SOURCE_KICKOFF_DISAGREEMENT" if possibilities
                    else "NO_INDEPENDENT_NBA_GAME_FOUND")
            unverified.append({**base,"reason":reason,
                               "candidate_official_game_ids":[n["nba_game_id"] for n in possibilities],
                               "action":"NO_OUTCOME_GRADE_NO_RETROACTIVE_PREDICTION"})
    # The two providers have independent event IDs. A one-to-many match can
    # otherwise count one NBA-owned fixture as two independently corroborated
    # ESPN events even though each row passed the local team/time tolerance.
    # Quarantine every claimant; choosing one by iteration order is unsafe.
    claims=defaultdict(list)
    for row in matched:
        claims[row["nba_official_game_id"]].append(row)
    duplicate_ids={game_id for game_id, rows in claims.items() if len(rows)>1}
    if duplicate_ids:
        matched=[row for row in matched
                 if row["nba_official_game_id"] not in duplicate_ids]
        for game_id in sorted(duplicate_ids):
            for row in claims[game_id]:
                unverified.append({
                    "espn_game_id":row["espn_game_id"],
                    "teams":row["teams"],
                    "espn_saved_tipoff_utc":row["espn_saved_tipoff_utc"],
                    "reason":"NON_UNIQUE_ESPN_TO_NBA_MAPPING",
                    "candidate_official_game_ids":[game_id],
                    "action":"NO_OUTCOME_GRADE_NO_RETROACTIVE_PREDICTION",
                })
        unverified.sort(key=lambda row:row["espn_game_id"])
    return {"espn_observed_games":len(espn),
            "strict_schedule_correlated":len(matched),
            "not_correlated":len(unverified),
            "matched":matched,"unverified":unverified,
            "official_final_scoring_enabled":False,
            "forecasting_enabled":False,"NO_BET":True,"actual_wagers":0}


def run(fetch,*,base=Path("."),now=None,quarantine_future_cup_slots=False):
    base=Path(base);now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("UTC clock required")
    if type(quarantine_future_cup_slots) is not bool:
        raise ValueError('Explicit NBA source-slot policy required')
    stamp=now.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    archive_path(base/ROOT/'captures'/stamp, directory=True, allow_missing=True)
    captures=sorted((base/obs.ROOT/"captures").glob("*/manifest.json"))
    if not captures:
        raise ValueError("No archived NBA ESPN capture available")
    last=archive_path(captures[-1])
    if last.stat().st_size > MAX_BLOB_SIZE:
        raise ValueError('Oversized NBA linked provider manifest')
    manifest, _, _ = audit_capture(last)
    if not any(x["league"]=="NBA" for x in manifest["snapshots"]):
        raise ValueError("Latest expansion capture has no NBA source")
    raw=fetch(NBA_URL)
    if not isinstance(raw,bytes) or len(raw)>MAX_BYTES:
        raise ValueError("Missing or oversized independent NBA schedule response")
    # Also validate raw JSON when the opt-in NBA slot parser owns decoding.
    strict_json_loads(raw)
    if quarantine_future_cup_slots:
        import sports_nba_schedule_slots as slots
        official,quarantined=slots.parse(raw,observed_at=now.isoformat())
    else:
        official=official_games(raw)
    espn=espn_games(manifest,last.parent)
    report=compare(official,espn)
    stamp=now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    dest=base/ROOT/"captures"/stamp
    if dest.exists():
        raise ValueError("Immutable NBA source-capture timestamp collision")
    dest.mkdir(parents=True)
    (dest/"nba_schedule.json.gz").write_bytes(gzip.compress(raw,mtime=0))
    saved={
        "schema":"nba-espn-independent-schedule-corroboration-v1",
        "created_at_utc":now.astimezone(timezone.utc).isoformat(),
        "nba_official_source_url":NBA_URL,
        "nba_raw_sha256":hashlib.sha256(raw).hexdigest(),
        "nba_raw_file":"nba_schedule.json.gz",
        "espn_capture":last.parent.name,
        "espn_manifest_sha256":hashlib.sha256(last.read_bytes()).hexdigest(),
        "report":report,
        "not_an_independently_verified_final_result":True,
        "NO_BET":True,"actual_wagers":0,"promotion_allowed":False,
    }
    if quarantine_future_cup_slots:
        saved.update(schema='nba-espn-independent-schedule-corroboration-v2',
                     nba_quarantine_policy=slots.POLICY,
                     nba_source_season=strict_json_loads(raw)['leagueSchedule']['seasonYear'],
                     quarantined_future_cup_slots=quarantined,
                     nba_known_game_count=len(official),source_scope_complete=False,
                     forecasting_enabled=False,model_training_enabled=False,
                     official_final_scoring_enabled=False)
    (dest/"manifest.json").write_bytes(obs.canonical(saved))
    return saved


def main():
    from sports_nba_historical_owned import fetch_bytes
    report=run(fetch_bytes,quarantine_future_cup_slots=True)
    print(json.dumps({"at":report["created_at_utc"],
                      "matching":report["report"]["strict_schedule_correlated"],
                      "unverified":report["report"]["not_correlated"],
                      "NO_BET":True},sort_keys=True))


if __name__=="__main__":
    main()
