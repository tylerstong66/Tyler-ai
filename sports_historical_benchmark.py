"""Offline NFL baseline. No app imports, LLM calls, ledger writes or wagers.

Retrospective schedule snapshots do not prove historical publication times.
Results become eligible after kickoff + 24h; this is an explicit assumption.
Moneylines are evaluation-only, never predictors. Injury effects are disabled.
"""
import csv
import hashlib
import heapq
import json
import math
import random
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

VERSION = "nfl-independent-baseline-v1"
FEATURES = ("intercept", "elo_difference_200", "home_venue", "rest_difference_7", "prior_margin_difference_14")
TEAM_ALIASES = {"OAK": "LV", "SD": "LAC", "STL": "LA"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def utc(value):
    value = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("A timezone-aware timestamp is required.")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class Game:
    identifier: str
    season: int
    week: int
    game_type: str
    kickoff: datetime
    home: str
    away: str
    neutral: bool
    home_score: int
    away_score: int
    home_price: int | None
    away_price: int | None

    @property
    def outcome(self):
        return "home" if self.home_score > self.away_score else "away" if self.home_score < self.away_score else "tie"


def price(value):
    if value == "":
        return None
    number = int(value)
    if abs(number) < 100:
        raise ValueError("Malformed American moneyline.")
    return number


def read_games(path, first=2010, last=2025):
    games, seen = [], set()
    with Path(path).open(newline="") as stream:
        for row in csv.DictReader(stream):
            season = int(row["season"])
            if not first <= season <= last:
                continue
            if row["game_type"] not in {"REG", "WC", "DIV", "CON", "SB"}:
                raise ValueError("Unsupported game type.")
            if row["game_id"] in seen:
                raise ValueError("Duplicate game ID.")
            seen.add(row["game_id"])
            if not row["home_score"] or not row["away_score"]:
                raise ValueError("Selected historical game lacks a final score.")
            if row["location"] not in {"Home", "Neutral"}:
                raise ValueError("Historical venue designation is unknown.")
            start = datetime.fromisoformat(row["gameday"] + "T" + row["gametime"]).replace(tzinfo=ZoneInfo("America/New_York")).astimezone(timezone.utc)
            home = TEAM_ALIASES.get(row["home_team"], row["home_team"])
            away = TEAM_ALIASES.get(row["away_team"], row["away_team"])
            scores = int(row["home_score"]), int(row["away_score"])
            if home == away or min(scores) < 0:
                raise ValueError("Invalid teams or scores.")
            games.append(Game(row["game_id"], season, int(row["week"]), row["game_type"], start,
                home, away, row["location"] == "Neutral", *scores, price(row["home_moneyline"]), price(row["away_moneyline"])))
    return sorted(games, key=lambda g: (g.kickoff, g.identifier))


class PriorState:
    def __init__(self):
        self.ratings = defaultdict(lambda: 1500.0)
        self.margins = defaultdict(lambda: deque(maxlen=8))
        self.last_played = {}
        self.latest_available = None
        self.season = None
        self.used_results = 0

    def new_season(self, season):
        if self.season is not None and season != self.season:
            for team in self.ratings:
                self.ratings[team] = 1500 + (self.ratings[team] - 1500) * (2 / 3)
        self.season = season

    def apply(self, game, available):
        difference = self.ratings[game.home] - self.ratings[game.away] + (0 if game.neutral else 55)
        expected = sigmoid(difference * math.log(10) / 400)
        actual = 1.0 if game.outcome == "home" else 0.0 if game.outcome == "away" else 0.5
        change = 20 * (actual - expected)
        self.ratings[game.home] += change
        self.ratings[game.away] -= change
        margin = game.home_score - game.away_score
        self.margins[game.home].append(margin)
        self.margins[game.away].append(-margin)
        for team in (game.home, game.away):
            self.last_played[team] = game.kickoff
        self.latest_available = available
        self.used_results += 1

    def features(self, game):
        def rest(team):
            previous = self.last_played.get(team)
            days = (game.kickoff - previous).total_seconds() / 86400 if previous else 7
            return 7 if days > 30 else min(14, max(3, days))
        def margin(team):
            prior = self.margins[team]
            return sum(prior) / len(prior) if prior else 0
        return [1.0, (self.ratings[game.home] - self.ratings[game.away]) / 200,
                float(not game.neutral), (rest(game.home) - rest(game.away)) / 7,
                (margin(game.home) - margin(game.away)) / 14]


def chronological_features(games, result_delay_hours=24):
    if result_delay_hours < 24:
        raise ValueError("Retrospective result delay must be at least 24 hours.")
    state, pending, rows = PriorState(), [], []
    for game in sorted(games, key=lambda g: (g.kickoff, g.identifier)):
        cutoff = game.kickoff - timedelta(seconds=1)
        while pending and pending[0][0] <= cutoff:
            available, _, prior = heapq.heappop(pending)
            state.apply(prior, available)
        state.new_season(game.season)
        x = state.features(game)  # Never reads current game's result or price.
        if state.latest_available is not None and state.latest_available > cutoff:
            raise RuntimeError("A future result entered the feature state.")
        rows.append({"game": game, "x": x, "cutoff": cutoff.isoformat(),
            "latest_result_available_at": state.latest_available.isoformat() if state.latest_available else None,
            "prior_results_used": state.used_results})
        heapq.heappush(pending, (game.kickoff + timedelta(hours=result_delay_hours), game.identifier, game))
    return rows


def verified_observations(records, identifier, cutoff):
    """Future injury/lineup adapter: reject unproven or post-cutoff snapshots.

    These observations are NOT features of v1 and are NOT fit by the runner.
    A retrieval made after kickoff cannot prove what was known beforehand.
    """
    cutoff = utc(cutoff)
    accepted = []
    for record in records:
        if record.get("game_id") != identifier:
            continue
        if not record.get("source_url", "").startswith("https://"):
            raise ValueError("Observation needs an HTTPS source.")
        if record.get("publication_time_verified") is not True:
            raise ValueError("Observation publication time is not verified.")
        published, retrieved = utc(record["published_at"]), utc(record["retrieved_at"])
        if published > retrieved or retrieved > cutoff:
            raise ValueError("Observation was unavailable by the prediction cutoff.")
        accepted.append(dict(record))
    return accepted


def sigmoid(value):
    return 1 / (1 + math.exp(-max(-40, min(40, value))))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def solve(matrix, vector):
    n = len(vector)
    a = [row[:] + [v] for row, v in zip(matrix, vector)]
    for j in range(n):
        pivot = max(range(j, n), key=lambda k: abs(a[k][j]))
        if abs(a[pivot][j]) < 1e-12:
            raise ValueError("Singular fit; do not publish unstable coefficients.")
        a[j], a[pivot] = a[pivot], a[j]
        divisor = a[j][j]
        a[j] = [x / divisor for x in a[j]]
        for i in range(n):
            if i != j:
                factor = a[i][j]
                a[i] = [v - factor * w for v, w in zip(a[i], a[j])]
    return [row[-1] for row in a]


def objective(rows, weights, penalty):
    decisive = [r for r in rows if r["game"].outcome != "tie"]
    if not decisive:
        raise ValueError("No decisive training results.")
    loss = 0
    for row in decisive:
        z = dot(weights, row["x"])
        y = float(row["game"].outcome == "home")
        loss += max(z, 0) + math.log1p(math.exp(-abs(z))) - y * z
    return loss / len(decisive) + penalty * sum(w * w for w in weights[1:]) / 2


def fit(rows, penalty, max_iterations=60):
    decisive = [r for r in rows if r["game"].outcome != "tie"]
    if penalty <= 0 or not decisive:
        raise ValueError("Positive regularization and decisive rows are required.")
    n, dimension = len(decisive), len(FEATURES)
    weights = [0.0] * dimension
    for iteration in range(max_iterations):
        gradient = [0.0] * dimension
        hessian = [[0.0] * dimension for _ in range(dimension)]
        for row in decisive:
            x = row["x"]; p = sigmoid(dot(weights, x)); y = float(row["game"].outcome == "home")
            for j in range(dimension):
                gradient[j] += (p - y) * x[j] / n
                for k in range(dimension):
                    hessian[j][k] += p * (1 - p) * x[j] * x[k] / n
        for j in range(1, dimension):
            gradient[j] += penalty * weights[j]
            hessian[j][j] += penalty
        if max(abs(g) for g in gradient) < 1e-8:
            return {"weights": weights, "penalty": penalty, "iterations": iteration, "converged": True}
        step = solve(hessian, gradient)
        previous, scale = objective(rows, weights, penalty), 1.0
        for _ in range(25):
            candidate = [w - scale * s for w, s in zip(weights, step)]
            if objective(rows, candidate, penalty) <= previous + 1e-12:
                weights = candidate
                break
            scale /= 2
        else:
            raise RuntimeError("Optimizer failed its descent check.")
    raise RuntimeError("Optimizer did not converge; no model artifact permitted.")


def tie_rate(rows):
    return (sum(r["game"].outcome == "tie" for r in rows) + 0.5) / (len(rows) + 1)


def probabilities(weights, row, tie):
    conditional = sigmoid(dot(weights, row["x"]))
    return {"home": (1 - tie) * conditional, "away": (1 - tie) * (1 - conditional), "tie": tie}


def market_probability(game):
    if game.home_price is None or game.away_price is None:
        return None
    def implied(p):
        return (-p) / (100 - p) if p < 0 else 100 / (p + 100)
    h, a = implied(game.home_price), implied(game.away_price)
    return h / (h + a)


def conditional_loss(p, outcome):
    p = min(1 - 1e-12, max(1e-12, p))
    return -math.log(p if outcome == "home" else 1 - p)


def summarize(rows, model, constant_home):
    full_brier, full_log, paired, wins, bins = [], [], [], [], defaultdict(list)
    for row in rows:
        game = row["game"]; outcome = game.outcome
        probs = probabilities(model["weights"], row, model["tie_probability"])
        full_brier.append(sum((probs[s] - (s == outcome)) ** 2 for s in probs))
        full_log.append(-math.log(max(1e-12, probs[outcome])))
        if outcome == "tie":
            continue
        p = probs["home"] / (1 - probs["tie"])
        win = ("home" if p >= 0.5 else "away") == outcome
        wins.append(win)
        confidence = max(p, 1 - p)
        bins[min(9, int(confidence * 10))].append((confidence, win))
        market = market_probability(game)
        if market is not None:
            y = float(outcome == "home")
            paired.append({"week": game.week, "model_brier": 2 * (p - y) ** 2,
                "market_brier": 2 * (market - y) ** 2, "constant_brier": 2 * (constant_home - y) ** 2,
                "model_log_loss": conditional_loss(p, outcome), "market_log_loss": conditional_loss(market, outcome),
                "constant_log_loss": conditional_loss(constant_home, outcome), "model_win": win,
                "favorite_win": ("home" if market >= .5 else "away") == outcome})
    mean = lambda values: sum(values) / len(values) if values else None
    return {"games": len(rows), "ties": len(rows) - len(wins), "decisive_games": len(wins),
        "correct": sum(wins), "decisive_accuracy": mean(wins),
        "full_three_outcome_brier": mean(full_brier), "full_three_outcome_log_loss": mean(full_log),
        "paired_priced_decisive_games": len(paired),
        "paired": {key: mean([p[key] for p in paired]) for key in
                   ("model_brier", "market_brier", "constant_brier", "model_log_loss", "market_log_loss", "constant_log_loss", "model_win", "favorite_win")},
        "confidence_bins": [{"band": f"{k/10:.1f}-{(k+1)/10:.1f}", "count": len(v),
            "mean_conditional_probability": mean([x[0] for x in v]), "observed_win_rate": mean([x[1] for x in v])}
            for k, v in sorted(bins.items())]}, paired


def week_bootstrap(paired, draws=2000, seed=1729):
    groups = defaultdict(list)
    for row in paired:
        groups[row["week"]].append(row["model_brier"] - row["market_brier"])
    if len(groups) < 2:
        return None
    rng, keys, differences = random.Random(seed), sorted(groups), []
    for _ in range(draws):
        values = [v for _ in keys for v in groups[rng.choice(keys)]]
        differences.append(sum(values) / len(values))
    differences.sort()
    return {"mean_model_minus_market": sum(v for g in groups.values() for v in g) / len(paired),
        "approximate_95_percent_interval": [differences[int(.025 * draws)], differences[int(.975 * draws)]],
        "blocks": len(keys), "draws": draws, "seed": seed,
        "limitation": "Week-block bootstrap on one held-out season; approximate, not proof of future profitability."}


def run_benchmark(snapshot, protocol, output):
    protocol = json.loads(Path(protocol).read_text())
    source_bytes = Path(snapshot).read_bytes()
    if sha256(source_bytes) != protocol["snapshot_sha256"]:
        raise ValueError("Historical snapshot hash differs from frozen protocol.")
    output = Path(output)
    if output.exists():
        raise ValueError("Output already exists; use a new directory to preserve prior runs.")
    output.mkdir(parents=True)
    rows = chronological_features(read_games(snapshot, **protocol["history"]), protocol["result_delay_hours"])
    regular = [r for r in rows if r["game"].game_type == "REG"]
    train = [r for r in regular if r["game"].season in protocol["train_seasons"]]
    validation = [r for r in regular if r["game"].season in protocol["validation_seasons"]]
    test = [r for r in regular if r["game"].season in protocol["test_seasons"]]
    if not all((train, validation, test)) or not (max(r["game"].kickoff for r in train) < min(r["game"].kickoff for r in validation)
            and max(r["game"].kickoff for r in validation) < min(r["game"].kickoff for r in test)):
        raise ValueError("Training, validation and test must be nonempty and chronological.")
    candidates = []
    for penalty in protocol["penalties"]:
        candidate = fit(train, penalty)
        loss = sum(conditional_loss(sigmoid(dot(candidate["weights"], r["x"])), r["game"].outcome)
            for r in validation if r["game"].outcome != "tie") / sum(r["game"].outcome != "tie" for r in validation)
        candidates.append({"penalty": penalty, "validation_conditional_log_loss": loss})
    chosen = min(candidates, key=lambda x: (x["validation_conditional_log_loss"], x["penalty"]))
    development = train + validation
    model = {**fit(development, chosen["penalty"]), "version": VERSION, "feature_names": FEATURES,
        "tie_probability": tie_rate(development), "trained_through_season": max(protocol["validation_seasons"]),
        "snapshot_sha256": protocol["snapshot_sha256"], "protocol_sha256": sha256(canonical(protocol)),
        "injuries_enabled": False, "decision": "NO BET", "production_promoted": False}
    # Freeze coefficients before any test metric is computed. Earlier test results
    # may update the rating/history state only after their assumed availability.
    frozen = canonical(model)
    (output / "model.json").write_bytes(frozen + b"\n")
    constant = (sum(r["game"].outcome == "home" for r in development) + .5) / (sum(r["game"].outcome != "tie" for r in development) + 1)
    metrics, paired = summarize(test, model, constant)
    report = {"version": VERSION, "decision": "NO BET", "production_promoted": False,
        "model_sha256": sha256(frozen), "protocol": protocol, "selection": candidates,
        "chosen_penalty": chosen["penalty"], "train_games": len(train), "validation_games": len(validation),
        "refit_games": len(development), "constant_home_probability": constant,
        "test": metrics, "week_block_brier_difference": week_bootstrap(paired),
        "limitations": ["Retrospective snapshot; historical publication times and revisions are not verified.",
            "Prior finals become available at kickoff plus 24 hours by assumption, not observed publication time.",
            "Moneylines have no bookmaker or quote timestamps; evaluation baseline only, no ROI or closing-line value.",
            "No injury, lineup, weather, quarterback or betting-price feature is fitted.",
            "Earlier held-out outcomes update only the pregame state; coefficients stay frozen.",
            "Historical held-out results are not a prospective live benchmark or proof of a profitable edge."]}
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    with (output / "test_predictions.jsonl").open("w") as stream:
        for row in test:
            g = row["game"]
            record = {"game_id": g.identifier, "season": g.season, "week": g.week, "home": g.home, "away": g.away,
                "kickoff": g.kickoff.isoformat(), "feature_cutoff": row["cutoff"], "x": row["x"],
                "latest_result_available_at": row["latest_result_available_at"], "prior_results_used": row["prior_results_used"],
                "forecast": probabilities(model["weights"], row, model["tie_probability"]),
                "evaluation_target": g.outcome, "evaluation_only_market_home_probability": market_probability(g),
                "model_sha256": report["model_sha256"], "decision": "NO BET"}
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run_benchmark(args.snapshot, args.protocol, args.output)
    print(json.dumps({"version": report["version"], "test": report["test"],
        "week_block_brier_difference": report["week_block_brier_difference"], "output": args.output}, indent=2))
