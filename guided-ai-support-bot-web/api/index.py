"""
api/index.py
------------
Flask app that exposes the support agent as a web API. This file is the
entry point Vercel's Python runtime uses (it auto-detects the `app`
Flask instance and wraps it as a serverless function).

Because serverless functions are stateless between requests, the browser
sends the full conversation history with each request and we send back
the updated history for it to store and resend next time.
"""

import os
import sys

# Allow importing the `app/` package (agent, tools, prompts) from the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, send_from_directory

from app.agent import SupportAgent
from app.prompts import WELCOME_MESSAGE

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")

app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path="")

_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = SupportAgent(verbose=False)
    return _agent


@app.route("/")
def serve_index():
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.route("/api/welcome", methods=["GET"])
def welcome():
    return jsonify({"message": WELCOME_MESSAGE.strip()})


@app.route("/api/chat", methods=["POST"])
def chat():
    if not os.getenv("ANTHROPIC_API_KEY"):
        return jsonify({"error": "Server misconfigured: ANTHROPIC_API_KEY is not set."}), 500

    body = request.get_json(force=True, silent=True) or {}
    user_message = (body.get("message") or "").strip()
    history = body.get("history") or []

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    history.append({"role": "user", "content": user_message})

    try:
        reply_text, updated_history = get_agent().respond(history)
    except Exception as e:  # noqa: BLE001 - surface a clean error to the client
        return jsonify({"error": f"Agent error: {e}"}), 500

    return jsonify({"reply": reply_text, "history": updated_history})


# Local dev: `python api/index.py` runs a normal Flask dev server.
if __name__ == "__main__":
    app.run(debug=True, port=5000)
