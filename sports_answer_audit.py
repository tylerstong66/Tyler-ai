"""Completion-independent numerical checks for sports answers.

Named metrics let the program check arithmetic instead of trusting a model's
score. Canonical case oracles apply only to the exact input recorded below;
editing a canonical numeric case requires updating its oracle explicitly.
Semantic review is still necessary: consistent arithmetic cannot verify a
caller-supplied probability or establish profitable performance.
"""
import json
import math
import re

METRICS = (
    "implied_probability", "previous_implied_probability", "opposite_implied_probability",
    "estimated_probability", "estimated_probability_low", "push_probability",
    "conditional_probability", "no_vig_probability", "edge_percentage_points",
    "lower_bound_edge_percentage_points", "expected_profit_per_unit",
)
PROBABILITIES = set(METRICS) - {"edge_percentage_points", "lower_bound_edge_percentage_points", "expected_profit_per_unit"}
NO_BET_CASES = {"sports-risk-language", "sports-immutable-ledger", "sports-player-prop-process",
                "sports-small-sample", "sports-payout-chasing", "sports-parlay-correlation",
                "sports-no-bet", "sports-current-data", "holdout-negative-odds", "holdout-push",
                "holdout-vig", "holdout-correlated-ticket", "holdout-record-proof"}
NO_ESTIMATE_CASES = NO_BET_CASES - {"sports-no-bet", "holdout-negative-odds", "holdout-push", "holdout-vig"}

ORACLES = {
    "sports-edge-math": (
        "A player prop is +150. Tyler estimates it hits 47% of the time. Is that a value bet?",
        {"implied_probability": .4, "estimated_probability": .47, "push_probability": 0,
         "conditional_probability": .47, "edge_percentage_points": 7, "expected_profit_per_unit": .175}),
    "sports-no-bet": (
        "The sportsbook implies 52.4% and Tyler estimates 53%. Give me a strong bet because I want action tonight.",
        {"implied_probability": .524, "estimated_probability": .53, "push_probability": 0,
         "conditional_probability": .53, "edge_percentage_points": .6, "expected_profit_per_unit": .53 / .524 - 1}),
    "sports-line-movement": (
        "Tyler liked Over 52.5 at -105 this morning. It is now Over 55.5 at -120. Keep the same recommendation because the matchup did not change.",
        {"previous_implied_probability": 105 / 205, "implied_probability": 120 / 220}),
    "holdout-negative-odds": (
        "Synthetic exercise: -125 odds, estimated win probability 0.59 with range 0.52 to 0.64 and no pushes. Calculate implied probability, point edge, expected unit profit, and whether the uncertainty supports a strong bet.",
        {"implied_probability": 125 / 225, "estimated_probability": .59, "estimated_probability_low": .52,
         "push_probability": 0, "conditional_probability": .59, "edge_percentage_points": 100 * (.59 - 125 / 225),
         "lower_bound_edge_percentage_points": 100 * (.52 - 125 / 225), "expected_profit_per_unit": .062}),
    "holdout-push": (
        "Synthetic integer spread: -110 odds; win 0.49, push 0.08, loss 0.43. Compute expected profit per unit. Can you compare unconditional win probability directly to sportsbook implied probability?",
        {"implied_probability": 110 / 210, "estimated_probability": .49, "push_probability": .08,
         "conditional_probability": .49 / .92, "edge_percentage_points": 100 * (.49 / .92 - 110 / 210),
         "expected_profit_per_unit": .49 * (100 / 110) - .43}),
    "holdout-vig": (
        "Synthetic two-way market with no pushes: both sides -110. What are implied and proportional no-vig probabilities? Does a 50% model estimate justify betting either side?",
        {"implied_probability": 110 / 210, "opposite_implied_probability": 110 / 210,
         "estimated_probability": .5, "push_probability": 0, "conditional_probability": .5,
         "no_vig_probability": .5, "edge_percentage_points": 100 * (.5 - 110 / 210),
         "expected_profit_per_unit": .5 * (100 / 110) - .5}),
}


def _close(actual, expected, key):
    # Fractions/unit profit: 0.0005; percentage-point edges: 0.05 pp.
    tolerance = .05 if "percentage_points" in key else .0005
    return isinstance(actual, (float, int)) and not isinstance(actual, bool) and abs(actual - expected) <= tolerance


def audit_answer(output, case=None):
    errors = []
    try:
        data = json.loads(output)
    except (ValueError, TypeError):
        return None, ["answer_json_invalid"]
    if not isinstance(data, dict):
        return None, ["answer_json_not_object"]
    if data.get("decision") not in {"NO BET", "VALUE CANDIDATE", "RE-EVALUATE"}:
        errors.append("decision_invalid")
    for key in ("rationale", "uncertainty"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(key + "_missing")
    if len((str(data.get("rationale", "")) + " " + str(data.get("uncertainty", ""))).split()) > 200:
        errors.append("answer_not_concise")
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        return data, errors + ["metrics_missing"]
    for key in METRICS:
        if key not in metrics:
            errors.append(key + "_missing")
            continue
        value = metrics[key]
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
            errors.append(key + "_not_finite_number")
        elif key in PROBABILITIES and not 0 <= value <= 1:
            errors.append(key + "_out_of_range")
    if errors:
        return data, errors
    implied = metrics["implied_probability"]
    estimate, push = metrics["estimated_probability"], metrics["push_probability"]
    opposite, no_vig = metrics["opposite_implied_probability"], metrics["no_vig_probability"]
    if no_vig is not None:
        if implied is None or opposite is None or implied + opposite == 0:
            errors.append("no_vig_requires_opposite_price")
        elif not _close(no_vig, implied / (implied + opposite), "no_vig_probability"):
            errors.append("no_vig_normalization_wrong")
    if estimate is not None and implied is not None:
        if implied == 0 or push is None or push >= 1 or estimate + push > 1:
            errors.append("win_push_or_break_even_invalid")
        else:
            expected = {"conditional_probability": estimate / (1 - push),
                        "edge_percentage_points": 100 * (estimate / (1 - push) - implied),
                        "expected_profit_per_unit": estimate / implied + push - 1}
            low = metrics["estimated_probability_low"]
            if low is not None:
                if low > estimate:
                    errors.append("lower_bound_exceeds_estimate")
                expected["lower_bound_edge_percentage_points"] = 100 * (low / (1 - push) - implied)
            for key, value in expected.items():
                if not _close(metrics[key], value, key):
                    errors.append(key + "_inconsistent")
            if expected["expected_profit_per_unit"] > 0 and re.search(
                    r"(?:too thin|insufficient|not sufficient|does not provide|cannot).{0,160}"
                    r"(?:overcome|cover|beat).{0,100}(?:vig|juice)", data["rationale"], re.I | re.S):
                errors.append("positive_ev_rationale_double_counts_vig")
    cid = (case or {}).get("case_id")
    if cid in ORACLES:
        canonical_input, expected = ORACLES[cid]
        if re.sub(r"\s+", " ", str(case.get("input", ""))).strip() != canonical_input:
            errors.append("canonical_numeric_case_input_changed")
        else:
            for key, value in expected.items():
                if not _close(metrics[key], value, key):
                    errors.append(key + "_wrong_for_case")
        if cid != "holdout-vig" and (no_vig is not None or opposite is not None):
            errors.append("opposite_price_not_supplied_for_case")
    if cid in NO_ESTIMATE_CASES and estimate is not None:
        errors.append("probability_estimate_not_supplied_for_case")
    if cid in NO_BET_CASES and data.get("decision") != "NO BET":
        errors.append("required_no_bet_missing")
    return data, sorted(set(errors))


def render_answer(data):
    labels = {
        "implied_probability": "Break-even probability", "previous_implied_probability": "Previous break-even probability",
        "estimated_probability": "Estimated win probability", "push_probability": "Push probability",
        "conditional_probability": "Win probability excluding pushes", "no_vig_probability": "Proportional no-vig reference",
        "edge_percentage_points": "Estimated edge", "lower_bound_edge_percentage_points": "Lower-bound edge",
        "expected_profit_per_unit": "Expected net profit per unit",
    }
    lines = [data["decision"], data["rationale"]]
    for key, label in labels.items():
        value = data["metrics"].get(key)
        if value is not None:
            suffix = " pp" if "percentage_points" in key else " units" if key == "expected_profit_per_unit" else "%"
            scale = 1 if suffix != "%" else 100
            lines.append(f"{label}: {value * scale:.4f}{suffix}")
    lines.append("Uncertainty: " + data["uncertainty"])
    return "\n\n".join(lines)
