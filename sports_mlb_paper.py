"""MLB paper trials matched to official game IDs, including doubleheader times."""
import copy
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from sports_betting import timestamp
from sports_nhl_paper import NhlPaperTrial
from sports_paper_trial import NflPublicFeed, PaperTrial

MLB_API = "https://statsapi.mlb.com/api/"


class MlbPublicFeed(NflPublicFeed):
    league = "MLB"
    endpoint = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/"

    def schedule_today(self):
        return timestamp(self.now_fn()).astimezone(ZoneInfo("America/New_York")).date()

    def official(self, game, official_id=None):
        if official_id is None:
            day = timestamp(game["event_start"]).astimezone(ZoneInfo("America/New_York")).date().isoformat()
            data, ev = self._fetch(MLB_API + "v1/schedule", {"sportId": 1, "date": day})
            matches = [g for d in data.get("dates", []) for g in d.get("games", [])
                if all(g.get("teams", {}).get(s, {}).get("team", {}).get("name") == game["teams"][s]["name"] for s in ("home", "away"))
                and abs((timestamp(g["gameDate"]) - timestamp(game["event_start"])).total_seconds()) <= 60]
            if len(matches) != 1:
                raise ValueError("Official MLB schedule must uniquely match both teams and start time.")
            official_id = str(matches[0]["gamePk"])
            game["evidence"]["official_schedule"] = ev
        if not str(official_id).isdigit() or not 5 <= len(str(official_id)) <= 10:
            raise ValueError("Invalid official MLB game identifier.")
        data, ev = self._fetch(MLB_API + "v1.1/game/" + str(official_id) + "/feed/live")
        gd, live = data["gameData"], data.get("liveData", {})
        if str(data.get("gamePk")) != str(official_id) or any(gd["teams"][s]["name"] != game["teams"][s]["name"] for s in ("home", "away")):
            raise ValueError("Official MLB event/team identities differ from the frozen forecast.")
        if abs((timestamp(gd["datetime"]["dateTime"]) - timestamp(game["event_start"])).total_seconds()) > 60:
            raise ValueError("Official MLB start time differs from publisher event.")
        if gd["game"].get("type") not in {"R", "D", "F", "L", "W"}:
            raise ValueError("Only regular-season and postseason MLB games are supported.")
        status = gd["status"]
        final = status.get("abstractGameState") == "Final" and status.get("codedGameState") == "F" and status.get("detailedState") == "Final"
        pre = status.get("abstractGameState") == "Preview" and status.get("detailedState") in {"Scheduled", "Pre-Game"}
        game.update(official_game_id=str(official_id), sport="MLB", market="two_way_moneyline_including_extra_innings",
                    state="post" if final else "pre" if pre else "in", completed=final,
                    official_game_state=status, probable_pitchers={}, published_lineups={})
        for side in ("home", "away"):
            game["teams"][side]["official_id"] = str(gd["teams"][side]["id"])
            game["teams"][side]["score"] = live.get("linescore", {}).get("teams", {}).get(side, {}).get("runs")
            game["probable_pitchers"][side] = gd.get("probablePitchers", {}).get(side)
            box = live.get("boxscore", {}).get("teams", {}).get(side, {})
            order = box.get("battingOrder", [])
            # A roster is not a lineup. Require exactly nine distinct published hitters.
            players = box.get("players", {})
            game["published_lineups"][side] = [players["ID" + str(p)]["person"]["fullName"] for p in order] if len(order) == 9 and len(set(order)) == 9 and all("ID" + str(p) in players for p in order) else None
        game["evidence"]["official_game"] = ev
        game["limitations"] = ["Official probable pitchers are probable, not confirmed starters.",
            "Published batting orders do not guarantee players will take the field.",
            "Publisher moneyline age and listed-pitcher bookmaker rules are unverified.",
            "Suspended, postponed, cancelled or nonstandard final states stay pending for review.",
            "Experimental probabilities are uncalibrated; NO BET."]
        return game

    def game(self, identifier):
        return self.official(super().game(identifier))

    def pregame(self, identifier):
        game = self.game(identifier)
        if game["state"] != "pre" or timestamp(game["event_start"]) <= timestamp(self.now_fn()):
            raise ValueError("MLB forecasts must be saved before the scheduled start.")
        return game

    def final_game(self, record):
        game = copy.deepcopy(record["snapshot"]); game["evidence"] = {}
        return self.official(game, record["snapshot"]["official_game_id"])


class MlbPaperTrial(NhlPaperTrial):
    prediction_category = "sports_mlb_paper_prediction"
    result_category = "sports_mlb_paper_result"
    quote_category = "sports_mlb_paper_quote"
    pipeline_version = "mlb-evidence-paper-v1"
    id_prefix = "MBP-"
    settlement_policy = "Paper MLB final winner includes extra innings; tied/abnormal finals stay pending. Bookmaker pitcher rules unverified."

    def record_extras(self, game):
        return {"sport": "MLB", "market": game["market"], "profile_role": "identity only; separate experimental MLB prompt"}

    def settle(self, identifier):
        record = self._prediction(identifier)
        final = self.feed.final_game(record)
        writer = type(self)(self.ledger, SimpleNamespace(game=lambda _: final), self.forecast_fn, self.model, self.profile_fn)
        return PaperTrial.settle(writer, identifier)

    def outcome(self, record, game, scores):
        if game["official_game_id"] != record["snapshot"]["official_game_id"] or any(game["teams"][s]["official_id"] != record["snapshot"]["teams"][s]["official_id"] for s in scores):
            raise ValueError("Official MLB result identity does not match the frozen forecast.")
        if scores["home"] == scores["away"]:
            raise ValueError("Tied MLB final remains pending for review.")
        return max(scores, key=scores.get)

    def report(self):
        report = PaperTrial.report(self)
        report.update(sport="MLB", market="two_way_moneyline_including_extra_innings",
            brier_definition="Mean sum of squared home/away errors; range 0 to 2, lower is better; includes extra innings.")
        return report
