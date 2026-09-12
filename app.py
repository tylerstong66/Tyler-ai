import os
import re
import json
import requests
from flask import Flask, request, jsonify

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

GROQ_MODEL = os.environ.get(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)


# =========================================================
# SECURITY
# =========================================================

def authorized():
    supplied = request.headers.get("X-Tyler-Key")

    return bool(
        TYLER_API_KEY
        and supplied
        and supplied == TYLER_API_KEY
    )


# =========================================================
# HELPERS
# =========================================================

def parse_json_object(text):
    text = str(text).strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found")

    return json.loads(
        text[start:end + 1]
    )


def clamp(value, low, high):
    try:
        value = int(value)
    except Exception:
        value = low

    return max(
        low,
        min(high, value)
    )


# =========================================================
# GROQ
# =========================================================

def call_groq(
    system_prompt,
    user_prompt,
    max_tokens=700,
    temperature=0.2
):
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not configured"
        )

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization":
                f"Bearer {GROQ_API_KEY}",
            "Content-Type":
                "application/json",
        },
        json={
            "model":
                GROQ_MODEL,

            "messages": [
                {
                    "role":
                        "system",
                    "content":
                        system_prompt,
                },
                {
                    "role":
                        "user",
                    "content":
                        user_prompt,
                },
            ],

            "temperature":
                temperature,

            "max_tokens":
                max_tokens,
        },
        timeout=90,
    )

    try:
        result = response.json()

    except Exception:
        raise RuntimeError(
            f"Groq returned "
            f"{response.status_code}: "
            f"{response.text[:500]}"
        )

    if not response.ok:
        error = result.get(
            "error",
            {}
        )

        if isinstance(
            error,
            dict
        ):
            message = error.get(
                "message",
                str(error)
            )

        else:
            message = str(error)

        raise RuntimeError(
            message
        )

    return (
        result["choices"][0]
        ["message"]["content"]
        .strip()
    )


# =========================================================
# SUPABASE
# =========================================================

def supabase_headers():
    if not SUPABASE_KEY:
        raise RuntimeError(
            "SUPABASE_KEY is not configured"
        )

    return {
        "apikey":
            SUPABASE_KEY,

        "Authorization":
            f"Bearer {SUPABASE_KEY}",

        "Content-Type":
            "application/json",
    }


def get_memories(limit=20):
    if not SUPABASE_URL:
        return []

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/memories",
        headers=
            supabase_headers(),

        params={
            "select":
                "id,created_at,memories,"
                "category,importance",

            "order":
                "importance.desc,"
                "created_at.desc",

            "limit":
                limit,
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
    importance=5
):
    if not SUPABASE_URL:
        raise RuntimeError(
            "SUPABASE_URL is not configured"
        )

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/memories",

        headers={
            **supabase_headers(),

            "Prefer":
                "return=representation",
        },

        json={
            "memories":
                text,

            "category":
                category,

            "importance":
                clamp(
                    importance,
                    1,
                    10
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
    target = (
        str(text)
        .strip()
        .lower()
    )

    try:
        memories = get_memories(
            50
        )

    except Exception:
        return False

    for item in memories:
        existing = (
            str(
                item.get(
                    "memories",
                    ""
                )
            )
            .strip()
            .lower()
        )

        if existing == target:
            return True

    return False


def compact_memory_context(
    limit=8
):
    try:
        memories = get_memories(
            limit
        )

    except Exception:
        return ""

    lines = []

    for item in memories:
        text = str(
            item.get(
                "memories",
                ""
            )
        )[:300]

        category = item.get(
            "category",
            "general"
        )

        lines.append(
            f"- [{category}] {text}"
        )

    return "\n".join(
        lines
    )


# =========================================================
# MEMORY SAFETY
# =========================================================

def looks_sensitive(text):
    lower = text.lower()

    blocked_terms = [
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
        term in lower
        for term in blocked_terms
    )


# =========================================================
# EXPLICIT MEMORY
# =========================================================

def explicit_memory_request(
    message
):
    lower = message.lower()

    phrases = [
        "remember that",
        "remember this",
        "save this to memory",
        "save that to memory",
        "store this",
        "don't forget",
        "do not forget",
    ]

    return any(
        phrase in lower
        for phrase in phrases
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
            flags=re.IGNORECASE
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
            "favourite",
            "prefer",
            "i like",
        ]
    ):
        return "preference"

    if any(
        x in lower
        for x in [
            "goal",
            "my goal",
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
                3,
        },

        timeout=60,
    )

    try:
        result = response.json()

    except Exception:
        raise RuntimeError(
            f"Tavily returned "
            f"{response.status_code}: "
            f"{response.text[:500]}"
        )

    if not response.ok:
        raise RuntimeError(
            str(result)
        )

    sources = []

    for item in result.get(
        "results",
        []
    )[:3]:

        sources.append(
            {
                "title":
                    item.get(
                        "title",
                        ""
                    ),

                "url":
                    item.get(
                        "url",
                        ""
                    ),

                "content":
                    str(
                        item.get(
                            "content",
                            ""
                        )
                    )[:450],
            }
        )

    return {
        "answer":
            str(
                result.get(
                    "answer",
                    ""
                )
            )[:900],

        "sources":
            sources,
    }


def compact_research(
    research
):
    pieces = []

    answer = research.get(
        "answer",
        ""
    )

    if answer:
        pieces.append(
            "SEARCH SUMMARY:\n"
            + answer
        )

    for index, source in enumerate(
        research.get(
            "sources",
            []
        ),
        start=1
    ):
        pieces.append(
            f"\nSOURCE {index}\n"
            f"Title: "
            f"{source.get('title', '')}\n"
            f"URL: "
            f"{source.get('url', '')}\n"
            f"Info: "
            f"{source.get('content', '')}"
        )

    return "\n".join(
        pieces
    )


# =========================================================
# N8N
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
    subject="Tyler AI Results"
):
    if not TYLER_DEFAULT_EMAIL:
        raise RuntimeError(
            "TYLER_DEFAULT_EMAIL "
            "is not configured"
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
            result[:300],
    }


# =========================================================
# FALLBACK ROUTER
# =========================================================

def fallback_route(
    message
):
    lower = message.lower()

    steps = []

    memory_terms = [
        "what you remember",
        "based on what you know",
        "my favorite",
        "my goal",
        "my preferences",
    ]

    research_terms = [
        "research",
        "latest",
        "current",
        "today",
        "news",
        "look up",
        "search",
        "recent",
        "right now",
    ]

    email_terms = [
        "email me",
        "send me an email",
        "email the results",
        "send the results",
    ]

    if any(
        term in lower
        for term in memory_terms
    ):
        steps.append(
            {
                "tool":
                    "read_memory",

                "instruction":
                    "Read relevant long-term memory."
            }
        )

    if any(
        term in lower
        for term in research_terms
    ):
        steps.append(
            {
                "tool":
                    "research_web",

                "instruction":
                    message
            }
        )

    steps.append(
        {
            "tool":
                "reason",

            "instruction":
                "Answer the user's request using previous results."
        }
    )

    if any(
        term in lower
        for term in email_terms
    ):
        steps.append(
            {
                "tool":
                    "send_email",

                "instruction":
                    "Email the completed result."
            }
        )

    return {
        "goal":
            message[:200],

        "steps":
            steps[:6],

        "router":
            "fallback-local",
    }


# =========================================================
# TOOL ROUTER V2.1
# =========================================================

def tool_router(
    message
):
    prompt = f"""
USER REQUEST:
{message}

You are Tyler AI's autonomous tool router.

Available tools:

1. read_memory
Read useful long-term information about the user.

2. research_web
Search the live internet.

3. reason
Analyze information, compare choices, rank options,
make decisions, or synthesize previous tool results.

4. save_memory
Store a durable preference, decision, project detail,
or long-term goal.

5. send_email
Email the final useful result to the user.

Create the smallest ordered plan needed to complete
the user's request.

Return ONLY valid JSON:

{{
  "goal": "short description of the goal",
  "steps": [
    {{
      "tool": "read_memory",
      "instruction": "what memory is needed"
    }},
    {{
      "tool": "research_web",
      "instruction": "what should be researched"
    }},
    {{
      "tool": "reason",
      "instruction": "what should be analyzed or decided"
    }},
    {{
      "tool": "save_memory",
      "instruction": "what durable result should be remembered"
    }},
    {{
      "tool": "send_email",
      "instruction": "what result should be emailed"
    }}
  ]
}}

Rules:

- Use only the listed tools.
- Put tools in execution order.
- Maximum 6 steps.
- Do not research unless current information is needed.
- Do not email unless the user asks for email.
- Do not save memory unless useful long term.
- Never save passwords, API keys, tokens,
  banking credentials, private keys, or secrets.
- Use read_memory when user preferences, goals,
  projects, or past decisions could improve the result.
- Use reason after research when comparison,
  ranking, selection, or synthesis is needed.
"""

    raw = call_groq(
        system_prompt=(
            "You are Tyler AI Tool Router v2.1. "
            "Create short ordered executable plans. "
            "Output JSON only."
        ),

        user_prompt=
            prompt,

        max_tokens=
            400,

        temperature=
            0.0,
    )

    route = parse_json_object(
        raw
    )

    allowed_tools = {
        "read_memory",
        "research_web",
        "reason",
        "save_memory",
        "send_email",
    }

    clean_steps = []

    for step in route.get(
        "steps",
        []
    )[:6]:

        tool = str(
            step.get(
                "tool",
                ""
            )
        ).strip()

        instruction = str(
            step.get(
                "instruction",
                ""
            )
        ).strip()

        if tool not in allowed_tools:
            continue

        if not instruction:
            instruction = message

        clean_steps.append(
            {
                "tool":
                    tool,

                "instruction":
                    instruction,
            }
        )

    if not clean_steps:
        clean_steps = [
            {
                "tool":
                    "reason",

                "instruction":
                    message,
            }
        ]

    return {
        "goal":
            str(
                route.get(
                    "goal",
                    message
                )
            )[:250],

        "steps":
            clean_steps,

        "router":
            "groq-v2.1-chain",
    }


# =========================================================
# REASONING STEP
# =========================================================

def reasoning_step(
    original_request,
    instruction,
    working_context
):
    prompt = f"""
ORIGINAL REQUEST:
{original_request}

CURRENT INSTRUCTION:
{instruction}

RESULTS FROM EARLIER TOOLS:
{working_context if working_context else "None yet."}

Perform the current reasoning step.

Rules:
- Use earlier tool results when relevant.
- Do not claim an action happened unless it appears above.
- Give concrete conclusions.
- Keep the result compact.
"""

    return call_groq(
        system_prompt=(
            "You are Tyler AI's reasoning engine."
        ),

        user_prompt=
            prompt,

        max_tokens=
            700,

        temperature=
            0.2,
    )


# =========================================================
# MEMORY FROM WORKING CONTEXT
# =========================================================

def create_memory_from_context(
    instruction,
    working_context
):
    prompt = f"""
MEMORY INSTRUCTION:
{instruction}

WORKING RESULTS:
{working_context}

Extract ONE concise durable memory worth saving.

Return ONLY JSON:

{{
  "memory": "durable fact",
  "category": "preference, project, goal, career, decision, or general",
  "importance": 5
}}

Never include secrets, tokens, passwords,
banking credentials, or authentication information.
"""

    raw = call_groq(
        system_prompt=(
            "You extract one safe long-term memory."
        ),

        user_prompt=
            prompt,

        max_tokens=
            220,

        temperature=
            0.0,
    )

    result = parse_json_object(
        raw
    )

    return {
        "memory":
            str(
                result.get(
                    "memory",
                    ""
                )
            )[:600],

        "category":
            str(
                result.get(
                    "category",
                    "general"
                )
            )[:50],

        "importance":
            clamp(
                result.get(
                    "importance",
                    5
                ),
                1,
                10
            ),
    }


# =========================================================
# CHAIN EXECUTOR
# =========================================================

def execute_chain(
    message,
    route
):
    results = []
    working_context = ""

    final_reply = ""
    email_result = None
    memory_result = None
    sources = []

    extra_groq_calls = 0

    for index, step in enumerate(
        route["steps"],
        start=1
    ):

        tool = step["tool"]
        instruction = step["instruction"]

        # -------------------------------------------------
        # READ MEMORY
        # -------------------------------------------------

        if tool == "read_memory":

            memory_text = (
                compact_memory_context(
                    8
                )
            )

            result = {
                "step":
                    index,

                "tool":
                    tool,

                "result":
                    memory_text,
            }

            results.append(
                result
            )

            working_context += (
                f"\n\nSTEP {index} MEMORY:\n"
                f"{memory_text}"
            )

        # -------------------------------------------------
        # RESEARCH WEB
        # -------------------------------------------------

        elif tool == "research_web":

            research = web_search(
                instruction
            )

            compact = compact_research(
                research
            )

            sources.extend(
                research.get(
                    "sources",
                    []
                )
            )

            result = {
                "step":
                    index,

                "tool":
                    tool,

                "result":
                    compact,

                "sources":
                    research.get(
                        "sources",
                        []
                    ),
            }

            results.append(
                result
            )

            working_context += (
                f"\n\nSTEP {index} RESEARCH:\n"
                f"{compact}"
            )

        # -------------------------------------------------
        # REASON
        # -------------------------------------------------

        elif tool == "reason":

            reasoning = reasoning_step(
                message,
                instruction,
                working_context
            )

            extra_groq_calls += 1

            final_reply = reasoning

            result = {
                "step":
                    index,

                "tool":
                    tool,

                "result":
                    reasoning,
            }

            results.append(
                result
            )

            working_context += (
                f"\n\nSTEP {index} REASONING:\n"
                f"{reasoning}"
            )

        # -------------------------------------------------
        # SAVE MEMORY
        # -------------------------------------------------

        elif tool == "save_memory":

            candidate = (
                create_memory_from_context(
                    instruction,
                    working_context
                )
            )

            extra_groq_calls += 1

            memory_text = (
                candidate["memory"]
                .strip()
            )

            if not memory_text:

                memory_result = {
                    "saved":
                        False,

                    "reason":
                        "No durable memory produced."
                }

            elif looks_sensitive(
                memory_text
            ):

                memory_result = {
                    "saved":
                        False,

                    "reason":
                        "Sensitive information was not stored."
                }

            elif memory_exists(
                memory_text
            ):

                memory_result = {
                    "saved":
                        False,

                    "reason":
                        "Memory already exists."
                }

            else:

                database_result = (
                    save_memory(
                        memory_text,

                        candidate[
                            "category"
                        ],

                        candidate[
                            "importance"
                        ]
                    )
                )

                memory_result = {
                    "saved":
                        True,

                    "memory":
                        memory_text,

                    "category":
                        candidate[
                            "category"
                        ],

                    "importance":
                        candidate[
                            "importance"
                        ],

                    "database_result":
                        database_result,
                }

            results.append(
                {
                    "step":
                        index,

                    "tool":
                        tool,

                    "result":
                        memory_result,
                }
            )

        # -------------------------------------------------
        # SEND EMAIL
        # -------------------------------------------------

        elif tool == "send_email":

            body = (
                final_reply
                if final_reply
                else working_context
            )

            if not body.strip():
                body = message

            email_result = send_email(
                body,
                "Tyler AI Results"
            )

            results.append(
                {
                    "step":
                        index,

                    "tool":
                        tool,

                    "result":
                        email_result,
                }
            )

            working_context += (
                f"\n\nSTEP {index} EMAIL:\n"
                f"Sent to "
                f"{email_result['to']}"
            )

    # -----------------------------------------------------
    # FINAL FALLBACK REASONING
    # -----------------------------------------------------

    if not final_reply:

        final_reply = reasoning_step(
            message,
            "Provide the final answer.",
            working_context
        )

        extra_groq_calls += 1

    return {
        "reply":
            final_reply,

        "results":
            results,

        "email_result":
            email_result,

        "memory_result":
            memory_result,

        "sources":
            sources,

        "extra_groq_calls":
            extra_groq_calls,
    }


# =========================================================
# HOME
# =========================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return jsonify(
        {
            "name":
                "Tyler AI",

            "status":
                "online",

            "version":
                "2.1-action-chain",

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

            "tools": [
                "read_memory",
                "research_web",
                "reason",
                "save_memory",
                "send_email",
            ],
        }
    )


# =========================================================
# HEALTH
# =========================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify(
        {
            "status":
                "healthy",

            "version":
                "2.1-action-chain",
        }
    )


# =========================================================
# MEMORIES
# =========================================================

@app.route(
    "/memories",
    methods=["GET"]
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
                    len(items),

                "memories":
                    items,
            }
        )

    except Exception as e:

        return jsonify(
            {
                "success":
                    False,

                "error":
                    str(e),
            }
        ), 500


# =========================================================
# CHAT
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
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
            ""
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


    # =====================================================
    # EXPLICIT MEMORY — ZERO GROQ CALLS
    # =====================================================

    if explicit_memory_request(
        message
    ):

        try:

            memory = (
                clean_explicit_memory(
                    message
                )
            )

            if not memory:

                raise RuntimeError(
                    "No memory text found."
                )

            if looks_sensitive(
                memory
            ):

                return jsonify(
                    {
                        "success":
                            False,

                        "type":
                            "memory",

                        "error":
                            "Sensitive information "
                            "will not be stored.",
                    }
                ), 400

            if memory_exists(
                memory
            ):

                return jsonify(
                    {
                        "success":
                            True,

                        "type":
                            "memory",

                        "saved":
                            False,

                        "reason":
                            "Memory already exists.",

                        "groq_calls":
                            0,
                    }
                )

            category = (
                guess_memory_category(
                    memory
                )
            )

            saved = save_memory(
                memory,
                category,
                7
            )

            return jsonify(
                {
                    "success":
                        True,

                    "type":
                        "memory",

                    "saved":
                        True,

                    "memory":
                        memory,

                    "category":
                        category,

                    "groq_calls":
                        0,

                    "database_result":
                        saved,
                }
            )

        except Exception as e:

            return jsonify(
                {
                    "success":
                        False,

                    "type":
                        "memory",

                    "error":
                        str(e),
                }
            ), 500


    # =====================================================
    # ROUTER
    # =====================================================

    router_calls = 0

    try:

        route = tool_router(
            message
        )

        router_calls = 1

    except Exception as e:

        print(
            "Router fallback:",
            str(e)
        )

        route = fallback_route(
            message
        )


    # =====================================================
    # EXECUTE CHAIN
    # =====================================================

    try:

        execution = execute_chain(
            message,
            route
        )

    except Exception as e:

        return jsonify(
            {
                "success":
                    False,

                "type":
                    "chain_execution",

                "version":
                    "2.1-action-chain",

                "route":
                    route,

                "error":
                    str(e),

                "router_calls":
                    router_calls,
            }
        ), 500


    return jsonify(
        {
            "success":
                True,

            "type":
                "chain_execution",

            "version":
                "2.1-action-chain",

            "goal":
                route["goal"],

            "route":
                route,

            "execution":
                execution[
                    "results"
                ],

            "reply":
                execution[
                    "reply"
                ],

            "memory_result":
                execution[
                    "memory_result"
                ],

            "email_result":
                execution[
                    "email_result"
                ],

            "sources":
                execution[
                    "sources"
                ],

            "router_calls":
                router_calls,

            "execution_groq_calls":
                execution[
                    "extra_groq_calls"
                ],

            "total_groq_calls":
                router_calls
                + execution[
                    "extra_groq_calls"
                ],
        }
    )


# =========================================================
# WEBHOOK
# =========================================================

@app.route(
    "/webhook",
    methods=["POST"]
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

    except Exception as e:

        return jsonify(
            {
                "success":
                    False,

                "error":
                    str(e),
            }
        ), 500


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
    )
