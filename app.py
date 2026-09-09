import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================================================
# ENVIRONMENT VARIABLES
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
    provided = request.headers.get("X-Tyler-Key")

    return bool(
        TYLER_API_KEY
        and provided
        and provided == TYLER_API_KEY
    )


# =========================================================
# GROQ
# =========================================================

def call_groq(
    system_prompt,
    user_prompt,
    max_tokens=900,
    temperature=0.2
):
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
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
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=90,
    )

    try:
        result = response.json()
    except Exception:
        raise RuntimeError(
            f"Groq returned {response.status_code}: "
            f"{response.text[:500]}"
        )

    if not response.ok:
        raise RuntimeError(
            result.get("error", {}).get(
                "message",
                str(result)
            )
        )

    return (
        result["choices"][0]["message"]["content"]
        .strip()
    )


# =========================================================
# SUPABASE MEMORY
# =========================================================

def supabase_headers():
    if not SUPABASE_KEY:
        raise RuntimeError(
            "SUPABASE_KEY is not configured"
        )

    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def get_memories(limit=8):
    if not SUPABASE_URL:
        return []

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/memories",
        headers=supabase_headers(),
        params={
            "select":
                "id,created_at,memories,category,importance",
            "order":
                "importance.desc,created_at.desc",
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


def memory_context(limit=6):
    try:
        memories = get_memories(limit)
    except Exception:
        return "No memory context available."

    if not memories:
        return "No saved long-term memories."

    lines = []

    for item in memories:
        text = str(
            item.get("memories", "")
        )[:350]

        category = item.get(
            "category",
            "general"
        )

        lines.append(
            f"- [{category}] {text}"
        )

    return "\n".join(lines)


def save_memory(
    memory_text,
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
            "Prefer": "return=representation",
        },
        json={
            "memories": memory_text,
            "category": category,
            "importance": importance,
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


# =========================================================
# SIMPLE ROUTING
# No Groq call is required to decide what tool to use.
# =========================================================

def wants_research(message):
    text = message.lower()

    triggers = [
        "research",
        "search the web",
        "look up",
        "find the latest",
        "latest ",
        "right now",
        "current ",
        "today",
        "recent ",
        "developments",
        "news",
    ]

    return any(
        trigger in text
        for trigger in triggers
    )


def wants_email(message):
    text = message.lower()

    triggers = [
        "email me",
        "send me an email",
        "email the",
        "send the results",
        "send results",
    ]

    return any(
        trigger in text
        for trigger in triggers
    )


def wants_memory_save(message):
    text = message.lower()

    triggers = [
        "remember that",
        "remember this",
        "save this to memory",
        "save that to memory",
        "store this",
        "don't forget",
        "do not forget",
    ]

    return any(
        trigger in text
        for trigger in triggers
    )


# =========================================================
# DIRECT MEMORY SAVING
# No Groq call.
# =========================================================

def clean_memory_text(message):
    cleaned = message.strip()

    prefixes = [
        r"^remember that\s+",
        r"^remember this[:\s]+",
        r"^save this to memory[:\s]+",
        r"^save that to memory[:\s]+",
        r"^store this[:\s]+",
        r"^don't forget(?: that)?\s+",
        r"^do not forget(?: that)?\s+",
    ]

    for pattern in prefixes:
        cleaned = re.sub(
            pattern,
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

    return cleaned.strip()


def infer_memory_category(text):
    lower = text.lower()

    if any(
        word in lower
        for word in [
            "goal",
            "want to become",
            "want tyler",
        ]
    ):
        return "goal"

    if any(
        word in lower
        for word in [
            "prefer",
            "favorite",
            "favourite",
            "like ",
        ]
    ):
        return "preference"

    if any(
        word in lower
        for word in [
            "project",
            "building",
            "tyler ai",
        ]
    ):
        return "project"

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
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": 3,
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
        raise RuntimeError(str(result))

    sources = []

    for item in result.get(
        "results",
        []
    )[:3]:

        sources.append(
            {
                "title":
                    item.get("title", ""),
                "url":
                    item.get("url", ""),
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


# =========================================================
# RESEARCH PROMPT BUILDER
# =========================================================

def compact_research_text(research):
    parts = []

    answer = research.get(
        "answer",
        ""
    )

    if answer:
        parts.append(
            "SEARCH SUMMARY:\n"
            + answer
        )

    for index, source in enumerate(
        research.get("sources", []),
        start=1
    ):
        parts.append(
            f"\nSOURCE {index}\n"
            f"Title: {source.get('title', '')}\n"
            f"URL: {source.get('url', '')}\n"
            f"Info: {source.get('content', '')}"
        )

    return "\n".join(parts)


# =========================================================
# N8N
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


def send_email(body, subject="Tyler AI Research Results"):
    if not TYLER_DEFAULT_EMAIL:
        raise RuntimeError(
            "TYLER_DEFAULT_EMAIL is not configured"
        )

    payload = {
        "action": "email",
        "data": {
            "to": TYLER_DEFAULT_EMAIL,
            "subject": subject,
            "message": body,
        },
    }

    response = send_to_n8n(payload)

    return {
        "sent": True,
        "to": TYLER_DEFAULT_EMAIL,
        "subject": subject,
        "n8n_response": response[:300],
    }


# =========================================================
# ONE-CALL RESEARCH ENGINE
# =========================================================

def research_and_answer(
    user_message,
    memories
):
    research = web_search(
        user_message
    )

    research_text = compact_research_text(
        research
    )

    prompt = f"""
USER REQUEST:
{user_message}

RELEVANT LONG-TERM MEMORY:
{memories}

CURRENT WEB RESEARCH:
{research_text}

Complete the user's request using the research above.

Requirements:
- Identify the most important findings.
- Explain why they matter.
- Rank them when appropriate.
- Clearly identify which matters most if asked.
- Do not invent current facts.
- Be concise but useful.
- Include the source URLs supplied above at the end.
"""

    reply = call_groq(
        system_prompt=(
            "You are Tyler AI, an autonomous personal "
            "research and reasoning assistant. "
            "Turn supplied web research into a clear, "
            "accurate final answer."
        ),
        user_prompt=prompt,
        max_tokens=900,
        temperature=0.2,
    )

    return reply, research


# =========================================================
# ONE-CALL NORMAL CHAT
# =========================================================

def normal_answer(
    user_message,
    memories
):
    prompt = f"""
USER:
{user_message}

LONG-TERM MEMORY:
{memories}

Answer the user's request directly and practically.
Do not mention memory unless relevant.
Keep the response focused.
"""

    return call_groq(
        system_prompt=(
            "You are Tyler AI, a capable personal "
            "assistant designed to help Tyler reason, "
            "plan and complete tasks."
        ),
        user_prompt=prompt,
        max_tokens=700,
        temperature=0.3,
    )


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "name": "Tyler AI",
            "status": "online",
            "version": "1.2-ultra-lean",
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
            "routing": "local",
            "tools": [
                "chat",
                "web_research",
                "email",
                "long_term_memory",
            ],
        }
    )


@app.route(
    "/health",
    methods=["GET"]
)
def health():
    return jsonify(
        {
            "status": "healthy",
            "version":
                "1.2-ultra-lean",
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
                "error": "Unauthorized",
            }
        ), 401

    try:
        items = get_memories(50)

        return jsonify(
            {
                "success": True,
                "count": len(items),
                "memories": items,
            }
        )

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "error": str(e),
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
                "error": "Unauthorized",
            }
        ), 401

    data = request.get_json(
        silent=True
    ) or {}

    user_message = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    if not user_message:
        return jsonify(
            {
                "success": False,
                "error": "Missing message",
            }
        ), 400

    # ---------------------------------------------
    # EXPLICIT MEMORY
    # ZERO GROQ CALLS
    # ---------------------------------------------

    if wants_memory_save(
        user_message
    ):
        try:
            memory = clean_memory_text(
                user_message
            )

            if not memory:
                raise RuntimeError(
                    "No memory text found."
                )

            category = (
                infer_memory_category(
                    memory
                )
            )

            saved = save_memory(
                memory,
                category,
                7,
            )

            return jsonify(
                {
                    "success": True,
                    "type": "memory",
                    "saved": True,
                    "category": category,
                    "memory": memory,
                    "database_result": saved,
                    "groq_calls": 0,
                }
            )

        except Exception as e:
            return jsonify(
                {
                    "success": False,
                    "type": "memory",
                    "error": str(e),
                }
            ), 500

    # ---------------------------------------------
    # LOAD SMALL MEMORY CONTEXT
    # ---------------------------------------------

    memories = memory_context(6)

    # ---------------------------------------------
    # RESEARCH
    # ONE GROQ CALL
    # ---------------------------------------------

    if wants_research(
        user_message
    ):
        try:
            reply, research = (
                research_and_answer(
                    user_message,
                    memories,
                )
            )

            email_result = None

            if wants_email(
                user_message
            ):
                email_result = (
                    send_email(
                        reply,
                        "Tyler AI Research Results",
                    )
                )

            return jsonify(
                {
                    "success": True,
                    "type":
                        "research_execution",
                    "reply": reply,
                    "email_result":
                        email_result,
                    "sources":
                        research.get(
                            "sources",
                            []
                        ),
                    "groq_calls": 1,
                    "planner":
                        "local-routing",
                }
            )

        except Exception as e:
            return jsonify(
                {
                    "success": False,
                    "type":
                        "research_execution",
                    "error": str(e),
                }
            ), 500

    # ---------------------------------------------
    # NORMAL CHAT
    # ONE GROQ CALL
    # ---------------------------------------------

    try:
        reply = normal_answer(
            user_message,
            memories,
        )

        email_result = None

        if wants_email(
            user_message
        ):
            email_result = send_email(
                reply,
                "Tyler AI Results",
            )

        return jsonify(
            {
                "success": True,
                "type": "reply",
                "reply": reply,
                "email_result":
                    email_result,
                "groq_calls": 1,
                "planner":
                    "local-routing",
            }
        )

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "error": str(e),
            }
        ), 500


# =========================================================
# N8N WEBHOOK PASS-THROUGH
# =========================================================

@app.route(
    "/webhook",
    methods=["POST"]
)
def webhook():
    if not authorized():
        return jsonify(
            {
                "success": False,
                "error": "Unauthorized",
            }
        ), 401

    data = request.get_json(
        silent=True
    ) or {}

    if not data.get("action"):
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
                "n8n_response":
                    result[:500],
            }
        )

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "error": str(e),
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
