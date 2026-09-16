"""Stable production launcher for Tyler AI.

Render should always start this module with::

    gunicorn wsgi:app

The active version is selected by the TYLER_APP_MODULE environment variable.
Changing that variable promotes or rolls back a version without changing the
Render start command. The value is deliberately restricted to versioned Tyler
modules in this repository so configuration cannot import an arbitrary Python
module.
"""

import importlib
import os
import re
import sys


DEFAULT_TYLER_APP_MODULE = "app_v2_15"
_MODULE_NAME_RE = re.compile(r"^app_v\d+(?:_\d+)+$")

# Compatibility template for the legacy base app. The original app.py contains
# the intended LOGIN_HTML assignment in an unreachable indented block after a
# return statement. Version modules still share that Flask app. Installing the
# template here repairs fresh unauthenticated UI requests without changing any
# authentication behavior, API routes, version routing, or maintenance logic.
_FALLBACK_LOGIN_HTML = '''
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tyler AI</title>
<style>
:root{color-scheme:dark;--bg:#07111f;--panel:#0d1a2c;--line:#20324d;--text:#eef6ff;--muted:#91a4bf;--blue:#2563eb}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
body{min-height:100vh;display:grid;place-items:center;padding:20px}
.card{width:min(92vw,420px);background:var(--panel);border:1px solid var(--line);border-radius:24px;padding:28px;box-shadow:0 24px 70px rgba(0,0,0,.35)}
h1{margin:0 0 6px;font-size:30px}.sub{color:var(--muted);margin:0 0 24px}
.input{width:100%;padding:14px 15px;border-radius:14px;border:1px solid #2b4161;background:#081322;color:#fff;font-size:16px;outline:none}
.input:focus{border-color:#4b8cff}.btn{width:100%;margin-top:12px;padding:14px;border:0;border-radius:14px;background:var(--blue);color:#fff;font-weight:700;font-size:16px;cursor:pointer}
.error{background:#3a1520;color:#fecdd3;padding:10px 12px;border-radius:12px;margin-bottom:14px}.tiny{font-size:12px;color:#70839f;margin-top:14px;line-height:1.45}
</style>
</head>
<body>
<form class="card" method="post" action="/ui/login">
<h1>Tyler AI</h1>
<p class="sub">Private assistant access</p>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<input class="input" name="key" type="password" autocomplete="current-password" placeholder="Tyler access key" required autofocus>
<button class="btn" type="submit">Open Tyler AI</button>
<div class="tiny">Your access key is checked by the server and is never embedded in this webpage.</div>
</form>
</body>
</html>
'''


def selected_module_name():
    """Return the validated versioned Tyler module selected for production."""
    value = os.environ.get("TYLER_APP_MODULE", DEFAULT_TYLER_APP_MODULE).strip()
    if not _MODULE_NAME_RE.fullmatch(value):
        raise RuntimeError(
            "Invalid TYLER_APP_MODULE. Expected a versioned Tyler module such "
            "as 'app_v2_15'."
        )
    return value


def _ensure_base_ui_compatibility():
    """Repair the legacy base UI template only when it is actually missing."""
    base_module = sys.modules.get("app")
    if base_module is not None and not getattr(base_module, "LOGIN_HTML", None):
        base_module.LOGIN_HTML = _FALLBACK_LOGIN_HTML


def load_selected_app(module_name=None):
    """Import a validated Tyler version and return its Flask application."""
    name = module_name or selected_module_name()
    if not _MODULE_NAME_RE.fullmatch(name):
        raise RuntimeError(
            "Invalid Tyler application module. Expected a versioned module such "
            "as 'app_v2_15'."
        )
    try:
        module = importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name == name:
            raise RuntimeError(
                f"Configured Tyler application module {name!r} does not exist."
            ) from exc
        raise

    _ensure_base_ui_compatibility()

    application = getattr(module, "app", None)
    if application is None:
        raise RuntimeError(
            f"Configured Tyler application module {name!r} does not export 'app'."
        )
    return module, application


ACTIVE_MODULE = selected_module_name()
ACTIVE_VERSION_MODULE, app = load_selected_app(ACTIVE_MODULE)
VERSION = getattr(ACTIVE_VERSION_MODULE, "VERSION", "unknown")
VERSION_SHORT = getattr(ACTIVE_VERSION_MODULE, "VERSION_SHORT", "unknown")


__all__ = [
    "app",
    "ACTIVE_MODULE",
    "ACTIVE_VERSION_MODULE",
    "VERSION",
    "VERSION_SHORT",
    "DEFAULT_TYLER_APP_MODULE",
    "selected_module_name",
    "load_selected_app",
]
