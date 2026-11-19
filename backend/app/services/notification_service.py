"""Helper service to dispatch and track user notifications."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from ..models import Notification


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def send_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
    link: str = "",
) -> Notification:
    notif = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        link=link,
        is_read=False,
        created_at=utcnow(),
    )
    db.add(notif)
    return notif
