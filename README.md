# Markdown Agent

What if your entire AI agent was just a markdown file? No framework to learn, no configuration to manage, no infrastructure to maintain. You write a markdown file that describes your agent's purpose, behavior, and tools — and it just works.

This prototype proves the idea. The agent below is defined in a single file called `agent.md`:

```markdown
# Talk to Docs

## Purpose

You are a document Q&A assistant. Users upload documents and ask you questions
about them. Your job is to search through the uploaded documents, find relevant
passages, and provide clear, accurate answers based on what you find.

## Tools

- search_docs: Search uploaded documents for relevant passages
- list_docs: List all uploaded documents and their chunk counts

## Behavior

- Always search the documents before answering a question about their content.
- Cite the source document name when referencing information.
- If the search returns no relevant results, say so honestly rather than guessing.

## Guardrails

- Never fabricate information that isn't in the uploaded documents.
- Do not execute code or access external systems.

## Model

claude-3-5-sonnet-20241022
```

And here is the complete `tools.py` — every capability the agent has:

```python
from backend.decorator import tool
from backend import store

@tool
def search_docs(query: str, top_k: int = 3):
    """Search uploaded documents for relevant passages.

    Args:
        query: The search query string.
        top_k: Number of top results to return.
    """
    results = store.search(query, top_k)
    if not results:
        return "No relevant documents found."
    formatted = []
    for r in results:
        formatted.append(f"[{r['doc_name']}] (score: {r['score']:.2f})\n{r['text']}")
    return "\n\n---\n\n".join(formatted)

@tool
def list_docs():
    """List all uploaded documents and their chunk counts."""
    docs = store.list_documents()
    if not docs:
        return "No documents uploaded yet."
    return "\n".join(f"- {d['name']} ({d['chunks']} chunks)" for d in docs)
```

That's it. Two files. The `@tool` decorator inspects the function signature,
reads the docstring, and generates a Claude-compatible tool schema automatically.
No configuration needed.

---

## Swapping agents

The runtime doesn't care what's in `agent.md`. Swap the file, restart the
server, and you have a completely different agent. Same code, same tools,
different soul.

```bash
# Start as a document Q&A agent
cp agents/talk-to-docs.md agent.md

# Become a customer support agent
cp agents/customer-support.md agent.md

# Become a code review agent
cp agents/code-review.md agent.md
```

Three example agents are included in `agents/`:

- **Talk to Docs** — answers questions about uploaded documents
- **Customer Support** — friendly support agent with knowledge base search
  (includes `check_order_status` tool to demonstrate the warning system for
  unimplemented tools)
- **Code Review** — senior engineer reviewing uploaded code files

The frontend includes a live agent swapper — click a button to switch agents
without touching the terminal. The agent card updates to show the new
definition, and chat history resets.

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/your-org/markdown-agent.git
cd markdown-agent

# 2. Add your API key
cp .env.template .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Create a virtualenv and install backend dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 4. Start the backend
source venv/bin/activate
export $(cat .env | xargs)
uvicorn backend.main:app --reload

# 5. Start the frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Upload a document. Ask a question.

---

## Deployment

### Backend (Railway)

The repo includes a `Dockerfile` and `railway.json`.

1. Connect your GitHub repo to Railway
2. Set `ANTHROPIC_API_KEY` in environment variables
3. Deploy — Railway auto-detects the Dockerfile

### Frontend (Vercel)

1. Import the repo on Vercel
2. Set `VITE_API_URL` to your backend URL (e.g. `https://markdown-agent.up.railway.app`)
3. Deploy — Vercel uses `vercel.json` to build the frontend

---

## The idea

We've been building agents wrong. Every framework asks you to learn its
abstractions, wire up its components, configure its pipelines. The result
is that building an agent feels like building infrastructure.

But an agent is just a personality, a set of capabilities, and some rules.
That's a document, not a codebase.

Markdown Agent is a bet on radical simplicity: your agent's identity lives
in a markdown file. Its capabilities are decorated Python functions. The
runtime reads the markdown, imports the functions, and handles everything
else — the API calls, the tool execution loop, the streaming, the
deployment.

Want a different agent? Write a different markdown file. Want a new
capability? Write a function with `@tool`. Want to deploy? Push to main.

The infrastructure disappears. What's left is just the idea of what your
agent should be — expressed in the most universal format we have: a text
file.
