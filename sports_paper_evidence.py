"""Sourced facts and bounded explanations for new, separate paper cohorts."""
import json
import math
import re
from types import SimpleNamespace
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from sports_betting import digest, implied_probability, timestamp
from sports_nhl_paper import NhlPublicFeed, NhlPaperTrial, validate_nhl
from sports_paper_trial import PaperTrial, validate_forecast

EASTERN = ZoneInfo("America/New_York")
GOALIE_URL = "https://puckbank.com/starting-goalies"


def goalie_games(html):
    """Read published Next.js page data, without executing publisher scripts."""
    matches = []
    for m in re.finditer(r'self\.__next_f\.push\((.*?)\)</script>', html, re.S):
        try:
            chunk = json.loads(m.group(1))[1]
            node = json.loads(chunk.split(":", 1)[1])
            data = node[3]["initialData"]
            if isinstance(data.get("games"), list):
                matches.append(data["games"])
        except (ValueError, TypeError, IndexError, KeyError, AttributeError):
            continue
    if len(matches) != 1:
        raise ValueError("Starter publisher data was missing or ambiguous.")
    return matches[0]


def starter_reports(game, rows, retrieved_at):
    date = timestamp(game["event_start"]).astimezone(EASTERN)
    matches = [r for r in rows if r.get("date") == date.date().isoformat()
        and r.get("time") == date.strftime("%H:%M")
        and all(r.get(s + "TeamName") == game["teams"][s]["name"] for s in ("home", "away"))]
    if len(matches) != 1:
        raise ValueError("Starter reports did not uniquely match this game, date and time.")
    row = matches[0]; reports = {}
    for side in ("home", "away"):
        name, strength = row.get(side + "GoalieName"), row.get(side + "NewsStrengthName")
        text, published = row.get(side + "NewsDetails"), row.get(side + "NewsCreatedAt")
        source = row.get(side + "NewsSourceUrl")
        verified = False
        try:
            pub, now = timestamp(published), timestamp(retrieved_at)
            # Same-day, opponent-specific report; reject recycled confirmations.
            opponent = game["teams"]["away" if side == "home" else "home"]["short_name"]
            verified = (strength == "Confirmed" and isinstance(name, str) and isinstance(text, str)
                and name.split()[-1].casefold() in text.casefold() and opponent.casefold() in text.casefold()
                and re.search(r"\bwill start\b", text, re.I) is not None
                and pub.astimezone(EASTERN).date() == date.date() and pub <= now
                and (now - pub).total_seconds() <= 24 * 3600
                and urlparse(source).scheme == "https" and urlparse(source).hostname in {"x.com", "twitter.com", "www.nhl.com"})
        except (ValueError, TypeError, AttributeError):
            pass
        reports[side] = {"name": name, "status": "reported_confirmed" if verified else "unconfirmed",
            "publisher_label": strength, "report_text": text if verified else None,
            "report_published_at": published, "report_source_name": row.get(side + "NewsSourceName"),
            "report_source_url": source, "retrieved_at": retrieved_at, "publisher_url": GOALIE_URL,
            "primary_report_independently_retrieved": False,
            "limitation": "Confirmation is relayed by PuckBank; primary social report not independently retrieved. Other aggregators are not independent corroboration."}
    return reports


class EvidenceNhlFeed(NhlPublicFeed):
    def pregame(self, identifier):
        game = super().pregame(identifier)
        game["starting_goalie_reports"] = {"home": None, "away": None}
        try:
            html, ev = self._fetch(GOALIE_URL, text=True)
            if len(html) > 1500000:
                raise ValueError("Starter publisher exceeded the read budget.")
            game["starting_goalie_reports"] = starter_reports(game, goalie_games(html), ev["retrieved_at"])
            game["evidence"]["starting_goalie_reports"] = ev
        except (RuntimeError, ValueError):
            game["limitations"].append("Dated starter reports unavailable or unmatched; starting goalies remain unknown.")
        # Preserve the stronger independently-confirmed field as null.
        return game


def market_probabilities(game):
    prices = (game.get("moneyline_quote") or {}).get("prices")
    if not prices:
        return None
    p = {s: implied_probability(prices[s]) for s in ("home", "away")}
    total = sum(p.values())
    return {s: v / total for s, v in p.items()}


def evidence_facts(game):
    facts = []
    def add(identifier, text, source):
        if source in game["evidence"]:
            facts.append({"id": identifier, "text": text, "source_key": source,
                "source_url": game["evidence"][source]["source_url"],
                "retrieved_at": game["evidence"][source]["retrieved_at"]})
    if game.get("neutral_site") is not None:
        add("venue", "Publisher designates this as a " + ("neutral-site game." if game["neutral_site"] else "non-neutral-site game."), "event_market_injuries")
    market = market_probabilities(game)
    if market:
        add("market", f"Observed two-way prices imply home {market['home']:.1%} and away {market['away']:.1%} after proportional margin removal; quote age is unknown.", "event_market_injuries")
    for side, team in game["teams"].items():
        records = team.get("record") or []
        if len(records) == 1 and isinstance(records[0], str) and re.fullmatch(r"[0-9]+-[0-9]+(?:-[0-9]+)?", records[0]):
            add(side + "_record", f"{team['name']} publisher season record is {records[0]}; this is not a measured recent-form advantage.", "event_market_injuries")
        goalie = (game.get("starting_goalie_reports") or {}).get(side)
        if goalie and goalie["status"] == "reported_confirmed":
            add(side + "_starter", f"PuckBank relays a same-day, opponent-specific report that {goalie['name']} will start for {team['name']}; primary report not independently retrieved.", "starting_goalie_reports")
        comparison = game.get("official_goalie_comparison") or {}
        totals = comparison.get(side + "Team", {}).get("teamTotals") or {}
        gp, gaa, save = totals.get("gamesPlayed"), totals.get("gaa"), totals.get("savePctg")
        if isinstance(gp, int) and not isinstance(gp, bool) and gp > 0 and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (gaa, save)) and 0 <= save <= 1 and gaa >= 0:
            add(side + "_goaltending", f"{team['name']} official {comparison.get('contextSeason')} team goaltending totals: {gp} games, {gaa:.2f} goals-against average, {save:.3f} save percentage; small sample, not starter confirmation.", "official_game")
        pitcher = (game.get("probable_pitchers") or {}).get(side)
        if pitcher and isinstance(pitcher.get("fullName"), str):
            add(side + "_pitcher", f"MLB lists {pitcher['fullName']} as probable for {team['name']}; probable does not mean confirmed.", "official_game")
        lineup = (game.get("published_lineups") or {}).get(side)
        if lineup:
            add(side + "_lineup", f"Official MLB feed publishes a nine-hitter batting order for {team['name']}; participation remains subject to change.", "official_game")
        practice = (game.get("official_practice_report") or {}).get(side)
        if isinstance(practice, list):
            out = [r.get("player") for r in practice if r.get("game_status", "").casefold() == "out" and r.get("player")]
            add(side + "_injuries", f"Official practice table lists {len(practice)} players for {team['name']} and {len(out)} with an explicit Out game status; blank statuses do not establish availability.", "official_practice_report")
    return facts


def bounded_forecast(raw, facts, sport):
    if not isinstance(raw, dict) or set(raw) != {"probabilities", "fact_ids"}:
        raise ValueError("Evidence forecast requires only probabilities and fact_ids; free-text claims are rejected.")
    ids = raw["fact_ids"]
    lookup = {f["id"]: f for f in facts}
    if not isinstance(ids, list) or not 1 <= len(ids) <= 3 or any(not isinstance(i, str) or i not in lookup for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("Forecast must cite one to three distinct supplied fact IDs.")
    value = {"probabilities": raw["probabilities"], "rationale": " ".join(lookup[i]["text"] for i in ids),
        "uncertainty": "Experimental, uncalibrated estimate. Missing offense, defense or form statistics cannot support claims. Prices may be stale; rosters may change. NO BET."}
    (validate_forecast if sport == "NFL" else validate_nhl)(value)
    return value


class EvidenceTrialMixin:
    def record_extras(self, game):
        return {**super().record_extras(game), "sport": self.sport,
            "evidence_method": "fact-ids-v1", "supporting_facts": evidence_facts(game),
            "bookmaker_baseline": market_probabilities(game),
            "baseline_method": "proportional two-way implied-price normalization; NFL conditional on no tie",
            "cohort": self.pipeline_version}


class EvidenceNflTrial(EvidenceTrialMixin, PaperTrial):
    sport = "NFL"
    prediction_category = "sports_nfl_evidence_prediction"
    result_category = "sports_nfl_evidence_result"
    quote_category = "sports_nfl_evidence_quote"
    pipeline_version = "nfl-evidence-paper-v2"
    id_prefix = "NEP-"


class EvidenceNhlTrial(EvidenceTrialMixin, NhlPaperTrial):
    sport = "NHL"
    prediction_category = "sports_nhl_evidence_prediction"
    result_category = "sports_nhl_evidence_result"
    quote_category = "sports_nhl_evidence_quote"
    pipeline_version = "nhl-evidence-paper-v2"
    id_prefix = "HEP-"

    def settle(self, identifier):
        record = self._prediction(identifier)
        final = self.feed.final_game(record)
        writer = type(self)(self.ledger, SimpleNamespace(game=lambda _: final), self.forecast_fn, self.model, self.profile_fn)
        return PaperTrial.settle(writer, identifier)
