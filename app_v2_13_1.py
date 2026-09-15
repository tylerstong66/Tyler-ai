import os
import re
from pathlib import Path

import app_v2_13 as v213


# v2.13.1 adds an explicit, isolated maintenance-planner drill. The drill uses
# a synthetic incident in memory only, never writes a real incident/plan,
# never changes production, and never retries an external side effect.
v213.base.VERSION = '2.13.1-safe-maintenance-planner-drill'
v213.base.VERSION_SHORT = 'v2.13.1'

base = v213.base
app = v213.app
ENGINE = v213.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
PLANNER = v213.PLANNER
OPS = v213.OPS


def _norm(message):
    return re.sub(r'\s+', ' ', str(message or '')).strip().lower()


def maintenance_drill_request(message):
    return _norm(message) in {
        'run maintenance planner test',
        'run maintenance planner drill',
        'run safe maintenance planner test',
        'run safe maintenance planner drill',
        'test maintenance planner',
    }


def _synthetic_incident():
    return {
        'schema': 'tyler_operational_incident_v1',
        'incident_id': 'INC-TEST21301',
        'fingerprint': 'drill:v2.13.1:unknown_n8n_outcome',
        'status': 'open',
        'event': 'raised',
        'service': 'n8n',
        'severity': 'critical',
        'kind': 'unknown_external_outcome',
        'title': 'SIMULATED n8n unknown external outcome',
        'message': (
            'SIMULATION ONLY: an email request may have crossed the side-effect boundary, '
            'but no downstream Gmail receipt is available. No real email was sent.'
        ),
        'simulation': True,
        'diagnostics': {
            'live': {
                'state': 'degraded',
                'configured': True,
                'observed': True,
                'last_latency_ms': 1500,
                'p50_latency_ms': 900,
                'p95_latency_ms': 1500,
                'window_success_rate': 0.5,
                'consecutive_failures': 1,
                'last_error_category': 'simulated_unknown_outcome',
                'last_outcome_unknown': True,
                'total_operations': 2,
            },
            'history': {
                'samples': 4,
                'latest_state': 'healthy',
                'healthy_sample_rate': 1.0,
                'average_latency_ms': 1100,
                'p95_latency_ms': 1500,
                'latency_trend': 'stable',
                'failure_samples': 0,
                'unknown_outcome_samples': 0,
            },
            'evidence': {
                'simulation': True,
                'real_side_effect_occurred': False,
            },
        },
    }


def _verify_plan(plan):
    plan = dict(plan or {})
    affected = list(plan.get('affected_code') or [])
    source_root = Path(__file__).resolve().parent
    verified_files = [str(item.get('file') or '') for item in affected if item.get('verified_present')]
    existing_files = [name for name in verified_files if (source_root / name).is_file()]
    patch = dict(plan.get('proposed_patch') or {})
    strategy_text = (' '.join([str(patch.get('strategy') or '')] + [str(x) for x in (patch.get('changes') or [])])).lower()
    tests_text = ' '.join(str(x) for x in (plan.get('test_plan') or [])).lower()

    checks = {
        'source_grounded': bool(plan.get('source_grounded')),
        'verified_source_present': bool(existing_files) and len(existing_files) == len(verified_files),
        'n8n_source_identified': any('n8n' in name.lower() or name in {'app.py', 'proactive_operations.py'} for name in existing_files),
        'unknown_outcome_requires_verification': 'verify' in strategy_text and 'outcome' in strategy_text,
        'no_blind_retry_strategy': ('do not patch or retry first' in strategy_text) or ('verify the downstream outcome' in strategy_text),
        'tests_cover_no_auto_retry': ('never auto-retry' in tests_text) or ('unknown-outcome' in tests_text),
        'approval_required': bool(plan.get('approval_required_before_execution')),
        'no_automatic_changes': not bool(plan.get('automatic_changes_performed')),
        'no_automatic_deploy': not bool(plan.get('automatic_deployment_performed')),
        'no_automatic_config': not bool(plan.get('automatic_configuration_changes_performed')),
        'no_unsafe_retry': not bool(plan.get('unsafe_retry_performed')),
    }
    return checks, existing_files


def run_maintenance_planner_drill():
    incident = _synthetic_incident()
    plan = PLANNER.build_plan(incident)
    plan['simulation'] = True
    plan['status'] = 'test_only'
    checks, files = _verify_plan(plan)
    passed = all(checks.values())

    lines = [
        'Safe maintenance planner drill complete.',
        'Scenario: SIMULATED n8n unknown external outcome',
        f"Source-grounded plan built: {'yes' if checks.get('source_grounded') else 'no'}",
        f"Verified deployed source identified: {'yes' if checks.get('verified_source_present') else 'no'}",
        f"Outcome verification required before retry: {'yes' if checks.get('unknown_outcome_requires_verification') else 'no'}",
        f"Blind automatic retry prevented: {'yes' if checks.get('no_unsafe_retry') and checks.get('no_blind_retry_strategy') else 'no'}",
        f"Approval required before execution: {'yes' if checks.get('approval_required') else 'no'}",
        'Real incident created: no',
        'Maintenance plan persisted to production history: no',
        'Code changed automatically: no',
        'Production deployed automatically: no',
        'Configuration changed automatically: no',
        'External side effect executed: no',
        '',
        f"Verified affected source: {', '.join(files) if files else 'none'}",
        '',
        f"Result: {'PASS' if passed else 'FAIL'}",
    ]

    if passed:
        lines.append('The planner produced a safe source-grounded maintenance plan without touching production.')
    else:
        failed = [name for name, value in checks.items() if not value]
        lines.append('Failed checks: ' + ', '.join(failed))

    return base.base_payload(
        'maintenance_planner_drill',
        '\n'.join(lines),
        used_tools=['maintenance_planner'],
        success=passed,
    ) | {
        'maintenance_planner_drill': {
            'simulation': True,
            'passed': passed,
            'checks': checks,
            'verified_source_files': files,
            'production_mutation_performed': False,
            'external_side_effect_performed': False,
            'persisted': False,
        },
        'maintenance_plan': plan,
    }


_PREVIOUS_HANDLE_MESSAGE = v213.handle_message_v213


def handle_message_v2131(message):
    if maintenance_drill_request(message):
        payload = run_maintenance_planner_drill()
        return payload, 200 if payload.get('success') else 500
    return _PREVIOUS_HANDLE_MESSAGE(message)


base.handle_message = handle_message_v2131


_ORIGINAL_CORE_PROJECT_TEXT = base.core_project_text
_ORIGINAL_PROJECT_REPLY = base.project_reply


def core_project_text_v2131():
    return (
        _ORIGINAL_CORE_PROJECT_TEXT()
        + ' v2.13.1 includes an explicit non-persistent safe maintenance-planner drill '
          'that builds a source-grounded plan for a synthetic unknown-outcome n8n incident '
          'without creating a real incident, writing production maintenance history, '
          'changing code/configuration, deploying, or executing an external side effect.'
    )


def project_reply_v2131():
    return (
        _ORIGINAL_PROJECT_REPLY()
        + '\n\nSafe maintenance planner drill:'
        + '\n- Explicit command only; never runs automatically'
        + '\n- Uses a synthetic n8n unknown-outcome scenario'
        + '\n- Verifies deployed source grounding and no-blind-retry behavior'
        + '\n- Does not create a real incident or persist a production maintenance plan'
        + '\n- Performs no code, deploy, configuration, or external side-effect action'
    )


base.core_project_text = core_project_text_v2131
base.project_reply = project_reply_v2131


_PREVIOUS_STATUS_VIEW = base.app.view_functions.get('status')
_PREVIOUS_HEALTH_VIEW = base.app.view_functions.get('health')


def status_v2131():
    response = _PREVIOUS_STATUS_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    capabilities = data.setdefault('capabilities', [])
    if 'safe_maintenance_planner_drill' not in capabilities:
        capabilities.append('safe_maintenance_planner_drill')
    return base.jsonify(data)


def health_v2131():
    response = _PREVIOUS_HEALTH_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    return base.jsonify(data)


base.app.view_functions['status'] = status_v2131
base.app.view_functions['health'] = health_v2131


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
