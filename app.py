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
