import json
import os

import app_v2_9 as v29


# v2.9.1 keeps the v2.9 skill system but hardens text-only skill calls against
# a known GPT-OSS behavior where the model may attempt a tool call even when no
# tools were supplied to the request.
v29.base.VERSION = '2.9.1-skill-tool-fallback'
v29.base.VERSION_SHORT = 'v2.9.1'

SKILL_FALLBACK_MODEL = os.environ.get(
    'GROQ_SKILL_FALLBACK_MODEL',
    'qwen/qwen3.6-27b',
)

_original_build_context = v29.ENGINE.build_context
_original_skill_complete = v29.ENGINE.complete


def _text_only_context(skill_name, example_limit=8, max_chars=7000):
    """Remove executable-looking tool labels from the model-facing skill prompt."""
    context = _original_build_context(
        skill_name,
        example_limit=example_limit,
        max_chars=max_chars,
    )
    lines = [
        line
        for line in str(context or '').splitlines()
        if not line.startswith('ALLOWED TOOLS:')
    ]
    return '\n'.join(lines)[:max_chars]


def _fallback_groq(messages, tokens=700, temperature=0.2, json_mode=False):
    if not v29.base.GROQ_API_KEY:
        raise RuntimeError('GROQ_API_KEY is not configured')

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

    payload = {
        'model': SKILL_FALLBACK_MODEL,
        'messages': hardened_messages,
        'temperature': temperature,
        'max_completion_tokens': tokens,
    }
    if json_mode:
        payload['response_format'] = {'type': 'json_object'}

    response = v29.base.requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {v29.base.GROQ_API_KEY}',
            'Content-Type': 'application/json',
        },
        json=payload,
        timeout=90,
    )

    try:
        data = response.json()
    except Exception:
        raise RuntimeError(
            f'Groq fallback returned {response.status_code}: {response.text[:500]}'
        )

    if not response.ok:
        error = data.get('error', {})
        if isinstance(error, dict):
            message = error.get('message', str(error))
        else:
            message = str(error)
        raise RuntimeError(message)

    choices = data.get('choices', [])
    if not choices:
        raise RuntimeError('Groq fallback returned no choices')

    message = choices[0].get('message', {}) or {}
    return str(message.get('content', '') or '').strip()


def _skill_complete(messages, tokens=700, temperature=0.2, json_mode=False):
    try:
        return _original_skill_complete(
            messages,
            tokens=tokens,
            temperature=temperature,
            json_mode=json_mode,
        )
    except RuntimeError as exc:
        error_text = str(exc).lower()
        tool_failure = (
            'tool choice is none' in error_text
            or 'tool_use_failed' in error_text
            or 'model called a tool' in error_text
        )
        if not tool_failure:
            raise

        return _fallback_groq(
            messages,
            tokens=tokens,
            temperature=temperature,
            json_mode=json_mode,
        )


v29.ENGINE.build_context = _text_only_context
v29.ENGINE.complete = _skill_complete

# Keep the profile generator text-only too. If GPT-OSS unexpectedly attempts a
# tool call there, v2.9 already falls back to a deterministic local profile.

app = v29.app
base = v29.base
ENGINE = v29.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
    )
