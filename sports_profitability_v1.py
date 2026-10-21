"""Strict, future-only NHL paper profitability arithmetic; NO wagers or source collection.

All inputs must be original, independently archived evidence from a *new* cohort.
This offline evaluator verifies structure/hashes but cannot attest publisher truth or
GitHub server publication times. It never retrofits the existing shadow ledgers.
"""
import hashlib
import json
import math
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ACTIVATION = "2026-10-23T00:00:00Z"
MODEL_SHA = "3ea760cc52051c9c094ffe33a9a2580256bbf7ab806f580babf7d217c039df3f"
BOOK = "draftkings"
MARKET = "nhl_full_game_moneyline_including_overtime_shootout"
MIN_EV = 0.05
UNIT_STAKE = 1
MIN_INTERVAL_GAMES = 30
MIN_INTERVAL_DATES = 5


def utc(value):
    if not isinstance(value, str):
        raise ValueError("UTC timestamp string required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timezone is required")
    return parsed.astimezone(timezone.utc)


def hash_record(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def verify_record(data):
    if not isinstance(data, dict) or data.get("sha256") != hash_record(
            {key: value for key, value in data.items() if key != "sha256"}):
        raise ValueError("Record hash missing or invalid")
    if data.get("NO_BET") is not True or data.get("actual_wagers") != 0:
        raise ValueError("All records must be NO_BET with zero real wagers")
    return data


def verify_original(source, archive_root):
    if not isinstance(source, dict):
        raise ValueError("Source snapshot required")
    path = source.get("path")
    link = source.get("source_url")
    digest = source.get("sha256")
    if not isinstance(path, str) or not path or not isinstance(link, str) or (
            urlsplit(link).scheme != "https" or not urlsplit(link).netloc):
        raise ValueError("Archived source path and HTTPS URL required")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("Archived source SHA-256 required")
    base = Path(archive_root).resolve()
    resolved = (base / path).resolve()
    if not resolved.is_relative_to(base) or not resolved.is_file():
        raise ValueError("Original source missing or outside archive")
    if hashlib.sha256(resolved.read_bytes()).hexdigest() != digest:
        raise ValueError("Original source bytes do not match archived SHA-256")
    return True


def same_event(a, b):
    for key in ("game_id", "event_id", "home", "away", "kickoff"):
        if a.get(key) != b.get(key):
            raise ValueError("Original event identity/start mismatch")


def decimal_odds(value):
    if isinstance(value, bool) or not isinstance(value, int) or abs(value) < 100:
        raise ValueError("Valid integer American odds required")
    return 1 + (value / 100 if value > 0 else 100 / abs(value))


def implied(value):
    return 1 / decimal_odds(value)


def check_prediction(prediction):
    verify_record(prediction)
    if prediction.get("model_sha256") != MODEL_SHA:
        raise ValueError("Unfrozen or different NHL baseline model")
    p = prediction.get("probabilities")
    if not isinstance(p, dict) or set(p) != {"home", "away"}:
        raise ValueError("Original two-way probabilities required")
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or
           not math.isfinite(x) or x <= 0 or x >= 1 for x in p.values()):
        raise ValueError("Probability must be strictly between zero and one")
    if not math.isclose(sum(p.values()), 1, rel_tol=0, abs_tol=1e-12):
        raise ValueError("Two-way probabilities must sum to one")
    if not (utc(prediction["generated_at"]) <= utc(prediction["recorded_at"])
            < utc(prediction["kickoff"])):
        raise ValueError("Forecast is not prior to original start")
    if not isinstance(prediction.get("entry_quote_sha256"), str):
        raise ValueError("Frozen original price fingerprint missing")


def check_quote(quote, pred, root, phase):
    verify_record(quote)
    same_event(pred, quote)
    verify_original(quote["source_snapshot"], root)
    if (quote.get("book_id") != BOOK or quote.get("market") != MARKET
            or quote.get("line", "missing") is not None
            or quote.get("quote_phase") != phase):
        raise ValueError("Book/period/market/line/phase mismatch")
    if quote.get("available_to_paper") is not True:
        raise ValueError("Sportsbook offering not verified at capture")
    prices = quote.get("prices")
    if not isinstance(prices, dict) or set(prices) != {"home", "away"}:
        raise ValueError("Exact same-book opposing moneyline pair required")
    for price in prices.values():
        decimal_odds(price)
    observed = utc(quote["observed_at"])
    published = utc(quote["provider_updated_at"])
    recorded = utc(quote["recorded_at"])
    started = utc(pred["kickoff"])
    if not (published <= observed <= recorded < started):
        raise ValueError("Quote chronology not genuinely pre-event")
    if quote["source_snapshot"].get("retrieved_at") != quote["observed_at"]:
        raise ValueError("Quote observation must match original source retrieval")
    if (observed - published).total_seconds() > 600 or (
            recorded - observed).total_seconds() > 300:
        raise ValueError("Provider quote age or archive delay exceeds policy")
    if phase == "entry":
        if (quote["sha256"] != pred["entry_quote_sha256"] or
                recorded > utc(pred["generated_at"]) or
                (utc(pred["generated_at"]) - observed).total_seconds() > 300):
            raise ValueError("Original quote not recorded before forecast or too old")
    else:
        if (quote.get("last_pre_start_offering_verified") is not True or
                observed <= utc(pred["recorded_at"]) or
                (started - observed).total_seconds() > 300):
            raise ValueError("No certified last pre-start offering")
    return prices


def check_result(result, pred, root):
    verify_record(result)
    same_event(pred, result)
    if result.get("prediction_sha256") != pred["sha256"]:
        raise ValueError("Result linked to different forecast bytes")
    if result.get("independent_final_verified") is not True:
        return False
    if result.get("outcome") not in ("home", "away"):
        raise ValueError("NHL moneyline requires an official winner")
    if utc(result["verified_at"]) <= utc(pred["kickoff"]):
        raise ValueError("Final verification was not after the game started")
    evidence = result.get("final_sources")
    if not isinstance(evidence, list) or len(evidence) != 2:
        raise ValueError("Two original independent final sources required")
    hosts = set()
    for source in evidence:
        verify_original(source, root)
        hosts.add(urlsplit(source["source_url"]).hostname)
    if len(hosts) != 2:
        raise ValueError("Two genuinely distinct final-source hosts required")
    return True


def interval(rows):
    blocks = defaultdict(list)
    for row in rows:
        blocks[row["day"]].append(row["profit"])
    if len(rows) < MIN_INTERVAL_GAMES or len(blocks) < MIN_INTERVAL_DATES:
        return {"ci95": None, "blocks": len(blocks), "draws": 0,
                "status": "insufficient_independent_dates_or_settlements"}
    rng = random.Random(1729)
    keys = sorted(blocks)
    samples = []
    for _ in range(1000):
        sampled = [profit for _ in keys for profit in blocks[rng.choice(keys)]]
        samples.append(sum(sampled) / len(sampled))
    samples.sort()
    return {"ci95": [samples[24], samples[974]], "blocks": len(blocks),
            "draws": 1000, "status": "descriptive_block_bootstrap_only"}


def evaluate(predictions, entry_quotes, settlements, closing_quotes=(), archive_root="."):
    """Pure readback. NO network, forecast changes, model updates or bets."""
    quote_by_id, final_by_id, close_by_id = {}, {}, {}
    for entries, dest in ((entry_quotes, quote_by_id), (settlements, final_by_id),
                          (closing_quotes, close_by_id)):
        for item in entries:
            verify_record(item)
            game = item["game_id"]
            if game in dest:
                raise ValueError("Duplicate original event evidence")
            dest[game] = item
    rows = []
    graded = []
    selected = 0
    pending = 0
    unpriced = 0
    no_selection = 0
    prior_activation = 0
    clv = []
    seen = set()
    for pred in predictions:
        check_prediction(pred)
        game = pred["game_id"]
        if game in seen:
            raise ValueError("Duplicate original forecast")
        seen.add(game)
        if utc(pred["recorded_at"]) < utc(ACTIVATION):
            prior_activation += 1
            continue
        quote = quote_by_id.get(game)
        if quote is None:
            unpriced += 1
            continue
        prices = check_quote(quote, pred, archive_root, "entry")
        p = pred["probabilities"]
        ev = {side: p[side] * decimal_odds(prices[side]) - 1 for side in p}
        side = max(("home", "away"), key=lambda s: (ev[s], s == "home"))
        is_selected = ev[side] >= MIN_EV
        if is_selected:
            selected += 1
        else:
            no_selection += 1
        result = final_by_id.get(game)
        if result is None or not check_result(result, pred, archive_root):
            if is_selected:
                pending += 1
            continue
        outcome = result["outcome"]
        graded.append({"day": utc(pred["kickoff"]).date().isoformat(),
                       "p_home": p["home"], "home_won": outcome == "home"})
        if not is_selected:
            continue
        profit = decimal_odds(prices[side]) - 1 if outcome == side else -1
        rows.append({"game_id": game, "day": utc(pred["kickoff"]).date().isoformat(),
                     "selection": side, "stake_units": UNIT_STAKE, "profit": profit,
                     "won": outcome == side, "entry_american": prices[side]})
        closing = close_by_id.get(game)
        if closing is not None:
            closed = check_quote(closing, pred, archive_root, "verified_closing")
            if utc(closing["observed_at"]) <= utc(quote["observed_at"]):
                raise ValueError("Closing observation not later than entry")
            clv.append(100 * (implied(closed[side]) - implied(prices[side])))
    n = len(rows)
    bins = []
    for index in range(5):
        subset = [g for g in graded if min(4, int(g["p_home"] * 5)) == index]
        bins.append({"range": [index / 5, (index + 1) / 5], "n": len(subset),
                     "mean_p_home": sum(g["p_home"] for g in subset) / len(subset) if subset else None,
                     "home_win_rate": sum(g["home_won"] for g in subset) / len(subset) if subset else None})
    return {"policy": "future-only-nhl-fixed-unit-v1", "activation_utc": ACTIVATION,
            "forecast_count": len(seen), "excluded_pre_activation": prior_activation,
            "unpriced_or_missing_original_quote": unpriced,
            "qualified_priced_forecasts": selected + no_selection,
            "no_paper_selection": no_selection, "paper_selections": selected,
            "paper_pending": pending, "paper_settled": n,
            "wins": sum(r["won"] for r in rows), "losses": n - sum(r["won"] for r in rows),
            "paper_profit_units": sum(r["profit"] for r in rows),
            "paper_roi": sum(r["profit"] for r in rows) / n if n else None,
            "paper_roi_block_uncertainty": interval(rows),
            "comparable_verified_closing_quotes": len(clv),
            "mean_price_clv_percentage_points": sum(clv) / len(clv) if clv else None,
            "graded_probability_forecasts": len(graded),
            "binary_brier": sum(2 * (g["p_home"] - g["home_won"]) ** 2 for g in graded) / len(graded) if graded else None,
            "binary_log_loss": sum(-math.log(g["p_home"] if g["home_won"] else 1 - g["p_home"]) for g in graded) / len(graded) if graded else None,
            "calibration_bins": bins, "NO_BET": True, "actual_wagers": 0,
            "model_promotion_allowed": False, "profitability_proven": False,
            "limitation": "Synthetic/offline arithmetic only until original source, independent final, sportsbook offering and GitHub-server chronology are separately verified; no retroactive availability, executed wagers or proven betting edge."}
