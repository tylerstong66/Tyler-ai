"""Tyler AI v2.19.3.6: provider receipts and a controlled fallback drill.

Every successful model-backed response receives a safe routing receipt. The
authenticated drill simulates a retryable Groq failure locally, sends one small
real Gemini request through the production fallback path, and never invokes
Groq, agent tools, email, n8n, memory actions, or other business side effects.
Passive dependency telemetry remains enabled.
"""

from contextvars import ContextVar
import re
import threading

import app_v2_19_3_5 as v21935
from dependency_observability import classify_error


v21935.base.VERSION = "2.19.3.6-provider-receipts-fallback-drill"
v21935.base.VERSION_SHORT = "v2.19.3.6"

base = v21935.base
app = v21935.app
ENGINE = v21935.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v21935.EXECUTOR


_PROVIDER_ROUTING = ContextVar("tyler_provider_routing", default=None)
_DRILL_LOCK = threading.RLock()
_DRILL_STATS = {
    "runs": 0,
    "passes": 0,
    "failures": 0,
    "last_result": None,
}


def _routing_receipt(provider, mode, reason=None, verified=True):
    receipt = {
        "provider": str(provider or "unknown")[:20],
        "mode": str(mode or "primary")[:30],
        "verified": bool(verified),
    }
    if reason:
        receipt["reason"] = str(reason)[:40]
    return receipt


_ORIGINAL_TRY_RUNTIME_FALLBACK = v21935._try_runtime_fallback


def _try_runtime_fallback_with_receipt(
    error, messages, tokens, temperature, json_mode
):
    reason = v21935._runtime_fallback_reason(error) or "provider_error"
    result = _ORIGINAL_TRY_RUNTIME_FALLBACK(
        error, messages, tokens, temperature, json_mode
    )
    _PROVIDER_ROUTING.set(
        _routing_receipt("gemini", "runtime_fallback", reason=reason)
    )
    return result


v21935._try_runtime_fallback = _try_runtime_fallback_with_receipt


_PREVIOUS_NORMAL_ROUTER = base.groq
_PREVIOUS_ENGINE_ROUTER = ENGINE.complete


def groq_with_provider_receipt(messages, tokens=700, temperature=0.2, json_mode=False):
    result = _PREVIOUS_NORMAL_ROUTER(
        messages,
        tokens=tokens,
        temperature=temperature,
        json_mode=json_mode,
    )
    if _PROVIDER_ROUTING.get() is None:
        _PROVIDER_ROUTING.set(_routing_receipt("groq", "primary"))
    return result


def engine_complete_with_provider_receipt(
    messages, tokens=700, temperature=0.2, json_mode=False
):
    result = _PREVIOUS_ENGINE_ROUTER(
        messages,
        tokens=tokens,
        temperature=temperature,
        json_mode=json_mode,
    )
    if _PROVIDER_ROUTING.get() is None:
        provider = (
            "gemini"
            if v21935.v21933._TRAINING_PROVIDER_CONTEXT.get()
            == v21935.v21933.TRAINING_PROVIDER
            else "groq"
        )
        mode = "provider_pinned_training" if provider == "gemini" else "primary"
        _PROVIDER_ROUTING.set(_routing_receipt(provider, mode))
    return result


base.groq = groq_with_provider_receipt
ENGINE.complete = engine_complete_with_provider_receipt


def fallback_drill_request(message):
    text = re.sub(r"\s+", " ", str(message or "")).strip().lower()
    return text in {
        "run runtime fallback drill",
        "run provider fallback drill",
        "run gemini fallback drill",
    }


def _update_drill_stats(passed):
    with _DRILL_LOCK:
        _DRILL_STATS["runs"] += 1
        if passed:
            _DRILL_STATS["passes"] += 1
            _DRILL_STATS["last_result"] = "passed"
        else:
            _DRILL_STATS["failures"] += 1
            _DRILL_STATS["last_result"] = "failed"


def _run_runtime_fallback_drill():
    """Exercise only the real Gemini branch with a locally simulated Groq error."""
    if not v21935._gemini_runtime_configured():
        _update_drill_stats(False)
        result = {
            "passed": False,
            "failure_category": "configuration",
            "groq_failure_simulated": True,
            "real_provider_calls": {"groq": 0, "gemini": 0},
            "business_side_effects_attempted": False,
        }
        reply = (
            "Runtime fallback drill: FAILED\n"
            "Gemini runtime fallback is not configured. No provider request or "
            "business side effect was attempted."
        )
        return base.base_payload(
            "runtime_fallback_drill",
            reply,
            used_tools=["runtime_fallback_drill"],
            success=False,
        ) | {"runtime_fallback_drill": result}, 200

    marker = "TYLER_FALLBACK_OK"
    messages = [
        {
            "role": "system",
            "content": (
                "This is an availability drill. Return exactly "
                f"{marker} and no other text. Do not call or describe tools."
            ),
        },
        {"role": "user", "content": "Confirm fallback availability."},
    ]
    try:
        response = v21935._try_runtime_fallback(
            RuntimeError("429 simulated rate limit for controlled fallback drill"),
            messages,
            24,
            0,
            False,
        )
        normalized = re.sub(r"[^A-Z_]", "", str(response or "").upper())
        passed = normalized == marker
        category = None if passed else "unexpected_response"
    except Exception as exc:
        response = ""
        passed = False
        category = classify_error(exc)

    _update_drill_stats(passed)
    receipt = _PROVIDER_ROUTING.get()
    result = {
        "passed": bool(passed),
        "failure_category": category,
        "groq_failure_simulated": True,
        "real_provider_calls": {"groq": 0, "gemini": 1},
        "business_side_effects_attempted": False,
        "provider_routing": receipt,
    }
    if passed:
        reply = (
            "Runtime fallback drill: PASSED\n"
            "A Groq rate-limit failure was simulated locally. Gemini completed "
            "one real bounded response. Groq, email, n8n, memory actions, and "
            "agent tools were not called."
        )
    else:
        reply = (
            "Runtime fallback drill: FAILED\n"
            f"Safe failure category: {category or 'provider_error'}. "
            "Groq, email, n8n, memory actions, and agent tools were not called."
        )
    payload = base.base_payload(
        "runtime_fallback_drill",
        reply,
        used_tools=["runtime_fallback_drill", "gemini_runtime_fallback"],
        success=bool(passed),
    ) | {
        "runtime_fallback_drill": result,
        "provider_routing": receipt,
    }
    return payload, 200


_PREVIOUS_HANDLE_MESSAGE = base.handle_message


def handle_message_v21936(message):
    token = _PROVIDER_ROUTING.set(None)
    try:
        if fallback_drill_request(message):
            payload, status = _run_runtime_fallback_drill()
        else:
            payload, status = _PREVIOUS_HANDLE_MESSAGE(message)
        output = dict(payload or {})
        receipt = _PROVIDER_ROUTING.get()
        if receipt:
            output["provider_routing"] = dict(receipt)
        return output, status
    finally:
        _PROVIDER_ROUTING.reset(token)


base.handle_message = handle_message_v21936


if "runtime_fallback_drill_api_v21936" not in app.view_functions:
    @app.route("/diagnostics/runtime-fallback/drill", methods=["POST"])
    def runtime_fallback_drill_api_v21936():
        if not (base.authorized() or base.ui_logged_in()):
            return base.jsonify({"success": False, "error": "Unauthorized"}), 401
        token = _PROVIDER_ROUTING.set(None)
        try:
            payload, status = _run_runtime_fallback_drill()
            return base.jsonify(payload), status
        finally:
            _PROVIDER_ROUTING.reset(token)


_PROVIDER_UI_JS = r'''
        if(
            meta.provider_routing
        ){
            const routing =
                meta.provider_routing;
            const provider =
                routing.provider === "gemini"
                ? "Gemini fallback"
                : "Groq primary";
            diagnostics.textContent +=
                "\nProvider: "
                + provider;
            if(routing.reason){
                diagnostics.textContent +=
                    " · "
                    + routing.reason;
            }
        }

'''


def _install_provider_receipt_ui(template):
    marker = "        if(\n            meta.memory_result\n        ){"
    if marker not in template:
        raise RuntimeError(
            "Tyler chat template changed; provider receipt UI patch was not applied."
        )
    return template.replace(marker, _PROVIDER_UI_JS + marker, 1)


base.CHAT_HTML = _install_provider_receipt_ui(base.CHAT_HTML)


_PREVIOUS_STATUS = app.view_functions["status"]


def status_v21936():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    with _DRILL_LOCK:
        drill_stats = dict(_DRILL_STATS)
    data["runtime_fallback_drill"] = {
        "enabled": True,
        "authentication_required": True,
        "simulated_groq_calls_per_run": 1,
        "real_groq_calls_per_run": 0,
        "maximum_real_gemini_calls_per_run": 1,
        "business_side_effects_enabled": False,
        **drill_stats,
    }
    capabilities = data.setdefault("capabilities", [])
    for item in [
        "provider_routing_receipts",
        "authenticated_runtime_fallback_drill",
        "zero_groq_call_fallback_drill",
    ]:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions["status"] = status_v21936


_ORIGINAL_SAFE_SOURCE_FILES = v21935._safe_source_files_v21935


def _safe_source_files_v21936():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_3_6.py"]))


v21935.v21934.v21933.v21932.v21931.v2193.v219231.v21923.v21922.v21921.v2192.v2191.v219.v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v21936
EXECUTOR.safe_source_files_fn = _safe_source_files_v21936


__all__ = list(v21935.__all__) + [
    "fallback_drill_request",
    "handle_message_v21936",
    "_run_runtime_fallback_drill",
    "_install_provider_receipt_ui",
    "_safe_source_files_v21936",
    "status_v21936",
]

