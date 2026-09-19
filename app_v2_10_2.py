import os
import re

import app_v2_10_1 as v2101
from persistent_health_history import (
    HEALTH_HISTORY_CATEGORY,
    PersistentHealthHistory,
)


# v2.10.2 persists compact, bounded dependency-health snapshots to Supabase so
# Tyler can analyze reliability/latency across Render restarts. It remains
# passive: no Groq/Tavily/n8n health probes are introduced.
v2101.base.VERSION = '2.10.2-persistent-health-history'
v2101.base.VERSION_SHORT = 'v2.10.2'

base = v2101.base
app = v2101.app
ENGINE = v2101.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
v210 = v2101.v210
DEPENDENCIES = v210.DEPENDENCIES

HEALTH_HISTORY_INTERVAL_SECONDS = int(os.environ.get('HEALTH_HISTORY_INTERVAL_SECONDS', '600'))
HEALTH_HISTORY_MAX_RECORDS = int(os.environ.get('HEALTH_HISTORY_MAX_RECORDS', '1500'))
HEALTH_HISTORY_TIMEOUT_SECONDS = int(os.environ.get('HEALTH_HISTORY_TIMEOUT_SECONDS', '8'))


# Keep telemetry rows out of ordinary user/project memory context.
base.SPECIAL_MEMORY_CATEGORIES.add(HEALTH_HISTORY_CATEGORY)


HISTORY = PersistentHealthHistory(
    supabase_url_fn=lambda: base.SUPABASE_URL,
    headers_fn=base.supabase_headers,
    snapshot_fn=lambda: v210.dependency_snapshot(include_errors=False),
    version_fn=lambda: base.VERSION_SHORT,
    interval_seconds=HEALTH_HISTORY_INTERVAL_SECONDS,
    max_records=HEALTH_HISTORY_MAX_RECORDS,
    timeout_seconds=HEALTH_HISTORY_TIMEOUT_SECONDS,
)


# ---------------------------------------------------------------------------
# Persist after real dependency events. Writes are best effort and bypass the
# observed Supabase wrappers, preventing telemetry recursion. A history failure
# can never turn a successful user operation into a failed one.
# ---------------------------------------------------------------------------
_ORIGINAL_RECORD_SUCCESS = DEPENDENCIES.record_success
_ORIGINAL_RECORD_FAILURE = DEPENDENCIES.record_failure


def _persist_after_observation(reason):
    try:
        HISTORY.maybe_persist(reason=reason)
    except Exception:
        # Persistent history is diagnostics, never business-critical execution.
        pass


def record_success_persistent(service, operation, latency_ms, side_effect=False):
    result = _ORIGINAL_RECORD_SUCCESS(
        service,
        operation,
        latency_ms,
        side_effect=side_effect,
    )
    _persist_after_observation(f'{service}_success')
    return result


def record_failure_persistent(
    service,
    operation,
    latency_ms,
    error,
    side_effect=False,
    outcome_unknown=False,
):
    result = _ORIGINAL_RECORD_FAILURE(
        service,
        operation,
        latency_ms,
        error,
        side_effect=side_effect,
        outcome_unknown=outcome_unknown,
    )
    _persist_after_observation(f'{service}_failure')
    return result


DEPENDENCIES.record_success = record_success_persistent
DEPENDENCIES.record_failure = record_failure_persistent


# Include the history implementation in future verified source grounding.
_ORIGINAL_SAFE_SOURCE_FILES = v210.v297._safe_source_files


def _safe_source_files_v2102():
    names = list(_ORIGINAL_SAFE_SOURCE_FILES())
    if 'persistent_health_history.py' not in names:
        names.append('persistent_health_history.py')
    return sorted(set(names))


v210.v297._safe_source_files = _safe_source_files_v2102


# ---------------------------------------------------------------------------
# User-facing historical health summaries.
# ---------------------------------------------------------------------------
def _history_hours(message):
    text = re.sub(r'\s+', ' ', str(message or '')).strip().lower()
    if re.search(r'\b(?:7|seven)\s*days?\b', text) or 'week' in text:
        return 24 * 7
    if re.search(r'\b(?:30|thirty)\s*days?\b', text) or 'month' in text:
        return 24 * 30
    match = re.search(r'\b(\d{1,3})\s*hours?\b', text)
    if match:
        return max(1, min(int(match.group(1)), 24 * 30))
    return 24


def health_history_request(message):
    text = re.sub(r'\s+', ' ', str(message or '')).strip().lower()
    return bool(
        re.search(r'\b(?:health|dependency|service)\s+(?:history|trend|trends)\b', text)
        or re.search(r'\b(?:history|trend|trends)\s+(?:of\s+)?(?:system|dependency|service)\s+health\b', text)
    )


def _trend_label(value):
    return {
        'faster': 'getting faster',
        'slower': 'getting slower',
        'stable': 'latency stable',
        'insufficient_data': 'not enough latency history',
    }.get(value, str(value or 'unknown'))


def health_history_payload(message=''):
    hours = _history_hours(message)
    # Capture the current passive snapshot before summarizing; this is a
    # Supabase history write only, not a service health probe.
    HISTORY.maybe_persist(force=True, reason='history_request')
    summary = HISTORY.summarize(hours=hours, limit=HISTORY.max_records)
    lines = [
        f"Persistent dependency history: last {hours} hours",
        'Historical snapshots from Supabase — no Groq, Gemini, Tavily, or n8n probe requests were sent.',
        f"Stored dependency snapshots in window: {summary.get('samples', 0)}",
        '',
    ]
    labels = {
        'groq': 'Groq', 'gemini': 'Gemini', 'tavily': 'Tavily',
        'supabase': 'Supabase', 'n8n': 'n8n',
    }
    for name in ['groq', 'gemini', 'tavily', 'supabase', 'n8n']:
        item = (summary.get('services') or {}).get(name) or {}
        samples = int(item.get('samples') or 0)
        if not samples:
            lines.append(f"{labels[name]}: not enough persisted history yet")
            continue
        healthy_rate = item.get('healthy_sample_rate')
        healthy_text = f"{round(healthy_rate * 100)}% healthy samples" if healthy_rate is not None else 'health rate unavailable'
        avg = item.get('average_latency_ms')
        p95 = item.get('p95_latency_ms')
        latency_text = 'latency unavailable'
        if avg is not None:
            latency_text = f'avg {avg} ms'
            if p95 is not None:
                latency_text += f' · p95 {p95} ms'
        lines.append(
            f"{labels[name]}: {item.get('latest_state') or 'unknown'} · {healthy_text} across "
            f"{samples} operation checkpoint{'s' if samples != 1 else ''} · "
            f"{latency_text} · {_trend_label(item.get('latency_trend'))} · "
            f"failure samples {item.get('failure_samples', 0)}"
        )
        ignored = int(item.get('ignored_repeated_snapshots') or 0)
        if ignored:
            lines.append(f"  Repeated unchanged snapshots excluded: {ignored}")
        categories = item.get('error_categories') or {}
        if categories:
            category_text = ', '.join(
                f"{name} {count}" for name, count in sorted(categories.items())
            )
            lines.append(f"  Failure categories: {category_text}")
        if item.get('unknown_outcome_samples'):
            lines.append(f"  Unknown external-outcome samples: {item.get('unknown_outcome_samples')}")

    persistence = summary.get('persistence') or HISTORY.status()
    if persistence.get('last_error_category'):
        lines.extend(['', f"History persistence status: degraded ({persistence.get('last_error_category')})"])
    else:
        lines.extend(['', 'History persistence status: healthy'])

    return base.base_payload(
        'dependency_health_history',
        '\n'.join(lines),
        used_tools=['dependency_health_history'],
        success=True,
    ) | {
        'dependency_health_history': summary,
    }


_PREVIOUS_HANDLE_MESSAGE = base.handle_message


def handle_message_v2102(message):
    if health_history_request(message):
        return health_history_payload(message), 200
    return _PREVIOUS_HANDLE_MESSAGE(message)


base.handle_message = handle_message_v2102


# ---------------------------------------------------------------------------
# Project self-description and diagnostics endpoints.
# ---------------------------------------------------------------------------
_ORIGINAL_CORE_PROJECT_TEXT = base.core_project_text
_ORIGINAL_PROJECT_REPLY = base.project_reply


def core_project_text_v2102():
    return (
        _ORIGINAL_CORE_PROJECT_TEXT()
        + ' Dependency-health snapshots are persisted to Supabase in a dedicated, '
          'bounded telemetry category at a throttled interval and on meaningful '
          'state changes. This allows cross-restart health and latency trend analysis '
          'without adding external service probes. Health-history persistence is '
          'best effort and can never fail the user operation that produced telemetry.'
    )


def project_reply_v2102():
    return (
        _ORIGINAL_PROJECT_REPLY()
        + '\n\nPersistent health history:'
        + '\n- Compact dependency snapshots stored in Supabase'
        + '\n- Cross-restart latency and reliability trends'
        + '\n- Bounded retention and throttled writes'
        + '\n- Immediate persistence on meaningful health-state changes'
        + '\n- Best-effort diagnostics never break user actions'
        + '\n- No active Groq, Tavily, or n8n health probes'
    )


base.core_project_text = core_project_text_v2102
base.project_reply = project_reply_v2102


_PREVIOUS_STATUS_VIEW = base.app.view_functions.get('status')
_PREVIOUS_HEALTH_VIEW = base.app.view_functions.get('health')


def status_v2102():
    response = _PREVIOUS_STATUS_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    capabilities = data.setdefault('capabilities', [])
    for capability in [
        'persistent_dependency_health_history',
        'cross_restart_dependency_trends',
        'bounded_health_history_retention',
    ]:
        if capability not in capabilities:
            capabilities.append(capability)
    tools = data.setdefault('tools', [])
    if 'dependency_health_history' not in tools:
        tools.append('dependency_health_history')
    data['health_history_persistence'] = HISTORY.status()
    return base.jsonify(data)


def health_v2102():
    response = _PREVIOUS_HEALTH_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    return base.jsonify(data)


base.app.view_functions['status'] = status_v2102
base.app.view_functions['health'] = health_v2102


if 'dependency_history_diagnostics_api' not in base.app.view_functions:
    @base.app.route('/diagnostics/dependencies/history', methods=['GET'])
    def dependency_history_diagnostics_api():
        if not (base.authorized() or base.ui_logged_in()):
            return base.jsonify({'success': False, 'error': 'Unauthorized'}), 401
        try:
            hours = int(base.request.args.get('hours', '24'))
        except Exception:
            hours = 24
        hours = max(1, min(hours, 24 * 30))
        HISTORY.maybe_persist(force=True, reason='history_api')
        return base.jsonify({
            'success': True,
            'version': base.VERSION,
            'version_short': base.VERSION_SHORT,
            'dependency_health_history': HISTORY.summarize(hours=hours, limit=HISTORY.max_records),
        })


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
    )
