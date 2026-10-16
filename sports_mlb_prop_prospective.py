"""Immutable MLB 1+ hit/HR conditional shadow records and separate official settlement.

NO BET: conditional estimates require at least one recorded at-bat. Official
lineup confirmation, sportsbook settlement/voids, vig, odds, pitcher-matchup
effects and real wagering are not included. Each frozen record is content-sealed,
written with exclusive create and never edited at settlement.
"""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from sports_mlb_sources import OfficialMlbReader, positive_id, utc, _roster_people
from sports_mlb_hit_prop_shadow import (
    MODEL_NAME, conditional_shadow_forecast, retrieve_game_logs
)

EASTERN=ZoneInfo("America/New_York")
SPORTS_VERSION="mlb_hit_prop_shadow_ledger_v1"


class MissingOfficialBattingFieldError(ValueError):
    """An absent official final batting count cannot be inferred as zero.

    The final feed may omit atBats, hits or homeRuns for a player who has no
    batting line. A missing field is neither a scored prop loss nor proof of
    zero at-bats. Keep the immutable player-game open for a future retry.
    """

    def __init__(self, field):
        self.field=field
        super().__init__("Official MLB final hitter "+field+
                         " unavailable; do not infer zero.")



def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False, ensure_ascii=False).encode("utf-8")


def _digest(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def _seal(core):
    if any(x in core for x in ("record_digest_sha256", "settlement")):
        raise ValueError("Reserved immutable record field.")
    return dict(core, record_digest_sha256=_digest(core))


def _verify(record):
    if not isinstance(record, dict):
        raise ValueError("Forecast record is not JSON object.")
    signature=record.get("record_digest_sha256")
    if not isinstance(signature, str) or len(signature)!=64:
        raise ValueError("Frozen prediction digest missing.")
    core={k:v for k,v in record.items() if k!="record_digest_sha256"}
    if not hmac.compare_digest(signature,_digest(core)):
        raise ValueError("Frozen forecast content digest mismatch.")
    return core


def _positive_stats(row):
    def valid(key):
        if key not in row or row[key] is None:
            raise MissingOfficialBattingFieldError(key)
        value=row[key]
        if isinstance(value,bool) or not isinstance(value,int) or value<0:
            raise ValueError("Official MLB final hitter "+key+" is missing or invalid.")
        return value
    ab,hits,hr=valid("atBats"),valid("hits"),valid("homeRuns")
    if not 0<=hr<=hits<=ab:
        raise ValueError("Official final batter statistics are inconsistent.")
    return ab,hits,hr


def freeze_pregame_hit_props(game_id, hitter_id, hitter_side, *, reader=None):
    """Return canonical seal of pregame experimental conditional estimates.

    The game/roster identities and all source fetches must predate first pitch.
    One cannot freeze a record without >=30 eligible historical games.
    """
    game_id=positive_id(game_id,"game_id")
    hitter_id=positive_id(hitter_id,"hitter_id")
    if hitter_side not in ("home","away"):
        raise ValueError("hitter_side must be official home or away.")
    reader=reader or OfficialMlbReader()
    started=utc(reader.clock())
    game,game_source=reader.load("game/"+str(game_id)+"/feed/live",api_version="v1.1")
    gd=game.get("gameData",{})
    if (game.get("gamePk")!=game_id or
            gd.get("status",{}).get("abstractGameState")!="Preview" or
            gd.get("status",{}).get("detailedState") not in ("Scheduled","Pre-Game")):
        raise ValueError("Official game ID not in pregame state.")
    first_pitch=utc(gd.get("datetime",{}).get("dateTime"))
    if started>=first_pitch:
        raise ValueError("Cannot freeze forecast at or after first pitch.")
    teams=gd.get("teams",{})
    hitter_team=positive_id(teams.get(hitter_side,{}).get("id"),"hitter_team_id")
    other="away" if hitter_side=="home" else "home"
    other_team=positive_id(teams.get(other,{}).get("id"),"opponent_team_id")
    if hitter_team==other_team:
        raise ValueError("Official game has duplicate team identity.")
    roster,roster_source=reader.load("teams/"+str(hitter_team)+"/roster",{
        "rosterType":"active",
        "date":first_pitch.astimezone(EASTERN).date().isoformat()})
    people=_roster_people(roster)
    hitter=people.get(hitter_id)
    if not hitter or hitter["position"]=="P":
        raise ValueError("Selected hitter not verified as active non-pitcher.")
    seasons=[first_pitch.year-1,first_pitch.year]
    before=len(reader.audit)
    rows,_=retrieve_game_logs(hitter_id,seasons,reader=reader)
    historical_sources=list(reader.audit[before:])
    forecast=conditional_shadow_forecast(rows,first_pitch.isoformat())
    if not forecast["model_ready"]:
        raise ValueError("Insufficient official prior at-bat game history; do not create prediction.")
    finalized=utc(reader.clock())
    if finalized>=first_pitch:
        raise ValueError("Source collection crossed scheduled first pitch.")
    # No current-date game is used even if this player appeared in an earlier
    # same-day doubleheader.
    estimates={event: forecast["estimates"][event]["experimental_conditional_probability"]
               for event in ("hit","hr")}
    if any(isinstance(p,bool) or not isinstance(p,(int,float)) or not 0<p<1
           for p in estimates.values()):
        raise ValueError("Conditional estimates must be finite internal probabilities.")
    core={
        "schema":SPORTS_VERSION,
        "model":MODEL_NAME,
        "game_id":game_id, "hitter_id":hitter_id,
        "hitter_name":hitter["name"],"hitter_side":hitter_side,
        "hitter_team_id":hitter_team, "opponent_team_id":other_team,
        "event_start_utc":first_pitch.isoformat(),
        "source_capture_started_at_utc":started.isoformat(),
        "frozen_at_utc":finalized.isoformat(),
        "training_game_day_before":forecast["historical_cutoff_game_day_exclusive"],
        "official_historical_games_observed":forecast["games_observed_before_target"],
        "official_historical_at_bat_eligible_games":forecast["at_bat_eligible_history"],
        "historical_input_sha256":forecast["historical_input_sha256"],
        "conditional_at_bat_probabilities":estimates,
        "condition":"at_least_one_official_at_bat",
        "source_receipts":{"pregame_game":game_source,"active_roster":roster_source,
                           "hitter_game_logs":historical_sources},
        "model_calibrated":False,
        "sportsbook_wager_eligible":False,
        "actual_wager":0,
        "status":"IMMUTABLE_PREGAME_SHADOW_NO_BET",
    }
    return _seal(core)


def settle_frozen_hit_props(record, *, reader=None):
    """Produce a *new* separately sealed settlement without editing prediction."""
    core=_verify(record)
    if (core.get("schema")!=SPORTS_VERSION or core.get("model")!=MODEL_NAME or
            core.get("status")!="IMMUTABLE_PREGAME_SHADOW_NO_BET" or
            core.get("sportsbook_wager_eligible") is not False or
            core.get("model_calibrated") is not False or
            core.get("actual_wager")!=0):
        raise ValueError("Not a recognized untouched no-bet shadow prediction.")
    begin=utc(core.get("frozen_at_utc"))
    event=utc(core.get("event_start_utc"))
    if begin>=event or utc(core.get("source_capture_started_at_utc"))>begin:
        raise ValueError("Shadow prediction was not validly frozen before first pitch.")
    reader=reader or OfficialMlbReader()
    if utc(reader.clock())<=event:
        raise ValueError("Cannot settle before the scheduled first pitch.")
    pk=positive_id(core.get("game_id"),"game_id")
    data,source=reader.load("game/"+str(pk)+"/feed/live",api_version="v1.1")
    gd=data.get("gameData",{})
    status=gd.get("status",{})
    if (data.get("gamePk")!=pk or status.get("abstractGameState")!="Final" or
            status.get("detailedState")!="Final" or
            utc(gd.get("datetime",{}).get("dateTime"))!=event):
        raise ValueError("Official final MLB game state/time/identity not verified.")
    side=core.get("hitter_side")
    other="away" if side=="home" else "home"
    if (gd.get("teams",{}).get(side,{}).get("id")!=core.get("hitter_team_id") or
            gd.get("teams",{}).get(other,{}).get("id")!=core.get("opponent_team_id")):
        raise ValueError("Settled teams do not match frozen event.")
    box=data.get("liveData",{}).get("boxscore",{}).get("teams",{}).get(side,{})
    players=box.get("players")
    if not isinstance(players,dict):
        raise ValueError("Official final boxscore players missing.")
    pid=positive_id(core.get("hitter_id"),"hitter_id")
    raw=players.get("ID"+str(pid))
    if raw is None:
        result="INELIGIBLE_NOT_IN_FINAL_BOXSCORE"
        batting=None
    else:
        if not isinstance(raw,dict) or raw.get("person",{}).get("id")!=pid:
            raise ValueError("Official final batter identity changed.")
        stats=raw.get("stats",{}).get("batting")
        if stats is None:
            raise MissingOfficialBattingFieldError("batting")
        if not isinstance(stats,dict):
            raise ValueError("Official final batter statistical entry invalid.")
        ab,hits,hr=_positive_stats(stats)
        batting={"at_bats":ab,"hits":hits,"home_runs":hr}
        result="SETTLED_CONDITIONAL" if ab>=1 else "INELIGIBLE_ZERO_AB"
    evaluations=None
    if result=="SETTLED_CONDITIONAL":
        estimates=core.get("conditional_at_bat_probabilities")
        if not isinstance(estimates,dict) or set(estimates)!= {"hit","hr"}:
            raise ValueError("Frozen binary event estimates missing.")
        evaluations={}
        for key,actual in (("hit",int(batting["hits"]>=1)),
                           ("hr",int(batting["home_runs"]>=1))):
            p=estimates[key]
            if isinstance(p,bool) or not isinstance(p,(int,float)) or not 0<p<1:
                raise ValueError("Frozen event estimate invalid.")
            evaluations[key]={"observed_binary_event":actual,
                              "frozen_probability":p,
                              "brier_error":round((p-actual)**2,8)}
    settlement={
        "schema":"mlb_hit_prop_shadow_settlement_v1",
        "prediction_digest_sha256":record["record_digest_sha256"],
        "game_id":pk,"hitter_id":pid,
        "official_final_source":source,
        "settled_at_utc":utc(reader.clock()).isoformat(),
        "status":result,"final_official_batting_stats":batting,
        "conditional_binary_scoring":evaluations,
        "sportsbook_settlement":None,
        "actual_wager":0,
    }
    return _seal(settlement)


def write_exclusive_json(path, record):
    """Exclusive create: immutable evidence must never be overwritten."""
    _verify(record)
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8") as handle:
        json.dump(record,handle,sort_keys=True,indent=2,allow_nan=False)
        handle.write("\n")
    return str(p)


def main():
    p=argparse.ArgumentParser(description="MLB immutable no-bet shadow trial")
    sub=p.add_subparsers(dest="action",required=True)
    capture=sub.add_parser("capture")
    capture.add_argument("--game-id",type=int,required=True)
    capture.add_argument("--hitter-id",type=int,required=True)
    capture.add_argument("--hitter-side",choices=("home","away"),required=True)
    capture.add_argument("--output",required=True)
    finish=sub.add_parser("settle")
    finish.add_argument("--prediction",required=True)
    finish.add_argument("--output",required=True)
    args=p.parse_args()
    if args.action=="capture":
        obj=freeze_pregame_hit_props(args.game_id,args.hitter_id,args.hitter_side)
    else:
        obj=settle_frozen_hit_props(json.loads(Path(args.prediction).read_text(encoding="utf-8")))
    write_exclusive_json(args.output,obj)
    print(json.dumps({
        "action":args.action,"file":args.output,
        "record_digest_sha256":obj["record_digest_sha256"],
        "status":obj["status"],"no_wagers":True
    },sort_keys=True))


if __name__=="__main__":
    main()
