"""Tyler AI v2.19.3.3 — provider-pinned Gemini training.

Uses Gemini for champion training while leaving normal Tyler AI requests on the
existing Groq path. Every benchmark and training session records its provider and
model, and a session may never continue on a different provider. This preserves
valid score comparisons while extending training beyond Groq's free daily quota.
"""

from contextvars import ContextVar
import os
import re
import types

import app_v2_19_3_2 as v21932
import skill_lab as labmod


v21932.base.VERSION = "2.19.3.3-provider-pinned-gemini-training"
v21932.base.VERSION_SHORT = "v2.19.3.3"

base = v21932.base
app = v21932.app
ENGINE = v21932.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v21932.EXECUTOR
DRILL_EXECUTOR = v21932.DRILL_EXECUTOR
PLANNER = v21932.PLANNER
OPS = v21932.OPS
REVIEW_GATE = v21932.REVIEW_GATE
PROMOTION = v21932.PROMOTION
MERGE_GATE = v21932.MERGE_GATE
SKILL_LAB = v21932.SKILL_LAB
TRAINER = v21932.TRAINER
verify_production = v21932.verify_production
BENCHMARK_OUTPUT_BUDGET = v21932.BENCHMARK_OUTPUT_BUDGET
BENCHMARK_TRANSPORT = v21932.BENCHMARK_TRANSPORT
ITERATIVE_BENCHMARK_OUTPUT_BUDGET = v21932.ITERATIVE_BENCHMARK_OUTPUT_BUDGET
ITERATIVE_CANDIDATE_OUTPUT_TOKENS = v21932.ITERATIVE_CANDIDATE_OUTPUT_TOKENS
MAX_MUTATED_FIELDS = v21932.MAX_MUTATED_FIELDS
MUTATION_ATTEMPT_CATEGORY = v21932.MUTATION_ATTEMPT_CATEGORY
MAX_NOVELTY_OPTIONS = v21932.MAX_NOVELTY_OPTIONS
MUTATION_TRANSPORT = v21932.MUTATION_TRANSPORT
MAX_LOCAL_FALLBACK_OPTIONS = v21932.MAX_LOCAL_FALLBACK_OPTIONS
MUTATION_OUTCOME_CATEGORY = v21932.MUTATION_OUTCOME_CATEGORY
OUTCOME_LEARNING_MODE = v21932.OUTCOME_LEARNING_MODE

TRAINING_PROVIDER = "gemini"
GEMINI_MODEL = re.sub(
    r"[^a-zA-Z0-9._-]", "", os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
) or "gemini-2.5-flash-lite"
GEMINI_TIMEOUT_SECONDS = 90
_TRAINING_PROVIDER_CONTEXT = ContextVar("tyler_training_provider", default=None)


def _gemini_key():
    return str(os.environ.get("GEMINI_API_KEY") or "").strip()


def _message_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(
            str(item.get("text") or "") if isinstance(item, dict) else str(item)
            for item in value
        ).strip()
    return str(value or "")


def _gemini_error(response):
    status = ""
    message = ""
    try:
        error = dict((response.json() or {}).get("error") or {})
        status = re.sub(r"[^A-Z0-9_ -]", "", str(error.get("status") or ""))[:80]
        message = re.sub(r"\s+", " ", str(error.get("message") or "")).strip()[:300]
    except Exception:
        pass
    code = int(getattr(response, "status_code", 0) or 0)
    if code == 429 or status == "RESOURCE_EXHAUSTED":
        return (
            "Gemini's free-tier quota is temporarily exhausted. No training round "
            "was consumed and the current session is preserved. Retry after the "
            "quota window resets."
        )
    detail = ": ".join(item for item in [status, message] if item)
    return f"Gemini training request failed ({code or 'provider error'})" + (
        f": {detail}" if detail else "."
    )


def _gemini_complete(messages, tokens=700, temperature=0.2, json_mode=False):
    """OpenAI-compatible completion adapter for Gemini's REST API."""
    key = _gemini_key()
    if not key:
        raise RuntimeError(
            "Gemini training is not configured. Add GEMINI_API_KEY in Render, "
            "then redeploy."
        )

    system_parts = []
    contents = []
    for message in messages or []:
        item = dict(message or {})
        text = _message_text(item.get("content"))
        if not text:
            continue
        if str(item.get("role") or "").lower() == "system":
            system_parts.append(text)
            continue
        role = "model" if str(item.get("role") or "").lower() == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": text}]})
    if not contents:
        contents.append({"role": "user", "parts": [{"text": "Respond to the task."}]})

    generation = {
        "temperature": max(0.0, min(float(temperature), 2.0)),
        "maxOutputTokens": max(1, min(int(tokens), 8192)),
    }
    if json_mode:
        generation["responseMimeType"] = "application/json"
    payload = {"contents": contents, "generationConfig": generation}
    if system_parts:
        payload["system_instruction"] = {
            "parts": [{"text": "\n\n".join(system_parts)}]
        }

    response = base.requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent",
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        json=payload,
        timeout=GEMINI_TIMEOUT_SECONDS,
    )
    if not getattr(response, "ok", False):
        raise RuntimeError(_gemini_error(response))
    try:
        parts = response.json()["candidates"][0]["content"]["parts"]
        text = "".join(str(part.get("text") or "") for part in parts).strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        text = ""
    if not text:
        raise RuntimeError("Gemini returned no usable training response.")
    return text


_PREVIOUS_ENGINE_COMPLETE = ENGINE.complete


def _provider_routed_complete(messages, tokens=700, temperature=0.2, json_mode=False):
    if _TRAINING_PROVIDER_CONTEXT.get() == TRAINING_PROVIDER:
        return _gemini_complete(
            messages, tokens=tokens, temperature=temperature, json_mode=json_mode
        )
    return _PREVIOUS_ENGINE_COMPLETE(
        messages, tokens=tokens, temperature=temperature, json_mode=json_mode
    )


ENGINE.complete = _provider_routed_complete


_ORIGINAL_LAB_SAVE = SKILL_LAB._save
_ORIGINAL_VALID_EVAL = SKILL_LAB._valid_eval


def _provider_annotated_lab_save(self, category, payload, importance=7):
    clean = dict(payload or {})
    if (
        category == labmod.SKILL_BENCHMARK_RUN_CATEGORY
        and _TRAINING_PROVIDER_CONTEXT.get() == TRAINING_PROVIDER
    ):
        clean.update({
            "evaluation_provider": TRAINING_PROVIDER,
            "evaluation_model": GEMINI_MODEL,
            "provider_consistent": True,
        })
    return _ORIGINAL_LAB_SAVE(category, clean, importance)


def _provider_valid_eval(self, profile, target_kind, candidate_id=None):
    if _TRAINING_PROVIDER_CONTEXT.get() != TRAINING_PROVIDER:
        return _ORIGINAL_VALID_EVAL(profile, target_kind, candidate_id)
    suite = self._suite_hash(profile["skill_id"])
    fingerprint = self._profile_fingerprint(profile)
    for run in self.evaluations(profile["skill_id"], target_kind, 100):
        if run.get("evaluation_provider") != TRAINING_PROVIDER:
            continue
        if run.get("evaluation_model") != GEMINI_MODEL:
            continue
        if run.get("suite_hash") != suite or run.get("profile_fingerprint") != fingerprint:
            continue
        if target_kind == "candidate" and run.get("candidate_id") != candidate_id:
            continue
        return run
    return None


SKILL_LAB._save = types.MethodType(_provider_annotated_lab_save, SKILL_LAB)
SKILL_LAB._valid_eval = types.MethodType(_provider_valid_eval, SKILL_LAB)


_ORIGINAL_VALID_CANDIDATE_RUNS = TRAINER._valid_candidate_runs
_ORIGINAL_SAVE_SESSION = TRAINER._save_session


def _provider_valid_candidate_runs(self, active, candidate):
    runs = _ORIGINAL_VALID_CANDIDATE_RUNS(active, candidate)
    if _TRAINING_PROVIDER_CONTEXT.get() != TRAINING_PROVIDER:
        return runs
    return [
        run for run in runs
        if run.get("evaluation_provider") == TRAINING_PROVIDER
        and run.get("evaluation_model") == GEMINI_MODEL
    ]


def _provider_save_session(self, session, importance=8):
    clean = dict(session or {})
    if _TRAINING_PROVIDER_CONTEXT.get() == TRAINING_PROVIDER:
        clean.update({
            "training_provider": TRAINING_PROVIDER,
            "training_model": GEMINI_MODEL,
            "provider_pinned": True,
        })
    return _ORIGINAL_SAVE_SESSION(clean, importance)


TRAINER._valid_candidate_runs = types.MethodType(
    _provider_valid_candidate_runs, TRAINER
)
TRAINER._save_session = types.MethodType(_provider_save_session, TRAINER)


_ORIGINAL_TRAINER_START = TRAINER.start
_ORIGINAL_TRAINER_ADVANCE = TRAINER.advance


def _restart_required_message():
    return (
        "The current training session predates Gemini provider pinning and cannot "
        "be mixed with Gemini scores. Run: Restart champion training "
        "tyler-ai-developer"
    )


def _gemini_training_start(self, skill_name, restart=False):
    if not _gemini_key():
        raise RuntimeError(
            "Gemini training is not configured. Add GEMINI_API_KEY in Render, "
            "then redeploy."
        )
    active = self.lab.engine.get_skill(skill_name)
    if not active:
        raise ValueError(f"Skill {skill_name!r} was not found.")
    current = self.latest_session(active["skill_id"])
    if current and current.get("status") not in self.TERMINAL and not restart:
        if current.get("training_provider") != TRAINING_PROVIDER:
            raise ValueError(_restart_required_message())
        if current.get("training_model") != GEMINI_MODEL:
            raise ValueError(
                "The configured Gemini model changed during training. Restart "
                "champion training before continuing."
            )
        return current

    token = _TRAINING_PROVIDER_CONTEXT.set(TRAINING_PROVIDER)
    try:
        # A provider-specific active baseline is mandatory before a new session;
        # prior Groq scores must not be used as Gemini's comparison reference.
        self.lab.evaluate(active["skill_id"], "active")
        return _ORIGINAL_TRAINER_START(skill_name, restart=True)
    finally:
        _TRAINING_PROVIDER_CONTEXT.reset(token)


def _gemini_training_advance(self, skill_name):
    session = self.latest_session(skill_name)
    if session and session.get("training_provider") != TRAINING_PROVIDER:
        raise ValueError(_restart_required_message())
    if session and session.get("training_model") != GEMINI_MODEL:
        raise ValueError(
            "The configured Gemini model changed during training. Restart champion "
            "training before continuing."
        )
    token = _TRAINING_PROVIDER_CONTEXT.set(TRAINING_PROVIDER)
    try:
        return _ORIGINAL_TRAINER_ADVANCE(skill_name)
    finally:
        _TRAINING_PROVIDER_CONTEXT.reset(token)


TRAINER.start = types.MethodType(_gemini_training_start, TRAINER)
TRAINER.advance = types.MethodType(_gemini_training_advance, TRAINER)


_PREVIOUS_STATUS = app.view_functions.get("status")


def status_v21933():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    data["training_provider"] = TRAINING_PROVIDER
    data["training_model"] = GEMINI_MODEL
    data["gemini_training_configured"] = bool(_gemini_key())
    data["provider_pinned_training_enabled"] = True
    data["normal_request_provider_unchanged"] = True
    data["automatic_skill_activation_enabled"] = False
    capabilities = data.setdefault("capabilities", [])
    for item in [
        "gemini_training_provider",
        "provider_pinned_benchmarks",
        "provider_consistent_champion_sessions",
    ]:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions["status"] = status_v21933

_ORIGINAL_SAFE_SOURCE_FILES = v21932._safe_source_files_v21932


def _safe_source_files_v21933():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_3_3.py"]))


v21932.v21931.v2193.v219231.v21923.v21922.v21921.v2192.v2191.v219.v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v21933
EXECUTOR.safe_source_files_fn = _safe_source_files_v21933


__all__ = [
    "app", "base", "ENGINE", "VERSION", "VERSION_SHORT", "EXECUTOR",
    "DRILL_EXECUTOR", "PLANNER", "OPS", "REVIEW_GATE", "PROMOTION",
    "MERGE_GATE", "SKILL_LAB", "TRAINER", "verify_production",
    "BENCHMARK_OUTPUT_BUDGET", "BENCHMARK_TRANSPORT",
    "ITERATIVE_BENCHMARK_OUTPUT_BUDGET", "ITERATIVE_CANDIDATE_OUTPUT_TOKENS",
    "MAX_MUTATED_FIELDS", "MUTATION_ATTEMPT_CATEGORY", "MAX_NOVELTY_OPTIONS",
    "MUTATION_TRANSPORT", "MAX_LOCAL_FALLBACK_OPTIONS",
    "MUTATION_OUTCOME_CATEGORY", "OUTCOME_LEARNING_MODE", "TRAINING_PROVIDER",
    "GEMINI_MODEL", "GEMINI_TIMEOUT_SECONDS", "_gemini_complete",
    "_provider_routed_complete", "_provider_valid_eval",
    "_provider_valid_candidate_runs", "_gemini_training_start",
    "_gemini_training_advance",
]
