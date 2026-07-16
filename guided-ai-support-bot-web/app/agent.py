"""
agent.py
--------
The core agent loop. This is where the "agentic" behavior lives:

    1. Send the conversation + available tools to Claude.
    2. If Claude responds with a `tool_use` block, execute the
       corresponding Python function ourselves.
    3. Feed the tool's result back to Claude as a `tool_result`.
    4. Repeat until Claude responds with plain text (no more tool calls).

This is the standard "ReAct-style" agent loop used across most
tool-calling agent frameworks, implemented here from scratch with the
raw Anthropic Messages API so you can see exactly how it works.

IMPORTANT: message history is kept as plain JSON-serializable dicts
(not SDK objects) at every step. This makes it safe to serialize the
conversation to send to a browser and back, which is required for a
stateless deployment like Vercel serverless functions.
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

from app.tools import TOOL_SCHEMAS, execute_tool
from app.prompts import SYSTEM_PROMPT

load_dotenv()

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
MAX_TOOL_ITERATIONS = 6  # safety limit to avoid infinite tool-call loops


def _block_to_dict(block) -> dict:
    """Convert an SDK content block into a plain JSON-serializable dict."""
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    return {"type": block.type}


class SupportAgent:
    def __init__(self, api_key: str | None = None, verbose: bool = True):
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.verbose = verbose

    def _log(self, msg: str):
        if self.verbose:
            print(f"[agent] {msg}")

    def respond(self, messages: list[dict]) -> tuple[str, list[dict]]:
        """
        Given the full message history (list of plain {"role", "content"} dicts),
        run the agent loop and return (final_text_reply, updated_messages).

        `updated_messages` is always JSON-serializable and can be stored/sent
        as-is and passed back into this method on the next call.
        """
        working_messages = list(messages)

        for _ in range(MAX_TOOL_ITERATIONS):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOL_SCHEMAS,
                messages=working_messages,
            )

            content_dicts = [_block_to_dict(b) for b in response.content]
            working_messages.append({"role": "assistant", "content": content_dicts})

            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

            if not tool_use_blocks:
                final_text = "".join(b["text"] for b in content_dicts if b["type"] == "text")
                return final_text, working_messages

            tool_results = []
            for block in tool_use_blocks:
                self._log(f"calling tool `{block.name}` with input {block.input}")
                result = execute_tool(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    }
                )

            working_messages.append({"role": "user", "content": tool_results})

        return (
            "I'm having trouble completing that request right now — let me "
            "connect you with a human agent instead.",
            working_messages,
        )
