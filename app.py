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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
