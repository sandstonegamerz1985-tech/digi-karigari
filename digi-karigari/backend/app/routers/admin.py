from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_roles
from ..models import ArtisanProfile, Order, OrderItem, Product, User
from ..serializers import serialize_artisan_row

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles("admin"))])


def _count(db: Session, model) -> int:
    return db.scalar(select(func.count(model.id))) or 0


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    """BASIC counts only. A full analytics dashboard is a planned feature."""
    revenue = db.scalar(select(func.coalesce(func.sum(OrderItem.price * OrderItem.quantity + OrderItem.shipping_fee), 0))) or 0
    return {
        "users": _count(db, User),
        "pending_artisans": db.scalar(select(func.count(ArtisanProfile.id)).where(ArtisanProfile.status == "pending")) or 0,
        "approved_artisans": db.scalar(select(func.count(ArtisanProfile.id)).where(ArtisanProfile.status == "approved")) or 0,
        "products": _count(db, Product),
        "orders": _count(db, Order),
        "test_sales_total": revenue,
        "note": "Test-mode numbers only. No real money is involved.",
    }


@router.get("/artisans")
def list_artisans(
    status: Literal["pending", "approved", "rejected", "all"] = Query(default="pending"),
    db: Session = Depends(get_db),
):
    stmt = select(User).join(ArtisanProfile, ArtisanProfile.user_id == User.id).order_by(ArtisanProfile.id.desc())
    if status != "all":
        stmt = stmt.where(ArtisanProfile.status == status)
    users = db.scalars(stmt).all()
    out = []
    for u in users:
        count = db.scalar(select(func.count(Product.id)).where(Product.artisan_id == u.id)) or 0
        out.append(serialize_artisan_row(u, count))
    return out


def _artisan_or_404(user_id: int, db: Session) -> User:
    user = db.get(User, user_id)
    if not user or not user.artisan_profile:
        raise HTTPException(status_code=404, detail="Artisan not found.")
    return user


@router.post("/artisans/{user_id}/approve")
def approve(user_id: int, db: Session = Depends(get_db)):
    user = _artisan_or_404(user_id, db)
    user.artisan_profile.status = "approved"  # this is what gives the Verified badge
    user.artisan_profile.reject_reason = ""
    db.commit()
    return serialize_artisan_row(user)


class RejectIn(BaseModel):
    reason: str = Field(min_length=3, max_length=300)


@router.post("/artisans/{user_id}/reject")
def reject(user_id: int, data: RejectIn, db: Session = Depends(get_db)):
    user = _artisan_or_404(user_id, db)
    user.artisan_profile.status = "rejected"
    user.artisan_profile.reject_reason = data.reason.strip()
    db.commit()
    return serialize_artisan_row(user)
