import json
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.models import AssistantMessage, User
from app.db.session import get_db
from app.ml.academic_assistant import generate_assistant_reply
from app.ml.model_registry import get_loaded_models
from app.schemas.domain import AssistantQueryRequest

router = APIRouter(prefix="/assistant", tags=["Academic Intelligence Assistant"])


@router.get("/history")
def get_assistant_history(
    session_id: str = "default",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    messages = (
        db.query(AssistantMessage)
        .filter(AssistantMessage.user_id == current_user.id, AssistantMessage.session_id == session_id)
        .order_by(AssistantMessage.created_at.asc(), AssistantMessage.id.asc())
        .limit(50)
        .all()
    )
    return {
        "session_id": session_id,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "citations": json.loads(m.citations_json) if m.citations_json else [],
                "suggested_actions": json.loads(m.suggested_actions_json) if m.suggested_actions_json else [],
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }


@router.post("/query")
def query_assistant(
    payload: AssistantQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    models_data = get_loaded_models(db)
    result = generate_assistant_reply(
        db=db,
        user=current_user,
        query=payload.query.strip(),
        model_metrics=models_data["metrics"],
    )

    user_msg = AssistantMessage(
        user_id=current_user.id,
        session_id=payload.session_id,
        role="user",
        content=payload.query.strip(),
    )
    assistant_msg = AssistantMessage(
        user_id=current_user.id,
        session_id=payload.session_id,
        role="assistant",
        content=result["answer"],
        citations_json=json.dumps(result["citations"]),
        suggested_actions_json=json.dumps(result["suggested_actions"]),
    )
    db.add(user_msg)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return {
        "message": {
            "id": assistant_msg.id,
            "role": "assistant",
            "content": assistant_msg.content,
            "intent": result["intent"],
            "citations": result["citations"],
            "suggested_actions": result["suggested_actions"],
            "created_at": assistant_msg.created_at.isoformat(),
        }
    }


@router.delete("/history")
def clear_assistant_history(
    session_id: str = "default",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(AssistantMessage).filter(
        AssistantMessage.user_id == current_user.id, AssistantMessage.session_id == session_id
    ).delete()
    db.commit()
    return {"cleared": True, "session_id": session_id}
