import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
TYLER_API_KEY = os.environ.get("TYLER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
TYLER_DEFAULT_EMAIL = os.environ.get("TYLER_DEFAULT_EMAIL")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

GROQ_MODEL = "openai/gpt-oss-20b"


def authorized():
    provided_key = request.headers.get("X-Tyler-Key")
    return bool(
        TYLER_API_KEY
        and provided_key
        and provided_key == TYLER_API_KEY
    )


def call_groq(messages, temperature=0.2, max_tokens=1200):
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
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": messages,
        },
        timeout=90,
    )

    result = response.json()

    if not response.ok:
        raise RuntimeError(str(result))

    return result["choices"][0]["message"]["content"].strip()


def supabase_headers():
    if not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_KEY is not configured")

    return {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
    }


def get_memories(limit=12):
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is not configured")

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
            f"Supabase read failed: {response.status_code} {response.text}"
        )

    return response.json()


def save_memory(memory_text, category="general", importance=5):
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
            f"Supabase save failed: {response.status_code} {response.text}"
        )

    return response.json()


def update_memory(memory_id, memory_text, category="general", importance=5):
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/memories",
        headers={
            **supabase_headers(),
            "Prefer": "return=representation",
        },
        params={"id": f"eq.{memory_id}"},
        json={
            "memories": memory_text,
            "category": category,
            "importance": importance,
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase update failed: {response.status_code} {response.text}"
        )

    return response.json()


def memory_context(limit=8):
    memories = get_memories(limit)

    if not memories:
        return "No saved long-term memories."

    lines = []

    for item in memories:
        lines.append(
            f"ID {item.get('id')} | "
            f"{item.get('category', 'general')} | "
            f"{item.get('memories', '')} | "
            f"importance {item.get('importance', 5)}"
        )

    return "\n".join(lines)


def wants_to_remember(message):
    text = message.lower()

    triggers = [
        "remember that",
        "remember this",
        "save this",
        "save that",
        "add this to memory",
        "store this",
        "don't forget",
    ]

    return any(trigger in text for trigger in triggers)


def analyze_memory(user_message, memory_text, explicit=False):
    prompt = f"""
You manage long-term memory for Tyler AI.

USER MESSAGE:
{user_message}

EXISTING MEMORIES:
{memory_text}

Explicit memory request: {explicit}

Decide whether this message should affect long-term memory.

Return ONLY valid JSON in one of these forms.

NO CHANGE:
{{
  "action": "skip",
  "reason": "not worth storing or already covered"
}}

CREATE:
{{
  "action": "create",
  "memory": "concise durable fact",
  "category": "preference, project, person, task, goal, career, or general",
  "importance": 5
}}

UPDATE:
{{
  "action": "update",
  "id": 2,
  "memory": "merged or improved durable fact",
  "category": "preference, project, person, task, goal, career, or general",
  "importance": 5
}}

Rules:
- Be selective unless explicit memory request is true.
- Never store passwords, API keys, tokens, banking credentials, or secrets.
- Never update an unrelated memory.
- Importance must be 1 to 10.
"""

    raw = call_groq(
        [
            {
                "role": "system",
                "content": "You are Tyler AI's memory manager.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        max_tokens=500,
    )

    try:
        result = json.loads(raw)
    except Exception:
        return {"action": "skip", "reason": "invalid memory decision"}

    action = result.get("action", "skip")

    if action not in {"create", "update", "skip"}:
        return {"action": "skip", "reason": "invalid action"}

    if action in {"create", "update"}:
        importance = int(result.get("importance", 5))
        importance = max(1, min(10, importance))
        result["importance"] = importance

    return result


def apply_memory_decision(decision):
    action = decision.get("action")

    if action == "create":
        save_memory(
            decision.get("memory", ""),
            decision.get("category", "general"),
            decision.get("importance", 5),
        )

        return {
            "saved": True,
            "action": "create",
            "memory": decision.get("memory", ""),
        }

    if action == "update":
        memory_id = decision.get("id")

        if memory_id is None:
            return {
                "saved": False,
                "action": "skip",
                "reason": "missing memory id",
            }

        update_memory(
            memory_id,
            decision.get("memory", ""),
            decision.get("category", "general"),
            decision.get("importance", 5),
        )

        return {
            "saved": True,
            "action": "update",
            "id": memory_id,
            "memory": decision.get("memory", ""),
        }

    return {
        "saved": False,
        "action": "skip",
        "reason": decision.get("reason", "not stored"),
    }


def web_search(query):
    if not TAVILY_API_KEY:
        raise RuntimeError("TAVILY_API_KEY is not configured")

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
            "max_results": 3,
        },
        timeout=60,
    )

    result = response.json()

    if not response.ok:
        raise RuntimeError(str(result))

    trimmed_sources = []

    for item in result.get("results", [])[:3]:
        content = str(item.get("content", ""))[:700]

        trimmed_sources.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "content": content,
            }
        )

    return {
        "answer": str(result.get("answer", ""))[:1200],
        "sources": trimmed_sources,
    }


def send_to_n8n(payload):
    if not N8N_WEBHOOK_URL:
        return {
            "success": False,
            "error": "N8N_WEBHOOK_URL is not configured",
        }, 500

    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=60,
        )

        return {
            "success": response.ok,
            "status_code": response.status_code,
            "n8n_response": response.text,
        }, response.status_code

    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e),
        }, 502


def create_compact_plan(user_message, memory_text):
    prompt = f"""
You are Tyler AI Planner.

USER REQUEST:
{user_message}

LONG-TERM MEMORY:
{memory_text}

Available tools:
- research_web
- reason
- send_email

Return ONLY JSON:

{{
  "goal": "short goal",
  "needs_research": true,
  "needs_email": true,
  "research_query": "single compact search query",
  "analysis_instruction": "what Tyler should determine"
}}

Rules:
- needs_research should be true only if current/live web info is needed.
- needs_email should be true only if the user explicitly asked for an email.
- Keep the research query short and focused.
- Do not invent tools.
"""

    raw = call_groq(
        [
            {
                "role": "system",
                "content": "Create minimal executable plans.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        max_tokens=350,
    )

    try:
        result = json.loads(raw)

        return {
            "goal": result.get("goal", user_message),
            "needs_research": bool(result.get("needs_research", False)),
            "needs_email": bool(result.get("needs_email", False)),
            "research_query": result.get("research_query", user_message),
            "analysis_instruction": result.get(
                "analysis_instruction",
                user_message,
            ),
        }

    except Exception:
        return {
            "goal": user_message,
            "needs_research": False,
            "needs_email": False,
            "research_query": user_message,
            "analysis_instruction": user_message,
        }


def analyze_and_answer(
    user_message,
    plan,
    memory_text,
    research=None,
):
    research_text = "No live research performed."

    if research:
        sources_text = ""

        for index, source in enumerate(
            research.get("sources", []),
            start=1,
        ):
            sources_text += f"""
SOURCE {index}
Title: {source.get("title")}
URL: {source.get("url")}
Content: {source.get("content")}
"""

        research_text = f"""
LIVE SEARCH ANSWER:
{research.get("answer", "")}

SOURCES:
{sources_text}
"""

    prompt = f"""
You are Tyler AI.

USER REQUEST:
{user_message}

GOAL:
{plan["goal"]}

ANALYSIS INSTRUCTION:
{plan["analysis_instruction"]}

LONG-TERM MEMORY:
{memory_text}

RESEARCH:
{research_text}

Create the final useful response.

Rules:
- Answer the original request directly.
- If research exists, use it and do not invent facts.
- If asked to rank or compare, do that clearly.
- If an email will be sent, produce content suitable for emailing too.
- Keep the answer concise enough to avoid wasting tokens.
"""

    return call_groq(
        [
            {
                "role": "system",
                "content": "You are Tyler AI's analysis and response engine.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_tokens=1000,
    )


def send_email(content, goal):
    if not TYLER_DEFAULT_EMAIL:
        raise RuntimeError("TYLER_DEFAULT_EMAIL is not configured")

    subject_prompt = f"""
Create a short email subject for this goal:

{goal}

Return only the subject text.
"""

    try:
        subject = call_groq(
            [
                {
                    "role": "system",
                    "content": "Create short email subjects.",
                },
                {
                    "role": "user",
                    "content": subject_prompt,
                },
            ],
            temperature=0.1,
            max_tokens=40,
        )
    except Exception:
        subject = "Tyler AI Results"

    payload = {
        "action": "email",
        "data": {
            "to": TYLER_DEFAULT_EMAIL,
            "subject": subject[:120],
            "message": content,
        },
    }

    result, status_code = send_to_n8n(payload)

    if not result.get("success"):
        raise RuntimeError(
            f"Email action failed: {result}"
        )

    return {
        "sent": True,
        "to": TYLER_DEFAULT_EMAIL,
        "subject": subject[:120],
    }


@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "name": "Tyler AI",
            "status": "online",
            "groq_connected": bool(GROQ_API_KEY),
            "tavily_connected": bool(TAVILY_API_KEY),
            "n8n_connected": bool(N8N_WEBHOOK_URL),
            "memory_connected": bool(
                SUPABASE_URL and SUPABASE_KEY
            ),
            "planner_enabled": True,
            "planner_version": "1.1-lean",
            "secured": bool(TYLER_API_KEY),
            "tools": [
                "planner",
                "reason",
                "web_research",
                "email",
                "long_term_memory",
                "memory_merge_update",
            ],
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "healthy",
            "planner_version": "1.1-lean",
        }
    )


@app.route("/memories", methods=["GET"])
def memories_route():
    if not authorized():
        return jsonify(
            {
                "success": False,
                "error": "Unauthorized",
            }
        ), 401

    try:
        memories = get_memories(50)

        return jsonify(
            {
                "success": True,
                "count": len(memories),
                "memories": memories,
            }
        )

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "error": str(e),
            }
        ), 500


@app.route("/chat", methods=["POST"])
def chat():
    if not authorized():
        return jsonify(
            {
                "success": False,
                "error": "Unauthorized",
            }
        ), 401

    data = request.get_json(silent=True) or {}

    user_message = data.get("message")

    if not user_message:
        return jsonify(
            {
                "success": False,
                "error": "Missing message",
            }
        ), 400

    try:
        memory_text = memory_context(8)
    except Exception:
        memory_text = "Memory unavailable."

    explicit_memory = wants_to_remember(user_message)

    memory_result = None

    try:
        memory_decision = analyze_memory(
            user_message,
            memory_text,
            explicit=explicit_memory,
        )

        memory_result = apply_memory_decision(
            memory_decision
        )

    except Exception as e:
        memory_result = {
            "saved": False,
            "action": "error",
            "reason": str(e),
        }

    if explicit_memory:
        return jsonify(
            {
                "success": True,
                "type": "memory",
                "memory_result": memory_result,
            }
        )

    try:
        plan = create_compact_plan(
            user_message,
            memory_text,
        )
    except Exception as e:
        return jsonify(
            {
                "success": False,
                "error": f"Planner failed: {str(e)}",
            }
        ), 500

    research = None

    if plan["needs_research"]:
        try:
            research = web_search(
                plan["research_query"]
            )
        except Exception as e:
            return jsonify(
                {
                    "success": False,
                    "plan": plan,
                    "error": f"Research failed: {str(e)}",
                }
            ), 500

    try:
        reply = analyze_and_answer(
            user_message,
            plan,
            memory_text,
            research,
        )
    except Exception as e:
        return jsonify(
            {
                "success": False,
                "plan": plan,
                "error": f"Analysis failed: {str(e)}",
            }
        ), 500

    email_result = None

    if plan["needs_email"]:
        try:
            email_result = send_email(
                reply,
                plan["goal"],
            )
        except Exception as e:
            return jsonify(
                {
                    "success": False,
                    "plan": plan,
                    "reply": reply,
                    "error": f"Email failed: {str(e)}",
                }
            ), 500

    return jsonify(
        {
            "success": True,
            "type": "planned_execution",
            "goal": plan["goal"],
            "plan": {
                "needs_research": plan["needs_research"],
                "needs_email": plan["needs_email"],
                "research_query": plan["research_query"],
                "analysis_instruction": plan["analysis_instruction"],
            },
            "memory_result": memory_result,
            "reply": reply,
            "email_result": email_result,
            "sources": (
                research.get("sources", [])
                if research
                else []
            ),
        }
    )


@app.route("/webhook", methods=["POST"])
def webhook():
    if not authorized():
        return jsonify(
            {
                "success": False,
                "error": "Unauthorized",
            }
        ), 401

    data = request.get_json(silent=True) or {}

    if not data.get("action"):
        return jsonify(
            {
                "success": False,
                "error": "Missing action",
            }
        ), 400

    result, status_code = send_to_n8n(data)

    return jsonify(result), status_code


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
