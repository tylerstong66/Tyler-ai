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
# TAVILY WEB SEARCH
# ==================================================

def web_search(query):

    if not TAVILY_API_KEY:
        raise RuntimeError("TAVILY_API_KEY is not configured")

    response = requests.post(
        "https://api.tavily.com/search",
        headers={
            "Authorization": f"Bearer {TAVILY_API_KEY}",
            "Content-Type": "application/json"
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

    for item in result.get("results", []):
        sources.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("content")
        })

    return {
        "answer": result.get("answer", ""),
        "sources": sources
    }


# ==================================================
# N8N
# ==================================================

def send_to_n8n(payload):

    if not N8N_WEBHOOK_URL:
        return {
            "success": False,
            "error": "N8N_WEBHOOK_URL is not configured"
        }, 500

    try:

        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=60
        )

        return {
            "success": response.ok,
            "status_code": response.status_code,
            "n8n_response": response.text
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

    return any(trigger in text for trigger in triggers)


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

    return any(trigger in text for trigger in triggers)


# ==================================================
# RESEARCH SUMMARY
# ==================================================

def create_research_summary(user_message, research):

    source_text = ""

    for index, source in enumerate(research["sources"], start=1):

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
- Base the response on the supplied live search results.
- Do not invent facts.
- Mention uncertainty when appropriate.
- Include a short Sources section with the URLs.
"""

    return call_groq(
        [
            {
                "role": "system",
                "content": (
                    "You are Tyler AI. "
                    "You analyze live web research and produce clear reports."
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

def create_email_from_content(user_request, content):

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
                    "Create concise, useful emails."
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
            "subject": "Message from Tyler AI",
            "message": content
        }


# ==================================================
# HOME
# ==================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "name": "Tyler AI",
        "status": "online",
        "groq_connected": bool(GROQ_API_KEY),
        "tavily_connected": bool(TAVILY_API_KEY),
        "n8n_connected": bool(N8N_WEBHOOK_URL),
        "secured": bool(TYLER_API_KEY),
        "default_email_configured": bool(TYLER_DEFAULT_EMAIL),
        "tools": [
            "chat",
            "web_research",
            "email"
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
# CHAT + TOOL USE
# ==================================================

@app.route("/chat", methods=["POST"])
def chat():

    if not authorized():

        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    data = request.get_json(silent=True) or {}

    user_message = data.get("message")

    if not user_message:

        return jsonify({
            "success": False,
            "error": "Missing message"
        }), 400


    email_requested = wants_email(user_message)
    research_requested = wants_research(user_message)


    # ==================================================
    # RESEARCH
    # ==================================================

    if research_requested:

        try:

            research = web_search(user_message)

            summary = create_research_summary(
                user_message,
                research
            )

            # ------------------------------------------
            # RESEARCH + EMAIL
            # ------------------------------------------

            if email_requested:

                if not TYLER_DEFAULT_EMAIL:

                    return jsonify({
                        "success": False,
                        "error": (
                            "TYLER_DEFAULT_EMAIL "
                            "is not configured"
                        )
                    }), 500

                email = create_email_from_content(
                    user_message,
                    summary
                )

                payload = {
                    "action": "email",
                    "data": {
                        "to": TYLER_DEFAULT_EMAIL,
                        "subject": email["subject"],
                        "message": email["message"]
                    }
                }

                n8n_result, status_code = send_to_n8n(
                    payload
                )

                if not n8n_result.get("success"):

                    return jsonify({
                        "success": False,
                        "type": "action",
                        "action": "research_and_email",
                        "error": n8n_result
                    }), status_code

                return jsonify({
                    "success": True,
                    "type": "action",
                    "action": "research_and_email",
                    "message": (
                        "Research completed and "
                        "email sent successfully."
                    ),
                    "to": TYLER_DEFAULT_EMAIL,
                    "subject": email["subject"],
                    "research_summary": summary,
                    "sources": research["sources"]
                })


            # ------------------------------------------
            # RESEARCH ONLY
            # ------------------------------------------

            return jsonify({
                "success": True,
                "type": "research",
                "reply": summary,
                "sources": research["sources"]
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
                "error": (
                    "TYLER_DEFAULT_EMAIL "
                    "is not configured"
                )
            }), 500

        try:

            email = create_email_from_content(
                user_message,
                user_message
            )

            payload = {
                "action": "email",
                "data": {
                    "to": TYLER_DEFAULT_EMAIL,
                    "subject": email["subject"],
                    "message": email["message"]
                }
            }

            n8n_result, status_code = send_to_n8n(
                payload
            )

            if not n8n_result.get("success"):

                return jsonify({
                    "success": False,
                    "type": "action",
                    "action": "email",
                    "error": n8n_result
                }), status_code

            return jsonify({
                "success": True,
                "type": "action",
                "action": "email",
                "message": "Email sent successfully.",
                "to": TYLER_DEFAULT_EMAIL,
                "subject": email["subject"]
            })


        except Exception as e:

            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    # ==================================================
    # NORMAL CHAT
    # ==================================================

    try:

        reply = call_groq(
            [
                {
                    "role": "system",
                    "content": """
You are Tyler AI.

You currently have these real tools:
1. Live web research
2. Email
3. General reasoning and conversation

Never claim you performed an external action unless
the application actually executed that action.

Be practical, concise, and useful.
"""
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        return jsonify({
            "success": True,
            "type": "reply",
            "reply": reply
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

    data = request.get_json(silent=True) or {}

    if not data.get("action"):

        return jsonify({
            "success": False,
            "error": "Missing action"
        }), 400

    result, status_code = send_to_n8n(data)

    return jsonify(result), status_code


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
