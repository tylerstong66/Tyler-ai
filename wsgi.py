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


DEFAULT_TYLER_APP_MODULE = "app_v2_15"
_MODULE_NAME_RE = re.compile(r"^app_v\d+(?:_\d+)+$")


def selected_module_name():
    """Return the validated versioned Tyler module selected for production."""
    value = os.environ.get("TYLER_APP_MODULE", DEFAULT_TYLER_APP_MODULE).strip()
    if not _MODULE_NAME_RE.fullmatch(value):
        raise RuntimeError(
            "Invalid TYLER_APP_MODULE. Expected a versioned Tyler module such "
            "as 'app_v2_15'."
        )
    return value


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
