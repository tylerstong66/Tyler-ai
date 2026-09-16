"""Tyler AI v2.17.2 — production verification hotfix.

Fixes a false-negative in v2.17.1 where final production verification made an
HTTP request back into the same single-sync-worker Gunicorn service. The
external GitHub deployment workflow already verifies /status and /health. This
layer uses Render's local RENDER_GIT_COMMIT for the final runtime identity and
allows a prior verification_failed record to be safely re-verified.
"""

import app_v2_17_1 as v2171


v2171.base.VERSION = "2.17.2-production-verification-hotfix"
v2171.base.VERSION_SHORT = "v2.17.2"

base = v2171.base
app = v2171.app
ENGINE = v2171.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v2171.EXECUTOR
DRILL_EXECUTOR = v2171.DRILL_EXECUTOR
PLANNER = v2171.PLANNER
OPS = v2171.OPS
REVIEW_GATE = v2171.REVIEW_GATE
PROMOTION = v2171.PROMOTION
MERGE_GATE = v2171.MERGE_GATE


def _runtime_status_local():
    """Return the running Render commit without self-HTTP recursion."""
    return {
        "commit": v2171._runtime_commit(),
        "version": base.VERSION_SHORT,
    }


def verify_production_v2172(deployment_id):
    """Re-verify a dispatched production promotion without calling ourselves.

    The GitHub deployment workflow is the external health authority. A
    successful workflow means it already observed both /status and /health on
    the exact target commit. This final step binds that result to the currently
    running Render instance via RENDER_GIT_COMMIT.
    """
    record = v2171._record(deployment_id)
    if not record:
        return {"success": False, "error": "deployment_not_found"}

    state = str(record.get("status") or "")
    if state == "deployed":
        return {
            "success": True,
            "deployment": record,
            "terminal": True,
            "existing": True,
        }

    # v2.17.1 could persist verification_failed solely because its self-HTTP
    # check timed out on a one-worker Gunicorn process. Permit a deterministic
    # re-check of that terminal-looking state; never redispatch the deployment.
    if state not in {
        "deployment_dispatched",
        "dispatch_outcome_unknown",
        "verification_failed",
    }:
        return {
            "success": False,
            "error": "deployment_not_dispatched",
            "deployment": record,
        }

    run = v2171._find_run(record.get("deployment_id"))
    if not run or run.get("status") != "completed":
        return {
            "success": True,
            "pending": True,
            "deployment": record,
            "workflow_run": run,
        }

    runtime = _runtime_status_local()
    target = v2171._sha(record.get("target_commit_sha"))
    rollback = v2171._sha(record.get("rollback_commit_sha"))

    if run.get("conclusion") == "success" and runtime.get("commit") == target:
        updated = dict(record)
        updated.update(
            {
                "status": "deployed",
                "production_deployment_performed": True,
                "post_deploy_health_verified": True,
                "verified_runtime_commit_sha": target,
                "workflow_run_url": run.get("html_url"),
                "verification_source": "external_workflow_plus_render_git_commit",
                "deployed_at": v2171._iso(v2171._now()),
            }
        )
        return {
            "success": v2171._post(updated),
            "deployment": updated,
            "workflow_run": run,
            "terminal": True,
        }

    if runtime.get("commit") == rollback:
        updated = dict(record)
        updated.update(
            {
                "status": "rolled_back",
                "rollback_performed": True,
                "verified_runtime_commit_sha": rollback,
                "workflow_run_url": run.get("html_url"),
                "verification_source": "external_workflow_plus_render_git_commit",
                "rolled_back_at": v2171._iso(v2171._now()),
            }
        )
        v2171._post(updated)
        return {
            "success": False,
            "error": "deployment_failed_and_rolled_back",
            "deployment": updated,
            "workflow_run": run,
            "terminal": True,
        }

    updated = dict(record)
    updated.update(
        {
            "status": "verification_failed",
            "workflow_run_url": run.get("html_url"),
            "verified_runtime_commit_sha": runtime.get("commit") or "",
            "verification_source": "external_workflow_plus_render_git_commit",
        }
    )
    v2171._post(updated)
    return {
        "success": False,
        "error": "production_verification_failed",
        "deployment": updated,
        "workflow_run": run,
        "terminal": True,
    }


# handle_message_v2171 resolves verify_production through the module globals at
# call time, so replacing the module attribute upgrades the existing chat route
# without duplicating or re-registering Flask endpoints.
v2171.verify_production = verify_production_v2172
verify_production = verify_production_v2172


__all__ = [
    "app",
    "base",
    "ENGINE",
    "VERSION",
    "VERSION_SHORT",
    "EXECUTOR",
    "DRILL_EXECUTOR",
    "PLANNER",
    "OPS",
    "REVIEW_GATE",
    "PROMOTION",
    "MERGE_GATE",
    "verify_production",
]
