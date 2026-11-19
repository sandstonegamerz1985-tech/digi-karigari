from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Conversation, Message, Notification, Product, User
from ..serializers import serialize_conversation, serialize_message, serialize_notification
from ..services.notification_service import send_notification


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


router = APIRouter(tags=["messaging-and-notifications"])


class StartConversationIn(BaseModel):
    artisan_id: int
    product_id: Optional[int] = None
    order_id: Optional[int] = None
    subject: Optional[str] = Field(default="", max_length=140)
    initial_message: str = Field(min_length=1, max_length=2000)


class SendMessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@router.get("/conversations")
def list_conversations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List inbox conversations for the authenticated user. Admins can view all."""
    if user.role == "admin":
        stmt = select(Conversation).order_by(Conversation.last_message_at.desc())
    else:
        stmt = (
            select(Conversation)
            .where(or_(Conversation.buyer_id == user.id, Conversation.artisan_id == user.id))
            .order_by(Conversation.last_message_at.desc())
        )
    convos = db.scalars(stmt).all()
    return [serialize_conversation(c, user.id) for c in convos]


@router.post("/conversations", status_code=201)
def start_conversation(
    data: StartConversationIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Buyer starts an inquiry with an artisan, or contacts regarding a product."""
    if data.artisan_id == user.id:
        raise HTTPException(status_code=400, detail="You cannot start a conversation with yourself.")

    recipient = db.get(User, data.artisan_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Artisan not found.")

    # Check if an active conversation exists for this buyer, artisan, and product
    stmt = select(Conversation).where(
        Conversation.buyer_id == user.id,
        Conversation.artisan_id == data.artisan_id,
    )
    if data.product_id:
        stmt = stmt.where(Conversation.product_id == data.product_id)

    convo = db.scalars(stmt).first()
    now = utcnow()

    if not convo:
        subj = data.subject.strip()
        if not subj and data.product_id:
            p = db.get(Product, data.product_id)
            if p:
                subj = f"Inquiry: {p.title}"
        if not subj:
            subj = f"Conversation with {recipient.name}"

        convo = Conversation(
            buyer_id=user.id,
            artisan_id=data.artisan_id,
            product_id=data.product_id,
            order_id=data.order_id,
            subject=subj,
            last_message_text=data.initial_message.strip()[:290],
            last_message_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(convo)
        db.flush()

    msg = Message(
        conversation_id=convo.id,
        sender_id=user.id,
        text=data.initial_message.strip(),
        created_at=now,
    )
    db.add(msg)
    convo.last_message_text = data.initial_message.strip()[:290]
    convo.last_message_at = now
    convo.updated_at = now

    # Dispatch notification to recipient
    send_notification(
        db=db,
        user_id=data.artisan_id,
        notification_type="new_message",
        title=f"New message from {user.name}",
        message=f"{user.name}: {data.initial_message[:100]}...",
        link=f"/messages?convo={convo.id}",
    )

    db.commit()
    db.refresh(convo)
    return serialize_conversation(convo, user.id)


def _check_convo_access(convo: Conversation, user: User):
    if user.role != "admin" and convo.buyer_id != user.id and convo.artisan_id != user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this conversation.")


@router.get("/conversations/{convo_id}")
def get_conversation_thread(
    convo_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convo = db.get(Conversation, convo_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    _check_convo_access(convo, user)

    # Mark messages from the other user as read
    now = utcnow()
    changed = False
    for m in convo.messages:
        if m.sender_id != user.id and m.read_at is None:
            m.read_at = now
            changed = True
    if changed:
        db.commit()

    return {
        "conversation": serialize_conversation(convo, user.id),
        "messages": [serialize_message(m) for m in convo.messages],
    }


@router.post("/conversations/{convo_id}/messages")
def send_message(
    convo_id: int,
    data: SendMessageIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convo = db.get(Conversation, convo_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    _check_convo_access(convo, user)

    now = utcnow()
    msg = Message(
        conversation_id=convo.id,
        sender_id=user.id,
        text=data.text.strip(),
        created_at=now,
    )
    db.add(msg)
    convo.last_message_text = data.text.strip()[:290]
    convo.last_message_at = now
    convo.updated_at = now

    recipient_id = convo.artisan_id if user.id == convo.buyer_id else convo.buyer_id
    send_notification(
        db=db,
        user_id=recipient_id,
        notification_type="new_message",
        title=f"New message from {user.name}",
        message=f"{data.text[:100]}...",
        link=f"/messages?convo={convo.id}",
    )

    db.commit()
    db.refresh(msg)
    return serialize_message(msg)


# --- Notifications ---

@router.get("/notifications")
def list_notifications(
    limit: int = Query(default=30, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.id.desc())
        .limit(limit)
    )
    rows = db.scalars(stmt).all()
    unread_count = db.scalar(
        select(Notification)
        .where(Notification.user_id == user.id, Notification.is_read.is_(False))
    )
    return {
        "unread_count": db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read.is_(False)).count(),
        "notifications": [serialize_notification(n) for n in rows],
    }


@router.post("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.get(Notification, notif_id)
    if not n or n.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found.")
    n.is_read = True
    db.commit()
    return {"status": "ok"}


@router.post("/notifications/read-all")
def mark_all_notifications_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read.is_(False)).update({"is_read": True})
    db.commit()
    return {"status": "ok"}
