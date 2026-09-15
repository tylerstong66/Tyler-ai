import ast
import hashlib
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

import requests


MAINTENANCE_PLAN_CATEGORY = 'maintenance_plan'
MAINTENANCE_PLAN_SCHEMA = 'tyler_maintenance_plan_v1'
DEFAULT_TIMEOUT_SECONDS = 8

SERVICE_TERMS = {
    'groq': ['groq', 'model', 'fallback', 'reason', 'completion'],
    'tavily': ['tavily', 'research', 'search'],
    'supabase': ['supabase', 'memory', 'history', 'persist', 'incident'],
    'n8n': ['n8n', 'email', 'webhook', 'receipt'],
}

SERVICE_FILES = {
    'groq': ['app.py', 'app_v2_9_6.py', 'app_v2_10.py', 'app_v2_10_1.py'],
    'tavily': ['app.py', 'app_v2_10.py'],
    'supabase': ['app.py', 'persistent_health_history.py', 'proactive_operations.py'],
    'n8n': ['app.py', 'app_v2_10.py', 'app_v2_10_1.py', 'proactive_operations.py'],
}


def _utcnow():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.isoformat() if value else None


def _safe_text(value, limit=500):
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    text = re.sub(
        r'(?i)\b(api[_-]?key|token|password|secret|authorization)\s*[:=]\s*[^,;|]+',
        r'\1=<redacted>',
        text,
    )
    text = re.sub(r'(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+', 'Bearer <redacted>', text)
    return text[:limit]


def maintenance_plan_id_for(incident_id):
    digest = hashlib.sha256(str(incident_id or '').upper().encode('utf-8')).hexdigest()[:10].upper()
    return f'MNT-{digest}'


def _function_index(path):
    try:
        text = Path(path).read_text(encoding='utf-8', errors='replace')
        tree = ast.parse(text, filename=str(path))
    except Exception:
        return []
    names = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(node.name)
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    names.append(f'{node.name}.{child.name}')
    return names


def verified_affected_code(service, safe_source_files, source_root=None):
    source_root = Path(source_root or Path(__file__).resolve().parent)
    safe = set(safe_source_files or [])
    preferred = [name for name in SERVICE_FILES.get(service, []) if name in safe]
    if not preferred:
        preferred = sorted(name for name in safe if name.endswith('.py'))[:6]

    terms = SERVICE_TERMS.get(service, [service])
    output = []
    for name in preferred:
        functions = _function_index(source_root / name)
        matched = [fn for fn in functions if any(term in fn.lower() for term in terms)]
        output.append({
            'file': name,
            'functions': matched[:12],
            'verified_present': True,
        })
    return output[:8]


def likely_cause(incident):
    incident = dict(incident or {})
    kind = str(incident.get('kind') or '')
    service = str(incident.get('service') or 'dependency')
    diagnostics = dict(incident.get('diagnostics') or {})
    live = dict(diagnostics.get('live') or {})
    history = dict(diagnostics.get('history') or {})
    error_category = _safe_text(live.get('last_error_category'), 100)

    if kind == 'unknown_external_outcome':
        return (
            f'The {service} request may have crossed the external side-effect boundary, but Tyler does not have '
            'a confirmed downstream receipt. The real-world outcome must be verified before any retry.'
        )
    if kind == 'latency_regression':
        return (
            f'{service} latency has materially worsened relative to persisted history. '
            f"Recent p95={live.get('p95_latency_ms')} ms; historical p95={history.get('p95_latency_ms')} ms. "
            'The cause could be provider-side, payload/model-related, or local request-path growth and requires evidence before changes.'
        )
    if kind == 'historical_reliability':
        return (
            f'{service} has a recurring reliability pattern across persisted observations '
            f"({history.get('failure_samples', 0)} failure samples). The dominant repeatable failure mode should be isolated before patching."
        )
    if kind in {'live_unhealthy', 'live_degraded'}:
        suffix = f' Last safe error category: {error_category}.' if error_category else ''
        return (
            f'{service} is currently reporting {live.get("state") or kind.replace("live_", "")}. '
            'The immediate cause is not assumed; correlate the live signal with the most recent deploy/configuration/provider evidence.'
            + suffix
        )
    return (
        f'The incident identifies a {service} operational problem, but the exact root cause is not yet verified. '
        'Use the recorded diagnostics and source evidence before making a change.'
    )


def patch_strategy(incident, affected_code):
    service = str((incident or {}).get('service') or '')
    kind = str((incident or {}).get('kind') or '')
    files = [item.get('file') for item in affected_code if item.get('file')]

    if kind == 'unknown_external_outcome':
        return {
            'strategy': 'Do not patch or retry first. Verify the downstream outcome and receipt path before deciding whether code needs to change.',
            'changes': [
                'Inspect the existing receipt-verification and unknown-outcome handling path.',
                'If the downstream action completed, reconcile the receipt/state without repeating the side effect.',
                'If the action definitely did not complete, prepare a single explicit retry for approval.',
                'Only propose code changes if the verified failure exposes a deterministic gap in receipt handling.',
            ],
            'candidate_files': files,
        }

    changes = [
        'Reproduce the verified failure in a test before changing production behavior.',
        'Modify the smallest verified function/path responsible for the failure.',
        'Preserve existing safety gates, receipt validation, passive telemetry, and source grounding.',
        'Add a regression test that fails before the patch and passes after it.',
    ]
    if service == 'groq':
        changes.append('Preserve adaptive model discovery/fallback and do not hard-code a preview model as the only fallback.')
    elif service == 'tavily':
        changes.append('Keep research failures isolated from unrelated chat paths and avoid artificial probe traffic.')
    elif service == 'supabase':
        changes.append('Keep persistence best-effort where designed so telemetry/history failures cannot break the user request.')
    elif service == 'n8n':
        changes.append('Preserve deterministic Gmail receipt requirements and never auto-retry an uncertain external email outcome.')

    return {
        'strategy': f'Prepare a minimal reversible {service or "dependency"} fix only after the root cause is verified.',
        'changes': changes,
        'candidate_files': files,
    }


def test_plan_for(incident):
    service = str((incident or {}).get('service') or '')
    kind = str((incident or {}).get('kind') or '')
    tests = [
        'Run the complete existing Tyler AI regression suite.',
        'Run a targeted unit/regression test for the verified failure mode.',
        'Smoke-import the new application version and verify /health remains a side-effect-free liveness endpoint.',
        'Verify no credentials, raw secrets, or unsafe diagnostic text are exposed.',
    ]
    if service == 'n8n' or kind == 'unknown_external_outcome':
        tests.extend([
            'Verify confirmed n8n/Gmail receipts are accepted exactly once.',
            'Verify timeout/unknown-outcome paths never auto-retry the email action.',
        ])
    if service == 'groq':
        tests.append('Verify inaccessible/model-not-found/tool-call failures move to an accessible text-only fallback without duplicate side effects.')
    if service == 'supabase':
        tests.append('Verify a persistence/history write failure does not break the original user response.')
    if service == 'tavily':
        tests.append('Verify research failure does not trigger unrelated external actions or fake a successful research result.')
    return tests


def rollback_plan():
    return [
        'Keep the currently verified stable Render start command/version recorded before deployment.',
        'Deploy the proposed change as a new versioned app module rather than overwriting the stable module.',
        'If smoke/regression checks fail, immediately restore the previous Render start command.',
        'After rollback, verify /health and one safe user request before further changes.',
    ]


def deployment_plan():
    return [
        'Create a new versioned application module and focused regression tests.',
        'Commit the proposed patch to GitHub.',
        'Require all CI and smoke tests to pass.',
        'Request explicit approval before changing Render production configuration/start command.',
        'After approval, deploy the new module and verify the displayed version plus /health.',
        'Exercise only the minimum safe production test needed to confirm the fix.',
        'Keep the prior version available for immediate rollback.',
    ]


class MaintenancePlanner:
    def __init__(
        self,
        incident_loader,
        safe_source_files_fn,
        supabase_url_fn,
        headers_fn,
        version_fn,
        source_root=None,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        now_fn=None,
    ):
        self.incident_loader = incident_loader
        self.safe_source_files_fn = safe_source_files_fn
        self.supabase_url_fn = supabase_url_fn
        self.headers_fn = headers_fn
        self.version_fn = version_fn
        self.source_root = Path(source_root or Path(__file__).resolve().parent)
        self.timeout_seconds = max(2, min(int(timeout_seconds), 30))
        self.now_fn = now_fn or _utcnow
        self._lock = threading.RLock()
        self._plans_prepared = 0
        self._last_error_category = None

    def configured(self):
        try:
            return bool(self.supabase_url_fn() and self.headers_fn())
        except Exception:
            return False

    def status(self):
        with self._lock:
            return {
                'configured': self.configured(),
                'plans_prepared_this_process': int(self._plans_prepared),
                'last_error_category': self._last_error_category,
                'automatic_code_changes_enabled': False,
                'automatic_deployment_enabled': False,
                'automatic_configuration_changes_enabled': False,
                'approval_required_before_execution': True,
            }

    def _post_memory(self, payload, importance=7):
        if not self.configured():
            return False
        try:
            response = requests.post(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers={**self.headers_fn(), 'Prefer': 'return=minimal'},
                json={
                    'memories': json.dumps(payload, separators=(',', ':'), sort_keys=True),
                    'category': MAINTENANCE_PLAN_CATEGORY,
                    'importance': max(1, min(int(importance), 10)),
                },
                timeout=self.timeout_seconds,
            )
            if response.ok:
                self._last_error_category = None
                return True
            self._last_error_category = f'http_{response.status_code}'
        except requests.Timeout:
            self._last_error_category = 'timeout'
        except Exception:
            self._last_error_category = 'write_error'
        return False

    def _load_rows(self, limit=50):
        if not self.configured():
            return []
        try:
            response = requests.get(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers=self.headers_fn(),
                params={
                    'select': 'id,created_at,memories',
                    'category': f'eq.{MAINTENANCE_PLAN_CATEGORY}',
                    'order': 'created_at.desc',
                    'limit': max(1, min(int(limit), 100)),
                },
                timeout=self.timeout_seconds,
            )
            if not response.ok:
                return []
            output = []
            for row in response.json() or []:
                try:
                    item = json.loads(str(row.get('memories') or ''))
                except Exception:
                    continue
                if isinstance(item, dict):
                    item['row_id'] = row.get('id')
                    item['stored_at'] = row.get('created_at')
                    output.append(item)
            return output
        except Exception:
            return []

    def build_plan(self, incident):
        incident = dict(incident or {})
        incident_id = str(incident.get('incident_id') or '').upper()
        service = str(incident.get('service') or '')
        safe_files = list(self.safe_source_files_fn() or [])
        affected = verified_affected_code(service, safe_files, source_root=self.source_root)
        plan = {
            'schema': MAINTENANCE_PLAN_SCHEMA,
            'maintenance_plan_id': maintenance_plan_id_for(incident_id),
            'incident_id': incident_id,
            'incident_status': incident.get('status'),
            'service': service,
            'severity': incident.get('severity'),
            'kind': incident.get('kind'),
            'title': _safe_text(incident.get('title'), 180),
            'prepared_at': _iso(self.now_fn()),
            'version': str(self.version_fn() or ''),
            'status': 'prepared',
            'source_grounded': True,
            'verified_source_files': [item['file'] for item in affected],
            'affected_code': affected,
            'likely_cause': likely_cause(incident),
            'proposed_patch': patch_strategy(incident, affected),
            'test_plan': test_plan_for(incident),
            'rollback_plan': rollback_plan(),
            'deployment_plan': deployment_plan(),
            'approval_required_before_execution': True,
            'automatic_changes_performed': False,
            'automatic_deployment_performed': False,
            'automatic_configuration_changes_performed': False,
            'unsafe_retry_performed': False,
        }
        return plan

    def prepare_for_incident(self, incident_id, persist=True):
        incident = self.incident_loader(str(incident_id or '').upper())
        if not incident:
            return {'success': False, 'error': 'incident_not_found', 'plan': None, 'saved': False}
        if incident.get('simulation'):
            return {'success': False, 'error': 'simulation_incident_not_planned', 'plan': None, 'saved': False}
        plan = self.build_plan(incident)
        saved = self._post_memory(plan, importance=8) if persist else False
        with self._lock:
            self._plans_prepared += 1
        return {'success': True, 'plan': plan, 'saved': bool(saved)}

    def recent_plans(self, limit=20):
        latest = {}
        for item in self._load_rows(limit=max(20, int(limit) * 3)):
            plan_id = str(item.get('maintenance_plan_id') or '')
            if plan_id and plan_id not in latest:
                latest[plan_id] = item
        return list(latest.values())[:max(1, min(int(limit), 50))]

    def plan(self, plan_or_incident_id):
        target = str(plan_or_incident_id or '').strip().upper()
        for item in self.recent_plans(limit=50):
            if str(item.get('maintenance_plan_id') or '').upper() == target:
                return item
            if str(item.get('incident_id') or '').upper() == target:
                return item
        return None
