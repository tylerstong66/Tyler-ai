"""Deterministic, opt-in NHL model evidence response for chat.

Only a trusted server caller may supply the manifest and archive root. Never
derive archive paths from an untrusted chat message or web search excerpt.
"""
from sports_chat_nhl_evidence_manifest import compare_nhl_manifest


def nhl_chat_evidence_response(manifest, archive_root, now=None):
    result = compare_nhl_manifest(manifest, archive_root, now=now)
    if result.get("status") != "hypothetical_only" or result.get("NO_BET") is not True:
        return ("Verified prospective NHL model/price evidence unavailable. "
                "No model probability, expected value or executable price can be claimed. "
                "NO_BET=true.")
    outcomes = result["outcomes"]
    lines = [
        "Read-only NHL archived model comparison (hypothetical; NOT an executable quote).",
        "Game: " + str(result["game_id"]),
        "Model SHA-256: " + result["model_sha256"],
        "Book: " + result["book"] + "; market: " + result["market"],
    ]
    for side in ("home", "away"):
        row = outcomes[side]
        lines.append(
            f"{side}: model probability {row['model_probability']:.4f}; "
            f"archived American odds {row['american_odds']:+d}; "
            f"hypothetical EV/unit {row['hypothetical_ev_per_unit']:+.4f}"
        )
    lines.extend((result["caveat"], "NO_BET=true; no real wagers or model promotion."))
    return "\n".join(lines)
