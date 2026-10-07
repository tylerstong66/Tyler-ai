"""Necessary topic coverage checks, not proof of semantic correctness.

Requirements follow scenario intent, never benchmark IDs or hidden answers.
Passing word coverage still requires semantic judging and human review.
"""
import re

PROP = {
    "expected_carries": ("Expected carries/opportunity", r"\bcarr(?:ies|y)\b|rushing attempts|expected attempts"),
    "snap_route_role": ("Snap/route role and usage", r"\bsnaps?\b|\broutes?\b"),
    "injuries": ("Current injuries", r"injur"),
    "offensive_line": ("Offensive line", r"offensive line|blocking"),
    "opponent_front": ("Opponent front", r"opponent.{0,30}front|defensive front|front[- ]seven"),
    "game_script": ("Game script", r"game script"),
    "line_movement": ("Current line movement", r"line movement|market movement|line changes"),
    "outcome_distribution": ("Outcome distribution around the current line", r"distribution"),
}
SAMPLE = {
    "larger_tracked_sample": ("Larger tracked sample; no fixed size guarantees an edge", r"(?:larger|longer|much more).{0,35}(?:sample|track|record)|tracked.{0,25}(?:larger|longer)"),
    "calibration": ("Calibration", r"calibrat"),
    "closing_line_value": ("Closing-line value", r"closing[- ]line value|\bclv\b"),
    "roi": ("ROI/net returns, not win rate alone", r"\broi\b|return on investment|net returns"),
    "market_buckets": ("Performance by market bucket", r"market[- ](?:specific|level)|by market|market.{0,30}(?:bucket|group|segment)"),
    "confidence_buckets": ("Performance by confidence bucket", r"confidence.{0,30}(?:bucket|group|segment)|by.{0,20}confidence"),
}
PARLAY = {
    "joint_ticket_estimate": ("Correlation-aware joint probability for the whole ticket; cannot assume independence", r"joint.{0,30}(?:probability|model|estimate)|correlation[- ](?:aware|adjusted).{0,35}(?:ticket|probability|estimate)|combined.{0,20}(?:probability|estimate)"),
}
PAYOUT = {
    "standalone_leg_value": ("Require defensible standalone leg value, not a payout target", r"standalone|leg[- ]level|each leg.{0,35}(?:value|edge)"),
    "keep_or_pass": ("Keep the lower payout or pass if the extra leg/ticket lacks value", r"keep.{0,35}(?:payout|ticket|parlay)|\bpass\b|decline|avoid adding|do not add|reject"),
}


def topics(request_text, facts=None):
    text = str(request_text).lower()
    required = {}
    if re.search(r"running back|player prop|rushing", text) and re.search(r"streak|straight|consecutive|again", text):
        required.update(PROP)
    if re.search(r"(?:first|last).{0,25}(?:bets|picks)|(?:real|proven|profitable|sustainable).{0,25}edge", text):
        required.update(SAMPLE)
    if "parlay" in text:
        required.update(PARLAY)
        if re.search(r"\bqb\b|quarterback", text) and re.search(r"\bwr\d?\b|receiv", text):
            required["qb_receiver_connection"] = ("Explain quarterback passing and receiver receiving share opportunity and can be positively correlated", r"(?:quarterback|\bqb\b).{0,100}(?:receiver|receiving).{0,100}(?:positive|correlat)|(?:positive|correlat).{0,100}(?:quarterback|\bqb\b).{0,100}(?:receiver|receiving)")
            required["opponent_scoring_context"] = ("Discuss opponent scoring and game script; do not equate opponent under with game-total under or assume a fixed sign", r"oppon(?:ent|sing).{0,40}(?:scor|under)|(?:scor|under).{0,40}oppon")
        if re.search(r"weak|add|target|payout", text):
            required.update(PAYOUT)
    if facts and (facts.get("metrics", {}).get("expected_profit_per_unit") or 0) > 0:
        required["positive_ev_meaning"] = ("State that the supplied point estimate gives positive net expected profit at the offered price; NO BET may still reflect uncertainty, never a claim that variance or vig erases EV", r"positive.{0,35}(?:ev|expected (?:net )?profit|expectation)|(?:ev|expected (?:net )?profit|expectation).{0,35}positive")
    return required


def descriptions(request_text, facts):
    return [item[0] for item in topics(request_text, facts).values()]


def missing(request_text, answer):
    prose = str(answer.get("rationale", "")) + " " + str(answer.get("uncertainty", ""))
    facts = {"metrics": answer.get("metrics", {})}
    return ["explanation_missing_" + name for name, (_, pattern) in topics(request_text, facts).items()
            if not re.search(pattern, prose, re.I | re.S)]
