import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "name": "Tyler AI",
        "status": "online",
        "n8n_connected": bool(N8N_WEBHOOK_URL)
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

@app.route("/webhook", methods=["POST"])
def webhook():
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

    if action == "email":
        to = data.get("to")
        subject = data.get("subject")
        message = data.get("message")

        if not to or not subject or not message:
            return jsonify({
                "success": False,
                "error": "Email action requires to, subject, and message"
            }), 400

        payload = {
            "action": "email",
            "data": {
                "to": to,
                "subject": subject,
                "message": message
            }
        }

    elif action == "test":
        payload = {
            "action": "test",
            "message": data.get("message", "Tyler AI test")
        }

    else:
        return jsonify({
            "success": False,
            "error": f"Unknown action: {action}"
        }), 400

    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
