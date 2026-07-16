"""
tools.py
--------
Defines the tools (functions) our agent is allowed to call, plus their
JSON schemas in the format the Claude Messages API expects.

This is the "agentic" core of the project: instead of the LLM just
generating text, it decides WHEN to call these functions, WITH WHAT
arguments, based on the conversation -- and we execute the real Python
code and feed the result back to it.
"""

import json
import os
from datetime import datetime, UTC

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FAQ_PATH = os.path.join(DATA_DIR, "faq.json")
ORDERS_PATH = os.path.join(DATA_DIR, "orders.json")

# Serverless platforms like Vercel only allow writes to /tmp (the rest of the
# filesystem is read-only at runtime). We write tickets there when we can't
# write next to the source code, so ticket creation still works when deployed.
TICKETS_PATH = os.path.join(DATA_DIR, "tickets.json")
if not os.access(DATA_DIR, os.W_OK):
    TICKETS_PATH = os.path.join("/tmp", "tickets.json")


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------

def search_faq(query: str) -> dict:
    """Search the FAQ knowledge base for entries relevant to the query."""
    faqs = _load_json(FAQ_PATH, [])
    query_words = set(query.lower().split())

    scored = []
    for entry in faqs:
        haystack = (entry["question"] + " " + entry["answer"] + " " + entry["category"]).lower()
        score = sum(1 for w in query_words if w in haystack)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_matches = [entry for _, entry in scored[:3]]

    if not top_matches:
        return {"found": False, "message": "No matching FAQ entries found."}

    return {"found": True, "results": top_matches}


def check_order_status(order_id: str) -> dict:
    """Look up the status of an order by its order ID."""
    orders = _load_json(ORDERS_PATH, {})
    order_id = order_id.strip().upper()

    if order_id not in orders:
        return {"found": False, "message": f"No order found with ID '{order_id}'."}

    return {"found": True, "order_id": order_id, **orders[order_id]}


def create_support_ticket(customer_name: str, email: str, issue_summary: str, priority: str = "normal") -> dict:
    """Create a support ticket for issues that can't be resolved automatically."""
    tickets = _load_json(TICKETS_PATH, [])
    ticket_id = f"TCK{1000 + len(tickets) + 1}"

    ticket = {
        "ticket_id": ticket_id,
        "customer_name": customer_name,
        "email": email,
        "issue_summary": issue_summary,
        "priority": priority,
        "status": "open",
        "created_at": datetime.now(UTC).isoformat(),
    }
    tickets.append(ticket)
    _save_json(TICKETS_PATH, tickets)

    return {"created": True, "ticket": ticket}


def escalate_to_human(reason: str, urgency: str = "normal") -> dict:
    """Flag the current conversation for handoff to a human support agent."""
    return {
        "escalated": True,
        "reason": reason,
        "urgency": urgency,
        "message": "This conversation has been flagged for a human agent. "
                    "Expected response time: 24 hours (or sooner if urgent).",
    }


# ---------------------------------------------------------------------
# Tool registry: maps tool name -> python function
# ---------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "search_faq": search_faq,
    "check_order_status": check_order_status,
    "create_support_ticket": create_support_ticket,
    "escalate_to_human": escalate_to_human,
}

# ---------------------------------------------------------------------
# Tool schemas: what we hand to the Claude API so the model knows
# these tools exist and how to call them.
# ---------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "search_faq",
        "description": (
            "Search the company's FAQ knowledge base for an answer to a general "
            "question about shipping, returns, billing, account, or technical issues. "
            "Use this before escalating or creating a ticket for common questions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The customer's question or a short phrase describing what they want to know.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_order_status",
        "description": (
            "Look up the live status of a customer's order using their order ID "
            "(format like ORD1001). Use this whenever a customer asks about a "
            "specific order, delivery, or shipment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID, e.g. 'ORD1001'.",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "create_support_ticket",
        "description": (
            "Create a formal support ticket when an issue cannot be resolved via FAQ "
            "or order lookup (e.g. damaged item, billing dispute, complex complaint). "
            "Always confirm the customer's name and email before calling this."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "Full name of the customer."},
                "email": {"type": "string", "description": "Customer's email address."},
                "issue_summary": {"type": "string", "description": "A concise summary of the issue."},
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high", "urgent"],
                    "description": "How urgent the issue is.",
                },
            },
            "required": ["customer_name", "email", "issue_summary"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Escalate the conversation to a human support agent. Use this when the "
            "customer explicitly asks for a human, is highly frustrated, or the issue "
            "is outside what FAQ/order lookup/tickets can resolve."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Why this needs a human agent."},
                "urgency": {
                    "type": "string",
                    "enum": ["low", "normal", "high", "urgent"],
                },
            },
            "required": ["reason"],
        },
    },
]


def execute_tool(name: str, tool_input: dict) -> dict:
    """Dispatch a tool call by name and return its JSON-serializable result."""
    if name not in TOOL_FUNCTIONS:
        return {"error": f"Unknown tool '{name}'"}
    try:
        return TOOL_FUNCTIONS[name](**tool_input)
    except Exception as e:  # noqa: BLE001 - we want to surface any tool error to the model
        return {"error": str(e)}
