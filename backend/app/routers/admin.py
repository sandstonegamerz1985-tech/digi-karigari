from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..constants import CATEGORIES
from ..database import get_db
from ..deps import require_roles
from ..models import ArtisanProfile, Dispute, Order, OrderItem, Product, Review, User
from ..serializers import serialize_artisan_row, serialize_product, serialize_review
from ..services.notification_service import send_notification


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles("admin"))])


def _count(db: Session, model) -> int:
    return db.scalar(select(func.count(model.id))) or 0


@router.get("/stats")
def basic_stats(db: Session = Depends(get_db)):
    revenue = (
        db.scalar(
            select(
                func.coalesce(func.sum(OrderItem.price * OrderItem.quantity + OrderItem.shipping_fee), 0)
            )
        )
        or 0
    )
    return {
        "users": _count(db, User),
        "pending_artisans": db.scalar(
            select(func.count(ArtisanProfile.id)).where(ArtisanProfile.status == "pending")
        )
        or 0,
        "approved_artisans": db.scalar(
            select(func.count(ArtisanProfile.id)).where(ArtisanProfile.status == "approved")
        )
        or 0,
        "pending_listings": db.scalar(
            select(func.count(Product.id)).where(Product.status == "pending_review")
        )
        or 0,
        "products": _count(db, Product),
        "orders": _count(db, Order),
        "disputes": _count(db, Dispute),
        "test_sales_total": revenue,
        "note": "Test-mode simulation data. No real currency is involved.",
    }


@router.get("/analytics")
def analytics_dashboard(
    time_range: Literal["7d", "30d", "90d", "all"] = Query(default="30d", alias="range"),
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Rich marketplace analytics with date-range and category filters."""
    now = utcnow()
    since = None
    if time_range == "7d":
        since = now - timedelta(days=7)
    elif time_range == "30d":
        since = now - timedelta(days=30)
    elif time_range == "90d":
        since = now - timedelta(days=90)

    # Base query for order items
    order_item_stmt = select(OrderItem).join(Order, Order.id == OrderItem.order_id)
    if since:
        order_item_stmt = order_item_stmt.where(Order.created_at >= since)
    if category:
        order_item_stmt = order_item_stmt.join(Product, Product.id == OrderItem.product_id).where(
            Product.category == category
        )

    items = db.scalars(order_item_stmt).all()

    total_sales = sum(i.price * i.quantity + i.shipping_fee for i in items)
    order_volume = len(items)

    unique_buyers = len({i.order.buyer_id for i in items if i.order})
    unique_sellers = len({i.artisan_id for i in items})

    total_buyers = db.scalar(select(func.count(User.id)).where(User.role == "buyer")) or 1
    conversion_rate = round((unique_buyers / max(1, total_buyers)) * 100, 1)

    # Status distribution
    status_counts = {"placed": 0, "packed": 0, "shipped": 0, "delivered": 0}
    for i in items:
        status_counts[i.status] = status_counts.get(i.status, 0) + 1

    # Popular categories
    cat_sales = {}
    for i in items:
        cat_name = i.product.category if i.product else "Craft"
        cat_sales[cat_name] = cat_sales.get(cat_name, 0) + (i.price * i.quantity)

    popular_categories = [
        {"category": cat, "sales": sales, "share_pct": round((sales / max(1, total_sales)) * 100, 1) if total_sales > 0 else 0}
        for cat, sales in sorted(cat_sales.items(), key=lambda x: x[1], reverse=True)[:6]
    ]

    # Disputes
    dispute_stmt = select(Dispute)
    if since:
        dispute_stmt = dispute_stmt.where(Dispute.created_at >= since)
    disputes = db.scalars(dispute_stmt).all()
    total_disputes = len(disputes)
    open_disputes = sum(1 for d in disputes if d.status in ("open", "artisan_replied", "under_review"))
    resolved_disputes = sum(1 for d in disputes if d.status in ("resolved_refunded", "resolved_rejected", "closed"))
    dispute_rate = round((total_disputes / max(1, order_volume)) * 100, 1) if order_volume > 0 else 0.0

    # Reviews
    review_stmt = select(Review).where(Review.status == "published")
    if since:
        review_stmt = review_stmt.where(Review.created_at >= since)
    reviews = db.scalars(review_stmt).all()
    total_reviews = len(reviews)
    avg_rating = round(sum(r.rating for r in reviews) / max(1, total_reviews), 1) if total_reviews > 0 else 0.0
    rating_dist = {star: sum(1 for r in reviews if r.rating == star) for star in range(1, 6)}

    has_enough_data = order_volume > 0 or total_reviews > 0

    return {
        "range": time_range,
        "selected_category": category,
        "has_enough_data": has_enough_data,
        "empty_state_note": None if has_enough_data else "Not enough transaction activity recorded in this time window.",
        "summary": {
            "total_sales": total_sales,
            "order_volume": order_volume,
            "active_buyers": unique_buyers,
            "active_sellers": unique_sellers,
            "conversion_rate_percent": conversion_rate,
            "dispute_rate_percent": dispute_rate,
            "average_rating": avg_rating,
            "total_reviews": total_reviews,
        },
        "order_status_distribution": status_counts,
        "popular_categories": popular_categories,
        "dispute_metrics": {
            "total": total_disputes,
            "open": open_disputes,
            "resolved": resolved_disputes,
            "rate_percent": dispute_rate,
        },
        "review_metrics": {
            "total_reviews": total_reviews,
            "average_rating": avg_rating,
            "distribution": rating_dist,
        },
    }


# --- Listing Review & Moderation Queue ---

@router.get("/listings")
def list_listings_for_review(
    status: Literal["all", "pending_review", "approved", "rejected"] = Query(default="all"),
    db: Session = Depends(get_db),
):
    """Admin queue of products with AI advisory checks for explicit approval/rejection."""
    stmt = select(Product).order_by(Product.id.desc())
    if status != "all":
        stmt = stmt.where(Product.status == status)
    products = db.scalars(stmt).all()
    return [serialize_product(p) for p in products]


@router.post("/listings/{product_id}/approve")
def approve_listing(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    """Admin explicitly approves a listing. AI advice never auto-publishes."""
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found.")
    p.status = "approved"
    p.reject_reason = ""
    send_notification(
        db=db,
        user_id=p.artisan_id,
        notification_type="listing",
        title=f"Listing Approved: {p.title}",
        message="An admin reviewed and approved your handcrafted listing. It is now live in the marketplace!",
        link=f"/product/{p.id}",
    )
    db.commit()
    return serialize_product(p)


class RejectListingIn(BaseModel):
    reason: str = Field(min_length=3, max_length=300)


@router.post("/listings/{product_id}/reject")
def reject_listing(
    product_id: int,
    data: RejectListingIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    """Admin rejects a listing with feedback. AI advice never auto-rejects."""
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found.")
    p.status = "rejected"
    p.reject_reason = data.reason.strip()
    send_notification(
        db=db,
        user_id=p.artisan_id,
        notification_type="listing",
        title=f"Listing Update Needed: {p.title}",
        message=f"Admin feedback: {data.reason}. You can edit and resubmit your listing.",
        link=f"/seller",
    )
    db.commit()
    return serialize_product(p)


# --- Artisan Profiles ---

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
def approve_artisan(user_id: int, db: Session = Depends(get_db)):
    user = _artisan_or_404(user_id, db)
    user.artisan_profile.status = "approved"
    user.artisan_profile.reject_reason = ""
    # Update trust tier if still at initial level
    if user.artisan_profile.trust_tier == "new_artisan":
        user.artisan_profile.trust_tier = "verified_maker"

    send_notification(
        db=db,
        user_id=user.id,
        notification_type="tier",
        title="Artisan Profile Verified!",
        message="Your artisan profile has been approved with the Verified Maker badge. You can now add listings.",
        link="/seller",
    )
    db.commit()
    return serialize_artisan_row(user)


class RejectIn(BaseModel):
    reason: str = Field(min_length=3, max_length=300)


@router.post("/artisans/{user_id}/reject")
def reject_artisan(user_id: int, data: RejectIn, db: Session = Depends(get_db)):
    user = _artisan_or_404(user_id, db)
    user.artisan_profile.status = "rejected"
    user.artisan_profile.reject_reason = data.reason.strip()
    db.commit()
    return serialize_artisan_row(user)


# --- Users Management ---

@router.get("/users")
def list_users(
    role: Literal["all", "buyer", "artisan", "admin"] = "all",
    db: Session = Depends(get_db),
):
    stmt = select(User).order_by(User.id.desc())
    if role != "all":
        stmt = stmt.where(User.role == role)
    users = db.scalars(stmt).all()
    result = []
    for u in users:
        order_count = db.scalar(select(func.count(Order.id)).where(Order.buyer_id == u.id)) or 0
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "order_count": order_count,
            "artisan_status": u.artisan_profile.status if u.artisan_profile else None,
            "trust_tier": u.artisan_profile.trust_tier if u.artisan_profile else None,
        })
    return result


# --- Review Moderation ---

@router.get("/reviews")
def list_reviews_for_moderation(
    status: Literal["all", "published", "hidden_by_admin", "flagged"] = "all",
    db: Session = Depends(get_db),
):
    stmt = select(Review).order_by(Review.id.desc())
    if status != "all":
        stmt = stmt.where(Review.status == status)
    reviews = db.scalars(stmt).all()
    return [serialize_review(r, include_product=True) for r in reviews]


class ReviewModerationIn(BaseModel):
    status: Literal["published", "hidden_by_admin", "flagged"]
    moderation_note: str = Field(default="", max_length=300)


@router.post("/reviews/{review_id}/moderate")
def moderate_review(
    review_id: int,
    data: ReviewModerationIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    r = db.get(Review, review_id)
    if not r:
        raise HTTPException(status_code=404, detail="Review not found.")
    r.status = data.status
    r.moderation_note = data.moderation_note.strip()
    db.commit()
    return serialize_review(r, include_product=True)
