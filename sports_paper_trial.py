"""On-demand NFL paper forecasts with fetched evidence and append-only records.

Publisher feeds are evidence, not guaranteed current bookmaker quotes. No bets,
paid feeds, background polling, skill promotion or calibration claims.
"""
import copy
import json
import math
import re
import uuid
from datetime import datetime, timezone
from html.parser import HTMLParser

import requests

from sports_betting import digest, implied_probability, price_analysis, timestamp

PAPER_PREDICTIONS = "sports_paper_prediction"
PAPER_RESULTS = "sports_paper_result"
PAPER_QUOTES = "sports_paper_quote"
PAPER_VERSION = "nfl-paper-v1"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/"


def event_id(value):
    if not re.fullmatch(r"[0-9]{6,12}", str(value)):
        raise ValueError("Supply an ESPN NFL event identifier from sports paper schedule.")
    return str(value)


class InjuryTables(HTMLParser):
    """Keep empty cells; a blank game status is never an active designation."""
    def __init__(self):
        super().__init__()
        self.title_depth = 0
        self.title = ""
        self.team = ""
        self.row = None
        self.cell = None
        self.tables = {}
        self.headers_ok = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div":
            if self.title_depth:
                self.title_depth += 1
            elif "d3-o-section-sub-title" in attrs.get("class", "").split():
                self.title_depth, self.title = 1, ""
        if tag == "table":
            self.headers_ok = False
        if tag == "tr":
            self.row = []
        if tag in {"td", "th"} and self.row is not None:
            self.cell = ""

    def handle_data(self, value):
        if self.title_depth:
            self.title += value
        if self.cell is not None:
            self.cell += value

    def handle_endtag(self, tag):
        if tag == "div" and self.title_depth:
            self.title_depth -= 1
            if not self.title_depth:
                self.team = " ".join(self.title.split())
        if tag in {"td", "th"} and self.cell is not None:
            self.row.append(" ".join(self.cell.split()))
            self.cell = None
        if tag == "tr" and self.row is not None:
            if self.row == ["Player", "Position", "Injuries", "Practice Status", "Game Status"]:
                self.headers_ok = True
                self.tables.setdefault(self.team, [])
            elif self.headers_ok and len(self.row) == 5:
                self.tables[self.team].append(dict(zip(
                    ["player", "position", "injury", "practice_status", "game_status"], self.row)))
            self.row = None


class NflPublicFeed:
    def __init__(self, get=None, now_fn=None):
        self.get = get or requests.get
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc).isoformat())

    def _fetch(self, url, params=None, text=False):
        try:
            response = self.get(url, params=params, timeout=20, allow_redirects=False)
            if response.status_code != 200:
                raise RuntimeError("Public feed returned HTTP " + str(response.status_code))
            data = response.text if text else response.json()
            return data, {"source_url": url, "parameters": params or {},
                          "retrieved_at": self.now_fn(), "provider_updated_at": None,
                          "response_sha256": digest(data)}
        except (requests.RequestException, ValueError):
            raise RuntimeError("Public feed could not be read; no current data was assumed.") from None

    def schedule(self, date):
        try:
            day = datetime.strptime(str(date), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date must be YYYY-MM-DD.") from None
        if not 0 <= (day - timestamp(self.now_fn()).date()).days <= 7:
            raise ValueError("Paper schedule supports today through seven days ahead.")
        data, evidence = self._fetch(ESPN + "scoreboard", {"dates": day.strftime("%Y%m%d")})
        events = []
        for item in data.get("events", []):
            if item.get("status", {}).get("type", {}).get("state") != "pre":
                continue
            if timestamp(item["date"]) <= timestamp(self.now_fn()):
                continue
            events.append({"event_id": event_id(item["id"]), "event": item["name"],
                           "event_start": item["date"]})
        return {"events": events, "evidence": evidence}

    def game(self, identifier):
        identifier = event_id(identifier)
        data, evidence = self._fetch(ESPN + "summary", {"event": identifier})
        header = data.get("header", {})
        if str(header.get("id")) != identifier:
            raise ValueError("Feed returned a different event.")
        if header.get("league", {}).get("abbreviation") != "NFL":
            raise ValueError("Feed did not identify an NFL event.")
        competitions = header.get("competitions") or []
        if len(competitions) != 1:
            raise ValueError("NFL feed must contain one competition.")
        competition = competitions[0]
        teams = {}
        for item in competition.get("competitors", []):
            side = item.get("homeAway")
            if side in {"home", "away"}:
                team = item["team"]
                teams[side] = {"id": str(item["id"]), "name": team["displayName"],
                               "short_name": team.get("name"), "abbreviation": team.get("abbreviation"),
                               "record": [r.get("summary") for r in item.get("record", []) if r.get("type") == "total"],
                               "score": item.get("score")}
        if set(teams) != {"home", "away"}:
            raise ValueError("NFL feed must identify exactly two opposing teams.")
        quote = None
        for item in data.get("pickcenter", []):
            market = item.get("moneyline", {})
            prices = {}
            for side in ("home", "away"):
                value = market.get(side, {}).get("close", {}).get("odds")
                try:
                    if not re.fullmatch(r"[+-]?[0-9]+", str(value)):
                        raise ValueError("Invalid American odds.")
                    parsed = int(value)
                    implied_probability(parsed)
                    prices[side] = parsed
                except (ValueError, TypeError):
                    break
            if len(prices) == 2:
                quote = {"provider": item.get("provider", {}).get("name", "unspecified"),
                         "prices": prices, "provider_updated_at": None,
                         "retrieved_at": evidence["retrieved_at"],
                         "quote_age_verified": False,
                         "limitation": "ESPN-displayed price; close is a feed field, not a verified closing line or executable quote."}
                break
        injuries = []
        for item in data.get("injuries", []):
            if str(item.get("team", {}).get("id")) in {t["id"] for t in teams.values()}:
                injuries.append({"team": item.get("team", {}).get("displayName"), "players": [
                    {"player": p.get("athlete", {}).get("displayName"), "status": p.get("status"),
                     "provider_updated_at": p.get("date")} for p in item.get("injuries", [])]})
        season, week = header.get("season", {}), header.get("week")
        return {"event_id": identifier, "event": teams["away"]["name"] + " at " + teams["home"]["name"],
                "event_start": competition["date"], "state": competition.get("status", {}).get("type", {}).get("state"),
                "completed": competition.get("status", {}).get("type", {}).get("completed") is True,
                "season": season, "week": week, "teams": teams,
                "neutral_site": competition.get("neutralSite") if isinstance(competition.get("neutralSite"), bool) else None,
                "venue": data.get("gameInfo", {}).get("venue"), "moneyline_quote": quote,
                "publisher_predictor": data.get("predictor"), "reported_injuries": injuries,
                "evidence": {"event_market_injuries": evidence},
                "limitations": ["Public ESPN feed is not a contracted odds feed; quote update time is unavailable.",
                                "Reported injuries do not establish final active rosters or complete injury coverage.",
                                "Independent probability-model calibration and player-usage modeling are unavailable."]}

    def pregame(self, identifier):
        game = self.game(identifier)
        if game["state"] != "pre" or timestamp(game["event_start"]) <= timestamp(self.now_fn()):
            raise ValueError("Paper forecasts must be generated before a scheduled event starts.")
        year, week = game["season"].get("year"), game["week"]
        if isinstance(year, int) and isinstance(week, int) and game["season"].get("type") == 2:
            url = f"https://www.nfl.com/injuries/league/{year}/reg{week}"
            try:
                html, evidence = self._fetch(url, text=True)
                parser = InjuryTables()
                parser.feed(html)
                game["official_practice_report"] = {side: parser.tables.get(t["short_name"]) for side, t in game["teams"].items()}
                game["evidence"]["official_practice_report"] = evidence
            except RuntimeError:
                game["official_practice_report"] = {"home": None, "away": None}
        game["limitations"].append("Official report retrieval time is not its publication time; blank game statuses remain unknown.")
        self._weather(game)
        return game

    def _weather(self, game):
        game["weather"] = None
        venue = game.get("venue") or {}
        address = venue.get("address") or {}
        code = {"England": "GB", "United States": "US", "Germany": "DE", "Mexico": "MX"}.get(address.get("country"))
        city = address.get("city")
        if not city or not code:
            game["limitations"].append("Verified venue coordinates and usable city weather are unavailable.")
            return
        try:
            locations, geo_evidence = self._fetch("https://geocoding-api.open-meteo.com/v1/search",
                                                {"name": city, "count": 5, "countryCode": code, "language": "en"})
            matches = [x for x in locations.get("results", []) if x.get("country_code") == code and str(x.get("name", "")).casefold() == city.casefold()]
            if len(matches) != 1:
                raise RuntimeError("City coordinates are ambiguous.")
            place = matches[0]
            params = {"latitude": place["latitude"], "longitude": place["longitude"], "timezone": "UTC",
                      "hourly": "temperature_2m,precipitation_probability,wind_speed_10m", "forecast_days": 8}
            weather, evidence = self._fetch("https://api.open-meteo.com/v1/forecast", params)
            times = weather.get("hourly", {}).get("time", [])
            hour = timestamp(game["event_start"]).strftime("%Y-%m-%dT%H:00")
            index = times.index(hour)
            game["weather"] = {"forecast_hour_utc": hour + "Z", "city": city,
                               "location_precision": "city proxy, not verified stadium coordinates",
                               "values": {k: v[index] for k, v in weather["hourly"].items() if k != "time"},
                               "units": weather.get("hourly_units", {}), "attribution": "Open-Meteo.com"}
            game["evidence"].update(weather=evidence, weather_location=geo_evidence)
            game["limitations"].append("Weather is a city-proxy forecast, not a stadium observation; roof/indoor status is unverified.")
        except (RuntimeError, ValueError, KeyError, IndexError, TypeError):
            game["limitations"].append("Usable kickoff weather could not be retrieved; no weather assumptions were made.")


def validate_forecast(value):
    if not isinstance(value, dict) or set(value) != {"probabilities", "rationale", "uncertainty"}:
        raise ValueError("Paper forecast must contain probabilities, rationale and uncertainty only.")
    probabilities = value["probabilities"]
    if not isinstance(probabilities, dict) or set(probabilities) != {"home", "away", "tie"}:
        raise ValueError("Forecast must account for home, away and tie outcomes.")
    if any(isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities.values()):
        raise ValueError("Forecast probabilities must be finite numbers between zero and one.")
    if abs(sum(probabilities.values()) - 1) > 1e-6 or probabilities["tie"] == 1:
        raise ValueError("Forecast probabilities must sum to one with a non-tie possibility.")
    if any(not isinstance(value[k], str) or not value[k].strip() for k in ("rationale", "uncertainty")):
        raise ValueError("Paper forecast needs reasoning and uncertainty.")
    if len((value["rationale"] + " " + value["uncertainty"]).split()) > 160:
        raise ValueError("Paper forecast explanation exceeds its word budget.")
    return value


class PaperTrial:
    def __init__(self, ledger, feed, forecast_fn, model, profile_fn):
        self.ledger, self.feed, self.forecast_fn = ledger, feed, forecast_fn
        self.model, self.profile_fn = model, profile_fn

    def analyze(self, identifier):
        identifier = event_id(identifier)
        with self.ledger.lock:
            if any(r["event_id"] == identifier for r in self.records()):
                raise ValueError("An original paper forecast already exists for this event; show latest sports paper prediction. Do not overwrite or retry.")
        profile = copy.deepcopy(self.profile_fn())
        game = self.feed.pregame(identifier)
        # The forecast remains an experimental, uncalibrated hypothesis.
        forecast = validate_forecast(self.forecast_fn(copy.deepcopy(game)))
        with self.ledger.lock:
            if any(r["event_id"] == identifier for r in self.records()):
                raise ValueError("An original paper forecast was saved concurrently; no second forecast recorded.")
            if digest(self.profile_fn()) != digest(profile):
                raise ValueError("Active profile changed while forecasting; forecast was not recorded.")
            now = timestamp(self.ledger.now_fn())
            if now >= timestamp(game["event_start"]):
                raise ValueError("Event started while generating the forecast; it was not recorded.")
            side = max(("home", "away"), key=lambda s: forecast["probabilities"][s])
            prices = (game.get("moneyline_quote") or {}).get("prices")
            metrics = None
            if prices:
                metrics = price_analysis(prices[side], forecast["probabilities"][side], forecast["probabilities"]["tie"], prices["away" if side == "home" else "home"])
            record = {"paper_prediction_id": "PP-" + uuid.uuid4().hex[:16].upper(), "recorded_at": now.isoformat(),
                      "pipeline_version": PAPER_VERSION, "model": self.model,
                      "profile_version": profile.get("version"), "profile_fingerprint": digest(profile),
                      "event_id": game["event_id"], "event": game["event"], "event_start": game["event_start"],
                      "selection_side": side, "selection": game["teams"][side]["name"],
                      "forecast": forecast, "snapshot": game, "hypothetical_price_metrics": metrics,
                      "decision": "NO BET", "trial_status": "PAPER FORECAST SAVED",
                      "probability_method": "experimental_uncalibrated_language_model_forecast",
                      "settlement_policy": "Paper moneyline: tie is a push; actual bookmaker settlement rule unverified.",
                      "closing_line": None, "profitability_proven": False, "wager_executed": False}
            from skill_lab import _contains_secret_literal
            if _contains_secret_literal(json.dumps(record)):
                raise ValueError("Paper records cannot contain credential literals.")
            return self.ledger._append(PAPER_PREDICTIONS, record)

    def records(self):
        return self.ledger._records(PAPER_PREDICTIONS)

    def latest(self):
        records = self.records()
        return max(records, key=lambda r: r["recorded_at"]) if records else {"trial_status": "not_started"}

    def _prediction(self, identifier):
        record = next((r for r in self.records() if r["paper_prediction_id"] == identifier), None)
        if not record:
            raise ValueError("Paper prediction not found in the latest 1000 records.")
        return record

    def capture_quote(self, identifier):
        record = self._prediction(identifier)
        game = self.feed.game(record["event_id"])
        if game["state"] != "pre" or timestamp(self.ledger.now_fn()) >= timestamp(record["event_start"]):
            raise ValueError("Only pre-event quotes can be captured; no retrospective closing quote is inferred.")
        if not game.get("moneyline_quote"):
            raise ValueError("Publisher has no usable moneyline quote; no quote was recorded.")
        return self.ledger._append(PAPER_QUOTES, {"paper_prediction_id": identifier,
            "prediction_sha256": digest(record), "captured_at": self.ledger.now_fn(),
            "quote": game.get("moneyline_quote"), "evidence": game["evidence"],
            "verified_closing_line": False, "limitation": "Observed pre-event price only; publisher quote age unknown."})

    def settle(self, identifier):
        record = self._prediction(identifier)
        game = self.feed.game(record["event_id"])
        if not game["completed"] or game["state"] != "post":
            raise ValueError("Publisher has not confirmed a final result; paper prediction remains pending.")
        if timestamp(self.ledger.now_fn()) < timestamp(record["event_start"]):
            raise ValueError("Cannot settle before the recorded event starts.")
        try:
            if any(isinstance(game["teams"][s]["score"], bool) or not re.fullmatch(r"[0-9]+", str(game["teams"][s]["score"])) for s in ("home", "away")):
                raise ValueError("Invalid score.")
            scores = {s: int(game["teams"][s]["score"]) for s in ("home", "away")}
        except (ValueError, TypeError):
            raise ValueError("Final scores are unavailable.") from None
        if any(s < 0 for s in scores.values()):
            raise ValueError("Invalid final scores.")
        if any(game["teams"][s]["id"] != record["snapshot"]["teams"][s]["id"] for s in scores):
            raise ValueError("Result team identities do not match the original prediction.")
        outcome = "tie" if scores["home"] == scores["away"] else max(scores, key=scores.get)
        prices = (record["snapshot"].get("moneyline_quote") or {}).get("prices")
        profit = None
        if prices:
            from sports_betting import american_to_decimal
            profit = 0 if outcome == "tie" else american_to_decimal(prices[record["selection_side"]]) - 1 if outcome == record["selection_side"] else -1
        with self.ledger.lock:
            if any(r["paper_prediction_id"] == identifier for r in self.ledger._records(PAPER_RESULTS)):
                raise ValueError("Paper result already recorded; originals cannot be rewritten.")
            return self.ledger._append(PAPER_RESULTS, {"paper_prediction_id": identifier,
                "prediction_sha256": digest(record), "settled_at": self.ledger.now_fn(),
                "outcome": outcome, "scores": scores, "evidence": game["evidence"],
                "hypothetical_flat_unit_profit": profit, "verified_closing_line": None,
                "price_clv_percentage_points": None,
                "clv_limitation": "A verified pre-kickoff closing quote was not captured; the feed close field is insufficient."})

    def report(self):
        predictions = {r["paper_prediction_id"]: r for r in self.records()}
        results = self.ledger._records(PAPER_RESULTS)
        brier, profits, bins = [], [], {}
        for result in results:
            record = predictions.get(result["paper_prediction_id"])
            if not record:
                continue
            if result["prediction_sha256"] != digest(record):
                raise RuntimeError("Paper result integrity linkage failed.")
            probabilities = record["forecast"]["probabilities"]
            brier.append(sum((p - (s == result["outcome"])) ** 2 for s, p in probabilities.items()))
            if result["hypothetical_flat_unit_profit"] is not None:
                profits.append(result["hypothetical_flat_unit_profit"])
            p = probabilities[record["selection_side"]]
            bucket = min(int(p * 10), 9)
            bins.setdefault(bucket, []).append((p, result["outcome"] == record["selection_side"]))
        return {"pipeline_version": PAPER_VERSION, "predictions_in_window": len(predictions),
                "observed_pre_event_quotes_in_window": len(self.ledger._records(PAPER_QUOTES)),
                "settled_in_window": len(brier), "pending_in_window": len(predictions) - len(brier),
                "multiclass_brier_score": sum(brier) / len(brier) if brier else None,
                "hypothetical_flat_unit_roi": sum(profits) / len(profits) if profits else None,
                "priced_result_count": len(profits), "verified_closing_line_value": None,
                "calibration_bins": [{"probability_band": f"{b/10:.1f}-{(b+1)/10:.1f}", "count": len(v),
                    "mean_probability": sum(p for p, y in v)/len(v), "observed_win_rate": sum(y for p, y in v)/len(v)} for b, v in sorted(bins.items())],
                "profitability_proven": False, "wager_executed": False,
                "brier_definition": "Mean sum of squared errors across home, away and tie; range 0 to 2, lower is better.",
                "limitation": "One original forecast per event in the read window. Uncalibrated forecasts; observed prices have unverified age. Descriptive metrics, not a proven edge. Read window 1000 per category."}
