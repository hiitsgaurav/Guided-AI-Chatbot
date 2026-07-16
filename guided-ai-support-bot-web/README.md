# 🤖 BrightCart — Guided AI Customer Support Chatbot

A **guided, agentic AI customer support chatbot** built from scratch in Python using the
[Anthropic Claude API](https://docs.claude.com) and its native **tool use (function calling)**.
Built as a personal project for an Agentic AI internship.

Unlike a plain chatbot that just talks, this bot **acts**: it decides when to look up an
order, search a knowledge base, file a support ticket, or escalate to a human — by calling
real Python functions and reasoning over their results.

Ships two ways:
- **CLI** (`main.py`) — chat with it in your terminal, for local dev/demo
- **Web app** (`api/` + `public/`) — a Flask API + browser chat UI, deployable to **Vercel**

---

## ✨ Features

- **Guided conversation flow** — greets the user, routes them through order/returns/
  billing/technical categories, and asks clarifying questions before acting.
- **Agentic tool use** — the LLM decides which tool to call and with what arguments:
  - `search_faq` — semantic-ish lookup over a JSON FAQ knowledge base
  - `check_order_status` — looks up live order status from a mock orders "database"
  - `create_support_ticket` — files a ticket for issues that need follow-up
  - `escalate_to_human` — flags the conversation for human handoff
- **Multi-step tool loop** — the agent can call multiple tools in sequence before
  replying, implemented from scratch (no framework) so the mechanics are visible.
- **Conversation memory** — full session history is kept and saved to disk as a
  transcript after each chat.
- **Clean, extensible structure** — add a new tool by writing one function + one schema.

---

## 🏗️ Architecture

```
User message
     │
     ▼
┌─────────────────┐      tool_use requested?      ┌──────────────────┐
│  Claude (LLM)    │ ─────────────────────────────▶│  execute_tool()   │
│  + system prompt │                                │  (real Python fn) │
│  + tool schemas  │◀───────────────────────────── │  returns JSON      │
└─────────────────┘        tool_result             └──────────────────┘
     │
     │ no more tools needed
     ▼
Final reply shown to user
```

This loop (`app/agent.py`) repeats until Claude responds with plain text instead of a
tool call — the standard pattern behind most "agentic AI" systems.

---

## 📁 Project Structure

```
guided-ai-support-bot/
├── main.py                 # CLI entry point — run this to chat in a terminal
├── api/
│   └── index.py             # Flask API — Vercel serverless entry point
├── public/
│   └── index.html           # Browser chat UI (served by Flask / Vercel)
├── app/
│   ├── agent.py             # Core agent loop (Claude + tool calling)
│   ├── tools.py             # Tool implementations + schemas
│   ├── prompts.py           # System prompt & guided welcome message
│   └── memory.py            # Conversation history helper (used by CLI)
├── data/
│   ├── faq.json              # Mock FAQ knowledge base
│   └── orders.json           # Mock order database
├── tests/
│   └── test_tools.py         # Unit tests for the tool functions
├── vercel.json               # Vercel deployment config
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/<your-username>/guided-ai-support-bot.git
   cd guided-ai-support-bot
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate    # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add your API key**
   ```bash
   cp .env.example .env
   # then edit .env and paste your ANTHROPIC_API_KEY
   ```
   Get a key at [console.anthropic.com](https://console.anthropic.com).

5. **Run it — pick one:**

   **CLI (terminal chat):**
   ```bash
   python main.py
   ```

   **Web app (local browser chat):**
   ```bash
   python api/index.py
   # then open http://localhost:5000
   ```

---

## ☁️ Deploying to Vercel

The `main.py` CLI script itself **cannot** be deployed to Vercel — Vercel only
hosts web apps (serverless functions + static files), not interactive
terminal programs. That's what `api/index.py` and `public/index.html` are
for: the same agent, wrapped in a small Flask API with a browser-based chat
UI, which Vercel *can* run.

1. **Push this repo to GitHub** (see below).

2. **Import the repo in Vercel**
   - Go to [vercel.com/new](https://vercel.com/new) and import your GitHub repo.
   - Vercel will detect `vercel.json` and `api/index.py` automatically
     (Python runtime via `@vercel/python`).

3. **Add your environment variable**
   - In the Vercel project settings → **Environment Variables**, add:
     ```
     ANTHROPIC_API_KEY = your_api_key_here
     ```
   - Never commit your real key to GitHub — that's what `.env` / `.gitignore` are for.

4. **Deploy**
   - Vercel will build and give you a live URL (e.g. `your-project.vercel.app`).
   - Open it — you'll get the browser chat UI talking to your deployed agent.

**Or deploy via CLI:**
```bash
npm i -g vercel
vercel login
vercel            # deploy a preview
vercel --prod     # deploy to production
```
(Vercel CLI will prompt you to add `ANTHROPIC_API_KEY` as an environment variable too.)

> **Note on statelessness:** serverless functions don't keep memory between
> requests, so the browser keeps the running conversation and re-sends it
> with each message (see `public/index.html`). This is normal for
> serverless deployments — for durable, cross-device memory you'd add a
> real database (e.g. Vercel Postgres or Redis) keyed by a session ID.

---

## 💬 Example Session

```
Nova: Hi! I'm Nova, your BrightCart support assistant. I can help with:
  1) Order status & delivery
  2) Returns & refunds
  3) Billing questions
  4) Account / technical issues
  5) Something else

What can I help you with today?

You: Hi, can you check order ORD1002?
[agent] calling tool `check_order_status` with input {'order_id': 'ORD1002'}

Nova: Your order ORD1002 (Running Shoes - Size 9) is Out for Delivery,
expected today, July 8. Anything else I can help with?

You: what's your return policy
[agent] calling tool `search_faq` with input {'query': 'return policy'}

Nova: You can return any item within 30 days of delivery for a full
refund, as long as it's unused and in original packaging.
```

---

## 🧪 Running Tests

```bash
python -m pytest tests/
```

---

## 🔧 Extending the Bot

To add a new capability:
1. Write a Python function in `app/tools.py`.
2. Add it to `TOOL_FUNCTIONS`.
3. Add a matching JSON schema entry to `TOOL_SCHEMAS`.

Claude will automatically pick up the new tool and decide when to call it —
no changes needed to `agent.py`.

---

## 🗺️ Possible Next Steps

- Swap the CLI for a Flask/FastAPI + simple web chat UI
- Replace the mock JSON "databases" with a real SQL database
- Add streaming responses
- Add a real vector-search FAQ lookup instead of keyword matching
- Deploy as a Slack/WhatsApp bot

---

## 📄 License

MIT — free to use for learning, coursework, or your own portfolio.
