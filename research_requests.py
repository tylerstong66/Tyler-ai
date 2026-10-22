"""Bounded search inputs; the original task is retained for reasoning."""
import re


def is_sports_research(message):
    text = str(message or "")
    return bool(re.search(r"\b(?:NFL|NBA|NHL|MLB|football|basketball|baseball|hockey)\b", text, re.I)
                and re.search(r"\b(?:research|odds|parlay|moneyline|matchup|touchdown)\b", text, re.I))


def search_query(message):
    """Keep short queries unchanged; distill oversized instructions locally.

    Leave headroom below Tavily's observed 1500-character limit. Dates can occur
    late in a specification, so retain them before the bounded topic excerpt.
    No model call or fallback provider is needed to repair an oversized input.
    """
    text = re.sub(r"\s+", " ", str(message or "")).strip()
    if not text:
        raise ValueError("Search query is empty")
    if len(text) <= 1400:
        return text
    dates = list(dict.fromkeys(re.findall(
        r"\b(?:\d{4}-\d{2}-\d{2}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:[–—-]\d{1,2})?(?:,?\s+\d{4})?)\b",
        text, re.I)))
    scope = re.search(r"(?:Your mission is to|Please research|Research)\s+(.{20,500}?)(?:\.\s|$)", text, re.I)
    prefix = " ".join(dates)[:250]
    if scope:
        prefix += " " + scope.group(1)
    if is_sports_research(text):
        prefix += " schedule matchups injuries statistics EPA FanDuel moneyline anytime touchdown game totals"
    return (prefix.strip() + " " + text)[:1400].strip()
