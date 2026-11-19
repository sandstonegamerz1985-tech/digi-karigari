from datetime import datetime, timezone
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import Order, OrderItem, Product, Review, User
from ..serializers import serialize_review
from ..services.notification_service import send_notification


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


router = APIRouter(prefix="/reviews", tags=["reviews"])


class CreateReviewIn(BaseModel):
    order_item_id: int
    rating: int = Field(ge=1, le=5)
    title: str = Field(min_length=2, max_length=120)
    comment: str = Field(min_length=5, max_length=1000)


class ModerateReviewIn(BaseModel):
    status: Literal["published", "hidden_by_admin", "flagged"]
    moderation_note: str = Field(default="", max_length=300)


@router.get("/eligible")
def list_eligible_items(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns order items purchased by the buyer that have not been reviewed yet."""
    # Find buyer's order items
    stmt = (
        select(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.buyer_id == user.id)
        .order_by(OrderItem.id.desc())
    )
    items = db.scalars(stmt).all()
    unreviewed = [
        {
            "order_item_id": i.id,
            "order_id": i.order_id,
            "product_id": i.product_id,
            "title": i.title,
            "image_url": f"/uploads/{i.image}" if i.image else None,
            "artisan_id": i.artisan_id,
            "artisan_name": i.artisan.name if i.artisan else "",
            "order_status": i.status,
            "ordered_at": i.order.created_at.isoformat() if i.order else None,
        }
        for i in items
        if i.review is None
    ]
    return unreviewed


@router.post("", status_code=201)
def create_review(
    data: CreateReviewIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a verified purchase review. Prevents duplicate reviews for the same order item."""
    order_item = db.get(OrderItem, data.order_item_id)
    if not order_item:
        raise HTTPException(status_code=404, detail="Purchased item not found.")

    if order_item.order.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="You can only review items you purchased.")

    # Check for duplicate review
    existing = db.scalar(select(Review).where(Review.order_item_id == order_item.id))
    if existing:
        raise HTTPException(status_code=400, detail="You have already submitted a review for this purchase.")

    if not order_item.product_id:
        raise HTTPException(status_code=400, detail="Product is no longer available.")

    now = utcnow()
    review = Review(
        product_id=order_item.product_id,
        order_id=order_item.order_id,
        order_item_id=order_item.id,
        buyer_id=user.id,
        artisan_id=order_item.artisan_id,
        rating=data.rating,
        title=data.title.strip(),
        comment=data.comment.strip(),
        status="published",
        created_at=now,
        updated_at=now,
    )
    db.add(review)

    # Notify artisan
    send_notification(
        db=db,
        user_id=order_item.artisan_id,
        notification_type="review_received",
        title=f"New {data.rating}-star review for '{order_item.title}'",
        message=f"{user.name} wrote: '{data.title}'",
        link=f"/product/{order_item.product_id}",
    )

    db.commit()
    db.refresh(review)
    return serialize_review(review)


@router.get("/product/{product_id}")
def get_product_reviews(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Public reviews and rating summary for a product."""
    reviews = db.scalars(
        select(Review)
        .where(Review.product_id == product_id, Review.status == "published")
        .order_by(Review.id.desc())
    ).all()

    total = len(reviews)
    avg = round(sum(r.rating for r in reviews) / total, 1) if total > 0 else 0.0
    breakdown = {i: sum(1 for r in reviews if r.rating == i) for i in range(1, 6)}

    return {
        "product_id": product_id,
        "average_rating": avg,
        "total_reviews": total,
        "rating_breakdown": breakdown,
        "reviews": [serialize_review(r) for r in reviews],
    }


@router.get("/artisan/{artisan_id}")
def get_artisan_reviews(
    artisan_id: int,
    db: Session = Depends(get_db),
):
    """Public reviews and overall rating summary for an artisan."""
    reviews = db.scalars(
        select(Review)
        .where(Review.artisan_id == artisan_id, Review.status == "published")
        .order_by(Review.id.desc())
    ).all()

    total = len(reviews)
    avg = round(sum(r.rating for r in reviews) / total, 1) if total > 0 else 0.0

    return {
        "artisan_id": artisan_id,
        "average_rating": avg,
        "total_reviews": total,
        "reviews": [serialize_review(r, include_product=True) for r in reviews],
    }
