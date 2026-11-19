from datetime import datetime, timezone
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import Dispute, DisputeAudit, DisputeMessage, Order, OrderItem, User
from ..serializers import serialize_dispute
from ..services.notification_service import send_notification
from ..services.payment_service import get_payment_provider


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


router = APIRouter(tags=["disputes-and-refunds"])


class CreateDisputeIn(BaseModel):
    order_id: int
    order_item_id: Optional[int] = None
    reason: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=10, max_length=2000)
    requested_resolution: Literal["full_refund", "partial_refund", "replacement"] = "full_refund"
    requested_amount: int = Field(default=0, ge=0)


class AddDisputeMessageIn(BaseModel):
    message: str = Field(min_length=2, max_length=2000)


class ResolveDisputeIn(BaseModel):
    decision: Literal["refund_approved", "refund_rejected", "settled_mutual"]
    refund_amount: int = Field(default=0, ge=0)
    resolution_notes: str = Field(min_length=5, max_length=1000)
    manual_transaction_reference: Optional[str] = None


@router.get("/disputes")
def list_disputes(
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List disputes relevant to current user."""
    stmt = select(Dispute).order_by(Dispute.id.desc())
    if user.role == "admin":
        if status:
            stmt = stmt.where(Dispute.status == status)
    elif user.role == "artisan":
        stmt = stmt.where(Dispute.artisan_id == user.id)
        if status:
            stmt = stmt.where(Dispute.status == status)
    else:
        stmt = stmt.where(Dispute.buyer_id == user.id)
        if status:
            stmt = stmt.where(Dispute.status == status)

    rows = db.scalars(stmt).all()
    return [serialize_dispute(d) for d in rows]


@router.post("/disputes", status_code=201)
def open_dispute(
    data: CreateDisputeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Buyer opens a dispute for an eligible order."""
    order = db.get(Order, data.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    if order.buyer_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only dispute your own orders.")

    # Determine item and artisan
    artisan_id = None
    if data.order_item_id:
        item = db.get(OrderItem, data.order_item_id)
        if not item or item.order_id != order.id:
            raise HTTPException(status_code=400, detail="Invalid order item.")
        artisan_id = item.artisan_id
    elif order.items:
        artisan_id = order.items[0].artisan_id
    else:
        raise HTTPException(status_code=400, detail="Order has no items.")

    now = utcnow()
    dispute = Dispute(
        order_id=order.id,
        order_item_id=data.order_item_id,
        buyer_id=order.buyer_id,
        artisan_id=artisan_id,
        reason=data.reason.strip(),
        description=data.description.strip(),
        requested_resolution=data.requested_resolution,
        requested_amount=data.requested_amount or order.items[0].price,
        status="open",
        created_at=now,
        updated_at=now,
    )
    db.add(dispute)
    db.flush()

    # Initial audit log
    audit = DisputeAudit(
        dispute_id=dispute.id,
        actor_id=user.id,
        actor_role=user.role,
        action="dispute_opened",
        notes=f"Buyer opened case for '{data.reason}': {data.description[:100]}",
        created_at=now,
    )
    db.add(audit)

    # Notify artisan and admins
    send_notification(
        db=db,
        user_id=artisan_id,
        notification_type="dispute",
        title=f"Order dispute opened: #{order.id}",
        message=f"Buyer opened a dispute: {data.reason}. Please review and reply.",
        link=f"/seller?tab=disputes",
    )

    db.commit()
    db.refresh(dispute)
    return serialize_dispute(dispute)


def _check_dispute_access(d: Dispute, user: User):
    if user.role != "admin" and d.buyer_id != user.id and d.artisan_id != user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to view this dispute.")


@router.get("/disputes/{dispute_id}")
def get_dispute(
    dispute_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    d = db.get(Dispute, dispute_id)
    if not d:
        raise HTTPException(status_code=404, detail="Dispute not found.")
    _check_dispute_access(d, user)
    return serialize_dispute(d)


@router.post("/disputes/{dispute_id}/messages")
def add_dispute_message(
    dispute_id: int,
    data: AddDisputeMessageIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    d = db.get(Dispute, dispute_id)
    if not d:
        raise HTTPException(status_code=404, detail="Dispute not found.")
    _check_dispute_access(d, user)

    now = utcnow()
    msg = DisputeMessage(
        dispute_id=d.id,
        sender_id=user.id,
        sender_role=user.role,
        message=data.message.strip(),
        created_at=now,
    )
    db.add(msg)

    # Update dispute status if artisan replies
    if user.id == d.artisan_id and d.status == "open":
        d.status = "artisan_replied"
        audit = DisputeAudit(
            dispute_id=d.id,
            actor_id=user.id,
            actor_role=user.role,
            action="artisan_responded",
            notes=f"Artisan sent a reply: {data.message[:80]}",
            created_at=now,
        )
        db.add(audit)

    d.updated_at = now

    # Notify counterparty
    recipient_id = d.artisan_id if user.id == d.buyer_id else d.buyer_id
    send_notification(
        db=db,
        user_id=recipient_id,
        notification_type="dispute",
        title=f"New response on Dispute #{d.id}",
        message=f"{user.name}: {data.message[:100]}",
        link=f"/orders?dispute={d.id}",
    )

    db.commit()
    db.refresh(d)
    return serialize_dispute(d)


@router.post("/admin/disputes/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: int,
    data: ResolveDisputeIn,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    """Admin resolves dispute and processes mock/manual refund if approved."""
    d = db.get(Dispute, dispute_id)
    if not d:
        raise HTTPException(status_code=404, detail="Dispute not found.")

    now = utcnow()
    refund_ref = ""
    refund_amount = 0

    if data.decision == "refund_approved":
        payment_prov = get_payment_provider()
        refund_res = payment_prov.process_refund(
            order_id=d.order_id,
            amount=data.refund_amount,
            reason=data.resolution_notes,
            admin_id=user.id,
            manual_reference=data.manual_transaction_reference,
        )
        refund_ref = refund_res["reference_id"]
        refund_amount = data.refund_amount
        d.status = "resolved_refunded"
        d.resolution_decision = "refund_approved"
        d.refunded_amount = refund_amount
        d.refund_reference = refund_ref

        # Update order item / payment status
        if d.order:
            d.order.payment_status = "refunded_test"
    elif data.decision == "refund_rejected":
        d.status = "resolved_rejected"
        d.resolution_decision = "refund_rejected"
    else:
        d.status = "closed"
        d.resolution_decision = "settled_mutual"

    d.updated_at = now

    # Record auditable action
    audit = DisputeAudit(
        dispute_id=d.id,
        actor_id=user.id,
        actor_role="admin",
        action=f"resolved_{data.decision}",
        notes=(
            f"Admin {user.name} resolved case: {data.decision}. "
            f"Refund Amount: Rs {refund_amount}. Reference: {refund_ref or 'None'}. "
            f"Notes: {data.resolution_notes}"
        ),
        created_at=now,
    )
    db.add(audit)

    # Notify buyer and artisan
    send_notification(
        db=db,
        user_id=d.buyer_id,
        notification_type="dispute",
        title=f"Dispute #{d.id} Resolution: {data.decision.replace('_', ' ').title()}",
        message=f"Admin decision: {data.resolution_notes}. Refund: Rs {refund_amount}",
        link=f"/orders?dispute={d.id}",
    )
    send_notification(
        db=db,
        user_id=d.artisan_id,
        notification_type="dispute",
        title=f"Dispute #{d.id} Decision: {data.decision.replace('_', ' ').title()}",
        message=f"Admin decision recorded: {data.resolution_notes}",
        link=f"/seller?tab=disputes",
    )

    db.commit()
    db.refresh(d)
    return serialize_dispute(d)
