"""
FastAPI server.

Endpoints:
  GET  /          → serve chat UI (static/index.html)
  POST /chat      → main chat endpoint
  GET  /health    → health check
  POST /reset     → reset a session
"""

import uuid
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel

from utils.session import session_store
from chatbot import handle_message

app = FastAPI(title="Welfare Scheme Chatbot", version="1.0")

# Serve static files (our UI)
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    state: str


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Create session_id if first message
    session_id = req.session_id or str(uuid.uuid4())
    session = session_store.get_or_create(session_id)

    reply = await handle_message(session, req.message)

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        state=session.state,
    )


@app.post("/reset")
async def reset_session(req: Request):
    body = await req.json()
    session_id = body.get("session_id")
    if session_id:
        session_store.reset(session_id)
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok", "sessions": len(session_store._store)}