import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==================================================
# ENVIRONMENT VARIABLES
# ==================================================

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
TYLER_API_KEY = os.environ.get("TYLER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
TYLER_DEFAULT_EMAIL = os.environ.get("TYLER_DEFAULT_EMAIL")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


# ==================================================
# SECURITY
# ==================================================

def authorized():
    provided_key = request.headers.get("X-Tyler-Key")

    return bool(
        TYLER_API_KEY
        and provided_key
        and provided_key == TYLER_API_KEY
    )


# ==================================================
# GROQ
# ==================================================

def call_groq(messages, temperature=0.3):

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-oss-20b",
            "temperature": temperature,
            "messages": messages
        },
        timeout=90
    )

    result = response.json()

    if not response.ok:
        raise RuntimeError(str(result))

    return result["choices"][0]["message"]["content"].strip()


# ==================================================
# SUPABASE MEMORY
# ==================================================

def supabase_headers():

    if not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_KEY is not configured")

    return {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }


def save_memory(memory_text, category="general", importance=5):

    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is not configured")

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/memories",
        headers={
            **supabase_headers(),
            "Prefer": "return=representation"
        },
        json={
            "memories": memory_text,
            "category": category,
            "importance": importance
        },
        timeout=30
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase save failed: "
            f"{response.status_code} {response.text}"
        )

    return response.json()


def get_memories(limit=20):

    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is not configured")

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/memories",
        headers=supabase_headers(),
        params={
            "select": "id,created_at,memories,category,importance",
            "order": "importance.desc,created_at.desc",
            "limit": limit
        },
        timeout=30
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase read failed: "
            f"{response.status_code} {response.text}"
        )

    return response.json()


def memory_context(limit=12):

    memories = get_memories(limit)

    if not memories:
        return "No saved long-term memories yet."

    lines = []

    for item in memories:

        lines.append(
            f"- [{item.get('category', 'general')}] "
            f"{item.get('memories', '')} "
            f"(importance {item.get('importance', 5)})"
        )

    return "\n".join(lines)


def memory_already_exists(memory_text):

    try:

        memories = get_memories(50)

        target = memory_text.strip().lower()

        for item in memories:

            existing = str(
                item.get("memories", "")
            ).strip().lower()

            if existing == target:
                return True

        return False

    except Exception:
        return False


# ==================================================
# EXPLICIT MEMORY
# ==================================================

def wants_to_remember(message):

    text = message.lower()

    triggers = [
        "remember that",
        "remember this",
        "save this",
        "save that",
        "add this to memory",
        "store this",
        "don't forget"
    ]

    return any(trigger in text for trigger in triggers)


def create_memory_from_request(user_message):

    prompt = f"""
The user explicitly asked Tyler AI to remember something.

User message:
{user_message}

Extract the useful long-term information.

Return ONLY valid JSON:

{{
  "memory": "concise memory",
  "category": "preference, project, person, task, goal, career, or general",
  "importance": 5
}}

Importance must be an integer from 1 to 10.

Never store:
- passwords
- API keys
- authentication tokens
- credit card numbers
- banking credentials
- private security information

Do not include markdown.
"""

    raw = call_groq(
        [
            {
                "role": "system",
                "content": (
                    "You extract concise long-term memories "
                    "for an AI assistant."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1
    )

    try:

        result = json.loads(raw)

        importance = int(
            result.get("importance", 5)
        )

        importance = max(
            1,
            min(10, importance)
        )

        return {
            "memory": result.get(
                "memory",
                user_message
            ),
            "category": result.get(
                "category",
                "general"
            ),
            "importance": importance
        }

    except Exception:

        return {
            "memory": user_message,
            "category": "general",
            "importance": 5
        }


# ==================================================
# AUTOMATIC MEMORY DETECTION
# ==================================================

def analyze_for_automatic_memory(user_message):

    prompt = f"""
Decide whether this user message contains information
worth saving in long-term memory for Tyler AI.

User message:
{user_message}

Save durable information such as:
- stable preferences
- long-term goals
- important projects
- ongoing plans
- career direction
- recurring workflows
- important decisions
- useful personal context that will help future responses

Do NOT save:
- casual conversation
- one-time questions
- temporary instructions
- news requests
- search queries
- email commands
- passwords
- API keys
- tokens
- financial account credentials
- authentication information
- highly sensitive secrets

Return ONLY valid JSON.

If it should NOT be saved:

{{
  "save": false
}}

If it SHOULD be saved:

{{
  "save": true,
  "memory": "concise durable fact",
  "category": "preference, project, person, task, goal, career, or general",
  "importance": 5
}}

Importance must be 1 through 10.
"""

    raw = call_groq(
        [
            {
                "role": "system",
                "content": (
                    "You are the memory manager for Tyler AI. "
                    "Be selective. Only durable useful information "
                    "should become long-term memory."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1
    )

    try:

        result = json.loads(raw)

        if not result.get("save"):
            return None

        memory_text = str(
            result.get("memory", "")
        ).strip()

        if not memory_text:
            return None

        importance = int(
            result.get("importance", 5)
        )

        importance = max(
            1,
            min(10, importance)
        )

        return {
            "memory": memory_text,
            "category": result.get(
                "category",
                "general"
            ),
            "importance": importance
        }

    except Exception:
        return None


def maybe_save_automatic_memory(user_message):

    try:

        candidate = analyze_for_automatic_memory(
            user_message
        )

        if not candidate:
            return None

        if memory_already_exists(
            candidate["memory"]
        ):
            return {
                "saved": False,
                "reason": "duplicate",
                "memory": candidate["memory"]
            }

        save_memory(
            candidate["memory"],
            candidate["category"],
            candidate["importance"]
        )

        return {
            "saved": True,
            "memory": candidate["memory"],
            "category": candidate["category"],
            "importance": candidate["importance"]
        }

    except Exception as e:

        print(
            "Automatic memory error:",
            str(e)
        )

        return None


# ==================================================
# TAVILY WEB SEARCH
# ==================================================

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
                "application/json"
        },
        json={
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": 5
        },
        timeout=60
    )

    result = response.json()

    if not response.ok:
        raise RuntimeError(str(result))

    sources = []

    for item in result.get(
        "results",
        []
    ):

        sources.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("content")
        })

    return {
        "answer": result.get(
            "answer",
            ""
        ),
        "sources": sources
    }


# ==================================================
# N8N
# ==================================================

def send_to_n8n(payload):

    if not N8N_WEBHOOK_URL:

        return {
            "success": False,
            "error":
                "N8N_WEBHOOK_URL is not configured"
        }, 500

    try:

        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=60
        )

        return {
            "success": response.ok,
            "status_code":
                response.status_code,
            "n8n_response":
                response.text
        }, response.status_code

    except requests.RequestException as e:

        return {
            "success": False,
            "error": str(e)
        }, 502


# ==================================================
# INTENT DETECTION
# ==================================================

def wants_email(message):

    text = message.lower()

    triggers = [
        "email me",
        "send me an email",
        "send an email to me",
        "email this to me",
        "email that to me",
        "email me a",
        "email me the"
    ]

    return any(
        trigger in text
        for trigger in triggers
    )


def wants_research(message):

    text = message.lower()

    triggers = [
        "research",
        "search the web",
        "search online",
        "look online",
        "look up",
        "latest",
        "current news",
        "latest news",
        "find information",
        "find out"
    ]

    return any(
        trigger in text
        for trigger in triggers
    )


# ==================================================
# RESEARCH SUMMARY
# ==================================================

def create_research_summary(
    user_message,
    research
):

    source_text = ""

    for index, source in enumerate(
        research["sources"],
        start=1
    ):

        source_text += f"""
SOURCE {index}
Title: {source.get("title")}
URL: {source.get("url")}
Content: {source.get("content")}
"""

    prompt = f"""
The user asked:

{user_message}

Live web search returned:

Tavily answer:
{research["answer"]}

Sources:
{source_text}

Create a useful, concise research report.

Rules:
- Base the response on supplied live results.
- Do not invent facts.
- Mention uncertainty when appropriate.
- Include a short Sources section with URLs.
"""

    return call_groq(
        [
            {
                "role": "system",
                "content": (
                    "You are Tyler AI. "
                    "You analyze live web research."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )


# ==================================================
# EMAIL CREATION
# ==================================================

def create_email_from_content(
    user_request,
    content
):

    prompt = f"""
The user requested:

{user_request}

Here is the content to use:

{content}

Create an email.

Return ONLY valid JSON:

{{
  "subject": "short subject",
  "message": "email body"
}}

Do not include markdown fences.
"""

    raw = call_groq(
        [
            {
                "role": "system",
                "content": (
                    "You are Tyler AI. "
                    "Create concise useful emails."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    try:

        result = json.loads(raw)

        return {
            "subject": result.get(
                "subject",
                "Message from Tyler AI"
            ),
            "message": result.get(
                "message",
                content
            )
        }

    except json.JSONDecodeError:

        return {
            "subject":
                "Message from Tyler AI",
            "message":
                content
        }


# ==================================================
# HOME
# ==================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "name": "Tyler AI",
        "status": "online",

        "groq_connected":
            bool(GROQ_API_KEY),

        "tavily_connected":
            bool(TAVILY_API_KEY),

        "n8n_connected":
            bool(N8N_WEBHOOK_URL),

        "memory_connected":
            bool(
                SUPABASE_URL
                and SUPABASE_KEY
            ),

        "secured":
            bool(TYLER_API_KEY),

        "default_email_configured":
            bool(TYLER_DEFAULT_EMAIL),

        "tools": [
            "chat",
            "web_research",
            "email",
            "long_term_memory",
            "automatic_memory"
        ]
    })


# ==================================================
# HEALTH
# ==================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "healthy"
    })


# ==================================================
# MEMORY ENDPOINT
# ==================================================

@app.route("/memories", methods=["GET"])
def memories_route():

    if not authorized():

        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    try:

        memories = get_memories(50)

        return jsonify({
            "success": True,
            "count": len(memories),
            "memories": memories
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================================================
# CHAT
# ==================================================

@app.route("/chat", methods=["POST"])
def chat():

    if not authorized():

        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    user_message = data.get(
        "message"
    )

    if not user_message:

        return jsonify({
            "success": False,
            "error": "Missing message"
        }), 400


    # ==================================================
    # EXPLICIT MEMORY
    # ==================================================

    if wants_to_remember(
        user_message
    ):

        try:

            memory = (
                create_memory_from_request(
                    user_message
                )
            )

            if not memory_already_exists(
                memory["memory"]
            ):

                save_memory(
                    memory["memory"],
                    memory["category"],
                    memory["importance"]
                )

            return jsonify({
                "success": True,
                "type": "memory",
                "action": "saved",
                "memory":
                    memory["memory"],
                "category":
                    memory["category"],
                "importance":
                    memory["importance"]
            })

        except Exception as e:

            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    email_requested = wants_email(
        user_message
    )

    research_requested = wants_research(
        user_message
    )


    # ==================================================
    # AUTOMATIC MEMORY CHECK
    # ==================================================

    automatic_memory = (
        maybe_save_automatic_memory(
            user_message
        )
    )


    # ==================================================
    # RESEARCH
    # ==================================================

    if research_requested:

        try:

            research = web_search(
                user_message
            )

            summary = (
                create_research_summary(
                    user_message,
                    research
                )
            )

            if email_requested:

                if not TYLER_DEFAULT_EMAIL:

                    return jsonify({
                        "success": False,
                        "error":
                            "TYLER_DEFAULT_EMAIL is not configured"
                    }), 500

                email = (
                    create_email_from_content(
                        user_message,
                        summary
                    )
                )

                payload = {
                    "action": "email",
                    "data": {
                        "to":
                            TYLER_DEFAULT_EMAIL,
                        "subject":
                            email["subject"],
                        "message":
                            email["message"]
                    }
                }

                n8n_result, status_code = (
                    send_to_n8n(payload)
                )

                if not n8n_result.get(
                    "success"
                ):

                    return jsonify({
                        "success": False,
                        "type": "action",
                        "action":
                            "research_and_email",
                        "error":
                            n8n_result
                    }), status_code

                return jsonify({
                    "success": True,
                    "type": "action",
                    "action":
                        "research_and_email",
                    "message":
                        "Research completed and email sent successfully.",
                    "to":
                        TYLER_DEFAULT_EMAIL,
                    "subject":
                        email["subject"],
                    "research_summary":
                        summary,
                    "sources":
                        research["sources"],
                    "automatic_memory":
                        automatic_memory
                })

            return jsonify({
                "success": True,
                "type": "research",
                "reply": summary,
                "sources":
                    research["sources"],
                "automatic_memory":
                    automatic_memory
            })

        except Exception as e:

            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    # ==================================================
    # EMAIL ONLY
    # ==================================================

    if email_requested:

        if not TYLER_DEFAULT_EMAIL:

            return jsonify({
                "success": False,
                "error":
                    "TYLER_DEFAULT_EMAIL is not configured"
            }), 500

        try:

            context = memory_context(
                12
            )

            email_content = f"""
User request:
{user_message}

Relevant long-term memory:
{context}
"""

            email = (
                create_email_from_content(
                    user_message,
                    email_content
                )
            )

            payload = {
                "action": "email",
                "data": {
                    "to":
                        TYLER_DEFAULT_EMAIL,
                    "subject":
                        email["subject"],
                    "message":
                        email["message"]
                }
            }

            n8n_result, status_code = (
                send_to_n8n(payload)
            )

            if not n8n_result.get(
                "success"
            ):

                return jsonify({
                    "success": False,
                    "type": "action",
                    "action": "email",
                    "error":
                        n8n_result
                }), status_code

            return jsonify({
                "success": True,
                "type": "action",
                "action": "email",
                "message":
                    "Email sent successfully.",
                "to":
                    TYLER_DEFAULT_EMAIL,
                "subject":
                    email["subject"],
                "automatic_memory":
                    automatic_memory
            })

        except Exception as e:

            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    # ==================================================
    # NORMAL CHAT WITH MEMORY
    # ==================================================

    try:

        context = memory_context(
            12
        )

        reply = call_groq(
            [
                {
                    "role": "system",
                    "content": f"""
You are Tyler AI.

You currently have these real tools:

1. Live web research
2. Email
3. Persistent long-term memory
4. Automatic memory
5. General reasoning

Long-term memory:

{context}

Use memory only when relevant.

Never claim you performed an external action
unless the application actually executed it.

Be practical, concise, and useful.
"""
                },
                {
                    "role": "user",
                    "content":
                        user_message
                }
            ]
        )

        return jsonify({
            "success": True,
            "type": "reply",
            "reply": reply,
            "automatic_memory":
                automatic_memory
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================================================
# DIRECT N8N ACTION ENDPOINT
# ==================================================

@app.route("/webhook", methods=["POST"])
def webhook():

    if not authorized():

        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    if not data.get("action"):

        return jsonify({
            "success": False,
            "error": "Missing action"
        }), 400

    result, status_code = (
        send_to_n8n(data)
    )

    return jsonify(
        result
    ), status_code


# ==================================================
# START SERVER
# ==================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
