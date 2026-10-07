"""Conservative input extraction and application-owned sports calculations.

No benchmark IDs, expected answers, live feeds, or inferred opposing prices.
Unsupported prose stays unknown. Structured input is preferred for precision.
"""
import json
import re

from sports_betting import implied_probability, probability, price_analysis

FIELDS = (
    "implied_probability", "previous_implied_probability", "opposite_implied_probability",
    "estimated_probability", "estimated_probability_low", "push_probability",
    "conditional_probability", "no_vig_probability", "edge_percentage_points",
    "lower_bound_edge_percentage_points", "expected_profit_per_unit",
)
QUOTE = r"(?<![\w.])[+-]\d{3,}(?!\d|\.\d|\s*%)"
VALUE = r"(?:0(?:\.\d+)?|1(?:\.0+)?|\d+(?:\.\d+)?\s*%)"


def _one(text, patterns):
    values = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.I):
            raw = match[1].replace(" ", "")
            value = float(raw.rstrip("%")) / (100 if raw.endswith("%") else 1)
            values.append(probability(value))
    if len(set(values)) > 1:
        raise ValueError("Conflicting probability labels; use structured JSON.")
    return values[0] if values else None


def calculate(text, *, synthetic=False):
    """Synthetic lab exercises may declare a no-push assumption; live calls may not."""
    text = str(text)
    metrics = dict.fromkeys(FIELDS)
    assumptions, issues = [], []
    odds = opposite = previous = win = push = low = high = loss = None
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError("Duplicate structured input key.")
            obj[key] = value
        return obj
    try:
        data = json.loads(text, object_pairs_hook=unique)
    except ValueError:
        if text.lstrip().startswith(("{", "[")):
            raise ValueError("Invalid or ambiguous structured sports input.") from None
        data = None
    if data is not None and not isinstance(data, dict):
        raise ValueError("Structured sports input must be an object.")
    if isinstance(data, dict):
        odds = data.get("odds")
        previous = data.get("previous_odds")
        if data.get("opposite_odds") is not None:
            if data.get("market_type") != "two_way":
                raise ValueError("Opposing odds require market_type=two_way.")
            opposite = data["opposite_odds"]
        for key in ("p_win", "p_push", "p_low", "p_high", "p_loss", "implied_probability"):
            if key in data:
                probability(data[key], key)
        win, push = data.get("p_win"), data.get("p_push")
        low, high, loss = data.get("p_low"), data.get("p_high"), data.get("p_loss")
        if data.get("implied_probability") is not None:
            metrics["implied_probability"] = probability(data["implied_probability"])
    else:
        quotes = [int(m[0]) for m in re.finditer(QUOTE, text)]
        both = re.search(r"\bboth sides\s+(" + QUOTE + r")", text, re.I)
        now = re.search(r"\bit is now\b(?:[^.!?]|\.(?=\d)){0,160}?(" + QUOTE + r")", text, re.I)
        if both and len(set(quotes)) == 1:
            odds = opposite = int(both[1])
        elif now and len(quotes) == 2:
            previous, odds = quotes
            if odds != int(now[1]):
                raise ValueError("Ambiguous changed prices; use structured JSON.")
        elif len(quotes) == 1:
            odds = quotes[0]
        elif quotes:
            issues.append("Multiple unassigned prices; calculations withheld.")
        end = r"(?!\d|%|\.\d)"
        metrics["implied_probability"] = _one(text, [r"\b(?:sportsbook|book) implies\s+(" + VALUE + r")" + end])
        win = _one(text, [
            r"\b(?:estimated win probability|supplied win estimate|win)\s+(" + VALUE + r")" + end,
            r"\bTyler estimates(?: it hits)?\s+(" + VALUE + r")" + end,
            r"\b(" + VALUE + r")\s+model estimate\b",
        ])
        push = _one(text, [r"\bpush(?: probability)?\s+(" + VALUE + r")" + end])
        loss = _one(text, [r"\bloss\s+(" + VALUE + r")" + end])
        interval = re.search(r"\b(?:range|interval)\s+(" + VALUE + r")\s+to\s+(" + VALUE + r")" + end, text, re.I)
        if interval:
            low = _one("low " + interval[1], [r"low (" + VALUE + r")"])
            high = _one("high " + interval[2], [r"high (" + VALUE + r")"])
        if re.search(r"\b(?:no pushes|no-push|without pushes)\b", text, re.I):
            if push not in (None, 0):
                raise ValueError("Conflicting push information.")
            push = 0
    if odds is not None:
        implied = implied_probability(odds)
        if metrics["implied_probability"] is not None and abs(metrics["implied_probability"] - implied) > 1e-9:
            raise ValueError("Conflicting odds and implied probability.")
        metrics["implied_probability"] = implied
    if previous is not None:
        metrics["previous_implied_probability"] = implied_probability(previous)
    if opposite is not None:
        if odds is None:
            raise ValueError("Opposing price requires a selected-side price.")
        other = implied_probability(opposite)
        metrics["opposite_implied_probability"] = other
        metrics["no_vig_probability"] = metrics["implied_probability"] / (metrics["implied_probability"] + other)
        assumptions.append("No-vig is proportional normalization, not true probability.")
    win = probability(win) if win is not None else None
    low = probability(low) if low is not None else None
    high = probability(high) if high is not None else None
    if low is not None or high is not None:
        if win is None or low is None or high is None or not low <= win <= high:
            raise ValueError("Probability interval must contain the supplied estimate.")
    if push is None and win is not None and synthetic:
        push = 0
        assumptions.append("Synthetic lab calculation assumes no pushes; not verified for a live market.")
    push = probability(push) if push is not None else None
    if push is not None and (push == 1 or win is not None and win + push > 1 or high is not None and high + push > 1):
        raise ValueError("Win/push probabilities are inconsistent.")
    if loss is not None and (win is None or push is None or abs(win + push + probability(loss) - 1) > 1e-9):
        raise ValueError("Win, push, and loss must sum to one.")
    metrics.update(estimated_probability=win, estimated_probability_low=low, push_probability=push)
    implied = metrics["implied_probability"]
    if implied is not None and implied <= 0:
        raise ValueError("Break-even probability must be positive.")
    if win is not None and implied is not None and push is not None:
        if odds is not None:
            result = price_analysis(odds, win, push, opposite)
            conditional, edge, profit = (result["estimated_probability_given_no_push"],
                                         result["edge_percentage_points"], result["expected_profit_per_unit"])
        else:
            conditional = win / (1 - push)
            edge, profit = 100 * (conditional - implied), win / implied + push - 1
        metrics.update(conditional_probability=conditional, edge_percentage_points=edge,
                       expected_profit_per_unit=profit)
        if low is not None:
            metrics["lower_bound_edge_percentage_points"] = 100 * (low / (1 - push) - implied)
    elif win is not None and implied is not None:
        issues.append("Push probability missing; EV and edge withheld.")
    return {"metrics": metrics, "assumptions": assumptions, "issues": issues,
            "provenance": "Application calculations from caller-supplied inputs; inputs and probability model unverified."}
