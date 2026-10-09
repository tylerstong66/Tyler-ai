"""On-demand NHL two-way paper forecasts; official final scores include OT/SO."""
import json
import re
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

from sports_betting import price_analysis, timestamp
from sports_paper_trial import NflPublicFeed, PaperTrial, validate_forecast

NHL_VERSION = "nhl-paper-v1"
NHL_PREDICTIONS = "sports_nhl_paper_prediction"
NHL_RESULTS = "sports_nhl_paper_result"
NHL_QUOTES = "sports_nhl_paper_quote"
NHL_API = "https://api-web.nhle.com/v1/"


class PreviewArticle(HTMLParser):
    def __init__(self):
        super().__init__()
        self.script = None
        self.articles = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self.script = ""

    def handle_data(self, data):
        if self.script is not None:
            self.script += data

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            try:
                article = json.loads(self.script)
                if isinstance(article, dict) and article.get("@type") == "NewsArticle" and isinstance(article.get("articleBody"), str):
                    self.articles.append(article)
            except ValueError:
                pass
            self.script = None


class NhlPublicFeed(NflPublicFeed):
    league = "NHL"
    endpoint = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/"

    def schedule_today(self):
        return timestamp(self.now_fn()).astimezone(ZoneInfo("America/New_York")).date()

    def official(self, game, official_id=None):
        if official_id is None:
            day = timestamp(game["event_start"]).astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
            schedule, evidence = self._fetch(NHL_API + "schedule/" + day)
            matches = [g for d in schedule.get("gameWeek", []) for g in d.get("games", [])
                if all(g.get(s + "Team", {}).get("abbrev") == game["teams"][s]["abbreviation"] for s in ("home", "away"))
                and abs((timestamp(g["startTimeUTC"]) - timestamp(game["event_start"])).total_seconds()) <= 60]
            if len(matches) != 1:
                raise ValueError("Official NHL schedule did not uniquely match both teams and start time.")
            official_id = str(matches[0]["id"])
            game["evidence"]["official_schedule"] = evidence
        if not re.fullmatch(r"[0-9]{10}", str(official_id)):
            raise ValueError("Invalid official NHL game identifier.")
        data, evidence = self._fetch(NHL_API + "gamecenter/" + str(official_id) + "/landing")
        if str(data.get("id")) != str(official_id) or any(data.get(s + "Team", {}).get("abbrev") != game["teams"][s]["abbreviation"] for s in ("home", "away")):
            raise ValueError("Official NHL game/team identities differ from publisher event.")
        if abs((timestamp(data["startTimeUTC"]) - timestamp(game["event_start"])).total_seconds()) > 60:
            raise ValueError("Official NHL start time differs from publisher event.")
        if data.get("gameType") not in (2, 3) or data.get("tiesInUse") is not False or data.get("gameScheduleState") != "OK":
            raise ValueError("Only scheduled regular-season/playoff NHL games with a decisive winner are supported.")
        game.update(official_game_id=str(official_id), official_game_state=data.get("gameState"),
                    sport="NHL", market="two_way_moneyline_including_overtime_shootout")
        state = data.get("gameState")
        game["state"] = "pre" if state in ("FUT", "PRE") else "post" if state in ("FINAL", "OFF") else "in"
        game["completed"] = state in ("FINAL", "OFF")
        for side in ("home", "away"):
            team = data[side + "Team"]
            game["teams"][side]["official_id"] = str(team["id"])
            game["teams"][side]["score"] = team.get("score")
            game["teams"][side]["official_record"] = team.get("record")
        game["evidence"]["official_game"] = evidence
        game["official_goalie_comparison"] = data.get("matchup", {}).get("goalieComparison")
        game["confirmed_starting_goalies"] = {"home": None, "away": None}
        game["limitations"] = [
            "Publisher moneyline quote update time and executable availability are unverified; close is only a feed field.",
            "Goalie-comparison leaders are season statistics, not confirmed starters; projected lineups do not prove final active rosters.",
            "Small early-season samples and an unfitted language-model estimate do not establish calibrated probabilities or an edge.",
            "Paper scoring includes overtime/shootout; actual bookmaker settlement rules are unverified."]
        return game

    def game(self, identifier):
        return self.official(super().game(identifier))

    def final_game(self, record):
        # Settle by the pinned official ID, even if an ESPN schedule later changes.
        import copy
        game = copy.deepcopy(record["snapshot"])
        game["evidence"] = {}
        return self.official(game, record["snapshot"]["official_game_id"])

    def pregame(self, identifier):
        game = self.game(identifier)
        if game["state"] != "pre" or timestamp(game["event_start"]) <= timestamp(self.now_fn()):
            raise ValueError("NHL forecasts must be saved before the event starts.")
        # ESPN's injury schema is also normalized in the shared reader; optional
        # official preview preserves publisher prose and its projection label.
        date = timestamp(game["event_start"]).astimezone(ZoneInfo("America/New_York"))
        names = "-".join(re.sub(r"[^a-z0-9]+", "-", game["teams"][s]["name"].lower()).strip("-") for s in ("away", "home"))
        suffix = date.strftime("%B").lower() + "-" + str(date.day) + "-" + str(date.year)
        url = "https://www.nhl.com/news/" + names + "-game-preview-" + suffix
        game["official_projected_lineup"] = None
        try:
            html, evidence = self._fetch(url, text=True)
            parser = PreviewArticle(); parser.feed(html)
            if len(parser.articles) != 1:
                raise RuntimeError("Official preview was not parseable.")
            article = parser.articles[0]
            body = article["articleBody"]
            if len(body) > 8000 or any(game["teams"][s]["short_name"].casefold() not in body.casefold() for s in ("home", "away")):
                raise RuntimeError("Preview did not identify both teams within the text budget.")
            game["official_projected_lineup"] = {"headline": article.get("headline"), "text": body,
                "provider_published_at": article.get("datePublished"), "status": "projected, not confirmed"}
            evidence["provider_updated_at"] = article.get("dateModified")
            game["evidence"]["official_projected_lineup"] = evidence
        except RuntimeError:
            game["limitations"].append("Official projected lineup was unavailable; no lineup or starter was assumed.")
        return game


def validate_nhl(value):
    if not isinstance(value, dict) or not isinstance(value.get("probabilities"), dict) or set(value["probabilities"]) != {"home", "away"}:
        raise ValueError("NHL two-way forecast needs exactly home and away probabilities; no tie outcome.")
    validate_forecast({**value, "probabilities": {**value["probabilities"], "tie": 0}})
    return value


class NhlPaperTrial(PaperTrial):
    prediction_category = NHL_PREDICTIONS
    result_category = NHL_RESULTS
    quote_category = NHL_QUOTES
    pipeline_version = NHL_VERSION
    id_prefix = "NHP-"
    settlement_policy = "Paper NHL two-way moneyline: final winner includes overtime/shootout; no tie push. Actual bookmaker rules unverified."
    validate = staticmethod(validate_nhl)

    def price_metrics(self, prices, forecast, side):
        return price_analysis(prices[side], forecast["probabilities"][side], 0, prices["away" if side == "home" else "home"])

    def record_extras(self, game):
        return {"sport": "NHL", "market": game["market"],
                "profile_role": "active-profile identity only; forecasting uses a separate experimental NHL prompt"}

    def outcome(self, record, game, scores):
        if game["official_game_id"] != record["snapshot"]["official_game_id"] or any(game["teams"][s]["official_id"] != record["snapshot"]["teams"][s]["official_id"] for s in scores):
            raise ValueError("Official result identity does not match the frozen NHL forecast.")
        if scores["home"] == scores["away"]:
            raise ValueError("Final NHL two-way result cannot be tied; leave the forecast pending.")
        return max(scores, key=scores.get)

    def settle(self, identifier):
        # The shared result writer validates scores, hashes and duplicate results.
        record = self._prediction(identifier)
        final = self.feed.final_game(record)
        from types import SimpleNamespace
        writer = NhlPaperTrial(self.ledger, SimpleNamespace(game=lambda _: final), self.forecast_fn, self.model, self.profile_fn)
        return PaperTrial.settle(writer, identifier)

    def report(self):
        report = super().report()
        report.update(sport="NHL", market="two_way_moneyline_including_overtime_shootout",
                      brier_definition="Mean sum of squared home/away errors; range 0 to 2, lower is better. Final winner includes OT/SO.")
        return report
