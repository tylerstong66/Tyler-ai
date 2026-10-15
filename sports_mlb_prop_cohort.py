"""Retrospective, descriptive MLB hitter shadow cohort review.

Aggregates independently validated per-hitter date-block replay metrics. Does
NOT establish a betting edge: convenience player cohorts may have survivorship
bias; baseball player props have different settlement eligibility rules.
"""
from sports_mlb_hit_prop_shadow import retrospective_walk_forward


def summarize_hitter_cohort(players, *, season):
    """players is a caller-declared iterable of (verified MLB id, name, logs).

    Per-player weight is the actual number of eligible recorded game outcomes,
    never the number of active-roster slots or scraped market prices.
    """
    if isinstance(season, bool) or not isinstance(season, int):
        raise ValueError("Invalid evaluation season.")
    if not isinstance(players, list) or not 1 <= len(players) <= 50:
        raise ValueError("Evaluate a preregistered collection of 1 to 50 hitters.")
    seen = set()
    all_hitter_results = []
    aggregate = {event: {metric: 0.0 for metric in (
        "model_brier", "fixed_prior_brier", "model_log_loss", "fixed_prior_log_loss")}
        for event in ("hit", "hr")}
    totals = {"hit": 0, "hr": 0}
    for record in players:
        if not isinstance(record, dict):
            raise ValueError("Malformed cohort record.")
        hitter = record.get("hitter_id")
        if isinstance(hitter, bool) or not isinstance(hitter, int) or hitter <= 0 or hitter in seen:
            raise ValueError("Invalid or repeated official MLB hitter identity.")
        seen.add(hitter)
        name = record.get("hitter_name")
        rows = record.get("game_logs")
        if not isinstance(name, str) or not name.strip() or not isinstance(rows, list):
            raise ValueError("Missing hitter name or game logs.")
        if any(r.get("hitter_id") != hitter for r in rows):
            raise ValueError("Cohort includes a foreign player's game log.")
        review = retrospective_walk_forward(rows, evaluation_season=season)
        summary = {"hitter_id": hitter, "hitter_name": name.strip(),
                   "evaluation_season": season, "outcomes": review["outcomes"],
                   "retrospective_only": True}
        all_hitter_results.append(summary)
        for event in ("hit", "hr"):
            item = review["outcomes"][event]
            n = item["n_games_with_at_least_one_ab"]
            totals[event] += n
            if n:
                for metric in aggregate[event]:
                    aggregate[event][metric] += n * item[metric]
    pooled = {}
    for event in ("hit", "hr"):
        n = totals[event]
        measures = {metric: round(value / n, 6) if n else None
                    for metric, value in aggregate[event].items()}
        pooled[event] = {
            "eligible_player_games": n,
            **measures,
            "retrospective_model_better_than_fixed_baseline": (
                measures["model_brier"] < measures["fixed_prior_brier"] if n else None),
            "improvement_proven": False,
        }
    return {
        "type": "MLB_PROVISIONAL_HITTER_COHORT_RETROSPECTIVE",
        "evaluation_season": season,
        "hitter_count": len(players), "hitter_ids": [x["hitter_id"] for x in players],
        "per_hitter": all_hitter_results, "pooled": pooled,
        "chronological_replay": True, "independently_frozen_prospective": False,
        "model_approved_for_sportsbook_value": False,
        "wager_execution": False,
        "limitations": [
            "Pooling equally weights eligible recorded player-games, not individual players.",
            "Historical gameLogs were requested after the fact, not independently archived before each game.",
            "Only games with at least one at-bat are enrolled; actual sportsbook void and lineup rules differ.",
            "A snapshot of currently active roster players can cause sample selection/survivorship bias.",
            "Comparators are fixed exploratory priors, not real market prices or published state-of-the-art models.",
            "Differences require independent prospective data and uncertainty intervals; neither is supplied by this review.",
        ],
    }
