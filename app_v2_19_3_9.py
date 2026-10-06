"""Tyler AI v2.19.3.9: bootstrap the NFL-first Sports Betting Analyst skill.

The bootstrap is idempotent. It is attempted at import time and retried on later
requests if Supabase was temporarily unavailable while the service started.
No wager is ever executed; the skill is analysis/recommendation only.
"""

import threading
import time

import app_v2_19_3_8 as v21938


v21938.base.VERSION = "2.19.3.9-sports-betting-analyst"
v21938.base.VERSION_SHORT = "v2.19.3.9"

base = v21938.base
app = v21938.app
ENGINE = v21938.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v21938.EXECUTOR
SKILL_LAB = v21938.SKILL_LAB
TRAINER = v21938.TRAINER

_BOOTSTRAP_LOCK = threading.RLock()
_BOOTSTRAP_STATE = {
    "ready": False,
    "last_attempt": 0.0,
    "last_error": None,
    "result": None,
}


def ensure_sports_betting_skill(force=False):
    if _BOOTSTRAP_STATE["ready"]:
        return _BOOTSTRAP_STATE["result"]

    now = time.monotonic()
    if not force and now - float(_BOOTSTRAP_STATE["last_attempt"] or 0.0) < 30.0:
        return None

    with _BOOTSTRAP_LOCK:
        if _BOOTSTRAP_STATE["ready"]:
            return _BOOTSTRAP_STATE["result"]

        now = time.monotonic()
        if not force and now - float(_BOOTSTRAP_STATE["last_attempt"] or 0.0) < 30.0:
            return None

        _BOOTSTRAP_STATE["last_attempt"] = now
        try:
            result = SKILL_LAB.bootstrap_sports_betting_skill()
        except Exception as exc:
            _BOOTSTRAP_STATE["last_error"] = str(exc)[:500]
            return None

        _BOOTSTRAP_STATE["ready"] = True
        _BOOTSTRAP_STATE["last_error"] = None
        _BOOTSTRAP_STATE["result"] = result
        return result


# Best-effort startup registration. A temporarily unavailable Supabase project
# must not prevent Tyler AI from starting; the before-request hook retries later.
ensure_sports_betting_skill(force=True)


@app.before_request
def _sports_skill_bootstrap_before_request():
    ensure_sports_betting_skill(force=False)


__all__ = [
    "app",
    "base",
    "ENGINE",
    "VERSION",
    "VERSION_SHORT",
    "EXECUTOR",
    "SKILL_LAB",
    "TRAINER",
    "ensure_sports_betting_skill",
]


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(__import__("os").environ.get("PORT", 10000)),
    )
