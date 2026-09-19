import os
import re
import time
from pathlib import Path

import app_v2_9_7 as v297
from dependency_observability import DependencyObservability


# v2.10 adds passive dependency observability. It never probes external
# services just to decide whether they are healthy; it learns from real calls.
# This avoids extra cost, rate-limit pressure, and accidental side effects.
v297.base.VERSION = '2.10.0-dependency-observability'
v297.base.VERSION_SHORT = 'v2.10.0'

base = v297.base
app = v297.app
ENGINE = v297.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT

TELEMETRY_HISTORY_SIZE = int(os.environ.get('DEPENDENCY_TELEMETRY_HISTORY_SIZE', '50'))
TELEMETRY_STALE_SECONDS = int(os.environ.get('DEPENDENCY_TELEMETRY_STALE_SECONDS', '1800'))
DEPENDENCIES = DependencyObservability(history_size=TELEMETRY_HISTORY_SIZE)


def _configured_dependencies():
    return {
        'groq': bool(base.GROQ_API_KEY),
        'gemini': bool(os.environ.get('GEMINI_API_KEY')),
        'tavily': bool(base.TAVILY_API_KEY),
        'supabase': bool(base.SUPABASE_URL and base.SUPABASE_KEY),
        'n8n': bool(base.N8N_WEBHOOK_URL and base.N8N_WEBHOOK_KEY),
    }


def dependency_snapshot(include_errors=False):
    return DEPENDENCIES.snapshot(
        configured=_configured_dependencies(),
        stale_after_seconds=TELEMETRY_STALE_SECONDS,
        include_errors=include_errors,
    )


def _elapsed_ms(start):
    return max(0, int(round((time.perf_counter() - start) * 1000)))


def _observe_call(service, operation, function, *args, side_effect=False, unknown_outcome_fn=None, **kwargs):
    start = time.perf_counter()
    try:
        result = function(*args, **kwargs)
    except Exception as exc:
        unknown = False
        if unknown_outcome_fn is not None:
            try:
                unknown = bool(unknown_outcome_fn(exc))
            except Exception:
                unknown = False
        DEPENDENCIES.record_failure(
            service,
            operation,
            _elapsed_ms(start),
            exc,
            side_effect=side_effect,
            outcome_unknown=unknown,
        )
        raise
    DEPENDENCIES.record_success(
        service,
        operation,
        _elapsed_ms(start),
        side_effect=side_effect,
    )
    return result


def _n8n_outcome_unknown(exc):
    text = str(exc or '').lower()
    # These failures happen before dispatch, so no real-world outcome exists.
    if any(term in text for term in [
        'n8n_webhook_url is required',
        'n8n_webhook_key is not configured',
        'tyler_default_email is not configured',
    ]):
        return False
    # Once dispatch may have happened, Tyler remains conservative.
    return True


# ---------------------------------------------------------------------------
# Instrument real dependency calls. These wrappers preserve the existing
# behavior and exceptions; they only record bounded in-memory telemetry.
# ---------------------------------------------------------------------------
_ORIGINAL_GROQ = base.groq
_ORIGINAL_TAVILY_SEARCH = base.tavily_search
_ORIGINAL_GET_MEMORIES = base.get_memories
_ORIGINAL_GET_MEMORY = base.get_memory
_ORIGINAL_SAVE_MEMORY = base.save_memory
_ORIGINAL_PATCH_MEMORY_RAW = base.patch_memory_raw
_ORIGINAL_DELETE_MEMORY = base.delete_memory
_ORIGINAL_PERSIST_TASK = base.persist_task
_ORIGINAL_SYNC_CORE_PROJECT_MEMORY = base.sync_core_project_memory
_ORIGINAL_SEND_EMAIL = base.send_email_via_n8n


def groq_observed(messages, tokens=700, temperature=0.2, json_mode=False):
    return _observe_call(
        'groq',
        'completion',
        _ORIGINAL_GROQ,
        messages,
        tokens=tokens,
        temperature=temperature,
        json_mode=json_mode,
    )


def tavily_search_observed(query):
    return _observe_call('tavily', 'search', _ORIGINAL_TAVILY_SEARCH, query)


def get_memories_observed(limit=100, category=None):
    return _observe_call(
        'supabase',
        'get_memories',
        _ORIGINAL_GET_MEMORIES,
        limit,
        category=category,
    )


def get_memory_observed(memory_id):
    return _observe_call('supabase', 'get_memory', _ORIGINAL_GET_MEMORY, memory_id)


def save_memory_observed(text, category='general', importance=5):
    return _observe_call(
        'supabase',
        'save_memory',
        _ORIGINAL_SAVE_MEMORY,
        text,
        category=category,
        importance=importance,
        side_effect=True,
    )


def patch_memory_raw_observed(memory_id, text, category=None, importance=None):
    return _observe_call(
        'supabase',
        'patch_memory',
        _ORIGINAL_PATCH_MEMORY_RAW,
        memory_id,
        text,
        category=category,
        importance=importance,
        side_effect=True,
    )


def delete_memory_observed(memory_id):
    return _observe_call(
        'supabase',
        'delete_memory',
        _ORIGINAL_DELETE_MEMORY,
        memory_id,
        side_effect=True,
    )


def persist_task_observed(task):
    return _observe_call(
        'supabase',
        'persist_task',
        _ORIGINAL_PERSIST_TASK,
        task,
        side_effect=True,
    )


def sync_core_project_memory_observed():
    return _observe_call(
        'supabase',
        'sync_core_project_memory',
        _ORIGINAL_SYNC_CORE_PROJECT_MEMORY,
        side_effect=True,
    )


def send_email_via_n8n_observed(subject, body, to=None):
    return _observe_call(
        'n8n',
        'email_dispatch',
        _ORIGINAL_SEND_EMAIL,
        subject,
        body,
        to=to,
        side_effect=True,
        unknown_outcome_fn=_n8n_outcome_unknown,
    )


base.groq = groq_observed
base.tavily_search = tavily_search_observed
base.get_memories = get_memories_observed
base.get_memory = get_memory_observed
base.save_memory = save_memory_observed
base.patch_memory_raw = patch_memory_raw_observed
base.delete_memory = delete_memory_observed
base.persist_task = persist_task_observed
base.sync_core_project_memory = sync_core_project_memory_observed
base.send_email_via_n8n = send_email_via_n8n_observed


# Skill calls captured base.groq before v2.10 existed. Instrument both the
# primary skill model and the adaptive fallback without changing their logic.
v291 = v297.v296.v291
_ORIGINAL_SKILL_PRIMARY = v291._original_skill_complete
_ORIGINAL_SKILL_FALLBACK = v291._fallback_groq


def _skill_primary_observed(messages, tokens=700, temperature=0.2, json_mode=False):
    return _observe_call(
        'groq',
        'skill_primary_completion',
        _ORIGINAL_SKILL_PRIMARY,
        messages,
        tokens=tokens,
        temperature=temperature,
        json_mode=json_mode,
    )


def _skill_fallback_observed(messages, tokens=700, temperature=0.2, json_mode=False):
    return _observe_call(
        'groq',
        'skill_fallback_completion',
        _ORIGINAL_SKILL_FALLBACK,
        messages,
        tokens=tokens,
        temperature=temperature,
        json_mode=json_mode,
    )


v291._original_skill_complete = _skill_primary_observed
v291._fallback_groq = _skill_fallback_observed


# Include the observability module in future Developer-skill source grounding.
_ORIGINAL_SAFE_SOURCE_FILES = v297._safe_source_files


def _safe_source_files_v210():
    names = list(_ORIGINAL_SAFE_SOURCE_FILES())
    path = Path(__file__).resolve().parent / 'dependency_observability.py'
    if path.is_file() and 'dependency_observability.py' not in names:
        names.append('dependency_observability.py')
    return sorted(set(names))


v297._safe_source_files = _safe_source_files_v210


# ---------------------------------------------------------------------------
# User-facing health summary. This is passive telemetry only; showing health
# never calls Groq, Tavily, Supabase, or n8n.
# ---------------------------------------------------------------------------
def _service_line(name, item):
    label = {
        'groq': 'Groq',
        'gemini': 'Gemini',
        'tavily': 'Tavily',
        'supabase': 'Supabase',
        'n8n': 'n8n',
    }.get(name, name)
    state = item.get('state', 'unknown')
    parts = [f'{label}: {state}']
    if item.get('observed'):
        if item.get('last_latency_ms') is not None:
            parts.append(f"last {item.get('last_latency_ms')} ms")
        rate = item.get('window_success_rate')
        if rate is not None:
            parts.append(f"{round(rate * 100)}% recent success")
        if item.get('last_error_category'):
            parts.append(f"last error: {item.get('last_error_category')}")
        if item.get('last_outcome_unknown'):
            parts.append('external outcome may be unknown')
    elif item.get('configured'):
        parts.append('no real call observed since this process started')
    else:
        parts.append('not configured')
    return ' · '.join(parts)


def dependency_health_payload():
    snapshot = dependency_snapshot(include_errors=False)
    lines = [
        f"Dependency health: {snapshot.get('overall')}",
        'Passive telemetry only — no probe requests were sent.',
        '',
    ]
    for name in ['groq', 'gemini', 'tavily', 'supabase', 'n8n']:
        item = snapshot.get('services', {}).get(name)
        if item:
            lines.append(_service_line(name, item))
    return base.base_payload(
        'dependency_health',
        '\n'.join(lines),
        used_tools=['dependency_telemetry'],
        success=snapshot.get('overall') not in {'unhealthy'},
    ) | {
        'dependency_health': snapshot,
    }


def dependency_health_request(message):
    text = re.sub(r'\s+', ' ', str(message or '')).strip().lower()
    return bool(re.fullmatch(
        r'(?:show\s+)?(?:system|dependency|service)\s+health(?:\s+status)?',
        text,
    ))


_ORIGINAL_HANDLE_MESSAGE = base.handle_message


def handle_message_v210(message):
    if dependency_health_request(message):
        return dependency_health_payload(), 200
    return _ORIGINAL_HANDLE_MESSAGE(message)


base.handle_message = handle_message_v210


# Keep canonical project context current without replacing prior information.
_ORIGINAL_CORE_PROJECT_TEXT = base.core_project_text
_ORIGINAL_PROJECT_REPLY = base.project_reply


def core_project_text_v210():
    return (
        _ORIGINAL_CORE_PROJECT_TEXT()
        + ' Dependency observability records bounded passive telemetry from real '
          'Groq, Gemini, Tavily, Supabase, and n8n operations, including latency, recent '
          'success rate, failure category, and unknown-outcome signals. Health '
          'reporting performs no automatic external probes and does not retry side effects.'
    )


def project_reply_v210():
    return (
        _ORIGINAL_PROJECT_REPLY()
        + '\n\nDependency observability:'
        + '\n- Passive health telemetry from real service calls'
        + '\n- Latency and recent success-rate tracking'
        + '\n- Safe failure categorization without exposing secrets'
        + '\n- Unknown-outcome tracking for external side effects'
        + '\n- No automatic health probes or side-effect retries'
    )


base.core_project_text = core_project_text_v210
base.project_reply = project_reply_v210


# ---------------------------------------------------------------------------
# Existing /health stays a cheap liveness check. /status gains a safe public
# telemetry summary. Detailed sanitized errors require API or UI authentication.
# ---------------------------------------------------------------------------
_PREVIOUS_STATUS_VIEW = base.app.view_functions.get('status')
_PREVIOUS_HEALTH_VIEW = base.app.view_functions.get('health')


def status_v210():
    if _PREVIOUS_STATUS_VIEW is not None:
        response = _PREVIOUS_STATUS_VIEW()
        data = response.get_json() if hasattr(response, 'get_json') else {}
    else:
        data = {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    data['mode'] = 'persistent-multistep-autonomy-plus-skill-training-plus-observability'
    capabilities = data.setdefault('capabilities', [])
    for capability in [
        'dependency_observability',
        'passive_service_health',
        'dependency_latency_metrics',
        'safe_dependency_diagnostics',
    ]:
        if capability not in capabilities:
            capabilities.append(capability)
    tools = data.setdefault('tools', [])
    if 'dependency_telemetry' not in tools:
        tools.append('dependency_telemetry')
    data['dependency_observability'] = dependency_snapshot(include_errors=False)
    return base.jsonify(data)


def health_v210():
    # Render liveness must not fail because a downstream provider is unavailable.
    snapshot = dependency_snapshot(include_errors=False)
    return base.jsonify({
        'status': 'healthy',
        'process': 'alive',
        'version': base.VERSION,
        'version_short': base.VERSION_SHORT,
        'dependency_overall': snapshot.get('overall'),
        'active_probes': False,
    })


base.app.view_functions['status'] = status_v210
base.app.view_functions['health'] = health_v210


if 'dependency_diagnostics_api' not in base.app.view_functions:
    @base.app.route('/diagnostics/dependencies', methods=['GET'])
    def dependency_diagnostics_api():
        if not (base.authorized() or base.ui_logged_in()):
            return base.jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return base.jsonify({
            'success': True,
            'version': base.VERSION,
            'dependency_observability': dependency_snapshot(include_errors=True),
        })


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
    )
