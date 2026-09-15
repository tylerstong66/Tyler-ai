import os
import time

import requests

import app_v2_9_5 as v295


# v2.9.6 removes the single-preview-model dependency from the skill fallback.
# Tyler now asks Groq which models the current API key can access, prefers
# text-friendly alternatives, remembers the first model that works, and skips
# unavailable/restricted models instead of failing the whole skill request.
v295.base.VERSION = '2.9.6-adaptive-groq-fallback'
v295.base.VERSION_SHORT = 'v2.9.6'

MODEL_CACHE_TTL_SECONDS = int(os.environ.get('GROQ_MODEL_CACHE_TTL_SECONDS', '600'))
MODEL_LIST_TIMEOUT_SECONDS = int(os.environ.get('GROQ_MODEL_LIST_TIMEOUT_SECONDS', '20'))
MODEL_CALL_TIMEOUT_SECONDS = int(os.environ.get('GROQ_MODEL_CALL_TIMEOUT_SECONDS', '90'))

_MODEL_CACHE = {
    'expires_at': 0.0,
    'ids': None,
}
_WORKING_FALLBACK_MODEL = None


def _base_module():
    return v295.v294.v293.v292.v291.v29.base


def _configured_fallback_model():
    return str(os.environ.get('GROQ_SKILL_FALLBACK_MODEL') or '').strip()


def _preferred_models():
    configured = _configured_fallback_model()
    values = [
        configured,
        'qwen/qwen3.8-27b',
        'qwen/qwen3.6-27b',
        'minimaxai/minimax-m2.7',
        'openai/gpt-oss-120b',
        'openai/gpt-oss-20b',
    ]
    output = []
    seen = set()
    for value in values:
        value = str(value or '').strip()
        if value and value not in seen:
            seen.add(value)
            output.append(value)
    return output


def _groq_headers():
    api_key = _base_module().GROQ_API_KEY
    if not api_key:
        raise RuntimeError('GROQ_API_KEY is not configured')
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }


def _accessible_model_ids(force_refresh=False):
    now = time.time()
    if (
        not force_refresh
        and _MODEL_CACHE.get('ids') is not None
        and now < float(_MODEL_CACHE.get('expires_at') or 0)
    ):
        return set(_MODEL_CACHE['ids'])

    try:
        response = requests.get(
            'https://api.groq.com/openai/v1/models',
            headers=_groq_headers(),
            timeout=MODEL_LIST_TIMEOUT_SECONDS,
        )
        if not response.ok:
            return None
        data = response.json()
        ids = {
            str(item.get('id') or '').strip()
            for item in (data.get('data') or [])
            if isinstance(item, dict) and str(item.get('id') or '').strip()
        }
        _MODEL_CACHE['ids'] = ids
        _MODEL_CACHE['expires_at'] = now + MODEL_CACHE_TTL_SECONDS
        return set(ids)
    except Exception:
        # Model discovery is an optimization, not a hard dependency. When it
        # fails, the caller still tries the preferred model list directly.
        return None


def _candidate_models():
    global _WORKING_FALLBACK_MODEL

    preferred = _preferred_models()
    accessible = _accessible_model_ids()

    candidates = []
    if _WORKING_FALLBACK_MODEL:
        candidates.append(_WORKING_FALLBACK_MODEL)

    if accessible is None:
        candidates.extend(preferred)
    else:
        candidates.extend(model for model in preferred if model in accessible)

        # If the account exposes another text model not in our preferred list,
        # include it after known choices. Avoid audio/whisper-only models.
        for model in sorted(accessible):
            lower = model.lower()
            if (
                model not in candidates
                and 'whisper' not in lower
                and 'speech' not in lower
                and 'tts' not in lower
            ):
                candidates.append(model)

    output = []
    seen = set()
    for model in candidates:
        if model and model not in seen:
            seen.add(model)
            output.append(model)
    return output


def _model_reasoning_effort(model):
    model = str(model or '').lower()
    if model in {'qwen/qwen3.6-27b', 'qwen/qwen3.8-27b'}:
        return 'none'
    if model in {'openai/gpt-oss-20b', 'openai/gpt-oss-120b'}:
        return 'low'
    return None


def _extract_groq_error(response):
    try:
        data = response.json()
    except Exception:
        return f'Groq returned {response.status_code}: {response.text[:500]}'
    error = data.get('error', {}) if isinstance(data, dict) else {}
    if isinstance(error, dict):
        return str(error.get('message') or error)
    return str(error or data)


def _retryable_model_failure(status_code, message):
    text = str(message or '').lower()
    return (
        status_code in {403, 404}
        or 'does not exist' in text
        or 'do not have access' in text
        or 'permission' in text
        or 'model_decommissioned' in text
        or 'tool choice is none' in text
        or 'tool_use_failed' in text
        or 'model called a tool' in text
    )


def _adaptive_fallback_groq(messages, tokens=700, temperature=0.2, json_mode=False):
    global _WORKING_FALLBACK_MODEL

    hardened_messages = [
        {
            'role': 'system',
            'content': (
                'TEXT-ONLY MODE. Do not invoke, simulate, request, or emit any tool '
                'or function call. Return only ordinary assistant text or, when JSON '
                'is requested, only the requested JSON object.'
            ),
        },
        *messages,
    ]

    candidates = _candidate_models()
    if not candidates:
        raise RuntimeError('No Groq text model is available to Tyler AI for skill fallback.')

    failures = []
    for model in candidates:
        payload = {
            'model': model,
            'messages': hardened_messages,
            'temperature': temperature,
            'max_completion_tokens': tokens,
        }
        reasoning_effort = _model_reasoning_effort(model)
        if reasoning_effort:
            payload['reasoning_effort'] = reasoning_effort
        if json_mode:
            payload['response_format'] = {'type': 'json_object'}

        try:
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=_groq_headers(),
                json=payload,
                timeout=MODEL_CALL_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            failures.append(f'{model}: request failed: {str(exc)[:160]}')
            continue

        if not response.ok:
            message = _extract_groq_error(response)
            failures.append(f'{model}: {message[:220]}')
            if _retryable_model_failure(response.status_code, message):
                if _WORKING_FALLBACK_MODEL == model:
                    _WORKING_FALLBACK_MODEL = None
                continue
            raise RuntimeError(message)

        try:
            data = response.json()
        except Exception:
            failures.append(f'{model}: invalid JSON response')
            continue

        choices = data.get('choices', []) if isinstance(data, dict) else []
        if not choices:
            failures.append(f'{model}: no choices returned')
            continue

        message = choices[0].get('message', {}) or {}
        content = str(message.get('content', '') or '').strip()
        if not content:
            failures.append(f'{model}: empty response')
            continue

        _WORKING_FALLBACK_MODEL = model
        return content

    summary = '; '.join(failures[-4:])
    raise RuntimeError(
        'No accessible Groq fallback model completed the Tyler AI skill request. '
        + summary
    )


# app_v2_9_1's _skill_complete resolves _fallback_groq dynamically from its
# module globals, so replacing it here upgrades all later v2.9.x skill calls.
v291 = v295.v294.v293.v292.v291
v291._fallback_groq = _adaptive_fallback_groq


app = v295.app
base = v295.base
ENGINE = v295.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
    )
