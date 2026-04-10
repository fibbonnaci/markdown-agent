"""
FastAPI server for Markdown Agent.
"""

import os as _os
from dotenv import load_dotenv
load_dotenv(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), ".env"))

import json
import os
import shutil
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agent_runtime import AgentRuntime
from backend import store

app = FastAPI(title="Markdown Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Project root is one level up from backend/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_MD_PATH = os.path.join(PROJECT_ROOT, "agent.md")
TOOLS_PY_PATH = os.path.join(PROJECT_ROOT, "backend", "tools.py")

# Singleton runtime
runtime: Optional[AgentRuntime] = None

# In-memory session histories
sessions: dict = {}


def init_runtime():
    global runtime
    runtime = AgentRuntime(AGENT_MD_PATH, TOOLS_PY_PATH)
    for w in runtime.warnings:
        print(f"⚠ {w}")


@app.on_event("startup")
async def startup():
    init_runtime()


# --- Endpoints ---


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "api_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "agent_name": runtime.config.name if runtime else None,
        "active_tools": list(runtime.tools.keys()) if runtime else [],
        "warnings": runtime.warnings if runtime else [],
    }


@app.get("/agent")
async def get_agent():
    if not runtime:
        raise HTTPException(status_code=500, detail="Runtime not initialized")
    return runtime.get_info()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@app.post("/chat")
async def chat(req: ChatRequest):
    if not runtime:
        raise HTTPException(status_code=500, detail="Runtime not initialized")

    # Get or create session history
    if req.session_id not in sessions:
        sessions[req.session_id] = []

    history = sessions[req.session_id]
    history.append({"role": "user", "content": req.message})

    async def event_stream():
        full_text = ""
        try:
            async for event in runtime.chat_stream(history):
                yield json.dumps(event) + "\n"
                if event["type"] == "text":
                    full_text += event["content"]
        except Exception as e:
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"
            yield json.dumps({"type": "done"}) + "\n"
            return

        # Add assistant response to history
        if full_text:
            history.append({"role": "assistant", "content": full_text})

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.post("/docs/upload")
async def upload_doc(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    content_type = file.content_type or "text/plain"

    # Determine type from extension if content_type is generic
    if file.filename.lower().endswith(".pdf"):
        content_type = "application/pdf"

    result = store.add_document(file.filename, content, content_type)
    return result


@app.get("/docs")
async def list_docs():
    return store.list_documents()


class SwapRequest(BaseModel):
    agent_file: str


@app.post("/agent/swap")
async def swap_agent(req: SwapRequest):
    global runtime, sessions

    # Validate the agent file exists
    source = os.path.join(PROJECT_ROOT, req.agent_file)
    if not os.path.isfile(source):
        raise HTTPException(status_code=404, detail=f"Agent file not found: {req.agent_file}")

    # Copy to root agent.md
    shutil.copy2(source, AGENT_MD_PATH)

    # Reset store and sessions
    store.reset()
    sessions.clear()

    # Reinitialize runtime
    init_runtime()

    return runtime.get_info()


@app.get("/agents")
async def list_agents():
    """List available agent files in agents/ directory."""
    agents_dir = os.path.join(PROJECT_ROOT, "agents")
    agents = []
    if os.path.isdir(agents_dir):
        for f in sorted(os.listdir(agents_dir)):
            if f.endswith(".md"):
                from backend.parser import parse_agent_md
                config = parse_agent_md(os.path.join(agents_dir, f))
                agents.append({
                    "file": f"agents/{f}",
                    "name": config.name,
                })
    return agents
