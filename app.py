import os
import re
import json
import hmac
import requests
from datetime import timedelta

from flask import (
    Flask,
    request,
    jsonify,
    render_template_string,
    session,
    redirect,
    url_for,
)

app = Flask(__name__)

# =========================================================
# CONFIG
# =========================================================

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
TYLER_API_KEY = os.environ.get("TYLER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
TYLER_DEFAULT_EMAIL = os.environ.get("TYLER_DEFAULT_EMAIL")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

MAX_AGENT_ACTIONS = 5
VERSION = "2.6-memory-management"
VERSION_SHORT = "v2.6"

app.secret_key = (
    os.environ.get("FLASK_SECRET_KEY")
    or TYLER_API_KEY
    or os.urandom(32)
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)

# =========================================================
# BASIC HELPERS
# =========================================================

def normalize_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def clamp(value, low, high):
    try:
        value = int(value)
    except Exception:
        value = low
    return max(low, min(high, value))


def authorized():
    supplied = request.headers.get("X-Tyler-Key")
    return bool(
        TYLER_API_KEY
        and supplied
        and hmac.compare_digest(supplied, TYLER_API_KEY)
    )


def parse_json_object(text):
    if not text:
        return None

    text = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        str(text).strip(),
        flags=re.I,
    )

    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        try:
            obj = json.loads(text[start:end + 1])
            return obj if isinstance(obj, dict) else None
        except Exception:
            pass

    return None

# =========================================================
# GROQ
# =========================================================

def groq_request(
    messages,
    max_completion_tokens=700,
    temperature=0.2,
    reasoning_effort=None,
    include_reasoning=None,
    response_format=None,
):
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": max_completion_tokens,
    }

    if reasoning_effort is not None:
        payload["reasoning_effort"] = reasoning_effort

    if include_reasoning is not None:
        payload["include_reasoning"] = include_reasoning

    if response_format is not None:
        payload["response_format"] = response_format

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=90,
    )

    try:
        data = response.json()
    except Exception:
        raise RuntimeError(
            f"Groq returned {response.status_code}: {response.text[:500]}"
        )

    if not response.ok:
        error = data.get("error", {})
        if isinstance(error, dict):
            message = error.get("message", str(error))
        else:
            message = str(error)
        raise RuntimeError(message)

    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("Groq returned no choices")

    return str(
        choices[0]
        .get("message", {})
        .get("content", "")
        or ""
    ).strip()


def call_controller(prompt):
    return groq_request(
        [{"role": "user", "content": prompt}],
        max_completion_tokens=220,
        temperature=0.0,
        reasoning_effort="low",
        include_reasoning=False,
        response_format={"type": "json_object"},
    )


def call_reasoner(
    system_prompt,
    user_prompt,
    max_tokens=800,
    temperature=0.2,
):
    return groq_request(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_completion_tokens=max_tokens,
        temperature=temperature,
        reasoning_effort="low",
        include_reasoning=False,
    )

# =========================================================
# SUPABASE MEMORY
# =========================================================

def supabase_headers():
    if not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_KEY is not configured")

    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def get_memories(limit=20):
    if not SUPABASE_URL:
        return []

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/memories",
        headers=supabase_headers(),
        params={
            "select": "id,created_at,memories,category,importance",
            "order": "importance.desc,created_at.desc",
            "limit": limit,
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase read failed: "
            f"{response.status_code} "
            f"{response.text[:500]}"
        )

    return response.json()


def get_memory_by_id(memory_id):
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is not configured")

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/memories",
        headers=supabase_headers(),
        params={
            "select": "id,created_at,memories,category,importance",
            "id": f"eq.{int(memory_id)}",
            "limit": 1,
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase memory read failed: "
            f"{response.status_code} "
            f"{response.text[:500]}"
        )

    rows = response.json()
    return rows[0] if rows else None


def save_memory(
    text,
    category="general",
    importance=5,
):
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is not configured")

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/memories",
        headers={
            **supabase_headers(),
            "Prefer": "return=representation",
        },
        json={
            "memories": text,
            "category": category,
            "importance": clamp(
                importance,
                1,
                10,
            ),
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase save failed: "
            f"{response.status_code} "
            f"{response.text[:500]}"
        )

    return response.json()


def update_memory(
    memory_id,
    text,
    category=None,
    importance=None,
):
    current = get_memory_by_id(memory_id)

    if not current:
        raise RuntimeError(
            f"Memory {memory_id} was not found."
        )

    if str(
        current.get(
            "category",
            "",
        )
    ).lower() == "project_core":
        raise RuntimeError(
            "The canonical project memory is protected and cannot be replaced this way."
        )

    payload = {
        "memories": text,
        "category": (
            category
            or current.get("category")
            or "general"
        ),
        "importance": clamp(
            importance
            if importance is not None
            else current.get("importance", 5),
            1,
            10,
        ),
    }

    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/memories",
        headers={
            **supabase_headers(),
            "Prefer": "return=representation",
        },
        params={
            "id": f"eq.{int(memory_id)}",
        },
        json=payload,
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase memory update failed: "
            f"{response.status_code} "
            f"{response.text[:500]}"
        )

    return response.json()


def delete_memory(memory_id):
    current = get_memory_by_id(memory_id)

    if not current:
        raise RuntimeError(
            f"Memory {memory_id} was not found."
        )

    if str(
        current.get(
            "category",
            "",
        )
    ).lower() == "project_core":
        raise RuntimeError(
            "The canonical project memory is protected and cannot be deleted."
        )

    response = requests.delete(
        f"{SUPABASE_URL}/rest/v1/memories",
        headers={
            **supabase_headers(),
            "Prefer": "return=representation",
        },
        params={
            "id": f"eq.{int(memory_id)}",
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase memory delete failed: "
            f"{response.status_code} "
            f"{response.text[:500]}"
        )

    return {
        "deleted": True,
        "memory": current,
    }


def memory_exists(text):
    target = normalize_text(text).lower()

    try:
        memories = get_memories(100)
    except Exception:
        return False

    return any(
        normalize_text(
            item.get(
                "memories",
                "",
            )
        ).lower()
        == target
        for item in memories
    )


def compact_memory_context(limit=10):
    try:
        memories = get_memories(limit)
    except Exception as exc:
        return f"Memory read failed: {exc}"

    return "\n".join(
        f"- [{item.get('category', 'general')}] "
        f"{normalize_text(item.get('memories', ''))[:300]}"
        for item in memories
    )[:2200]

# =========================================================
# STRUCTURED PROJECT MEMORY
# =========================================================

def core_project_memory_text():
    return (
        "TYLER_AI_CORE_PROFILE_V3 | "
        "Tyler AI is the user's personal autonomous AI assistant project. "
        "Architecture: Python Flask application deployed on Render; Groq provides "
        "AI reasoning and controller decisions; Supabase stores long-term memory; "
        "Tavily provides live web research; n8n handles external actions such as email. "
        "Interfaces: private server-side-session web chat plus a secured API. "
        "Current tools: read memory, research the web, reason, save memory, send email, "
        "and permission-controlled memory management. "
        "Memory management can audit saved memories, preview deletions or replacements, "
        "and only perform destructive changes after explicit confirmation. "
        "Safety: secrets are not intentionally stored as memory; API access is protected; "
        "email, memory writes, replacements, and deletions require user authorization. "
        "Current development state: memory priority, direct website memory saving, "
        "structured project memory, dynamic tool routing, autonomous next-action selection, "
        "and approval-based memory cleanup are implemented. "
        "A decision-logging feedback loop and model fine-tuning are future ideas and are "
        "NOT currently implemented. Long-term goal: become increasingly capable and "
        "autonomous while keeping important actions permission-controlled. "
        f"Current software version: {VERSION}."
    )


def sync_core_project_memory():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {
            "synced": False,
            "reason": "Memory backend is not configured.",
        }

    canonical = core_project_memory_text()

    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/memories",
            headers=supabase_headers(),
            params={
                "select": "id,memories,category,importance",
                "category": "eq.project_core",
                "order": "created_at.desc",
                "limit": 1,
            },
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                f"Supabase core read failed: "
                f"{response.status_code} "
                f"{response.text[:300]}"
            )

        rows = response.json()

        if rows:
            row = rows[0]

            if normalize_text(
                row.get(
                    "memories",
                    "",
                )
            ) == normalize_text(canonical):
                return {
                    "synced": True,
                    "updated": False,
                    "id": row.get("id"),
                }

            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/memories",
                headers={
                    **supabase_headers(),
                    "Prefer": "return=representation",
                },
                params={
                    "id": f"eq.{row.get('id')}",
                },
                json={
                    "memories": canonical,
                    "category": "project_core",
                    "importance": 10,
                },
                timeout=30,
            )

            if not response.ok:
                raise RuntimeError(
                    f"Supabase core update failed: "
                    f"{response.status_code} "
                    f"{response.text[:300]}"
                )

            return {
                "synced": True,
                "updated": True,
                "id": row.get("id"),
            }

        created = save_memory(
            canonical,
            "project_core",
            10,
        )

        return {
            "synced": True,
            "created": True,
            "database_result": created,
        }

    except Exception as exc:
        return {
            "synced": False,
            "reason": str(exc)[:300],
        }


def get_project_memories(limit=30):
    sync_core_project_memory()

    try:
        memories = get_memories(
            max(
                limit,
                50,
            )
        )
    except Exception:
        return []

    selected = []
    seen = set()

    for item in memories:
        category = str(
            item.get(
                "category",
                "general",
            )
            or "general"
        ).lower()

        text = normalize_text(
            item.get(
                "memories",
                "",
            )
        )

        lower = text.lower()

        relevant = (
            category
            in {
                "project_core",
                "project",
            }
            or (
                category == "goal"
                and (
                    "tyler ai"
                    in lower
                    or "autonomous"
                    in lower
                )
            )
        )

        if (
            not relevant
            or not text
            or text.lower()
            in seen
        ):
            continue

        seen.add(
            text.lower()
        )

        selected.append(
            item
        )

    selected.sort(
        key=lambda item: (
            0
            if str(
                item.get(
                    "category",
                    "",
                )
            ).lower()
            == "project_core"
            else 1,
            -clamp(
                item.get(
                    "importance",
                    5,
                ),
                1,
                10,
            ),
        )
    )

    return selected[:limit]


def project_memory_context(limit=12):
    memories = get_project_memories(
        limit
    )

    lines = [
        "CANONICAL PROJECT PROFILE (authoritative):",
        core_project_memory_text(),
    ]

    extras = []

    for item in memories:
        if str(
            item.get(
                "category",
                "",
            )
        ).lower() == "project_core":
            continue

        extras.append(
            f"- [{item.get('category', 'project')}] "
            f"{normalize_text(item.get('memories', ''))[:350]}"
        )

    if extras:
        lines.append(
            "SAVED PROJECT FACTS:"
        )
        lines.extend(
            extras[:6]
        )

    return "\n".join(
        lines
    )[:3600]


def project_recall_reply():
    memories = get_project_memories(
        20
    )

    core_lower = normalize_text(
        core_project_memory_text()
    ).lower()

    extra_facts = []

    for item in memories:
        if str(
            item.get(
                "category",
                "",
            )
        ).lower() == "project_core":
            continue

        text = normalize_text(
            item.get(
                "memories",
                "",
            )
        )

        if (
            text
            and text.lower()
            not in core_lower
        ):
            extra_facts.append(
                text
            )

    lines = [
        "Tyler AI is your personal autonomous AI assistant project.",
        "",
        "Current architecture:",
        "- Python Flask application deployed on Render",
        "- Groq for AI reasoning and controller decisions",
        "- Supabase for long-term memory",
        "- Tavily for live web research",
        "- n8n for external actions such as email",
        "- Private web chat plus a secured API",
        "",
        "Current capabilities:",
        "- Read and save long-term memory",
        "- Research the live web",
        "- Reason over memory and research",
        "- Select its next tool/action dynamically",
        "- Send email when you explicitly authorize it",
        "- Audit, replace, and delete memories with approval",
        "",
        "Current state:",
        f"- Running build {VERSION}",
        "- Structured project memory and direct website memory saving are implemented",
        "- Memory cleanup is approval-controlled; Tyler does not silently delete memories",
        "- Decision logging / feedback-loop fine-tuning is NOT implemented yet",
        "",
        "Long-term goal:",
        "- Become increasingly capable and autonomous while keeping important actions permission-controlled.",
    ]

    if extra_facts:
        lines.extend(
            [
                "",
                "Saved project facts:",
            ]
        )

        lines.extend(
            f"- {fact}"
            for fact
            in extra_facts[:5]
        )

    return "\n".join(
        lines
    )

# =========================================================
# MEMORY AUDIT / MANAGEMENT
# =========================================================

def memory_audit_item(
    item,
    seen_texts=None,
):
    if seen_texts is None:
        seen_texts = set()

    memory_id = item.get("id")
    category = str(
        item.get(
            "category",
            "general",
        )
        or "general"
    ).lower()

    text = normalize_text(
        item.get(
            "memories",
            "",
        )
    )

    lower = text.lower()

    if category == "project_core":
        return {
            "id": memory_id,
            "status": "protected",
            "reason": "Canonical Tyler AI project profile.",
            "recommend_delete": False,
        }

    if lower in seen_texts:
        return {
            "id": memory_id,
            "status": "duplicate",
            "reason": "Exact duplicate of another saved memory.",
            "recommend_delete": True,
        }

    seen_texts.add(lower)

    test_noise_terms = [
        "favorite test color",
        "cobalt blue",
        "top 3 ai-ready laptops",
        "dell pro max 18 plus",
        "laptop recommendation",
    ]

    if any(
        term in lower
        for term
        in test_noise_terms
    ):
        return {
            "id": memory_id,
            "status": "possible_test_noise",
            "reason": "Looks like old testing or laptop-evaluation data rather than core Tyler AI memory.",
            "recommend_delete": True,
        }

    stale_feedback_terms = [
        "decision-logging",
        "decision logging",
        "feedback loop",
        "fine-tune",
        "fine tune",
        "fine-tuning",
        "fine tuning",
    ]

    implemented_terms = [
        "has a",
        "has implemented",
        "is implemented",
        "you have implemented",
        "will iteratively fine-tune",
        "will iteratively fine tune",
    ]

    if (
        any(
            term in lower
            for term
            in stale_feedback_terms
        )
        and any(
            term in lower
            for term
            in implemented_terms
        )
    ):
        return {
            "id": memory_id,
            "status": "possible_conflict",
            "reason": (
                "May conflict with the canonical project profile: "
                "decision logging / feedback-loop fine-tuning is not implemented yet."
            ),
            "recommend_delete": True,
        }

    if lower.startswith(
        "tyler ai recommendation:"
    ):
        return {
            "id": memory_id,
            "status": "old_recommendation",
            "reason": "Saved recommendation, not a permanent project fact.",
            "recommend_delete": False,
        }

    return {
        "id": memory_id,
        "status": "keep",
        "reason": "No obvious duplicate, test-noise, or project-state conflict detected.",
        "recommend_delete": False,
    }


def audit_memories():
    memories = get_memories(
        100
    )

    memories = sorted(
        memories,
        key=lambda item: (
            clamp(
                item.get(
                    "importance",
                    5,
                ),
                1,
                10,
            ),
            str(
                item.get(
                    "created_at",
                    "",
                )
            ),
        ),
        reverse=True,
    )

    seen_texts = set()
    results = []

    for item in memories:
        result = memory_audit_item(
            item,
            seen_texts,
        )

        result.update(
            {
                "category": item.get(
                    "category",
                    "general",
                ),
                "importance": item.get(
                    "importance",
                    5,
                ),
                "text": normalize_text(
                    item.get(
                        "memories",
                        "",
                    )
                ),
            }
        )

        results.append(
            result
        )

    return results


def memory_audit_reply():
    results = audit_memories()

    issues = [
        item
        for item
        in results
        if item.get(
            "status"
        )
        not in {
            "keep",
            "protected",
        }
    ]

    recommended_ids = [
        item["id"]
        for item
        in issues
        if item.get(
            "recommend_delete"
        )
        and item.get(
            "id"
        )
        is not None
    ]

    lines = [
        "Memory audit complete.",
        "",
        f"Checked {len(results)} saved memories.",
    ]

    if not issues:
        lines.extend(
            [
                "",
                "I did not find any obvious duplicates, test noise, or project-state conflicts.",
                "No memories were changed or deleted.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "Memories worth reviewing:",
            ]
        )

        for item in issues[:20]:
            lines.extend(
                [
                    "",
                    f"ID {item.get('id')} · {item.get('status')}",
                    f"Reason: {item.get('reason')}",
                    f"Memory: {item.get('text', '')[:260]}",
                ]
            )

        lines.extend(
            [
                "",
                "Nothing has been deleted.",
            ]
        )

        if recommended_ids:
            id_text = ",".join(
                str(memory_id)
                for memory_id
                in recommended_ids
            )

            lines.extend(
                [
                    "",
                    "Suggested cleanup command:",
                    f"Delete memories {id_text}",
                    "",
                    "Tyler will show a preview first. Deletion still requires a separate confirmation.",
                ]
            )

    return "\n".join(
        lines
    )


def parse_memory_id_list(text):
    matches = re.findall(
        r"\d+",
        text,
    )

    ids = []

    for match in matches:
        value = int(match)

        if value not in ids:
            ids.append(value)

    return ids[:25]


def memory_audit_request(message):
    lower = normalized_intent_text(
        message
    )

    phrases = [
        "review my memories",
        "review my memory",
        "audit my memories",
        "audit my memory",
        "review tyler ai memory",
        "audit tyler ai memory",
        "clean up memory",
        "cleanup memory",
        "find bad memories",
        "find outdated memories",
        "find incorrect memories",
        "show memory cleanup",
    ]

    return any(
        phrase in lower
        for phrase
        in phrases
    )


def delete_preview_request(message):
    lower = normalize_text(
        message
    ).lower()

    return bool(
        re.match(
            r"^delete memor(?:y|ies)\s+\d",
            lower,
        )
    )


def delete_confirm_request(message):
    lower = normalize_text(
        message
    ).lower()

    return bool(
        re.match(
            r"^confirm delete memor(?:y|ies)\s+\d",
            lower,
        )
    )


def replace_preview_request(message):
    return bool(
        re.match(
            r"(?is)^replace memory\s+\d+\s+with\s*:",
            normalize_text(
                message
            ),
        )
    )


def replace_confirm_request(message):
    return bool(
        re.match(
            r"(?is)^confirm replace memory\s+\d+\s+with\s*:",
            normalize_text(
                message
            ),
        )
    )


def parse_replace_request(message):
    normalized = normalize_text(
        message
    )

    match = re.match(
        r"(?is)^(?:confirm\s+)?replace memory\s+(\d+)\s+with\s*:\s*(.+)$",
        normalized,
    )

    if not match:
        return None

    return (
        int(
            match.group(1)
        ),
        match.group(2).strip(),
    )


def preview_memory_delete(memory_ids):
    if not memory_ids:
        return {
            "success": False,
            "reply": "I couldn't find any memory IDs to preview.",
        }

    rows = []
    blocked = []

    for memory_id in memory_ids:
        memory = get_memory_by_id(
            memory_id
        )

        if not memory:
            rows.append(
                {
                    "id": memory_id,
                    "missing": True,
                }
            )
            continue

        if str(
            memory.get(
                "category",
                "",
            )
        ).lower() == "project_core":
            blocked.append(
                memory_id
            )
            continue

        rows.append(
            memory
        )

    lines = [
        "Deletion preview:",
        "",
    ]

    for row in rows:
        if row.get(
            "missing"
        ):
            lines.append(
                f"- ID {row.get('id')}: not found"
            )
        else:
            lines.append(
                f"- ID {row.get('id')}: "
                f"{normalize_text(row.get('memories', ''))[:260]}"
            )

    if blocked:
        lines.extend(
            [
                "",
                "Protected and excluded: "
                + ", ".join(
                    str(memory_id)
                    for memory_id
                    in blocked
                ),
            ]
        )

    deletable_ids = [
        row.get(
            "id"
        )
        for row in rows
        if not row.get(
            "missing"
        )
    ]

    if deletable_ids:
        lines.extend(
            [
                "",
                "Nothing has been deleted yet.",
                "To approve this deletion, send exactly:",
                "Confirm delete memories "
                + ",".join(
                    str(memory_id)
                    for memory_id
                    in deletable_ids
                ),
            ]
        )
    else:
        lines.extend(
            [
                "",
                "There are no deletable memories in this request.",
            ]
        )

    return {
        "success": True,
        "type": "memory_delete_preview",
        "reply": "\n".join(lines),
        "used_tools": [
            "audit_memory",
        ],
        "controller_attempts": 0,
        "controller_successes": 0,
        "priority_decisions": 0,
        "fallback_decisions": 0,
        "reasoning_calls": 0,
        "total_groq_calls": 0,
        "memory_result": {
            "preview": True,
            "deleted": False,
        },
        "email_result": None,
        "sources": [],
    }


def confirm_memory_delete(memory_ids):
    if not memory_ids:
        return {
            "success": False,
            "reply": "I couldn't find any memory IDs to delete.",
        }

    deleted = []
    errors = []

    for memory_id in memory_ids:
        try:
            result = delete_memory(
                memory_id
            )

            deleted.append(
                result.get(
                    "memory",
                    {},
                )
            )
        except Exception as exc:
            errors.append(
                f"ID {memory_id}: {exc}"
            )

    lines = []

    if deleted:
        lines.append(
            "Deleted memories:"
        )

        for item in deleted:
            lines.append(
                f"- ID {item.get('id')}: "
                f"{normalize_text(item.get('memories', ''))[:240]}"
            )

    if errors:
        if lines:
            lines.append("")

        lines.append(
            "Not deleted:"
        )

        lines.extend(
            f"- {error}"
            for error
            in errors
        )

    return {
        "success": bool(
            deleted
        ),
        "type": "memory_delete",
        "reply": "\n".join(
            lines
        )
        or "No memories were deleted.",
        "used_tools": [
            "delete_memory",
        ],
        "controller_attempts": 0,
        "controller_successes": 0,
        "priority_decisions": 0,
        "fallback_decisions": 0,
        "reasoning_calls": 0,
        "total_groq_calls": 0,
        "memory_result": {
            "deleted": bool(
                deleted
            ),
            "deleted_count": len(
                deleted
            ),
        },
        "email_result": None,
        "sources": [],
    }


def preview_memory_replace(
    memory_id,
    new_text,
):
    if looks_sensitive(
        new_text
    ):
        return {
            "success": False,
            "reply": "I won't replace a memory with text that appears to contain sensitive credentials or account data.",
        }

    current = get_memory_by_id(
        memory_id
    )

    if not current:
        return {
            "success": False,
            "reply": f"Memory {memory_id} was not found.",
        }

    if str(
        current.get(
            "category",
            "",
        )
    ).lower() == "project_core":
        return {
            "success": False,
            "reply": "The canonical project memory is protected and cannot be replaced this way.",
        }

    reply = (
        f"Replacement preview for memory {memory_id}:\n\n"
        f"Current:\n{normalize_text(current.get('memories', ''))}\n\n"
        f"New:\n{new_text}\n\n"
        "Nothing has been changed yet.\n"
        "To approve this replacement, send exactly:\n"
        f"Confirm replace memory {memory_id} with: {new_text}"
    )

    return {
        "success": True,
        "type": "memory_replace_preview",
        "reply": reply,
        "used_tools": [
            "audit_memory",
        ],
        "controller_attempts": 0,
        "controller_successes": 0,
        "priority_decisions": 0,
        "fallback_decisions": 0,
        "reasoning_calls": 0,
        "total_groq_calls": 0,
        "memory_result": {
            "preview": True,
            "replaced": False,
        },
        "email_result": None,
        "sources": [],
    }


def confirm_memory_replace(
    memory_id,
    new_text,
):
    if looks_sensitive(
        new_text
    ):
        return {
            "success": False,
            "reply": "I won't store replacement text that appears to contain sensitive credentials or account data.",
        }

    current = get_memory_by_id(
        memory_id
    )

    if not current:
        return {
            "success": False,
            "reply": f"Memory {memory_id} was not found.",
        }

    if str(
        current.get(
            "category",
            "",
        )
    ).lower() == "project_core":
        return {
            "success": False,
            "reply": "The canonical project memory is protected and cannot be replaced this way.",
        }

    category = guess_memory_category(
        new_text
    )

    updated = update_memory(
        memory_id,
        new_text,
        category=category,
        importance=current.get(
            "importance",
            5,
        ),
    )

    return {
        "success": True,
        "type": "memory_replace",
        "reply": (
            f"Replaced memory {memory_id}.\n\n"
            f"New memory: {new_text}"
        ),
        "used_tools": [
            "replace_memory",
        ],
        "controller_attempts": 0,
        "controller_successes": 0,
        "priority_decisions": 0,
        "fallback_decisions": 0,
        "reasoning_calls": 0,
        "total_groq_calls": 0,
        "memory_result": {
            "replaced": True,
            "id": memory_id,
            "database_result": updated,
        },
        "email_result": None,
        "sources": [],
    }

# =========================================================
# INTENT / PERMISSIONS
# =========================================================

def normalized_intent_text(message):
    lower = normalize_text(
        message
    ).lower()

    return (
        lower
        .replace(
            "tlyer",
            "tyler",
        )
        .replace(
            "tyelr",
            "tyler",
        )
    )


def is_personal_tyler_project_reference(message):
    lower = normalized_intent_text(
        message
    )

    terms = [
        "tyler ai",
        "tyler ai project",
        "tyler project",
        "my tyler ai",
        "my ai project",
        "our tyler ai",
        "the tyler ai project",
    ]

    if any(
        term in lower
        for term
        in terms
    ):
        return True

    return bool(
        re.search(
            r"\btyl\w{1,3}\s+(?:ai|project)\b",
            lower,
        )
    )


def needs_memory(message):
    lower = normalized_intent_text(
        message
    )

    if is_personal_tyler_project_reference(
        message
    ):
        return True

    terms = [
        "what you remember",
        "what do you remember",
        "what you know about me",
        "based on what you know",
        "my goals",
        "my goal",
        "my preferences",
        "my preference",
        "my favorite",
        "for me",
        "best fit for me",
    ]

    return any(
        term in lower
        for term
        in terms
    )


def needs_research(message):
    lower = normalized_intent_text(
        message
    )

    terms = [
        "research",
        "latest",
        "current",
        "today",
        "recent",
        "news",
        "look up",
        "search",
        "best current",
        "right now",
        "available now",
    ]

    return any(
        term in lower
        for term
        in terms
    )


def is_simple_project_recall(message):
    if (
        not is_personal_tyler_project_reference(
            message
        )
        or needs_research(
            message
        )
    ):
        return False

    lower = normalized_intent_text(
        message
    )

    phrases = [
        "what do you remember about",
        "what you remember about",
        "what do you know about",
        "what you know about",
        "tell me what you remember about",
        "summarize my tyler ai",
        "summarize tyler ai",
        "describe my tyler ai",
        "describe tyler ai",
        "what is my tyler ai",
        "what is tyler ai",
    ]

    return any(
        phrase in lower
        for phrase
        in phrases
    )


def looks_sensitive(text):
    lower = str(
        text
    ).lower()

    blocked = [
        "password",
        "api key",
        "apikey",
        "secret key",
        "access token",
        "auth token",
        "bearer token",
        "credit card",
        "cvv",
        "social security",
        "ssn",
        "bank account",
        "routing number",
        "private key",
    ]

    return any(
        item in lower
        for item
        in blocked
    )


def user_allows_email(message):
    lower = message.lower()

    deny = [
        "do not email",
        "don't email",
        "dont email",
        "no email",
        "do not send an email",
        "don't send an email",
        "dont send an email",
    ]

    if any(
        item in lower
        for item
        in deny
    ):
        return False

    allow = [
        "email me",
        "email the result",
        "email the results",
        "send me an email",
        "send it to my email",
        "send the result to my email",
        "send the results to my email",
    ]

    return any(
        item in lower
        for item
        in allow
    )


def user_allows_memory_write(message):
    lower = message.lower()

    deny = [
        "do not save",
        "don't save",
        "dont save",
        "do not remember",
        "don't remember",
        "dont remember",
        "no memory",
        "do not store",
        "don't store",
        "dont store",
    ]

    if any(
        item in lower
        for item
        in deny
    ):
        return False

    allow = [
        "remember that",
        "remember this",
        "remember which",
        "remember the recommendation",
        "remember my choice",
        "save to memory",
        "save it to memory",
        "save this to memory",
        "save that recommendation",
        "save the recommendation",
        "save this recommendation",
        "store this",
        "don't forget",
        "do not forget",
    ]

    return any(
        item in lower
        for item
        in allow
    )


def explicit_memory_request(message):
    lower = message.lower().strip()

    patterns = [
        r"^remember that(?:\s+|:\s*)",
        r"^remember this(?:\s+|:\s*)",
        r"^save this to memory(?:\s+|:\s*)",
        r"^save that to memory(?:\s+|:\s*)",
        r"^store this(?:\s+|:\s*)",
        r"^don't forget(?: that)?(?:\s+|:\s*)",
        r"^do not forget(?: that)?(?:\s+|:\s*)",
    ]

    return any(
        re.match(
            pattern,
            lower,
        )
        for pattern
        in patterns
    )


def clean_explicit_memory(message):
    text = message.strip()

    patterns = [
        r"^remember that\s+",
        r"^remember this[:\s]+",
        r"^save this to memory[:\s]+",
        r"^save that to memory[:\s]+",
        r"^store this[:\s]+",
        r"^don't forget(?: that)?\s+",
        r"^do not forget(?: that)?\s+",
    ]

    for pattern in patterns:
        text = re.sub(
            pattern,
            "",
            text,
            flags=re.I,
        )

    return text.strip()


def guess_memory_category(text):
    lower = text.lower()

    if any(
        x in lower
        for x in [
            "favorite",
            "prefer",
            "i like",
        ]
    ):
        return "preference"

    if any(
        x in lower
        for x in [
            "goal",
            "want to become",
        ]
    ):
        return "goal"

    if any(
        x in lower
        for x in [
            "project",
            "building",
            "tyler ai",
        ]
    ):
        return "project"

    if any(
        x in lower
        for x in [
            "job",
            "career",
            "work",
        ]
    ):
        return "career"

    return "general"


def handle_explicit_memory(message):
    memory = clean_explicit_memory(
        message
    )

    if not memory:
        raise RuntimeError(
            "No memory text found."
        )

    if looks_sensitive(
        memory
    ):
        return {
            "success": False,
            "type": "memory",
            "saved": False,
            "error": "Sensitive information will not be stored.",
            "reply": "I did not save that because it may contain sensitive information.",
        }, 400

    if memory_exists(
        memory
    ):
        return {
            "success": True,
            "type": "memory",
            "saved": False,
            "reason": "Memory already exists.",
            "memory": memory,
            "reply": "I already have that saved in memory.",
            "used_tools": [
                "save_memory",
            ],
            "controller_attempts": 0,
            "controller_successes": 0,
            "priority_decisions": 0,
            "fallback_decisions": 0,
            "reasoning_calls": 0,
            "total_groq_calls": 0,
            "sources": [],
            "memory_result": {
                "saved": False,
                "reason": "Memory already exists.",
                "memory": memory,
            },
            "email_result": None,
        }, 200

    category = guess_memory_category(
        memory
    )

    saved = save_memory(
        memory,
        category,
        7,
    )

    return {
        "success": True,
        "type": "memory",
        "saved": True,
        "memory": memory,
        "category": category,
        "reply": f"Saved to memory: {memory}",
        "used_tools": [
            "save_memory",
        ],
        "controller_attempts": 0,
        "controller_successes": 0,
        "priority_decisions": 0,
        "fallback_decisions": 0,
        "reasoning_calls": 0,
        "total_groq_calls": 0,
        "sources": [],
        "memory_result": {
            "saved": True,
            "memory": memory,
            "category": category,
            "importance": 7,
        },
        "email_result": None,
        "database_result": saved,
    }, 200


def project_recall_payload():
    return {
        "success": True,
        "type": "project_memory",
        "version": VERSION,
        "reply": project_recall_reply(),
        "actions": [
            {
                "action": 1,
                "tool": "read_memory",
                "decision": {
                    "decision_source": "structured-project-fast-path",
                    "why": "This is a direct Tyler AI project recall request.",
                },
            }
        ],
        "post_actions": [],
        "used_tools": [
            "read_memory",
        ],
        "memory_result": None,
        "email_result": None,
        "sources": [],
        "controller_attempts": 0,
        "controller_successes": 0,
        "priority_decisions": 1,
        "fallback_decisions": 0,
        "reasoning_calls": 0,
        "total_groq_calls": 0,
        "max_actions": MAX_AGENT_ACTIONS,
        "email_authorized": False,
        "memory_write_authorized": False,
    }


def memory_audit_payload():
    return {
        "success": True,
        "type": "memory_audit",
        "version": VERSION,
        "reply": memory_audit_reply(),
        "actions": [
            {
                "action": 1,
                "tool": "audit_memory",
                "decision": {
                    "decision_source": "memory-management-fast-path",
                    "why": "The user requested a memory review.",
                },
            }
        ],
        "post_actions": [],
        "used_tools": [
            "audit_memory",
        ],
        "memory_result": {
            "audited": True,
            "changed": False,
        },
        "email_result": None,
        "sources": [],
        "controller_attempts": 0,
        "controller_successes": 0,
        "priority_decisions": 1,
        "fallback_decisions": 0,
        "reasoning_calls": 0,
        "total_groq_calls": 0,
        "max_actions": MAX_AGENT_ACTIONS,
        "email_authorized": False,
        "memory_write_authorized": False,
    }

# =========================================================
# TAVILY / N8N
# =========================================================

def web_search(query):
    if not TAVILY_API_KEY:
        raise RuntimeError(
            "TAVILY_API_KEY is not configured"
        )

    response = requests.post(
        "https://api.tavily.com/search",
        headers={
            "Authorization": f"Bearer {TAVILY_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": 4,
        },
        timeout=60,
    )

    try:
        data = response.json()
    except Exception:
        raise RuntimeError(
            f"Tavily returned "
            f"{response.status_code}: "
            f"{response.text[:500]}"
        )

    if not response.ok:
        raise RuntimeError(
            str(
                data
            )
        )

    sources = []

    for item in data.get(
        "results",
        [],
    )[:4]:
        sources.append(
            {
                "title": item.get(
                    "title",
                    "",
                ),
                "url": item.get(
                    "url",
                    "",
                ),
                "content": normalize_text(
                    item.get(
                        "content",
                        "",
                    )
                )[:400],
            }
        )

    return {
        "answer": normalize_text(
            data.get(
                "answer",
                "",
            )
        )[:1100],
        "sources": sources,
    }


def compact_research(research):
    if not research:
        return ""

    pieces = []

    if research.get(
        "answer"
    ):
        pieces.append(
            "SEARCH SUMMARY:\n"
            + research[
                "answer"
            ]
        )

    for index, source in enumerate(
        research.get(
            "sources",
            [],
        )[:4],
        1,
    ):
        pieces.append(
            f"\nSOURCE {index}\n"
            f"Title: {source.get('title', '')}\n"
            f"Info: {source.get('content', '')}"
        )

    return "\n".join(
        pieces
    )[:3300]


def send_to_n8n(payload):
    if not N8N_WEBHOOK_URL:
        raise RuntimeError(
            "N8N_WEBHOOK_URL is not configured"
        )

    response = requests.post(
        N8N_WEBHOOK_URL,
        json=payload,
        timeout=60,
    )

    if not response.ok:
        raise RuntimeError(
            f"n8n returned "
            f"{response.status_code}: "
            f"{response.text[:500]}"
        )

    return response.text


def send_email(
    body,
    subject="Tyler AI Results",
):
    if not TYLER_DEFAULT_EMAIL:
        raise RuntimeError(
            "TYLER_DEFAULT_EMAIL is not configured"
        )

    result = send_to_n8n(
        {
            "action": "email",
            "data": {
                "to": TYLER_DEFAULT_EMAIL,
                "subject": subject,
                "message": body,
            },
        }
    )

    return {
        "sent": True,
        "to": TYLER_DEFAULT_EMAIL,
        "subject": subject,
        "n8n_response": result[:250],
    }

# =========================================================
# CONTROLLER
# =========================================================

ALL_TOOLS = [
    "read_memory",
    "research_web",
    "reason",
    "save_memory",
    "send_email",
    "finish",
]


def available_tools(
    used_tools,
    email_allowed,
    memory_allowed,
    has_final_reply,
    research_needed,
    memory_needed,
):
    tools = []

    for tool in ALL_TOOLS:
        if (
            tool != "finish"
            and tool in used_tools
        ):
            continue

        if (
            tool == "read_memory"
            and not memory_needed
        ):
            continue

        if (
            tool == "research_web"
            and not research_needed
        ):
            continue

        if (
            tool == "save_memory"
            and (
                not memory_allowed
                or not has_final_reply
            )
        ):
            continue

        if (
            tool == "send_email"
            and (
                not email_allowed
                or not has_final_reply
            )
        ):
            continue

        tools.append(
            tool
        )

    if "finish" not in tools:
        tools.append(
            "finish"
        )

    return tools


def validate_controller_choice(
    choice,
    allowed_tools,
):
    if not isinstance(
        choice,
        dict,
    ):
        raise RuntimeError(
            "Controller did not return a JSON object"
        )

    tool = normalize_text(
        choice.get(
            "tool",
            "",
        )
    ).lower()

    if tool not in allowed_tools:
        raise RuntimeError(
            f"Controller chose unavailable tool: {tool}"
        )

    return {
        "tool": tool,
        "instruction": normalize_text(
            choice.get(
                "instruction",
                "",
            )
        ),
        "why": normalize_text(
            choice.get(
                "why",
                "",
            )
        ),
    }


def fallback_next_action(
    message,
    used_tools,
    email_allowed,
    memory_allowed,
    has_final_reply,
):
    if (
        needs_memory(
            message
        )
        and "read_memory"
        not in used_tools
    ):
        return {
            "tool": "read_memory",
            "instruction": "Read relevant saved user context.",
            "why": "Saved context is relevant to this request.",
            "decision_source": "local-fallback",
        }

    if (
        needs_research(
            message
        )
        and "research_web"
        not in used_tools
    ):
        return {
            "tool": "research_web",
            "instruction": message,
            "why": "Current information is needed.",
            "decision_source": "local-fallback",
        }

    if (
        not has_final_reply
        and "reason"
        not in used_tools
    ):
        return {
            "tool": "reason",
            "instruction": "Produce the final answer using gathered information.",
            "why": "Enough information is available to reason.",
            "decision_source": "local-fallback",
        }

    if (
        memory_allowed
        and has_final_reply
        and "save_memory"
        not in used_tools
    ):
        return {
            "tool": "save_memory",
            "instruction": "Save the final recommendation.",
            "why": "The user requested memory storage.",
            "decision_source": "local-fallback",
        }

    if (
        email_allowed
        and has_final_reply
        and "send_email"
        not in used_tools
    ):
        return {
            "tool": "send_email",
            "instruction": "Email the completed answer.",
            "why": "The user requested email.",
            "decision_source": "local-fallback",
        }

    return {
        "tool": "finish",
        "instruction": "Finish the task.",
        "why": "The request is complete.",
        "decision_source": "local-fallback",
    }


def decide_next_action(
    message,
    used_tools,
    email_allowed,
    memory_allowed,
    has_memory,
    has_research,
    has_final_reply,
    memory_done,
    email_done,
):
    memory_needed = needs_memory(
        message
    )

    research_needed = needs_research(
        message
    )

    if (
        is_personal_tyler_project_reference(
            message
        )
        and "read_memory"
        not in used_tools
    ):
        return {
            "tool": "read_memory",
            "instruction": (
                "Read the canonical Tyler AI project profile "
                "and saved project facts first."
            ),
            "why": (
                "Tyler AI refers to the user's personal assistant project."
            ),
            "decision_source": "project-memory-priority",
            "available_tools": [
                "read_memory",
            ],
            "controller_raw": "",
        }

    tools = available_tools(
        used_tools,
        email_allowed,
        memory_allowed,
        has_final_reply,
        research_needed,
        memory_needed,
    )

    state = {
        "used_tools": used_tools,
        "memory_read": has_memory,
        "research_done": has_research,
        "final_answer_ready": has_final_reply,
        "memory_saved": memory_done,
        "email_sent": email_done,
        "memory_allowed": memory_allowed,
        "email_allowed": email_allowed,
        "personal_tyler_project": (
            is_personal_tyler_project_reference(
                message
            )
        ),
        "available_tools": tools,
    }

    prompt = f"""
You are Tyler AI's next-action controller.

IDENTITY RULE:
"Tyler AI", "my Tyler AI", "the Tyler AI project", and close typos refer to the
user's personal autonomous-assistant project, not Tyler Technologies.

USER REQUEST:
{message}

CURRENT STATE:
{json.dumps(state, separators=(',', ':'))}

Choose exactly ONE next action from ONLY this list:
{chr(10).join('- ' + tool for tool in tools)}

Rules:
1. Choose only a listed tool.
2. Use read_memory when available and relevant.
3. Use research_web only for current/latest/recent/news/search/research requests.
4. Choose reason when enough information exists to answer.
5. Use save_memory or send_email only when shown.
6. Choose finish when complete.
7. Never invent a tool.

Return ONLY valid JSON:
{{"tool":"one available tool name","instruction":"short instruction","why":"short reason"}}
"""

    raw = ""

    try:
        raw = call_controller(
            prompt
        )

        choice = validate_controller_choice(
            parse_json_object(
                raw
            ),
            tools,
        )

        return {
            **choice,
            "decision_source": "groq-controller",
            "available_tools": tools,
            "controller_raw": raw[:300],
        }

    except Exception as exc:
        fallback = fallback_next_action(
            message,
            used_tools,
            email_allowed,
            memory_allowed,
            has_final_reply,
        )

        fallback[
            "decision_error"
        ] = str(exc)[:300]

        fallback[
            "available_tools"
        ] = tools

        fallback[
            "controller_raw"
        ] = raw[:300]

        return fallback

# =========================================================
# REASONING / AGENT
# =========================================================

def reasoning_step(
    message,
    memory_text,
    research_text,
):
    personal_project = (
        is_personal_tyler_project_reference(
            message
        )
    )

    identity_note = (
        "This request refers to the user's personal Tyler AI autonomous-assistant project. "
        "Do NOT interpret Tyler AI as Tyler Technologies. "
        "The CANONICAL PROJECT PROFILE is authoritative."
        if personal_project
        else "Use saved user context when relevant."
    )

    prompt = f"""
USER REQUEST:
{message}

IDENTITY / GROUNDING:
{identity_note}

SAVED USER CONTEXT:
{memory_text[:3600] if memory_text else "None"}

LIVE RESEARCH:
{research_text[:3500] if research_text else "None"}

Instructions:
- Answer clearly and practically.
- The CANONICAL PROJECT PROFILE is authoritative for Tyler AI's identity, architecture,
  implemented capabilities, and development state.
- If old saved memory conflicts with the canonical profile, follow the canonical profile.
- Never describe planned decision logging, feedback-loop fine-tuning, or model fine-tuning
  as implemented unless the canonical profile says it is implemented.
- Saved user context takes precedence over ambiguous web results for project identity.
- If this is a memory question, summarize actual saved/canonical context and do not invent details.
- If live research was not requested, do not use outside knowledge as a substitute for memory.
- If comparing choices, identify a clear winner.
- Do not claim an email or memory save has happened yet.

End with exactly one line:
RECOMMENDATION: <one concise recommendation sentence>

If no recommendation is appropriate:
RECOMMENDATION: None
"""

    result = call_reasoner(
        (
            "You are Tyler AI, the user's personal autonomous assistant. "
            "Maintain project identity consistently."
        ),
        prompt,
        max_tokens=800,
        temperature=0.2,
    ).strip()

    if not result:
        raise RuntimeError(
            "Empty reasoning response"
        )

    return result


def build_fallback_answer(
    memory_text,
    research,
):
    pieces = []

    if memory_text:
        pieces.append(
            "Relevant saved context:\n"
            + memory_text
        )

    if research:
        answer = normalize_text(
            research.get(
                "answer",
                "",
            )
        )

        if answer:
            pieces.append(
                answer
            )

    if not pieces:
        pieces.append(
            "I received the request, "
            "but I could not generate a complete response."
        )

    return (
        "\n\n".join(
            pieces
        )[:3500]
        + "\n\nRECOMMENDATION: None"
    )


def extract_recommendation(
    final_reply
):
    if not final_reply:
        return None

    match = re.search(
        r"(?im)^\s*RECOMMENDATION:\s*(.+?)\s*$",
        final_reply,
    )

    if not match:
        return None

    recommendation = normalize_text(
        match.group(1)
    )

    if recommendation.lower() in {
        "none",
        "n/a",
        "not applicable",
    }:
        return None

    return recommendation[:350]


def build_clean_memory(
    final_reply
):
    recommendation = extract_recommendation(
        final_reply
    )

    if not recommendation:
        return None

    return (
        "Tyler AI recommendation: "
        + recommendation
    )[:400]


def run_agent(message):
    email_allowed = user_allows_email(
        message
    )

    memory_allowed = user_allows_memory_write(
        message
    )

    used_tools = []
    actions = []
    post_actions = []

    memory_text = ""
    research = None
    research_text = ""
    final_reply = ""

    memory_result = None
    email_result = None
    sources = []

    controller_attempts = 0
    controller_successes = 0
    priority_decisions = 0
    fallback_decisions = 0
    reasoning_calls = 0

    for action_number in range(
        1,
        MAX_AGENT_ACTIONS + 1,
    ):
        decision = decide_next_action(
            message=message,
            used_tools=used_tools,
            email_allowed=email_allowed,
            memory_allowed=memory_allowed,
            has_memory=bool(
                memory_text
            ),
            has_research=bool(
                research
            ),
            has_final_reply=bool(
                final_reply
            ),
            memory_done=(
                memory_result
                is not None
            ),
            email_done=(
                email_result
                is not None
            ),
        )

        source = decision.get(
            "decision_source"
        )

        if source == "groq-controller":
            controller_attempts += 1
            controller_successes += 1

        elif source == "project-memory-priority":
            priority_decisions += 1

        else:
            controller_attempts += 1
            fallback_decisions += 1

        tool = decision[
            "tool"
        ]

        if tool == "finish":
            actions.append(
                {
                    "action": action_number,
                    "tool": "finish",
                    "decision": decision,
                }
            )
            break

        if tool in used_tools:
            actions.append(
                {
                    "action": action_number,
                    "tool": tool,
                    "skipped": True,
                    "reason": "Duplicate tool prevented.",
                    "decision": decision,
                }
            )
            break

        used_tools.append(
            tool
        )

        if tool == "read_memory":
            try:
                memory_text = (
                    project_memory_context(
                        12
                    )
                    if is_personal_tyler_project_reference(
                        message
                    )
                    else compact_memory_context(
                        10
                    )
                )

                result = (
                    memory_text
                    or "No saved memory was found."
                )

            except Exception as exc:
                result = (
                    f"Memory read failed: {exc}"
                )

            actions.append(
                {
                    "action": action_number,
                    "tool": tool,
                    "decision": decision,
                    "result": result,
                }
            )

        elif tool == "research_web":
            try:
                research = web_search(
                    decision.get(
                        "instruction"
                    )
                    or message
                )

                research_text = compact_research(
                    research
                )

                sources.extend(
                    research.get(
                        "sources",
                        [],
                    )
                )

                result = research_text

            except Exception as exc:
                research = None
                research_text = ""

                result = (
                    f"Research failed: {exc}"
                )

            actions.append(
                {
                    "action": action_number,
                    "tool": tool,
                    "decision": decision,
                    "result": result,
                }
            )

        elif tool == "reason":
            try:
                reasoning_calls += 1

                final_reply = reasoning_step(
                    message,
                    memory_text,
                    research_text,
                )

                fallback_used = False
                reason_error = None

            except Exception as exc:
                final_reply = build_fallback_answer(
                    memory_text,
                    research,
                )

                fallback_used = True
                reason_error = str(
                    exc
                )[:300]

            record = {
                "action": action_number,
                "tool": tool,
                "decision": decision,
                "result": final_reply,
                "fallback_used": fallback_used,
            }

            if reason_error:
                record[
                    "reason_error"
                ] = reason_error

            actions.append(
                record
            )

        elif tool == "save_memory":
            candidate = build_clean_memory(
                final_reply
            )

            if not memory_allowed:
                result = {
                    "saved": False,
                    "reason": "Memory writing was not authorized.",
                }

            elif memory_result is not None:
                result = {
                    "saved": False,
                    "reason": "Memory write already attempted.",
                }

            elif not candidate:
                result = {
                    "saved": False,
                    "reason": "No clear recommendation was available to save.",
                }

            elif looks_sensitive(
                candidate
            ):
                result = {
                    "saved": False,
                    "reason": "Sensitive information was not stored.",
                }

            elif memory_exists(
                candidate
            ):
                result = {
                    "saved": False,
                    "reason": "Memory already exists.",
                    "memory": candidate,
                }

            else:
                try:
                    database_result = save_memory(
                        candidate,
                        "decision",
                        8,
                    )

                    result = {
                        "saved": True,
                        "memory": candidate,
                        "category": "decision",
                        "importance": 8,
                        "database_result": database_result,
                    }

                except Exception as exc:
                    result = {
                        "saved": False,
                        "reason": str(exc),
                    }

            memory_result = result

            actions.append(
                {
                    "action": action_number,
                    "tool": tool,
                    "decision": decision,
                    "result": result,
                }
            )

        elif tool == "send_email":
            if not email_allowed:
                result = {
                    "sent": False,
                    "reason": "Email was not authorized.",
                }

            elif email_result is not None:
                result = {
                    "sent": False,
                    "reason": "Email already attempted.",
                }

            else:
                try:
                    result = send_email(
                        final_reply,
                        "Tyler AI Results",
                    )

                except Exception as exc:
                    result = {
                        "sent": False,
                        "error": str(exc),
                    }

            email_result = result

            actions.append(
                {
                    "action": action_number,
                    "tool": tool,
                    "decision": decision,
                    "result": result,
                }
            )

    if not final_reply:
        try:
            reasoning_calls += 1

            final_reply = reasoning_step(
                message,
                memory_text,
                research_text,
            )

        except Exception:
            final_reply = build_fallback_answer(
                memory_text,
                research,
            )

    if (
        memory_allowed
        and memory_result
        is None
    ):
        candidate = build_clean_memory(
            final_reply
        )

        if not candidate:
            memory_result = {
                "saved": False,
                "reason": "No clear recommendation was available to save.",
            }

        elif looks_sensitive(
            candidate
        ):
            memory_result = {
                "saved": False,
                "reason": "Sensitive information was not stored.",
            }

        elif memory_exists(
            candidate
        ):
            memory_result = {
                "saved": False,
                "reason": "Memory already exists.",
                "memory": candidate,
            }

        else:
            try:
                database_result = save_memory(
                    candidate,
                    "decision",
                    8,
                )

                memory_result = {
                    "saved": True,
                    "memory": candidate,
                    "category": "decision",
                    "importance": 8,
                    "database_result": database_result,
                }

            except Exception as exc:
                memory_result = {
                    "saved": False,
                    "reason": str(exc),
                }

        post_actions.append(
            {
                "tool": "save_memory",
                "result": memory_result,
            }
        )

    if (
        email_allowed
        and email_result
        is None
    ):
        try:
            email_result = send_email(
                final_reply,
                "Tyler AI Results",
            )

        except Exception as exc:
            email_result = {
                "sent": False,
                "error": str(exc),
            }

        post_actions.append(
            {
                "tool": "send_email",
                "result": email_result,
            }
        )

    return {
        "reply": final_reply,
        "actions": actions,
        "post_actions": post_actions,
        "used_tools": used_tools,
        "memory_result": memory_result,
        "email_result": email_result,
        "sources": sources,
        "controller_attempts": controller_attempts,
        "controller_successes": controller_successes,
        "priority_decisions": priority_decisions,
        "fallback_decisions": fallback_decisions,
        "reasoning_calls": reasoning_calls,
        "total_groq_calls": (
            controller_attempts
            + reasoning_calls
        ),
        "max_actions": MAX_AGENT_ACTIONS,
        "email_authorized": email_allowed,
        "memory_write_authorized": memory_allowed,
    }

# =========================================================
# WEB UI
# =========================================================

LOGIN_HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tyler AI</title>
<style>
:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:#07111f;color:#eef6ff;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;min-height:100vh;display:grid;place-items:center}
.card{width:min(92vw,420px);background:#0d1a2c;border:1px solid #20324d;border-radius:24px;padding:28px;box-shadow:0 24px 70px rgba(0,0,0,.35)}
h1{margin:0 0 6px;font-size:30px}
.sub{color:#91a4bf;margin:0 0 24px}
.input{width:100%;padding:14px 15px;border-radius:14px;border:1px solid #2b4161;background:#081322;color:#fff;font-size:16px;outline:none}
.input:focus{border-color:#4b8cff}
.btn{width:100%;margin-top:12px;padding:14px;border:0;border-radius:14px;background:#2563eb;color:#fff;font-weight:700;font-size:16px;cursor:pointer}
.error{background:#3a1520;color:#fecdd3;padding:10px 12px;border-radius:12px;margin-bottom:14px}
.tiny{font-size:12px;color:#70839f;margin-top:14px;line-height:1.45}
</style>
</head>
<body>
<form class="card" method="post" action="/ui/login">
<h1>Tyler AI</h1>
<p class="sub">Private assistant access</p>
{% if error %}
<div class="error">{{ error }}</div>
{% endif %}
<input
    class="input"
    name="key"
    type="password"
    autocomplete="current-password"
    placeholder="Tyler access key"
    required
    autofocus
>
<button
    class="btn"
    type="submit"
>
Open Tyler AI
</button>
<div class="tiny">
Your access key is checked by the server
and is not embedded in this webpage.
</div>
</form>
</body>
</html>
"""

CHAT_HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta
    name="viewport"
    content="width=device-width,initial-scale=1,maximum-scale=1"
>
<title>Tyler AI</title>
<style>
:root{color-scheme:dark;--bg:#07111f;--panel:#0b1728;--panel2:#0f1f34;--line:#213551;--muted:#8ea1bc;--text:#edf5ff;--blue:#2563eb;--green:#22c55e}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.shell{height:100dvh;max-width:980px;margin:0 auto;display:flex;flex-direction:column;background:var(--panel)}
header{height:68px;display:flex;align-items:center;gap:12px;padding:0 18px;border-bottom:1px solid var(--line);flex:none}
.orb{width:34px;height:34px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#93c5fd,#2563eb 48%,#1e3a8a);box-shadow:0 0 22px rgba(37,99,235,.5)}
.title{font-weight:800;font-size:18px}
.status{font-size:12px;color:var(--muted)}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);margin-right:5px}
.spacer{flex:1}
.logout{border:1px solid var(--line);background:transparent;color:var(--muted);border-radius:10px;padding:7px 10px;cursor:pointer}
.chat{flex:1;overflow-y:auto;padding:22px 16px 30px;scroll-behavior:smooth}
.row{display:flex;margin:11px 0}
.row.user{justify-content:flex-end}
.bubble{max-width:min(78%,740px);white-space:pre-wrap;line-height:1.48;padding:13px 15px;border-radius:18px;overflow-wrap:anywhere}
.assistant .bubble{background:var(--panel2);border:1px solid var(--line);border-bottom-left-radius:6px}
.user .bubble{background:var(--blue);border-bottom-right-radius:6px}
.typing{color:var(--muted)}
details{margin-top:10px;border-top:1px solid #223955;padding-top:8px;color:var(--muted);font-size:12px}
summary{cursor:pointer;user-select:none}
.diag{padding-top:7px;line-height:1.55}
.sources a{color:#93c5fd;text-decoration:none}
.composer{flex:none;border-top:1px solid var(--line);padding:12px 14px 16px;background:rgba(7,17,31,.96)}
.box{display:flex;gap:10px;align-items:flex-end;background:#081423;border:1px solid #29415f;border-radius:18px;padding:8px}
.box textarea{flex:1;resize:none;min-height:44px;max-height:160px;border:0;outline:0;background:transparent;color:#fff;font:inherit;padding:10px;line-height:1.35}
.send{width:44px;height:44px;border-radius:13px;border:0;background:var(--blue);color:#fff;font-weight:900;font-size:18px;cursor:pointer}
.send:disabled{opacity:.45;cursor:default}
.hint{text-align:center;color:#60738f;font-size:11px;margin-top:7px}
@media(max-width:600px){
.bubble{max-width:90%}
.chat{padding:16px 10px 24px}
header{padding:0 12px}
.composer{padding:10px}
}
</style>
</head>
<body>

<div class="shell">

<header>
<div class="orb"></div>

<div>
<div class="title">Tyler AI</div>
<div class="status">
<span class="dot"></span>
online · {{ version_short }}
</div>
</div>

<div class="spacer"></div>

<form
    method="post"
    action="/ui/logout"
>
<button
    class="logout"
    type="submit"
>
Log out
</button>
</form>
</header>

<main
    id="chat"
    class="chat"
>
<div class="row assistant">
<div class="bubble">
Tyler AI is online. What do you want to work on?
</div>
</div>
</main>

<div class="composer">
<div class="box">
<textarea
    id="message"
    rows="1"
    placeholder="Message Tyler AI…"
></textarea>

<button
    id="send"
    class="send"
    aria-label="Send"
>
↑
</button>
</div>

<div class="hint">
Enter to send · Shift+Enter for a new line
</div>
</div>

</div>

<script>

const chat = document.getElementById("chat");
const input = document.getElementById("message");
const sendButton = document.getElementById("send");

function scrollDown() {
    chat.scrollTop = chat.scrollHeight;
}

function memoryStatus(meta) {
    if (!meta || !meta.memory_result) {
        return null;
    }

    const result = meta.memory_result;

    if (result.deleted) {
        return "deleted";
    }

    if (result.replaced) {
        return "replaced";
    }

    if (result.audited) {
        return "audited";
    }

    if (result.preview) {
        return "preview only";
    }

    if (result.saved) {
        return "saved";
    }

    if (result.saved === false) {
        return "not saved";
    }

    return null;
}

function addMessage(text, who, meta) {
    const row = document.createElement("div");
    row.className = "row " + who;

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    const body = document.createElement("div");
    body.textContent = text;
    bubble.appendChild(body);

    if (meta && who === "assistant") {
        const details = document.createElement("details");
        const summary = document.createElement("summary");
        summary.textContent = "Details";
        details.appendChild(summary);

        const d = document.createElement("div");
        d.className = "diag";

        const tools = (meta.used_tools || []).join(" → ") || "none";

        d.textContent =
            "Tools: " + tools
            + "\nController: "
            + (meta.controller_successes || 0)
            + "/"
            + (meta.controller_attempts || 0)
            + "\nPriority decisions: "
            + (meta.priority_decisions || 0)
            + "\nFallbacks: "
            + (meta.fallback_decisions || 0)
            + "\nGroq calls: "
            + (meta.total_groq_calls || 0);

        const memStatus = memoryStatus(meta);

        if (memStatus) {
            d.textContent += "\nMemory: " + memStatus;
        }

        if (meta.email_result) {
            d.textContent +=
                "\nEmail: "
                + (
                    meta.email_result.sent
                    ? "sent"
                    : "not sent"
                );
        }

        details.appendChild(d);

        if (
            meta.sources
            && meta.sources.length
        ) {
            const box = document.createElement("div");
            box.className = "sources";
            box.appendChild(
                document.createTextNode(
                    "Sources: "
                )
            );

            meta.sources
            .slice(0, 4)
            .forEach(
                (
                    source,
                    index
                ) => {
                    if (index) {
                        box.appendChild(
                            document.createTextNode(
                                " · "
                            )
                        );
                    }

                    const link = document.createElement("a");
                    link.href = source.url || "#";
                    link.target = "_blank";
                    link.rel = "noopener noreferrer";
                    link.textContent =
                        source.title
                        || (
                            "Source "
                            + (index + 1)
                        );

                    box.appendChild(link);
                }
            );

            details.appendChild(box);
        }

        bubble.appendChild(details);
    }

    row.appendChild(bubble);
    chat.appendChild(row);
    scrollDown();

    return row;
}

function resizeInput() {
    input.style.height = "auto";
    input.style.height =
        Math.min(
            input.scrollHeight,
            160
        )
        + "px";
}

input.addEventListener(
    "input",
    resizeInput
);

input.addEventListener(
    "keydown",
    event => {
        if (
            event.key === "Enter"
            && !event.shiftKey
        ) {
            event.preventDefault();
            sendMessage();
        }
    }
);

sendButton.addEventListener(
    "click",
    event => {
        event.preventDefault();
        sendMessage();
    }
);

async function sendMessage() {
    const text = input.value.trim();

    if (
        !text
        || sendButton.disabled
    ) {
        return;
    }

    addMessage(
        text,
        "user"
    );

    input.value = "";
    resizeInput();
    sendButton.disabled = true;

    const waiting = addMessage(
        "Thinking…",
        "assistant"
    );

    waiting
    .querySelector(
        ".bubble"
    )
    .classList.add(
        "typing"
    );

    try {
        const response = await fetch(
            "/ui/chat",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                credentials: "same-origin",
                body: JSON.stringify(
                    {
                        message: text
                    }
                )
            }
        );

        let data = {};

        try {
            data = await response.json();
        } catch (_) {
            data = {
                error:
                    "The server returned "
                    + "an unreadable response."
            };
        }

        waiting.remove();

        if (
            response.status
            === 401
        ) {
            window.location = "/";
            return;
        }

        if (
            !response.ok
            || !data.success
        ) {
            addMessage(
                data.error
                || data.reply
                || "Tyler could not complete that request.",
                "assistant"
            );
            return;
        }

        addMessage(
            data.reply
            || "No reply returned.",
            "assistant",
            data
        );

    } catch (error) {
        waiting.remove();

        addMessage(
            "Connection error: "
            + error.message,
            "assistant"
        );

    } finally {
        sendButton.disabled = false;
        input.focus();
    }
}

input.focus();

</script>
</body>
</html>
"""

# =========================================================
# CHAT ROUTING
# =========================================================

def handle_chat_message(message):
    if delete_confirm_request(
        message
    ):
        ids = parse_memory_id_list(
            message
        )

        payload = confirm_memory_delete(
            ids
        )

        payload[
            "version"
        ] = VERSION

        return (
            payload,
            200
            if payload.get(
                "success"
            )
            else 400,
        )

    if delete_preview_request(
        message
    ):
        ids = parse_memory_id_list(
            message
        )

        payload = preview_memory_delete(
            ids
        )

        payload[
            "version"
        ] = VERSION

        return (
            payload,
            200
            if payload.get(
                "success"
            )
            else 400,
        )

    if replace_confirm_request(
        message
    ):
        parsed = parse_replace_request(
            message
        )

        if not parsed:
            return {
                "success": False,
                "version": VERSION,
                "reply": "I couldn't parse that replacement request.",
            }, 400

        memory_id, new_text = parsed

        payload = confirm_memory_replace(
            memory_id,
            new_text,
        )

        payload[
            "version"
        ] = VERSION

        return (
            payload,
            200
            if payload.get(
                "success"
            )
            else 400,
        )

    if replace_preview_request(
        message
    ):
        parsed = parse_replace_request(
            message
        )

        if not parsed:
            return {
                "success": False,
                "version": VERSION,
                "reply": "I couldn't parse that replacement request.",
            }, 400

        memory_id, new_text = parsed

        payload = preview_memory_replace(
            memory_id,
            new_text,
        )

        payload[
            "version"
        ] = VERSION

        return (
            payload,
            200
            if payload.get(
                "success"
            )
            else 400,
        )

    if memory_audit_request(
        message
    ):
        return (
            memory_audit_payload(),
            200,
        )

    if explicit_memory_request(
        message
    ):
        payload, status_code = (
            handle_explicit_memory(
                message
            )
        )

        payload[
            "version"
        ] = VERSION

        return (
            payload,
            status_code,
        )

    if is_simple_project_recall(
        message
    ):
        return (
            project_recall_payload(),
            200,
        )

    return {
        "success": True,
        "type": "autonomous_agent",
        "version": VERSION,
        **run_agent(
            message
        ),
    }, 200

# =========================================================
# WEBSITE ROUTES
# =========================================================

def ui_logged_in():
    return bool(
        session.get(
            "tyler_ui_authenticated"
        )
    )


@app.after_request
def disable_ui_cache(response):
    if request.path in {
        "/",
        "/ui",
    }:
        response.headers[
            "Cache-Control"
        ] = (
            "no-store, no-cache, "
            "must-revalidate, max-age=0"
        )

        response.headers[
            "Pragma"
        ] = "no-cache"

        response.headers[
            "Expires"
        ] = "0"

    return response


@app.route(
    "/",
    methods=["GET"],
)
@app.route(
    "/ui",
    methods=["GET"],
)
def ui_home():
    if not ui_logged_in():
        return render_template_string(
            LOGIN_HTML,
            error=None,
        )

    return render_template_string(
        CHAT_HTML,
        version_short=VERSION_SHORT,
    )


@app.route(
    "/ui/login",
    methods=["POST"],
)
def ui_login():
    supplied = str(
        request.form.get(
            "key",
            "",
        )
    )

    if (
        not TYLER_API_KEY
        or not hmac.compare_digest(
            supplied,
            TYLER_API_KEY,
        )
    ):
        return render_template_string(
            LOGIN_HTML,
            error=(
                "That access key "
                "was not accepted."
            ),
        ), 401

    session.clear()

    session[
        "tyler_ui_authenticated"
    ] = True

    session.permanent = True

    return redirect(
        url_for(
            "ui_home"
        )
    )


@app.route(
    "/ui/logout",
    methods=["POST"],
)
def ui_logout():
    session.clear()

    return redirect(
        url_for(
            "ui_home"
        )
    )


@app.route(
    "/ui/chat",
    methods=["POST"],
)
def ui_chat():
    if not ui_logged_in():
        return jsonify(
            {
                "success": False,
                "error": "Unauthorized",
            }
        ), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    message = str(
        data.get(
            "message",
            "",
        )
    ).strip()

    if not message:
        return jsonify(
            {
                "success": False,
                "error": "Missing message",
            }
        ), 400

    try:
        payload, status_code = (
            handle_chat_message(
                message
            )
        )

        return jsonify(
            payload
        ), status_code

    except Exception as exc:
        return jsonify(
            {
                "success": False,
                "version": VERSION,
                "error": str(exc),
            }
        ), 500

# =========================================================
# STATUS / HEALTH
# =========================================================

@app.route(
    "/status",
    methods=["GET"],
)
def status():
    return jsonify(
        {
            "name": "Tyler AI",
            "status": "online",
            "version": VERSION,
            "mode": (
                "autonomous-next-action"
                "+web-chat"
                "+structured-project-memory"
                "+approval-memory-management"
            ),
            "secured": bool(
                TYLER_API_KEY
            ),
            "groq_connected": bool(
                GROQ_API_KEY
            ),
            "tavily_connected": bool(
                TAVILY_API_KEY
            ),
            "n8n_connected": bool(
                N8N_WEBHOOK_URL
            ),
            "memory_connected": bool(
                SUPABASE_URL
                and SUPABASE_KEY
            ),
            "max_actions": MAX_AGENT_ACTIONS,
            "tools": [
                "read_memory",
                "research_web",
                "reason",
                "save_memory",
                "send_email",
                "audit_memory",
                "replace_memory",
                "delete_memory",
            ],
        }
    )


@app.route(
    "/health",
    methods=["GET"],
)
def health():
    return jsonify(
        {
            "status": "healthy",
            "version": VERSION,
        }
    )

# =========================================================
# MEMORY API
# =========================================================

@app.route(
    "/memories",
    methods=["GET"],
)
def memories_route():
    if not authorized():
        return jsonify(
            {
                "success": False,
                "error": "Unauthorized",
            }
        ), 401

    try:
        items = get_memories(
            100
        )

        return jsonify(
            {
                "success": True,
                "count": len(
                    items
                ),
                "memories": items,
            }
        )

    except Exception as exc:
        return jsonify(
            {
                "success": False,
                "error": str(
                    exc
                ),
            }
        ), 500


@app.route(
    "/memory/audit",
    methods=["GET"],
)
def memory_audit_route():
    if not authorized():
        return jsonify(
            {
                "success": False,
                "error": "Unauthorized",
            }
        ), 401

    try:
        return jsonify(
            {
                "success": True,
                "version": VERSION,
                "audit": audit_memories(),
            }
        )

    except Exception as exc:
        return jsonify(
            {
                "success": False,
                "version": VERSION,
                "error": str(
                    exc
                ),
            }
        ), 500

# =========================================================
# MAIN API CHAT
# =========================================================

@app.route(
    "/chat",
    methods=["POST"],
)
def chat():
    if not authorized():
        return jsonify(
            {
                "success": False,
                "error": "Unauthorized",
            }
        ), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    message = str(
        data.get(
            "message",
            "",
        )
    ).strip()

    if not message:
        return jsonify(
            {
                "success": False,
                "error": "Missing message",
            }
        ), 400

    try:
        payload, status_code = (
            handle_chat_message(
                message
            )
        )

        return jsonify(
            payload
        ), status_code

    except Exception as exc:
        return jsonify(
            {
                "success": False,
                "version": VERSION,
                "error": str(
                    exc
                ),
            }
        ), 500

# =========================================================
# N8N WEBHOOK
# =========================================================

@app.route(
    "/webhook",
    methods=["POST"],
)
def webhook():
    if not authorized():
        return jsonify(
            {
                "success": False,
                "error": "Unauthorized",
            }
        ), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    if not data.get(
        "action"
    ):
        return jsonify(
            {
                "success": False,
                "error": "Missing action",
            }
        ), 400

    try:
        result = send_to_n8n(
            data
        )

        return jsonify(
            {
                "success": True,
                "n8n_response": result[:500],
            }
        )

    except Exception as exc:
        return jsonify(
            {
                "success": False,
                "error": str(
                    exc
                ),
            }
        ), 500

# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    port = int(
        os.environ.get(
            "PORT",
            10000,
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
            )
