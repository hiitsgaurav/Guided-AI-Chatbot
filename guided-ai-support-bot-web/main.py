"""
main.py
-------
CLI entry point for the BrightCart guided AI support chatbot.

Usage:
    python main.py
"""

import os
import sys

from dotenv import load_dotenv

from app.agent import SupportAgent
from app.memory import ConversationMemory
from app.prompts import WELCOME_MESSAGE

load_dotenv()


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set.")
        print("Copy .env.example to .env and add your API key, then try again.")
        sys.exit(1)

    agent = SupportAgent(verbose=True)
    memory = ConversationMemory()

    print(WELCOME_MESSAGE)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nNova: Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "bye"}:
            print("\nNova: Thanks for chatting with BrightCart Support. Have a great day!")
            break

        memory.add_user_message(user_input)

        reply_text, updated_messages = agent.respond(memory.get_messages())
        memory.messages = updated_messages  # keep full tool-call history for context

        print(f"\nNova: {reply_text}")

    saved_path = memory.save()
    print(f"\n(Session transcript saved to {saved_path})")


if __name__ == "__main__":
    main()
