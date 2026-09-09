import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --------------------------------------------------
# ENVIRONMENT VARIABLES
# --------------------------------------------------

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
TYLER_API_KEY = os.environ.get("TYLER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TYLER_DEFAULT_EMAIL = os.environ.get("TYLER_DEFAULT_EMAIL")


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def authorized():
    provided_key = request.headers.get("X-Tyler-Key")
    return bool(
        TYLER_API_KEY
        and provided_key
        and provided_key == TYLER_API_KEY
    )


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
        timeout=60
    )

    result = response.json()

    if not response.ok:
        raise RuntimeError(str(result))

    return result["choices"][0]["message"]["content"].strip()


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


def is_email_me_request(message):
    text = message.lower()

    triggers = [
        "email me",
        "send me an email",
        "send an email to me",
        "email this to me",
        "email that to me"
    ]

    return any(trigger in text for trigger in triggers)


def create_email_from_request(user_message):
    system_prompt = """
You are Tyler AI.

The user wants you to send them an email.

Create a concise email based on the user's request.

Return ONLY valid JSON in this exact structure:

{
  "subject": "email subject",
  "message": "email body"
}

Do not include markdown.
Do not include explanations.
Do not say you cannot send email.
"""

    raw = call_groq(
        [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        temperature=0.2
    )

    try:
        result = json.loads(raw)

        return {
            "subject": result.get("subject", "Message from Tyler AI"),
            "message": result.get("message", raw)
        }

    except json.JSONDecodeError:
        return {
            "subject": "Message from Tyler AI",
            "message": raw
        }


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "name": "Tyler AI",
        "status": "online",
        "groq_connected": bool(GROQ_API_KEY),
        "n8n_connected": bool(N8N_WEBHOOK_URL),
        "secured": bool(TYLER_API_KEY),
        "default_email_configured": bool(TYLER_DEFAULT_EMAIL)
    })


# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy"
    })


# --------------------------------------------------
# CHAT + TOOL USE
# --------------------------------------------------

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

    # --------------------------------------------------
    # EMAIL ME TOOL
    # --------------------------------------------------

    if is_email_me_request(user_message):

        if not TYLER_DEFAULT_EMAIL:
            return jsonify({
                "success": False,
                "error": "TYLER_DEFAULT_EMAIL is not configured"
            }), 500

        try:
            email = create_email_from_request(user_message)

            payload = {
                "action": "email",
                "data": {
                    "to": TYLER_DEFAULT_EMAIL,
                    "subject": email["subject"],
                    "message": email["message"]
                }
            }

            n8n_result, status_code = send_to_n8n(payload)

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

    # --------------------------------------------------
    # NORMAL AI CHAT
    # --------------------------------------------------

    try:
        reply = call_groq(
            [
                {
                    "role": "system",
                    "content": """
You are Tyler AI, a practical AI assistant.

You can currently:
- answer questions
- reason through problems
- help plan tasks
- generate content
- send an email to the user when they explicitly ask you to email them

Never claim you completed an external action unless the application actually executed it.
Be concise, useful, and action-oriented.
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


# --------------------------------------------------
# DIRECT N8N ACTION ENDPOINT
# --------------------------------------------------

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


# --------------------------------------------------
# START SERVER
# --------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
