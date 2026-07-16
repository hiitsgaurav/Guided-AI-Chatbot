"""
memory.py
---------
Lightweight session memory. Keeps the running message history in
memory during the chat, and can optionally persist a session transcript
to disk (data/../sessions/) so you can demonstrate "memory across
sessions" if your internship rubric asks for it.
"""

import json
import os
from datetime import datetime, UTC

SESSIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sessions"
)


class ConversationMemory:
    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or datetime.now(UTC).strftime("session_%Y%m%d_%H%M%S")
        self.messages: list[dict] = []

    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content):
        self.messages.append({"role": "assistant", "content": content})

    def get_messages(self):
        return self.messages

    def save(self):
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        path = os.path.join(SESSIONS_DIR, f"{self.session_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, indent=2, default=str)
        return path
