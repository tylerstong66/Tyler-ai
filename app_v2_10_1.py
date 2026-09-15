import re

import app_v2_10 as v210


# v2.10.1 closes two gaps found during live v2.10 testing:
# 1) ordinary chat reasoning now recovers from GPT-OSS spontaneous tool-call
#    failures using the same adaptive text-only Groq fallback as trained skills;
# 2) Tyler-AI-specific implementation/configuration questions are automatically
#    grounded in the source files deployed with the running application.
v210.base.VERSION = '2.10.1-resilient-grounded-chat'
v210.base.VERSION_SHORT = 'v2.10.1'

base = v210.base
app = v210.app
ENGINE = v210.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT


# ---------------------------------------------------------------------------
# Resilient text-only reasoning for ordinary Tyler AI chat.
# ---------------------------------------------------------------------------
_PRIMARY_NORMAL_GROQ = base.groq
_ADAPTIVE_TEXT_FALLBACK = v210._ORIGINAL_SKILL_FALLBACK


def _tool_call_failure(error):
    text = str(error or '').lower()
    return any(
        marker in text
        for marker in [
            'tool choice is none',
            'tool_use_failed',
            'model called a tool',
            'tool call',
            'function call',
        ]
    )


def _observed_text_fallback(messages, tokens=700, temperature=0.2, json_mode=False):
    return v210._observe_call(
        'groq',
        'text_fallback_completion',
        _ADAPTIVE_TEXT_FALLBACK,
        messages,
        tokens=tokens,
        temperature=temperature,
        json_mode=json_mode,
    )


def groq_resilient(messages, tokens=700, temperature=0.2, json_mode=False):
    try:
        return _PRIMARY_NORMAL_GROQ(
            messages,
            tokens=tokens,
            temperature=temperature,
            json_mode=json_mode,
        )
    except Exception as exc:
        # Only the known spontaneous tool-call failure is retried. Network,
        # auth, rate-limit, and other errors preserve their existing behavior.
        if not _tool_call_failure(exc):
            raise
        return _observed_text_fallback(
            messages,
            tokens=tokens,
            temperature=temperature,
            json_mode=json_mode,
        )


base.groq = groq_resilient


# ---------------------------------------------------------------------------
# Automatic local-source grounding for questions about Tyler AI itself.
# This is deliberately narrow so ordinary conversations do not pay the token
# cost of carrying source code they do not need.
# ---------------------------------------------------------------------------
_ORIGINAL_REASON_WITH_CONTEXT = base.reason_with_context

_SELF_IMPLEMENTATION_TERMS = {
    'architecture',
    'code',
    'codebase',
    'source',
    'implementation',
    'implemented',
    'model',
    'models',
    'fallback',
    'configuration',
    'configured',
    'config',
    'environment variable',
    'environment variables',
    'function',
    'functions',
    'module',
    'modules',
    'dependency',
    'dependencies',
    'deployment',
    'render',
    'version',
    'capability',
    'capabilities',
    'tool',
    'tools',
    'memory system',
    'n8n',
    'groq',
    'tavily',
    'supabase',
}


def _normalized(text):
    return re.sub(r'\s+', ' ', str(text or '')).strip().lower()


def _tyler_self_implementation_request(message):
    text = _normalized(message).replace('tlyer', 'tyler').replace('tyelr', 'tyler')
    if not any(term in text for term in ['tyler ai', 'tyler project', 'my ai project']):
        return False
    return any(term in text for term in _SELF_IMPLEMENTATION_TERMS)


def _append_verified_source_context(message, memory_context):
    if not _tyler_self_implementation_request(message):
        return memory_context

    grounding = v210.v297._developer_grounding(message, max_chars=10000)
    if not grounding:
        return memory_context

    existing = str(memory_context or '').strip()
    prefix = (
        'VERIFIED RUNNING-SOURCE CONTEXT (authoritative for current Tyler AI '
        'implementation; prefer this over saved descriptions when they conflict):\n'
    )
    verified = prefix + grounding
    if existing:
        return existing + '\n\n' + verified
    return verified


def reason_with_context_grounded(message, memory_context='', research_context=''):
    grounded_memory = _append_verified_source_context(message, memory_context)
    return _ORIGINAL_REASON_WITH_CONTEXT(
        message,
        memory_context=grounded_memory,
        research_context=research_context,
    )


base.reason_with_context = reason_with_context_grounded


# Keep project self-description current.
_ORIGINAL_CORE_PROJECT_TEXT = base.core_project_text
_ORIGINAL_PROJECT_REPLY = base.project_reply


def core_project_text_v2101():
    return (
        _ORIGINAL_CORE_PROJECT_TEXT()
        + ' Ordinary chat reasoning automatically retries known spontaneous '
          'Groq tool-call failures through an accessible text-only fallback model. '
          'Questions about Tyler AI code, models, configuration, dependencies, or '
          'deployment are automatically grounded in verified source files deployed '
          'with the running application.'
    )


def project_reply_v2101():
    return (
        _ORIGINAL_PROJECT_REPLY()
        + '\n\nReliability and self-knowledge:'
        + '\n- Adaptive text-only fallback for spontaneous Groq tool-call failures'
        + '\n- Automatic deployed-source grounding for Tyler AI implementation questions'
        + '\n- Ordinary unrelated conversations do not load source-code context'
    )


base.core_project_text = core_project_text_v2101
base.project_reply = project_reply_v2101


# Preserve v2.10 status/health behavior while reporting the new version.
_PREVIOUS_STATUS_VIEW = base.app.view_functions.get('status')
_PREVIOUS_HEALTH_VIEW = base.app.view_functions.get('health')


def status_v2101():
    response = _PREVIOUS_STATUS_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    capabilities = data.setdefault('capabilities', [])
    for capability in [
        'resilient_text_model_fallback',
        'automatic_self_source_grounding',
    ]:
        if capability not in capabilities:
            capabilities.append(capability)
    return base.jsonify(data)


def health_v2101():
    response = _PREVIOUS_HEALTH_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    return base.jsonify(data)


base.app.view_functions['status'] = status_v2101
base.app.view_functions['health'] = health_v2101


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(__import__('os').environ.get('PORT', 10000)),
    )
