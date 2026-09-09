import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Environment variables
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
TYLER_API_KEY = os.environ.get("TYLER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "name": "Tyler AI",
        "status": "online",
        "n8n_connected": bool(N8N_WEBHOOK_URL),
        "groq_connected": bool(GROQ_API_KEY)
    })


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy"
    })


# --------------------------------------------------
# AI CHAT - GROQ
# --------------------------------------------------

@app.route("/chat", methods=["POST"])
def chat():

    if not GROQ_API_KEY:
        return jsonify({
            "success": False,
            "error": "GROQ_API_KEY is not configured"
        }), 500

    data = request.get_json(silent=True) or {}

    message = data.get("message")

    if not message:
        return jsonify({
            "success": False,
            "error": "Missing message"
        }), 400

    try:

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",

            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },

            json={
                "model": "openai/gpt-oss-20b",

                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Tyler AI, a practical AI assistant. "
                            "You help with research, planning, automation, "
                            "reasoning, and completing tasks. "
                            "Be helpful, concise, and action-oriented."
                        )
                    },

                    {
                        "role": "user",
                        "content": message
                    }
                ]
            },

            timeout=60
        )

        result = response.json()

        if not response.ok:
            return jsonify({
                "success": False,
                "error": result
            }), response.status_code

        reply = result["choices"][0]["message"]["content"]

        return jsonify({
            "success": True,
            "reply": reply
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# --------------------------------------------------
# N8N ACTION WEBHOOK
# --------------------------------------------------

@app.route("/webhook", methods=["POST"])
def webhook():

    # Check Tyler API key
    provided_key = request.headers.get("X-Tyler-Key")

    if not TYLER_API_KEY or provided_key != TYLER_API_KEY:
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    if not N8N_WEBHOOK_URL:
        return jsonify({
            "success": False,
            "error": "N8N_WEBHOOK_URL is not configured"
        }), 500

    data = request.get_json(silent=True) or {}

    action = data.get("action")

    if not action:
        return jsonify({
            "success": False,
            "error": "Missing action"
        }), 400

    try:

        response = requests.post(
            N8N_WEBHOOK_URL,
            json=data,
            timeout=60
        )

        return jsonify({
            "success": response.ok,
            "status_code": response.status_code,
            "n8n_response": response.text
        }), response.status_code

    except requests.RequestException as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 502


# --------------------------------------------------
# START SERVER
# --------------------------------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
