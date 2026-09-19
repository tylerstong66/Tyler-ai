"""Tyler AI v2.19.3.5: bounded Groq-to-Gemini runtime fallback.

Normal text generation remains Groq-first. A single Gemini attempt is made only
when Groq fails for a retryable provider reason such as quota/rate limiting,
timeout, connection/provider outage, or model access. Authentication,
configuration, invalid-request, and safety failures are never silently bypassed.
No external side-effect operation is retried by this layer.
"""

import threading

import app_v2_10 as v210
import app_v2_19_3_3 as v21933
import app_v2_19_3_4 as v21934
from dependency_observability import classify_error


v21934.base.VERSION = "2.19.3.5-gemini-runtime-fallback"
v21934.base.VERSION_SHORT = "v2.19.3.5"

base = v21934.base
app = v21934.app
ENGINE = v21934.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v21934.EXECUTOR


_PREVIOUS_NORMAL_GROQ = base.groq
_PREVIOUS_ENGINE_COMPLETE = ENGINE.complete
_FALLBACK_LOCK = threading.RLock()
_FALLBACK_STATS = {
    "attempts": 0,
    "successes": 0,
    "failures": 0,
    "last_reason": None,
}


def _gemini_runtime_configured():
    return bool(v21933._gemini_key())


def _runtime_fallback_reason(error):
    """Return a safe retryable category, or None for non-fallback failures."""
    category = classify_error(error)
    if category in {"rate_limit", "timeout", "unavailable", "model_access"}:
        return category
    if category in {"authentication", "configuration"}:
        return None

    text = str(error or "").lower()
    if any(marker in text for marker in [
        "connection reset",
        "connection aborted",
        "connection refused",
        "remote disconnected",
        "temporary failure in name resolution",
        "service overloaded",
        "server overloaded",
        "provider outage",
    ]):
        return "unavailable"
    if any(marker in text for marker in [
        "no accessible groq fallback model",
        "groq returned no choices",
        "model is no longer available",
        "model not found",
    ]):
        return "model_access"
    return None


def _gemini_runtime_request(messages, tokens=700, temperature=0.2, json_mode=False):
    """Use the proven Gemini adapter while returning runtime-specific errors."""
    try:
        return v21933._gemini_complete(
            messages,
            tokens=tokens,
            temperature=temperature,
            json_mode=json_mode,
        )
    except Exception as exc:
        category = classify_error(exc)
        if category == "rate_limit":
            raise RuntimeError(
                "Gemini runtime fallback quota is temporarily exhausted."
            ) from None
        if category == "timeout":
            raise RuntimeError("Gemini runtime fallback timed out.") from None
        if category in {"unavailable", "model_access"}:
            raise RuntimeError(
                f"Gemini runtime fallback is unavailable ({category})."
            ) from None
        if category == "configuration":
            raise RuntimeError("Gemini runtime fallback is not configured.") from None
        raise RuntimeError("Gemini runtime fallback failed (provider_error).") from None


def _observed_gemini_runtime(messages, tokens=700, temperature=0.2, json_mode=False):
    return v210._observe_call(
        "gemini",
        "runtime_fallback_completion",
        _gemini_runtime_request,
        messages,
        tokens=tokens,
        temperature=temperature,
        json_mode=json_mode,
    )


def _fallback_stats_update(reason, outcome=None):
    with _FALLBACK_LOCK:
        if outcome is None:
            _FALLBACK_STATS["attempts"] += 1
            _FALLBACK_STATS["last_reason"] = str(reason or "provider_error")[:40]
        elif outcome == "success":
            _FALLBACK_STATS["successes"] += 1
        else:
            _FALLBACK_STATS["failures"] += 1


def _try_runtime_fallback(error, messages, tokens, temperature, json_mode):
    reason = _runtime_fallback_reason(error)
    if not reason or not _gemini_runtime_configured():
        raise error

    _fallback_stats_update(reason)
    try:
        result = _observed_gemini_runtime(
            messages,
            tokens=tokens,
            temperature=temperature,
            json_mode=json_mode,
        )
    except Exception as fallback_error:
        _fallback_stats_update(reason, "failure")
        fallback_category = classify_error(fallback_error)
        raise RuntimeError(
            "All configured text providers are temporarily unavailable. "
            f"Groq failed ({reason}); Gemini fallback failed ({fallback_category})."
        ) from None
    _fallback_stats_update(reason, "success")
    return result


def groq_with_gemini_runtime_fallback(
    messages, tokens=700, temperature=0.2, json_mode=False
):
    try:
        return _PREVIOUS_NORMAL_GROQ(
            messages,
            tokens=tokens,
            temperature=temperature,
            json_mode=json_mode,
        )
    except Exception as exc:
        return _try_runtime_fallback(
            exc, messages, tokens, temperature, json_mode
        )


def engine_complete_with_runtime_fallback(
    messages, tokens=700, temperature=0.2, json_mode=False
):
    """Extend normal skill/runtime completions without changing Gemini training."""
    try:
        return _PREVIOUS_ENGINE_COMPLETE(
            messages,
            tokens=tokens,
            temperature=temperature,
            json_mode=json_mode,
        )
    except Exception as exc:
        if v21933._TRAINING_PROVIDER_CONTEXT.get() == v21933.TRAINING_PROVIDER:
            raise
        return _try_runtime_fallback(
            exc, messages, tokens, temperature, json_mode
        )


base.groq = groq_with_gemini_runtime_fallback
ENGINE.complete = engine_complete_with_runtime_fallback


_PREVIOUS_STATUS = app.view_functions["status"]


def status_v21935():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    data["normal_request_provider_unchanged"] = False
    data["normal_request_provider_policy"] = "groq_primary_gemini_fallback"
    with _FALLBACK_LOCK:
        stats = dict(_FALLBACK_STATS)
    data["runtime_provider_fallback"] = {
        "enabled": _gemini_runtime_configured(),
        "primary": "groq",
        "fallback": "gemini",
        "maximum_fallback_attempts_per_completion": 1,
        **stats,
    }
    capabilities = data.setdefault("capabilities", [])
    for item in [
        "automatic_runtime_provider_fallback",
        "bounded_gemini_runtime_fallback",
        "gemini_dependency_telemetry",
    ]:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions["status"] = status_v21935


_ORIGINAL_SAFE_SOURCE_FILES = v21934._safe_source_files_v21934


def _safe_source_files_v21935():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_3_5.py"]))


v21934.v21933.v21932.v21931.v2193.v219231.v21923.v21922.v21921.v2192.v2191.v219.v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v21935
EXECUTOR.safe_source_files_fn = _safe_source_files_v21935


__all__ = list(v21934.__all__) + [
    "_runtime_fallback_reason",
    "_gemini_runtime_request",
    "_observed_gemini_runtime",
    "groq_with_gemini_runtime_fallback",
    "engine_complete_with_runtime_fallback",
    "_safe_source_files_v21935",
    "status_v21935",
]

