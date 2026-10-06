"""Deterministic sports analysis and application-level append-only records.

No sportsbook integration, model training, or independent source verification.
Snapshots are caller supplied; they can support a value candidate, never a
claim that the inputs or probability model were independently validated.
"""
import copy
import hashlib
import json
import math
import threading
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

PREDICTION_CATEGORY = "sports_prediction"
RESULT_CATEGORY = "sports_result"
PROTECTED_CATEGORIES = {PREDICTION_CATEGORY, RESULT_CATEGORY}


def number(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number.")
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a finite number.") from None
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number.")
    return result


def probability(value, name="probability"):
    result = number(value, name)
    if not 0 <= result <= 1:
        raise ValueError(f"{name} must be between 0 and 1, not a percentage.")
    return result


def american_to_decimal(odds):
    odds = number(odds, "American odds")
    if not odds.is_integer() or abs(odds) < 100:
        raise ValueError("American odds must be an integer >= +100 or <= -100.")
    return 1 + (odds / 100 if odds > 0 else 100 / abs(odds))


def implied_probability(odds):
    return 1 / american_to_decimal(odds)


def price_analysis(odds, p_win, p_push=0, opposite_odds=None):
    """Win/push are unconditional; implied probability conditions on no push."""
    p_win, p_push = probability(p_win, "p_win"), probability(p_push, "p_push")
    if p_win + p_push > 1 or p_push == 1:
        raise ValueError("Win and push probabilities must leave a valid non-push market.")
    decimal = american_to_decimal(odds)
    implied = 1 / decimal
    out = {
        "decimal_odds": decimal, "implied_probability": implied,
        "estimated_win_probability": p_win, "estimated_push_probability": p_push,
        "estimated_probability_given_no_push": p_win / (1 - p_push),
        "edge_percentage_points": 100 * (p_win / (1 - p_push) - implied),
        "expected_profit_per_unit": p_win * decimal + p_push - 1,
        "no_vig_market_probability": None,
        "vig_method": "Unavailable: need both prices for the same two-way market.",
    }
    if opposite_odds is not None:
        other = implied_probability(opposite_odds)
        out["no_vig_market_probability"] = implied / (implied + other)
        out["vig_method"] = "Proportional normalization; a market reference, not true probability."
    return out


def timestamp(value, name="timestamp"):
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be an ISO timestamp with timezone.") from None
    if result.tzinfo is None:
        raise ValueError(f"{name} must include a timezone.")
    return result.astimezone(timezone.utc)


def source(value):
    parsed = urlsplit(str(value or ""))
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Sources must be HTTPS URLs without embedded credentials.")
    # Do not persist credential-bearing query strings or fragments.
    if parsed.query or parsed.fragment:
        raise ValueError("Supply a source URL without query strings or fragments.")
    return str(value)


def evaluate_snapshot(snapshot, now=None):
    """Price supplied evidence; never fabricate a live line or fair probability."""
    if not isinstance(snapshot, dict):
        raise ValueError("Snapshot must be a JSON object.")
    now = now or datetime.now(timezone.utc)
    if isinstance(now, str):
        now = timestamp(now)
    for key in ("event", "market", "selection", "event_start", "odds", "p_win",
                "p_low", "p_high", "probability_method", "rationale"):
        if key not in snapshot or snapshot[key] is None or snapshot[key] == "":
            raise ValueError(f"Missing {key}.")
    start = timestamp(snapshot["event_start"], "event_start")
    p_win = probability(snapshot["p_win"], "p_win")
    low, high = probability(snapshot["p_low"], "p_low"), probability(snapshot["p_high"], "p_high")
    push = probability(snapshot.get("p_push", 0), "p_push")
    if not low <= p_win <= high or high + push > 1:
        raise ValueError("Probability interval must contain p_win and respect push probability.")
    result = price_analysis(snapshot["odds"], p_win, push, snapshot.get("opposite_odds"))
    problems = []
    if start <= now:
        problems.append("Event has started; v1 supports pre-event analysis only.")
    # Explicit indoor status avoids silently omitting weather for outdoor games.
    indoor = snapshot.get("indoor")
    if not isinstance(indoor, bool):
        problems.append("Indoor/outdoor venue status is missing.")
    required = {"odds": 30, "availability": 360, "usage": 1440}
    if indoor is not True:
        required["weather"] = 180
    evidence = snapshot.get("evidence") or {}
    if not isinstance(evidence, dict):
        raise ValueError("evidence must be an object keyed by evidence type.")
    for kind, max_minutes in required.items():
        item = evidence.get(kind)
        if not isinstance(item, dict) or not str(item.get("summary") or "").strip():
            problems.append(f"Missing {kind} evidence.")
            continue
        source(item.get("source_url"))
        captured = timestamp(item.get("captured_at"), f"{kind} captured_at")
        age = (now - captured).total_seconds() / 60
        if age < 0 or age > max_minutes:
            problems.append(f"{kind} evidence is future-dated or stale (policy: {max_minutes} minutes).")
    is_parlay = snapshot.get("is_parlay", False)
    if not isinstance(is_parlay, bool):
        raise ValueError("is_parlay must be a boolean.")
    if is_parlay:
        if snapshot.get("joint_probability_method") != "joint_model" or not snapshot.get("correlation_rationale"):
            problems.append("A parlay requires a joint model and explicit correlation rationale.")
    lower_edge = 100 * (low / (1 - push) - result["implied_probability"])
    result["lower_bound_edge_percentage_points"] = lower_edge
    # Policy thresholds are operating choices, not empirical profitability claims.
    if lower_edge < 2 or low * result["decimal_odds"] + push - 1 <= 0:
        problems.append("Uncertainty-adjusted edge is below the 2 percentage-point review threshold.")
    result.update({
        "decision": "NO BET" if problems else "VALUE CANDIDATE",
        "reasons": problems,
        "evaluated_at": now.isoformat(),
        "evidence_origin": "caller_supplied_not_independently_verified",
        "profitability_proven": False,
        "wager_executed": False,
    })
    return result


def digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


class SportsLedger:
    """Append only through this app; DB administrators can still alter rows.

    Uses existing server-side memory callbacks; no database permissions change.
    Reads cover the latest 1000 records of each category. The lock serializes
    writes within this process, not across workers. No global idempotency claim.
    """
    def __init__(self, get_rows, save_row, now_fn=None):
        self.get_rows, self.save_row = get_rows, save_row
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc).isoformat())
        self.lock = threading.RLock()

    def _records(self, category):
        out = []
        for row in self.get_rows(category, 1000) or []:
            data = json.loads(row["memories"])
            payload = data.get("payload")
            if not isinstance(payload, dict) or data.get("sha256") != digest(payload):
                raise RuntimeError("Sports ledger integrity check failed.")
            out.append(payload)
        return out

    def _append(self, category, payload):
        text = json.dumps({"payload": payload, "sha256": digest(payload)}, sort_keys=True, allow_nan=False)
        rows = self.save_row(text, category, 8)
        if not rows or not isinstance(rows[0], dict) or rows[0].get("id") is None:
            raise RuntimeError("Sports record persistence was not confirmed; outcome unknown. Do not blindly retry.")
        return copy.deepcopy(payload)

    def record_prediction(self, snapshot, profile_version, model):
        with self.lock:
            now = timestamp(self.now_fn())
            if timestamp(snapshot.get("event_start"), "event_start") <= now:
                raise ValueError("Predictions must be recorded before the event starts.")
            analysis = evaluate_snapshot(snapshot, now)
            payload = {
                "prediction_id": "SP-" + uuid.uuid4().hex[:16].upper(),
                "recorded_at": now.isoformat(), "snapshot": copy.deepcopy(snapshot),
                "analysis": analysis, "profile_version": profile_version, "model": model,
            }
            # Validate snapshots through the same credential-literal guard as skill cases.
            from skill_lab import _contains_secret_literal
            if _contains_secret_literal(json.dumps(payload)):
                raise ValueError("Sports records cannot contain credential literals.")
            return self._append(PREDICTION_CATEGORY, payload)

    def settle(self, prediction_id, outcome, source_url, closing_odds=None, closing_line=None):
        with self.lock:
            if outcome not in {"win", "loss", "push", "void"}:
                raise ValueError("outcome must be win, loss, push, or void.")
            prediction = next((x for x in self._records(PREDICTION_CATEGORY)
                               if x.get("prediction_id") == prediction_id), None)
            if not prediction:
                raise ValueError("Prediction not found in the latest 1000 records.")
            if any(x.get("prediction_id") == prediction_id for x in self._records(RESULT_CATEGORY)):
                raise ValueError("Prediction already has a result; its original record cannot be rewritten.")
            now = timestamp(self.now_fn())
            original = prediction["snapshot"]
            if now < timestamp(original["event_start"]):
                raise ValueError("An event cannot be settled before its start.")
            profit = american_to_decimal(original["odds"]) - 1 if outcome == "win" else -1 if outcome == "loss" else 0
            if closing_odds is not None:
                american_to_decimal(closing_odds)
            same_line = closing_line == original.get("line")
            clv = None
            if closing_odds is not None and same_line:
                clv = 100 * (implied_probability(closing_odds) - implied_probability(original["odds"]))
            return self._append(RESULT_CATEGORY, {
                "prediction_id": prediction_id, "prediction_sha256": digest(prediction),
                "outcome": outcome, "source_url": source(source_url), "settled_at": now.isoformat(),
                "flat_unit_profit": profit, "closing_odds": closing_odds, "closing_line": closing_line,
                "price_clv_percentage_points": clv,
                "clv_limitation": "Price CLV requires identical line; line movement is recorded separately.",
            })

    def report(self):
        predictions = {x["prediction_id"]: x for x in self._records(PREDICTION_CATEGORY)}
        results = self._records(RESULT_CATEGORY)
        usable = []
        for result in results:
            prediction = predictions.get(result["prediction_id"])
            if prediction and result["prediction_sha256"] != digest(prediction):
                raise RuntimeError("Sports prediction/result linkage integrity check failed.")
            if prediction and result["outcome"] in {"win", "loss"}:
                usable.append((prediction, result))
        brier = [
            (p["analysis"]["estimated_probability_given_no_push"] - (r["outcome"] == "win")) ** 2
            for p, r in usable
        ]
        # Pushes count in amount risked; voids do not. This is hypothetical unit ROI.
        settled = [r for r in results if r["prediction_id"] in predictions and r["outcome"] != "void"]
        clvs = [r["price_clv_percentage_points"] for r in settled if r.get("price_clv_percentage_points") is not None]
        return {
            "predictions_in_window": len(predictions), "graded_win_loss_count": len(usable),
            "hypothetical_flat_unit_roi": sum(r["flat_unit_profit"] for r in settled) / len(settled) if settled else None,
            "conditional_brier_score": sum(brier) / len(brier) if brier else None,
            "mean_same_line_price_clv_percentage_points": sum(clvs) / len(clvs) if clvs else None,
            "profitability_proven": False, "read_window_per_category": 1000,
            "limitation": "Descriptive paper records, not placed bets or evidence of a proven profitable edge.",
        }
