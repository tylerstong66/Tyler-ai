import os
import re
import json
import hmac
import requests
from datetime import timedelta

from flask import (
    Flask, request, jsonify, render_template_string,
    session, redirect, url_for,
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
VERSION = "2.4.2-web-memory-fix"

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or TYLER_API_KEY or os.urandom(32)
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

    text = str(text).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        try:
            obj = json.loads(text[start:end + 1])
            if isinstance(obj, dict):
                return obj
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
        [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_completion_tokens=220,
        temperature=0.0,
        reasoning_effort="low",
        include_reasoning=False,
        response_format={
            "type": "json_object"
        },
    )


def call_reasoner(
    system_prompt,
    user_prompt,
    max_tokens=700,
    temperature=0.2,
):
    return groq_request(
        [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
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


def memory_exists(text):
    target = normalize_text(
        text
    ).lower()

    try:
        memories = get_memories(
            50
        )
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


def compact_memory_context(
    limit=10,
):
    try:
        memories = get_memories(
            limit
        )
    except Exception as exc:
        return f"Memory read failed: {exc}"

    return "\n".join(
        f"- [{item.get('category', 'general')}] "
        f"{normalize_text(item.get('memories', ''))[:300]}"
        for item in memories
    )[:2200]


# =========================================================
# PROJECT IDENTITY
# =========================================================

def normalized_intent_text(
    message
):
    lower = normalize_text(
        message
    ).lower()

    lower = lower.replace(
        "tlyer",
        "tyler",
    )

    lower = lower.replace(
        "tyelr",
        "tyler",
    )

    return lower


def is_personal_tyler_project_reference(
    message
):
    lower = normalized_intent_text(
        message
    )

    project_terms = [
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
        for term in project_terms
    ):
        return True

    return bool(
        re.search(
            r"\btyl\w{1,3}\s+(?:ai|project)\b",
            lower,
        )
    )


def needs_memory(
    message
):
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
        for term in terms
    )


def needs_research(
    message
):
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
        for term in terms
    )


# =========================================================
# PERMISSIONS / MEMORY COMMANDS
# =========================================================

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
        for item in blocked
    )


def user_allows_email(
    message
):
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
        for item in deny
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
        for item in allow
    )


def user_allows_memory_write(
    message
):
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
        for item in deny
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
        for item in allow
    )


def explicit_memory_request(
    message
):
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
        for pattern in patterns
    )


def clean_explicit_memory(
    message
):
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


def guess_memory_category(
    text
):
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


def handle_explicit_memory(
    message
):
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
            "error":
                "Sensitive information will not be stored.",
            "reply":
                "I did not save that because it may contain sensitive information.",
        }, 400

    if memory_exists(
        memory
    ):
        return {
            "success": True,
            "type": "memory",
            "saved": False,
            "reason":
                "Memory already exists.",
            "memory":
                memory,
            "reply":
                "I already have that saved in memory.",
            "used_tools": [
                "save_memory"
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
                "reason":
                    "Memory already exists.",
                "memory":
                    memory,
            },
            "email_result":
                None,
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
        "reply":
            f"Saved to memory: {memory}",
        "used_tools": [
            "save_memory"
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
        "email_result":
            None,
        "database_result":
            saved,
    }, 200


# =========================================================
# TAVILY
# =========================================================

def web_search(query):
    if not TAVILY_API_KEY:
        raise RuntimeError(
            "TAVILY_API_KEY is not configured"
        )

    response = requests.post(
        "https://api.tavily.com/search",
        headers={
            "Authorization":
                f"Bearer {TAVILY_API_KEY}",
            "Content-Type":
                "application/json",
        },
        json={
            "query":
                query,
            "search_depth":
                "basic",
            "include_answer":
                True,
            "max_results":
                4,
        },
        timeout=
            60,
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
            str(data)
        )

    sources = []

    for item in data.get(
        "results",
        [],
    )[:4]:
        sources.append(
            {
                "title":
                    item.get(
                        "title",
                        "",
                    ),
                "url":
                    item.get(
                        "url",
                        "",
                    ),
                "content":
                    normalize_text(
                        item.get(
                            "content",
                            "",
                        )
                    )[:400],
            }
        )

    return {
        "answer":
            normalize_text(
                data.get(
                    "answer",
                    "",
                )
            )[:1100],
        "sources":
            sources,
    }


def compact_research(
    research
):
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
            f"Title: "
            f"{source.get('title', '')}\n"
            f"Info: "
            f"{source.get('content', '')}"
        )

    return "\n".join(
        pieces
    )[:3300]


# =========================================================
# N8N / EMAIL
# =========================================================

def send_to_n8n(
    payload
):
    if not N8N_WEBHOOK_URL:
        raise RuntimeError(
            "N8N_WEBHOOK_URL is not configured"
        )

    response = requests.post(
        N8N_WEBHOOK_URL,
        json=
            payload,
        timeout=
            60,
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
            "action":
                "email",
            "data": {
                "to":
                    TYLER_DEFAULT_EMAIL,
                "subject":
                    subject,
                "message":
                    body,
            },
        }
    )

    return {
        "sent":
            True,
        "to":
            TYLER_DEFAULT_EMAIL,
        "subject":
            subject,
        "n8n_response":
            result[:250],
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
        "tool":
            tool,
        "instruction":
            normalize_text(
                choice.get(
                    "instruction",
                    "",
                )
            ),
        "why":
            normalize_text(
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
            "tool":
                "read_memory",
            "instruction":
                "Read relevant saved user context.",
            "why":
                "Saved context is relevant to this request.",
            "decision_source":
                "local-fallback",
        }

    if (
        needs_research(
            message
        )
        and "research_web"
        not in used_tools
    ):
        return {
            "tool":
                "research_web",
            "instruction":
                message,
            "why":
                "Current information is needed.",
            "decision_source":
                "local-fallback",
        }

    if (
        not has_final_reply
        and "reason"
        not in used_tools
    ):
        return {
            "tool":
                "reason",
            "instruction":
                "Produce the final answer using gathered information.",
            "why":
                "Enough information is available to reason.",
            "decision_source":
                "local-fallback",
        }

    if (
        memory_allowed
        and has_final_reply
        and "save_memory"
        not in used_tools
    ):
        return {
            "tool":
                "save_memory",
            "instruction":
                "Save the final recommendation.",
            "why":
                "The user requested memory storage.",
            "decision_source":
                "local-fallback",
        }

    if (
        email_allowed
        and has_final_reply
        and "send_email"
        not in used_tools
    ):
        return {
            "tool":
                "send_email",
            "instruction":
                "Email the completed answer.",
            "why":
                "The user requested email.",
            "decision_source":
                "local-fallback",
        }

    return {
        "tool":
            "finish",
        "instruction":
            "Finish the task.",
        "why":
            "The request is complete.",
        "decision_source":
            "local-fallback",
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
            "tool":
                "read_memory",
            "instruction":
                "Read saved context about "
                "the user's Tyler AI project "
                "before doing anything else.",
            "why":
                "Tyler AI refers to the user's "
                "personal assistant project; "
                "saved project context has priority.",
            "decision_source":
                "project-memory-priority",
            "available_tools": [
                "read_memory"
            ],
            "controller_raw":
                "",
        }

    tools = available_tools(
        used_tools,
        email_allowed,
        memory_allowed,
        has_final_reply,
        research_needed=
            research_needed,
        memory_needed=
            memory_needed,
    )

    state = {
        "used_tools":
            used_tools,
        "memory_read":
            has_memory,
        "research_done":
            has_research,
        "final_answer_ready":
            has_final_reply,
        "memory_saved":
            memory_done,
        "email_sent":
            email_done,
        "memory_allowed":
            memory_allowed,
        "email_allowed":
            email_allowed,
        "personal_tyler_project":
            is_personal_tyler_project_reference(
                message
            ),
        "available_tools":
            tools,
    }

    tool_lines = "\n".join(
        f"- {tool}"
        for tool in tools
    )

    prompt = f"""
You are Tyler AI's next-action controller.

IMPORTANT IDENTITY RULE:

When the request refers to "Tyler AI",
"my Tyler AI", "the Tyler AI project",
or a close typo, that means the user's
personal autonomous-assistant project.

It does NOT mean Tyler Technologies.

Saved user context has priority for
identifying the user's own project.

USER REQUEST:

{message}

CURRENT STATE:

{json.dumps(state, separators=(',', ':'))}

Choose exactly ONE next action from ONLY
this list:

{tool_lines}

Rules:

1. You may ONLY choose a tool shown above.

2. Use read_memory when available and relevant.

3. Use research_web ONLY when the user asks
for current, latest, recent, news, search,
or research information.

4. Choose reason when enough information
exists to answer.

5. Choose save_memory only if shown.

6. Choose send_email only if shown.

7. Choose finish when the requested work
is complete.

8. Never invent a tool.

Return ONLY valid JSON:

{{
  "tool": "one available tool name",
  "instruction": "short instruction",
  "why": "short reason"
}}
"""

    raw = ""

    try:
        raw = call_controller(
            prompt
        )

        parsed = parse_json_object(
            raw
        )

        choice = validate_controller_choice(
            parsed,
            tools,
        )

        return {
            **choice,
            "decision_source":
                "groq-controller",
            "available_tools":
                tools,
            "controller_raw":
                raw[:300],
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
# REASONING
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

    if personal_project:
        identity_note = (
            "The request refers to the user's "
            "personal Tyler AI autonomous-assistant "
            "project. Do NOT interpret Tyler AI as "
            "Tyler Technologies or any unrelated "
            "commercial product. Use SAVED USER "
            "CONTEXT as the authoritative source "
            "for the identity and state of the "
            "user's project."
        )
    else:
        identity_note = (
            "Use saved user context "
            "when it is relevant."
        )

    prompt = f"""
USER REQUEST:

{message}

IDENTITY / GROUNDING:

{identity_note}

SAVED USER CONTEXT:

{memory_text[:2200] if memory_text else "None"}

LIVE RESEARCH:

{research_text[:3500] if research_text else "None"}

Instructions:

- Answer clearly and practically.

- Saved user context takes precedence over
  ambiguous web results for personal project
  identity.

- Never replace the user's project identity
  with an unrelated company or product because
  the names are similar.

- If this is a memory question, summarize what
  is actually present in saved context and do
  not invent missing details.

- If live research was not requested, do not
  rely on outside knowledge as a substitute
  for memory.

- If comparing choices, identify a clear winner.

- Do not claim an email or memory save has
  happened yet.

End with exactly one line:

RECOMMENDATION: <one concise recommendation sentence>

If no recommendation is appropriate:

RECOMMENDATION: None
"""

    result = call_reasoner(
        (
            "You are Tyler AI, the user's "
            "personal autonomous assistant. "
            "Maintain the user's project "
            "identity consistently."
        ),
        prompt,
        max_tokens=
            800,
        temperature=
            0.2,
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
            "but I could not generate "
            "a complete response."
        )

    return (
        "\n\n".join(
            pieces
        )[:3500]
        + "\n\n"
        + "RECOMMENDATION: None"
    )


def extract_recommendation(
    final_reply
):
    if not final_reply:
        return None

    match = re.search(
        r"(?im)^\s*"
        r"RECOMMENDATION:\s*"
        r"(.+?)\s*$",
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

    return recommendation[
        :350
    ]


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


# =========================================================
# AUTONOMOUS AGENT
# =========================================================

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
            message=
                message,
            used_tools=
                used_tools,
            email_allowed=
                email_allowed,
            memory_allowed=
                memory_allowed,
            has_memory=
                bool(memory_text),
            has_research=
                bool(research),
            has_final_reply=
                bool(final_reply),
            memory_done=
                memory_result
                is not None,
            email_done=
                email_result
                is not None,
        )

        decision_source = decision.get(
            "decision_source"
        )

        if decision_source == "groq-controller":
            controller_attempts += 1
            controller_successes += 1

        elif decision_source == "project-memory-priority":
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
                    "action":
                        action_number,
                    "tool":
                        "finish",
                    "decision":
                        decision,
                }
            )
            break

        if tool in used_tools:
            actions.append(
                {
                    "action":
                        action_number,
                    "tool":
                        tool,
                    "skipped":
                        True,
                    "reason":
                        "Duplicate tool prevented.",
                    "decision":
                        decision,
                }
            )
            break

        used_tools.append(
            tool
        )

        if tool == "read_memory":
            try:
                memory_text = (
                    compact_memory_context(
                        10
                    )
                )

                result = (
                    memory_text
                    or
                    "No saved memory was found."
                )

            except Exception as exc:
                result = (
                    f"Memory read failed: {exc}"
                )

            actions.append(
                {
                    "action":
                        action_number,
                    "tool":
                        tool,
                    "decision":
                        decision,
                    "result":
                        result,
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

                research_text = (
                    compact_research(
                        research
                    )
                )

                sources.extend(
                    research.get(
                        "sources",
                        [],
                    )
                )

                result = (
                    research_text
                )

            except Exception as exc:
                research = None
                research_text = ""

                result = (
                    f"Research failed: {exc}"
                )

            actions.append(
                {
                    "action":
                        action_number,
                    "tool":
                        tool,
                    "decision":
                        decision,
                    "result":
                        result,
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
                final_reply = (
                    build_fallback_answer(
                        memory_text,
                        research,
                    )
                )

                fallback_used = True
                reason_error = str(
                    exc
                )[:300]

            record = {
                "action":
                    action_number,
                "tool":
                    tool,
                "decision":
                    decision,
                "result":
                    final_reply,
                "fallback_used":
                    fallback_used,
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
                    "saved":
                        False,
                    "reason":
                        "Memory writing was not authorized.",
                }

            elif memory_result is not None:
                result = {
                    "saved":
                        False,
                    "reason":
                        "Memory write already attempted.",
                }

            elif not candidate:
                result = {
                    "saved":
                        False,
                    "reason":
                        "No clear recommendation was available to save.",
                }

            elif looks_sensitive(
                candidate
            ):
                result = {
                    "saved":
                        False,
                    "reason":
                        "Sensitive information was not stored.",
                }

            elif memory_exists(
                candidate
            ):
                result = {
                    "saved":
                        False,
                    "reason":
                        "Memory already exists.",
                    "memory":
                        candidate,
                }

            else:
                try:
                    database_result = save_memory(
                        candidate,
                        "decision",
                        8,
                    )

                    result = {
                        "saved":
                            True,
                        "memory":
                            candidate,
                        "category":
                            "decision",
                        "importance":
                            8,
                        "database_result":
                            database_result,
                    }

                except Exception as exc:
                    result = {
                        "saved":
                            False,
                        "reason":
                            str(exc),
                    }

            memory_result = result

            actions.append(
                {
                    "action":
                        action_number,
                    "tool":
                        tool,
                    "decision":
                        decision,
                    "result":
                        result,
                }
            )

        elif tool == "send_email":
            if not email_allowed:
                result = {
                    "sent":
                        False,
                    "reason":
                        "Email was not authorized.",
                }

            elif email_result is not None:
                result = {
                    "sent":
                        False,
                    "reason":
                        "Email already attempted.",
                }

            else:
                try:
                    result = send_email(
                        final_reply,
                        "Tyler AI Results",
                    )

                except Exception as exc:
                    result = {
                        "sent":
                            False,
                        "error":
                            str(exc),
                    }

            email_result = result

            actions.append(
                {
                    "action":
                        action_number,
                    "tool":
                        tool,
                    "decision":
                        decision,
                    "result":
                        result,
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
            final_reply = (
                build_fallback_answer(
                    memory_text,
                    research,
                )
            )

    if (
        memory_allowed
        and memory_result is None
    ):
        candidate = build_clean_memory(
            final_reply
        )

        if not candidate:
            memory_result = {
                "saved":
                    False,
                "reason":
                    "No clear recommendation was available to save.",
            }

        elif looks_sensitive(
            candidate
        ):
            memory_result = {
                "saved":
                    False,
                "reason":
                    "Sensitive information was not stored.",
            }

        elif memory_exists(
            candidate
        ):
            memory_result = {
                "saved":
                    False,
                "reason":
                    "Memory already exists.",
                "memory":
                    candidate,
            }

        else:
            try:
                database_result = save_memory(
                    candidate,
                    "decision",
                    8,
                )

                memory_result = {
                    "saved":
                        True,
                    "memory":
                        candidate,
                    "category":
                        "decision",
                    "importance":
                        8,
                    "database_result":
                        database_result,
                }

            except Exception as exc:
                memory_result = {
                    "saved":
                        False,
                    "reason":
                        str(exc),
                }

        post_actions.append(
            {
                "tool":
                    "save_memory",
                "result":
                    memory_result,
            }
        )

    if (
        email_allowed
        and email_result is None
    ):
        try:
            email_result = send_email(
                final_reply,
                "Tyler AI Results",
            )

        except Exception as exc:
            email_result = {
                "sent":
                    False,
                "error":
                    str(exc),
            }

        post_actions.append(
            {
                "tool":
                    "send_email",
                "result":
                    email_result,
            }
        )

    return {
        "reply":
            final_reply,
        "actions":
            actions,
        "post_actions":
            post_actions,
        "used_tools":
            used_tools,
        "memory_result":
            memory_result,
        "email_result":
            email_result,
        "sources":
            sources,
        "controller_attempts":
            controller_attempts,
        "controller_successes":
            controller_successes,
        "priority_decisions":
            priority_decisions,
        "fallback_decisions":
            fallback_decisions,
        "reasoning_calls":
            reasoning_calls,
        "total_groq_calls":
            controller_attempts
            + reasoning_calls,
        "max_actions":
            MAX_AGENT_ACTIONS,
        "email_authorized":
            email_allowed,
        "memory_write_authorized":
            memory_allowed,
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
h1{margin:0 0 6px;font-size:30px}.sub{color:#91a4bf;margin:0 0 24px}
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
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<input class="input" name="key" type="password" autocomplete="current-password" placeholder="Tyler access key" required autofocus>
<button class="btn" type="submit">Open Tyler AI</button>
<div class="tiny">Your access key is checked by the server and is not embedded in this webpage.</div>
</form>
</body>
</html>
"""

CHAT_HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>Tyler AI</title>
<style>
:root{color-scheme:dark;--bg:#07111f;--panel:#0b1728;--panel2:#0f1f34;--line:#213551;--muted:#8ea1bc;--text:#edf5ff;--blue:#2563eb;--green:#22c55e}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.shell{height:100dvh;max-width:980px;margin:0 auto;display:flex;flex-direction:column;background:var(--panel)}
header{height:68px;display:flex;align-items:center;gap:12px;padding:0 18px;border-bottom:1px solid var(--line);flex:none}
.orb{width:34px;height:34px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#93c5fd,#2563eb 48%,#1e3a8a);box-shadow:0 0 22px rgba(37,99,235,.5)}
.title{font-weight:800;font-size:18px}.status{font-size:12px;color:var(--muted)}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);margin-right:5px}
.spacer{flex:1}.logout{border:1px solid var(--line);background:transparent;color:var(--muted);border-radius:10px;padding:7px 10px;cursor:pointer}
.chat{flex:1;overflow-y:auto;padding:22px 16px 30px;scroll-behavior:smooth}
.row{display:flex;margin:11px 0}.row.user{justify-content:flex-end}
.bubble{max-width:min(78%,740px);white-space:pre-wrap;line-height:1.48;padding:13px 15px;border-radius:18px;overflow-wrap:anywhere}
.assistant .bubble{background:var(--panel2);border:1px solid var(--line);border-bottom-left-radius:6px}
.user .bubble{background:var(--blue);border-bottom-right-radius:6px}
.typing{color:var(--muted)}
details{margin-top:10px;border-top:1px solid #223955;padding-top:8px;color:var(--muted);font-size:12px}
summary{cursor:pointer;user-select:none}.diag{padding-top:7px;line-height:1.55}.sources a{color:#93c5fd;text-decoration:none}
.composer{flex:none;border-top:1px solid var(--line);padding:12px 14px 16px;background:rgba(7,17,31,.96)}
.box{display:flex;gap:10px;align-items:flex-end;background:#081423;border:1px solid #29415f;border-radius:18px;padding:8px}
.box textarea{flex:1;resize:none;min-height:44px;max-height:160px;border:0;outline:0;background:transparent;color:#fff;font:inherit;padding:10px;line-height:1.35}
.send{width:44px;height:44px;border-radius:13px;border:0;background:var(--blue);color:#fff;font-weight:900;font-size:18px;cursor:pointer}
.send:disabled{opacity:.45;cursor:default}.hint{text-align:center;color:#60738f;font-size:11px;margin-top:7px}
@media(max-width:600px){.bubble{max-width:90%}.chat{padding:16px 10px 24px}header{padding:0 12px}.composer{padding:10px}}
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
online · v2.4.2
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

const chat =
    document.getElementById(
        "chat"
    );

const input =
    document.getElementById(
        "message"
    );

const sendButton =
    document.getElementById(
        "send"
    );


function scrollDown() {
    chat.scrollTop =
        chat.scrollHeight;
}


function addMessage(
    text,
    who,
    meta
) {
    const row =
        document.createElement(
            "div"
        );

    row.className =
        "row " + who;

    const bubble =
        document.createElement(
            "div"
        );

    bubble.className =
        "bubble";

    const body =
        document.createElement(
            "div"
        );

    body.textContent =
        text;

    bubble.appendChild(
        body
    );


    if (
        meta
        && who === "assistant"
    ) {

        const details =
            document.createElement(
                "details"
            );

        const summary =
            document.createElement(
                "summary"
            );

        summary.textContent =
            "Details";

        details.appendChild(
            summary
        );

        const diagnostics =
            document.createElement(
                "div"
            );

        diagnostics.className =
            "diag";

        const tools =
            (
                meta.used_tools
                || []
            ).join(
                " → "
            )
            || "none";

        diagnostics.textContent =
            "Tools: "
            + tools

            + "\nController: "
            + (
                meta.controller_successes
                || 0
            )

            + "/"
            + (
                meta.controller_attempts
                || 0
            )

            + "\nPriority decisions: "
            + (
                meta.priority_decisions
                || 0
            )

            + "\nFallbacks: "
            + (
                meta.fallback_decisions
                || 0
            )

            + "\nGroq calls: "
            + (
                meta.total_groq_calls
                || 0
            );


        if (
            meta.memory_result
        ) {
            diagnostics.textContent +=
                "\nMemory: "
                + (
                    meta.memory_result.saved
                    ? "saved"
                    : "not saved"
                );
        }


        if (
            meta.email_result
        ) {
            diagnostics.textContent +=
                "\nEmail: "
                + (
                    meta.email_result.sent
                    ? "sent"
                    : "not sent"
                );
        }


        details.appendChild(
            diagnostics
        );


        if (
            meta.sources
            && meta.sources.length
        ) {

            const sourceBox =
                document.createElement(
                    "div"
                );

            sourceBox.className =
                "sources";

            sourceBox.appendChild(
                document.createTextNode(
                    "Sources: "
                )
            );


            meta.sources
            .slice(
                0,
                4
            )
            .forEach(
                (
                    source,
                    index
                ) => {

                    if (index) {
                        sourceBox.appendChild(
                            document.createTextNode(
                                " · "
                            )
                        );
                    }

                    const link =
                        document.createElement(
                            "a"
                        );

                    link.href =
                        source.url
                        || "#";

                    link.target =
                        "_blank";

                    link.rel =
                        "noopener noreferrer";

                    link.textContent =
                        source.title
                        || (
                            "Source "
                            + (
                                index + 1
                            )
                        );

                    sourceBox.appendChild(
                        link
                    );
                }
            );

            details.appendChild(
                sourceBox
            );
        }


        bubble.appendChild(
            details
        );
    }


    row.appendChild(
        bubble
    );

    chat.appendChild(
        row
    );

    scrollDown();

    return row;
}


function resizeInput() {
    input.style.height =
        "auto";

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

    const text =
        input.value.trim();

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

    input.value =
        "";

    resizeInput();

    sendButton.disabled =
        true;


    const waiting =
        addMessage(
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

        const response =
            await fetch(
                "/ui/chat",

                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    credentials:
                        "same-origin",

                    body:
                        JSON.stringify(
                            {
                                message:
                                    text
                            }
                        )
                }
            );


        let data = {};


        try {

            data =
                await response.json();

        }

        catch (_) {

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

            window.location =
                "/";

            return;
        }


        if (
            !response.ok
            || !data.success
        ) {

            addMessage(
                data.error
                || "Tyler could not "
                + "complete that request.",

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

    }

    catch (error) {

        waiting.remove();

        addMessage(
            "Connection error: "
            + error.message,

            "assistant"
        );

    }

    finally {

        sendButton.disabled =
            false;

        input.focus();
    }
}


input.focus();

</script>

</body>

</html>
"""


# =========================================================
# WEBSITE ROUTES
# =========================================================

def ui_logged_in():
    return bool(
        session.get(
            "tyler_ui_authenticated"
        )
    )


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
        CHAT_HTML
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
            error=
                "That access key "
                "was not accepted.",
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
                "success":
                    False,
                "error":
                    "Unauthorized",
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
                "success":
                    False,
                "error":
                    "Missing message",
            }
        ), 400

    if explicit_memory_request(
        message
    ):
        try:
            payload, status_code = (
                handle_explicit_memory(
                    message
                )
            )

            payload[
                "version"
            ] = VERSION

            return jsonify(
                payload
            ), status_code

        except Exception as exc:
            return jsonify(
                {
                    "success":
                        False,
                    "type":
                        "memory",
                    "version":
                        VERSION,
                    "error":
                        str(exc),
                }
            ), 500

    try:
        execution = run_agent(
            message
        )

        return jsonify(
            {
                "success":
                    True,
                "type":
                    "autonomous_agent",
                "version":
                    VERSION,
                **execution,
            }
        )

    except Exception as exc:
        return jsonify(
            {
                "success":
                    False,
                "type":
                    "autonomous_agent",
                "version":
                    VERSION,
                "error":
                    str(exc),
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
            "name":
                "Tyler AI",
            "status":
                "online",
            "version":
                VERSION,
            "mode":
                "autonomous-next-action"
                "+web-chat"
                "+memory-priority"
                "+web-memory-fix",
            "secured":
                bool(
                    TYLER_API_KEY
                ),
            "groq_connected":
                bool(
                    GROQ_API_KEY
                ),
            "tavily_connected":
                bool(
                    TAVILY_API_KEY
                ),
            "n8n_connected":
                bool(
                    N8N_WEBHOOK_URL
                ),
            "memory_connected":
                bool(
                    SUPABASE_URL
                    and SUPABASE_KEY
                ),
            "max_actions":
                MAX_AGENT_ACTIONS,
            "tools": [
                "read_memory",
                "research_web",
                "reason",
                "save_memory",
                "send_email",
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
            "status":
                "healthy",
            "version":
                VERSION,
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
                "success":
                    False,
                "error":
                    "Unauthorized",
            }
        ), 401

    try:
        items = get_memories(
            50
        )

        return jsonify(
            {
                "success":
                    True,
                "count":
                    len(
                        items
                    ),
                "memories":
                    items,
            }
        )

    except Exception as exc:
        return jsonify(
            {
                "success":
                    False,
                "error":
                    str(exc),
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
                "success":
                    False,
                "error":
                    "Unauthorized",
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
                "success":
                    False,
                "error":
                    "Missing message",
            }
        ), 400

    if explicit_memory_request(
        message
    ):
        try:
            payload, status_code = (
                handle_explicit_memory(
                    message
                )
            )

            payload[
                "version"
            ] = VERSION

            return jsonify(
                payload
            ), status_code

        except Exception as exc:
            return jsonify(
                {
                    "success":
                        False,
                    "type":
                        "memory",
                    "version":
                        VERSION,
                    "error":
                        str(exc),
                }
            ), 500

    try:
        execution = run_agent(
            message
        )

        return jsonify(
            {
                "success":
                    True,
                "type":
                    "autonomous_agent",
                "version":
                    VERSION,
                **execution,
            }
        )

    except Exception as exc:
        return jsonify(
            {
                "success":
                    False,
                "type":
                    "autonomous_agent",
                "version":
                    VERSION,
                "error":
                    str(exc),
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
                "success":
                    False,
                "error":
                    "Unauthorized",
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
                "success":
                    False,
                "error":
                    "Missing action",
            }
        ), 400

    try:
        result = send_to_n8n(
            data
        )

        return jsonify(
            {
                "success":
                    True,
                "n8n_response":
                    result[:500],
            }
        )

    except Exception as exc:
        return jsonify(
            {
                "success":
                    False,
                "error":
                    str(exc),
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
