"""Fail-closed authorization decisions for proposed Tyler AI self-improvement.

This policy is intentionally not wired into runtime commands yet. Until an
independent execution gate uses it, it grants NO new operational permissions.
The policy must not be modifiable by the same automation it governs.
"""

from pathlib import PurePosixPath

POLICY_VERSION = "tyler_autonomy_policy_v1"
ROUTINE_ACTIONS = frozenset({"create_branch", "edit_branch", "run_tests", "open_pr"})
MERGE_ACTION = "merge"
HIGH_IMPACT_ACTIONS = frozenset({
    "deploy", "spend", "place_bet", "send_message", "change_credentials",
    "change_permissions", "change_safety_policy", "delete_data", "modify_infrastructure",
})
# Only deliberately isolated, non-production paths can be auto-merged in v1.
LOW_RISK_MERGE_PREFIXES = ("docs/autonomy/", "experiments/autonomy/")
PROTECTED_PREFIXES = (".github/", ".git/", "secrets/", "credentials/")
PROTECTED_FILES = frozenset({
    "autonomy_policy.py", "test_autonomy_policy.py", ".gitignore",
    "requirements.txt", "Dockerfile", "Procfile", "render.yaml",
    "wsgi.py", "gunicorn.conf.py", "SPORTS_BETTING_V1_STATUS.md",
})


def _normalized_path(path):
    """Require a canonical, repo-relative POSIX path (no aliases/traversal)."""
    if not isinstance(path, str) or not path or "\\" in path or "\x00" in path:
        return None
    if path.startswith("/") or path.endswith("/") or ":" in path:
        return None
    if any(part in {"", ".", ".."} for part in path.split("/")):
        return None
    if str(PurePosixPath(path)) != path:
        return None
    return path


def assess_autonomous_change(
    *, action, paths, enabled=False, ci_passed=False,
    exact_head_verified=False, rollback_available=False,
    auto_deploy_disabled=False, external_side_effects=False,
):
    """Return an auditable allow/deny decision. Never performs an action.

    enabled must be a trusted operator-controlled switch, not model text.
    Every real mutating tool must enforce this gate itself, not rely on a
    chatbot prompt to request permission.
    """
    def deny(reason):
        return {"allowed": False, "reason": reason, "policy": POLICY_VERSION}

    if not enabled:
        return deny("autonomy_not_enabled")
    if action in HIGH_IMPACT_ACTIONS:
        return deny("high_impact_action_requires_explicit_approval")
    if action not in ROUTINE_ACTIONS | {MERGE_ACTION}:
        return deny("unrecognized_action")
    if external_side_effects:
        return deny("external_side_effect_requires_explicit_approval")
    if not isinstance(paths, (list, tuple)) or not paths or len(paths) > 20:
        return deny("invalid_change_scope")
    normalized = [_normalized_path(path) for path in paths]
    if any(path is None for path in normalized) or len(set(normalized)) != len(normalized):
        return deny("unsafe_or_duplicate_path")
    if any(path in PROTECTED_FILES or path.startswith(PROTECTED_PREFIXES) or
           any(part.startswith(".env") for part in path.split("/"))
           for path in normalized):
        return deny("protected_path_requires_explicit_approval")
    if action == MERGE_ACTION:
        if not all(path.startswith(LOW_RISK_MERGE_PREFIXES) for path in normalized):
            return deny("production_or_unreviewed_path_requires_explicit_approval")
        if not (ci_passed and exact_head_verified and rollback_available and auto_deploy_disabled):
            return deny("merge_evidence_incomplete")
    return {"allowed": True, "reason": "bounded_routine_action", "policy": POLICY_VERSION}
