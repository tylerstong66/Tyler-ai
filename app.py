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
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
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

        if isinstance(error, dict):
            message = error.get(
                "message",
                str(error)
            )
        else:
            message = str(error)

        raise RuntimeError(message)

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
        headers=supabase_headers(),
        params={
            "select":
                "id,created_at,memories,"
                "category,importance",
            "order":
                "importance.desc,created_at.desc",
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
        for item in get_memories(40):
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
    except Exception:
        pass

    return False


def compact_memory_context(limit=6):
    try:
        memories = get_memories(limit)
    except Exception:
        return ""

    lines = []

    for item in memories:
        memory = str(
            item.get(
                "memories",
                ""
            )
        )[:280]

        category = item.get(
            "category",
            "general"
        )

        lines.append(
            f"- [{category}] {memory}"
        )

    return "\n".join(lines)


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
# EXPLICIT MEMORY COMMANDS
# =========================================================

def explicit_memory_request(message):
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
            flags=re.IGNORECASE
        )

    return text.strip()


def guess_memory_category(text):
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
                    )[:400],
            }
        )

    return {
        "answer":
            str(
                result.get(
                    "answer",
                    ""
                )
            )[:800],
        "sources":
            sources,
    }


def compact_research(research):
    pieces = []

    if research.get("answer"):
        pieces.append(
            "SEARCH SUMMARY:\n"
            + research["answer"]
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
            f"{source.get('title', '')}\n"
            f"{source.get('url', '')}\n"
            f"{source.get('content', '')}"
        )

    return "\n".join(pieces)


# =========================================================
# N8N / EMAIL
# =========================================================

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
    subject="Tyler AI Results"
):
    if not TYLER_DEFAULT_EMAIL:
        raise RuntimeError(
            "TYLER_DEFAULT_EMAIL "
            "is not configured"
        )

    result = send_to_n8n(
        {
            "action": "email",
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
# FALLBACK LOCAL ROUTER
# Used if AI router is unavailable/rate-limited.
# =========================================================

def fallback_route(message):
    lower = message.lower()

    research_words = [
        "research",
        "latest",
        "current",
        "today",
        "news",
        "look up",
        "search",
        "right now",
        "recent",
        "development",
    ]

    email_words = [
        "email me",
        "email the",
        "send me an email",
        "send the results",
        "email the results",
    ]

    memory_words = [
        "remember",
        "based on what you know about me",
        "my favorite",
        "my goal",
        "what do i prefer",
    ]

    use_research = any(
        word in lower
        for word in research_words
    )

    send_mail = any(
        word in lower
        for word in email_words
    )

    use_memory = any(
        word in lower
        for word in memory_words
    )

    return {
        "goal":
            message[:180],

        "use_memory":
            use_memory,

        "use_research":
            use_research,

        "research_query":
            message,

        "save_memory":
            False,

        "memory_text":
            "",

        "memory_category":
            "general",

        "memory_importance":
            5,

        "send_email":
            send_mail,

        "analysis_instruction":
            "Answer the user's request directly.",
            
        "router":
            "fallback-local",
    }


# =========================================================
# TOOL ROUTER V2
# =========================================================

def tool_router(message):
    prompt = f"""
USER REQUEST:
{message}

Choose which Tyler AI tools are actually needed.

Available capabilities:

1. read_memory
Use saved long-term user context.

2. research_web
Search current internet information.

3. save_memory
Store durable preferences, goals, projects,
or other useful long-term information.

4. reason
Analyze and answer.

5. send_email
Email the finished result.

Return ONLY compact JSON:

{{
  "goal": "short goal",
  "use_memory": false,
  "use_research": false,
  "research_query": "",
  "save_memory": false,
  "memory_text": "",
  "memory_category": "general",
  "memory_importance": 5,
  "send_email": false,
  "analysis_instruction": "what the final answer should accomplish"
}}

Rules:

- Use research only when current information is needed.
- Email only if the user asks for an email.
- Save memory only for durable useful information.
- Never save passwords, API keys, tokens,
  banking credentials, or security secrets.
- Do not save a normal one-time question.
- Reading memory is appropriate when personal context
  could materially improve the answer.
- Keep research_query short.
- memory_importance must be 1 through 10.
"""

    raw = call_groq(
        system_prompt=(
            "You are Tyler AI Tool Router. "
            "Choose the minimum tools necessary. "
            "Output JSON only."
        ),
        user_prompt=prompt,
        max_tokens=300,
        temperature=0.0,
    )

    route = parse_json_object(
        raw
    )

    return {
        "goal":
            str(
                route.get(
                    "goal",
                    message
                )
            )[:250],

        "use_memory":
            bool(
                route.get(
                    "use_memory",
                    False
                )
            ),

        "use_research":
            bool(
                route.get(
                    "use_research",
                    False
                )
            ),

        "research_query":
            str(
                route.get(
                    "research_query",
                    ""
                )
            )[:400],

        "save_memory":
            bool(
                route.get(
                    "save_memory",
                    False
                )
            ),

        "memory_text":
            str(
                route.get(
                    "memory_text",
                    ""
                )
            )[:600],

        "memory_category":
            str(
                route.get(
                    "memory_category",
                    "general"
                )
            )[:50],

        "memory_importance":
            clamp(
                route.get(
                    "memory_importance",
                    5
                ),
                1,
                10
            ),

        "send_email":
            bool(
                route.get(
                    "send_email",
                    False
                )
            ),

        "analysis_instruction":
            str(
                route.get(
                    "analysis_instruction",
                    "Answer the user's request."
                )
            )[:500],

        "router":
            "groq-v2",
    }


# =========================================================
# FINAL REASONING
# =========================================================

def build_final_answer(
    user_message,
    route,
    memory_text="",
    research_text=""
):
    prompt = f"""
ORIGINAL REQUEST:
{user_message}

GOAL:
{route["goal"]}

INSTRUCTION:
{route["analysis_instruction"]}

MEMORY CONTEXT:
{memory_text if memory_text else "None needed."}

WEB RESEARCH:
{research_text if research_text else "No web research used."}

Give the user the completed result.

Rules:
- Answer the request directly.
- Use memory only when relevant.
- Use supplied research for current facts.
- Do not invent web research.
- If comparing or ranking, make the conclusion clear.
- Do not mention internal routing.
- Keep the answer useful and reasonably concise.
"""

    return call_groq(
        system_prompt=(
            "You are Tyler AI, an autonomous personal "
            "assistant. Synthesize tool results into "
            "the final useful answer."
        ),
        user_prompt=prompt,
        max_tokens=850,
        temperature=0.2,
    )


# =========================================================
# ROUTE EXECUTION
# =========================================================

def execute_route(
    message,
    route
):
    memory_text = ""
    research = None
    research_text = ""
    memory_result = None
    email_result = None

    # READ MEMORY
    if route["use_memory"]:
        memory_text = (
            compact_memory_context(6)
        )

    # RESEARCH WEB
    if route["use_research"]:
        query = (
            route["research_query"]
            or message
        )

        research = web_search(
            query
        )

        research_text = (
            compact_research(
                research
            )
        )

    # SAVE MEMORY
    if (
        route["save_memory"]
        and route["memory_text"]
    ):
        candidate = (
            route["memory_text"]
            .strip()
        )

        if looks_sensitive(candidate):
            memory_result = {
                "saved": False,
                "reason":
                    "Sensitive information "
                    "was not stored."
            }

        elif memory_exists(candidate):
            memory_result = {
                "saved": False,
                "reason":
                    "Memory already exists."
            }

        else:
            saved = save_memory(
                candidate,
                route[
                    "memory_category"
                ],
                route[
                    "memory_importance"
                ],
            )

            memory_result = {
                "saved": True,
                "memory":
                    candidate,
                "category":
                    route[
                        "memory_category"
                    ],
                "importance":
                    route[
                        "memory_importance"
                    ],
                "database_result":
                    saved,
            }

    # FINAL REASONING
    reply = build_final_answer(
        message,
        route,
        memory_text,
        research_text,
    )

    # EMAIL
    if route["send_email"]:
        email_result = send_email(
            reply,
            "Tyler AI Results"
        )

    return {
        "reply":
            reply,

        "memory_result":
            memory_result,

        "email_result":
            email_result,

        "sources":
            (
                research.get(
                    "sources",
                    []
                )
                if research
                else []
            ),
    }


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "name":
                "Tyler AI",

            "status":
                "online",

            "version":
                "2.0-tool-router",

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
                "save_memory",
                "reason",
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
                "2.0-tool-router",
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
                "success": False,
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
                "success": False,
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
                "success": False,
                "error":
                    "Missing message",
            }
        ), 400


    # =====================================================
    # EXPLICIT MEMORY
    # ZERO GROQ CALLS
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
    # TOOL ROUTER
    # =====================================================

    router_calls = 0

    try:
        route = tool_router(
            message
        )

        router_calls = 1

    except Exception as router_error:
        print(
            "Router fallback:",
            str(router_error)
        )

        route = fallback_route(
            message
        )


    # =====================================================
    # EXECUTE
    # =====================================================

    try:
        result = execute_route(
            message,
            route
        )

    except Exception as e:
        return jsonify(
            {
                "success":
                    False,
                "type":
                    "tool_execution",
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
                "tool_execution",

            "version":
                "2.0-tool-router",

            "route":
                route,

            "reply":
                result[
                    "reply"
                ],

            "memory_result":
                result[
                    "memory_result"
                ],

            "email_result":
                result[
                    "email_result"
                ],

            "sources":
                result[
                    "sources"
                ],

            "router_calls":
                router_calls,

            "answer_calls":
                1,

            "total_groq_calls":
                router_calls + 1,
        }
    )


# =========================================================
# DIRECT N8N PASS-THROUGH
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
