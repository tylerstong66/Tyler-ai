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
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import sports_expansion_observer as obs
from sports_expansion_audit import bounded_gzip_read

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
    payload=json.loads(raw)
    groups=payload["leagueSchedule"]["gameDates"]
    if not isinstance(groups,list) or len(groups)<50:
        raise ValueError("NBA schedule payload missing expected season calendar")
    games=[]
    seen=set()
    for date_block in groups:
        for item in date_block["games"]:
            identifier=str(item["gameId"])
            if not re.fullmatch(r"\d{10}",identifier):
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
                    elif isinstance(value,str) and value.isdigit():
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
        raw=bounded_gzip_read((capture_folder/snap["compressed_file"]).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=snap["original_response_sha256"]:
            raise ValueError("Archived ESPN NBA response hash disagrees")
        payload=json.loads(raw)
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


def compare(official,espn):
    """Select by unique team identity, then validate time; never fuzzy-force."""
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
        if len(close)==1 and len(possibilities)==1:
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
    return {"espn_observed_games":len(espn),
            "strict_schedule_correlated":len(matched),
            "not_correlated":len(unverified),
            "matched":matched,"unverified":unverified,
            "official_final_scoring_enabled":False,
            "forecasting_enabled":False,"NO_BET":True,"actual_wagers":0}


def run(fetch,*,base=Path("."),now=None):
    base=Path(base);now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("UTC clock required")
    captures=sorted((base/obs.ROOT/"captures").glob("*/manifest.json"))
    if not captures:
        raise ValueError("No archived NBA ESPN capture available")
    last=captures[-1]
    manifest=json.loads(last.read_text())
    if not any(x["league"]=="NBA" for x in manifest["snapshots"]):
        raise ValueError("Latest expansion capture has no NBA source")
    raw=fetch(NBA_URL)
    if not isinstance(raw,bytes) or len(raw)>MAX_BYTES:
        raise ValueError("Missing or oversized independent NBA schedule response")
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
    (dest/"manifest.json").write_bytes(obs.canonical(saved))
    return saved


def main():
    def fetch(url):
        r=requests.get(url,timeout=18,headers={
            "User-Agent":"Mozilla/5.0 (compatible; TylerAIResearchReadOnly/1.0)",
            "Accept":"application/json"})
        r.raise_for_status()
        return r.content
    report=run(fetch)
    print(json.dumps({"at":report["created_at_utc"],
                      "matching":report["report"]["strict_schedule_correlated"],
                      "unverified":report["report"]["not_correlated"],
                      "NO_BET":True},sort_keys=True))


if __name__=="__main__":
    main()
