from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import ChatMessage
from app.schemas.schemas import ChatRequest, ChatResponse, ChatStatus
from app.agents.chat_agent import run_chat_agent, GEMINI_API_KEY, GEMINI_MODEL

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/status", response_model=ChatStatus)
def chat_status():
    """Lets the frontend show whether the assistant is running with a live
    Gemini key (full natural-language understanding) or the rule-based
    fallback (pattern matching on a fixed set of intents)."""
    return ChatStatus(gemini_configured=bool(GEMINI_API_KEY), model=GEMINI_MODEL)


@router.post("/", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    # load short history for context (last 10 messages in this session)
    history_rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == payload.session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(10)
        .all()
    )
    history = [
        {"role": "user" if m.role == "user" else "model", "parts": [{"text": m.content}]}
        for m in history_rows
    ]

    result = run_chat_agent(db, payload.message, history)

    db.add(ChatMessage(session_id=payload.session_id, role="user", content=payload.message))
    db.add(ChatMessage(session_id=payload.session_id, role="assistant", content=result["reply"]))
    db.commit()

    return ChatResponse(
        session_id=payload.session_id,
        reply=result["reply"],
        data=result.get("data"),
        mode=result.get("mode", "unknown"),
    )


@router.get("/history/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [{"role": m.role, "content": m.content, "created_at": m.created_at} for m in rows]
