"""Comparable paper baselines, authenticated dashboard and bounded final collector."""
import html
import threading
import time

from sports_betting import american_to_decimal, digest, timestamp
from sports_paper_evidence import market_probabilities


def comparison(trial):
    predictions = {r["paper_prediction_id"]: r for r in trial.records()}
    results = trial.ledger._records(trial.result_category)
    paired, wins, profits, favorite_profits = [], [], [], []
    total_settled = 0; excluded_ties = 0
    for result in results:
        record = predictions.get(result["paper_prediction_id"])
        if not record:
            continue
        if digest(record) != result["prediction_sha256"]:
            raise RuntimeError("Baseline result integrity linkage failed.")
        total_settled += 1
        outcome = result["outcome"]
        if outcome == "tie":
            excluded_ties += 1
            continue
        win = outcome == record["selection_side"]
        wins.append(win)
        if result["hypothetical_flat_unit_profit"] is not None:
            profits.append(result["hypothetical_flat_unit_profit"])
        market = market_probabilities(record["snapshot"])
        if not market:
            continue
        p = record["forecast"]["probabilities"]
        non_tie = p["home"] + p["away"]
        tyler = {s: p[s] / non_tie for s in ("home", "away")}
        favorite = max(("home", "away"), key=market.get)
        favorite_win = outcome == favorite
        favorite_profit = american_to_decimal(record["snapshot"]["moneyline_quote"]["prices"][favorite]) - 1 if favorite_win else -1
        favorite_profits.append(favorite_profit)
        paired.append({"tyler_brier": sum((tyler[s] - (s == outcome)) ** 2 for s in tyler),
            "market_brier": sum((market[s] - (s == outcome)) ** 2 for s in market),
            "tyler_win": win, "favorite_win": favorite_win,
            "tyler_profit": result["hypothetical_flat_unit_profit"], "favorite_profit": favorite_profit})
    mean = lambda key: sum(r[key] for r in paired) / len(paired) if paired else None
    return {"settled_count": total_settled, "decisive_result_count": len(wins),
        "tyler_pick_accuracy": sum(wins) / len(wins) if wins else None,
        "paired_priced_count": len(paired), "excluded_tie_count": excluded_ties,
        "paired_tyler_brier": mean("tyler_brier"), "paired_market_brier": mean("market_brier"),
        "paired_tyler_accuracy": mean("tyler_win"), "paired_favorite_accuracy": mean("favorite_win"),
        "paired_tyler_hypothetical_roi": mean("tyler_profit"), "paired_favorite_hypothetical_roi": mean("favorite_profit"),
        "actual_wager_amount": 0,
        "baseline_definition": "Same-event paired comparisons. Market probabilities remove margin proportionally from observed two-way prices. Favorite picks the higher market probability, home on an exact tie. NFL Brier is conditional on no tie; tie results are excluded from these paired metrics. Full NFL three-outcome Brier remains in the cohort report.",
        "limitations": "Small descriptive samples, stale-price risk, no verified closing lines, no bookmaker rule verification and no established profitable edge."}


class FinalCollector:
    def __init__(self, trials, now_fn, enabled=False, interval=3600):
        self.trials, self.now_fn, self.enabled, self.interval = trials, now_fn, enabled, interval
        self.lock = threading.Lock(); self.last_started = None
        self.state = {"enabled": enabled, "running": False, "last_completed_at": None,
            "new_results": 0, "errors": 0, "counts": {}}

    def public_state(self):
        return dict(self.state)

    def maybe_start(self):
        if not self.enabled or (self.last_started is not None and time.monotonic() - self.last_started < self.interval):
            return
        # Claim synchronously to prevent many requests creating waiting threads.
        if not self.lock.acquire(blocking=False):
            return
        self.last_started = time.monotonic(); self.state = {**self.state, "running": True}
        threading.Thread(target=self._run_claimed, daemon=True, name="paper-final-collector").start()

    def collect(self):
        if not self.lock.acquire(blocking=False):
            return {"status": "already_running", **self.public_state()}
        self.last_started = time.monotonic(); self.state = {**self.state, "running": True}
        return self._run_claimed()

    def _run_claimed(self):
        new, errors, checked = 0, 0, 0; counts = {}
        try:
            for name, trial in self.trials.items():
                try:
                    done = {r["paper_prediction_id"] for r in trial.ledger._records(trial.result_category)}
                    predictions = trial.records()
                    for record in sorted(predictions, key=lambda r: r["event_start"]):
                        if checked >= 48 or record["paper_prediction_id"] in done or timestamp(record["event_start"]) > timestamp(self.now_fn()):
                            continue
                        checked += 1
                        try:
                            # No model calls and no forecasts are made by this collector.
                            trial.settle(record["paper_prediction_id"])
                            new += 1; done.add(record["paper_prediction_id"])
                        except ValueError as exc:
                            if "not confirmed a final" not in str(exc) and "already recorded" not in str(exc):
                                errors += 1
                        except (RuntimeError, KeyError, TypeError):
                            errors += 1
                    counts[name] = {"saved": len(predictions), "settled": len(done), "pending": len(predictions) - len(done)}
                except (RuntimeError, ValueError, KeyError, TypeError):
                    errors += 1
            self.state = {"enabled": self.enabled, "running": False, "last_completed_at": self.now_fn(),
                "new_results": new, "errors": errors, "checked": checked, "counts": counts,
                "limitation": "Request-triggered collection, at most hourly, latest 1000 per category, one-process lock. Sleeping service requires a wake-up request; no exact settlement-time guarantee."}
            return self.public_state()
        finally:
            self.state = {**self.state, "running": False}
            self.lock.release()


def dashboard_html(reports, comparisons, predictions, collector):
    esc = lambda value: html.escape(str(value), quote=True)
    fmt = lambda x: "—" if x is None else f"{x:.1%}"
    rows = []
    for name, report in reports.items():
        c = comparisons[name]
        rows.append("<tr>" + "".join("<td>" + esc(v) + "</td>" for v in [name, report["pipeline_version"], report["predictions_in_window"], report["settled_in_window"], report["pending_in_window"], fmt(c["tyler_pick_accuracy"]), fmt(c["paired_favorite_accuracy"]), c["paired_priced_count"], fmt(report["hypothetical_flat_unit_roi"])]) + "</tr>")
    detail = []
    for name, report in reports.items():
        c = comparisons[name]
        brier = lambda v: "—" if v is None else f"{v:.3f}"
        bins = report["calibration_bins"]
        detail.append(f"<section><h2>{esc(name)} comparison</h2><p>Paired Brier: Tyler {brier(c['paired_tyler_brier'])}; market {brier(c['paired_market_brier'])}. Paired hypothetical ROI: Tyler {fmt(c['paired_tyler_hypothetical_roi'])}; favorite {fmt(c['paired_favorite_hypothetical_roi'])}. Ties excluded: {c['excluded_tie_count']}.</p><p>{esc(c['baseline_definition'])}</p><h3>Confidence versus outcomes</h3>" + ("<table><tr><th>Probability band</th><th>Count</th><th>Mean forecast</th><th>Win rate</th></tr>" + "".join(f"<tr><td>{esc(b['probability_band'])}</td><td>{b['count']}</td><td>{fmt(b['mean_probability'])}</td><td>{fmt(b['observed_win_rate'])}</td></tr>" for b in bins) + "</table>" if bins else "<p>Awaiting settled forecasts.</p>") + "</section>")
    cards = []
    for cohort, r in sorted(predictions, key=lambda pair: pair[1]["recorded_at"], reverse=True):
        facts = r.get("supporting_facts", [])
        cards.append(f"<details><summary>{esc(r['event'])} · {esc(cohort)} · {esc(r['selection'])} {fmt(r['forecast']['probabilities'][r['selection_side']])}</summary><p>{esc(r['paper_prediction_id'])} · saved {esc(r['recorded_at'])} · starts {esc(r['event_start'])}</p><p>{esc(r['forecast']['rationale'])}</p><p>{esc(r['forecast']['uncertainty'])}</p>" + "".join(f"<p>{esc(f['id'])}: {esc(f['text'])}<br>{esc(f['source_url'])} · retrieved {esc(f['retrieved_at'])}</p>" for f in facts) + f"<p>Original SHA-256: {esc(digest(r))}</p></details>")
    return """<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Tyler paper results</title><style>body{font:16px system-ui;background:#07111f;color:#e4ecf5;max-width:1180px;margin:auto;padding:28px}a{color:#8ad6ff}h1{font-size:32px}table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;border-bottom:1px solid #30465e;padding:10px}section,details{background:#122237;border:1px solid #30465e;border-radius:10px;padding:18px;margin:18px 0}summary{cursor:pointer}p{line-height:1.5;overflow-wrap:anywhere}.table-wrap{overflow:auto}</style></head><body><p><a href="/ui">← Tyler AI</a> · <a href="/ui/paper-results">Refresh results</a></p><h1>Paper forecasts & results</h1><p>NO BET · actual wager amount $0 · experimental, uncalibrated probabilities. Original and improved cohorts remain separate.</p>""" + f"<p>Collector: {'running' if collector['running'] else 'idle'} · last completed {esc(collector['last_completed_at'])} · errors {collector['errors']}. Scheduled wake-ups are hourly; service sleep can delay results.</p><div class='table-wrap'><table><tr><th>Cohort</th><th>Method</th><th>Saved</th><th>Settled</th><th>Pending</th><th>Tyler accuracy</th><th>Favorite paired</th><th>Paired n</th><th>Hypothetical ROI</th></tr>" + "".join(rows) + "</table></div><p>Metrics are descriptive. Accuracy uses decisive results; favorite and paired Brier use only the same priced events. No verified closing-line value or proven profitable edge. Read window: latest 1000 per category.</p>" + "".join(detail) + "<h2>Frozen forecasts and sourced facts</h2>" + "".join(cards) + "</body></html>"
