"""Seller Trust Tier Calculation and Criteria Audit Engine.

Derives tiers from transparent, configurable metrics:
- Profile verification status
- Completed orders count
- Average buyer rating & review volume
- Order cancellation and dispute history

Explicit requirements:
- AI advisory results are NEVER used as trust-tier evidence.
- Full audit log maintained for automatic recalculations and admin manual overrides.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import ArtisanProfile, Dispute, OrderItem, Product, Review, TrustTierAudit, User


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


TIER_DEFINITIONS = {
    "new_artisan": {
        "key": "new_artisan",
        "name": "New Artisan",
        "badge": "🪴 New Maker",
        "level": 1,
        "description": "Artisan has joined Digi Karigari and is preparing their craft profile.",
        "requirements": [
            "Registered artisan account",
            "Initial artisan profile submitted",
        ],
    },
    "verified_maker": {
        "key": "verified_maker",
        "name": "Verified Maker",
        "badge": "🛡️ Verified Maker",
        "level": 2,
        "description": "Artisan identity and authentic handcrafted technique verified by admin.",
        "requirements": [
            "Admin-approved artisan profile (Verified Badge)",
            "At least 1 active approved product listing",
        ],
    },
    "trusted_artisan": {
        "key": "trusted_artisan",
        "name": "Trusted Artisan",
        "badge": "⭐ Trusted Artisan",
        "level": 3,
        "description": "Proven track record of high customer satisfaction, reliable delivery, and low disputes.",
        "requirements": [
            "Must be a Verified Maker",
            "At least 5 completed orders",
            "Average review rating of 4.0 or higher (min 2 reviews)",
            "Dispute rate below 5%",
        ],
    },
    "master_artisan": {
        "key": "master_artisan",
        "name": "Master Heritage Artisan",
        "badge": "👑 Master Artisan",
        "level": 4,
        "description": "Exceptional artisanal mastery, extensive sales history, and stellar community reputation.",
        "requirements": [
            "Must be a Verified Maker",
            "At least 15 completed orders",
            "Average review rating of 4.6 or higher (min 5 reviews)",
            "Zero unresolved disputes",
        ],
    },
}


def calculate_metrics(profile: ArtisanProfile, db: Session) -> Dict[str, Any]:
    user_id = profile.user_id

    # Count approved products
    approved_products = db.scalar(
        select(func.count(Product.id)).where(Product.artisan_id == user_id, Product.status == "approved")
    ) or 0

    # Count completed / delivered orders
    completed_orders = db.scalar(
        select(func.count(OrderItem.id)).where(OrderItem.artisan_id == user_id, OrderItem.status == "delivered")
    ) or 0

    total_orders = db.scalar(
        select(func.count(OrderItem.id)).where(OrderItem.artisan_id == user_id)
    ) or 0

    # Reviews and ratings
    reviews = db.scalars(
        select(Review).where(Review.artisan_id == user_id, Review.status == "published")
    ).all()
    review_count = len(reviews)
    avg_rating = round(sum(r.rating for r in reviews) / review_count, 1) if review_count > 0 else 0.0

    # Disputes
    disputes = db.scalars(
        select(Dispute).where(Dispute.artisan_id == user_id)
    ).all()
    total_disputes = len(disputes)
    unresolved_disputes = sum(1 for d in disputes if d.status in ("open", "artisan_replied", "under_review"))
    dispute_rate = round((total_disputes / max(1, total_orders)) * 100, 1) if total_orders > 0 else 0.0

    return {
        "is_verified": profile.status == "approved",
        "approved_products": approved_products,
        "completed_orders": completed_orders,
        "total_orders": total_orders,
        "review_count": review_count,
        "average_rating": avg_rating,
        "total_disputes": total_disputes,
        "unresolved_disputes": unresolved_disputes,
        "dispute_rate": dispute_rate,
    }


def compute_trust_tier(profile: ArtisanProfile, db: Session) -> str:
    # If admin set a manual override, that takes precedence
    if profile.manual_tier_override and profile.manual_tier_override in TIER_DEFINITIONS:
        return profile.manual_tier_override

    metrics = calculate_metrics(profile, db)

    if not metrics["is_verified"]:
        return "new_artisan"

    if metrics["approved_products"] == 0:
        return "new_artisan"

    # Check Master Heritage Artisan criteria
    if (
        metrics["completed_orders"] >= 15
        and metrics["review_count"] >= 5
        and metrics["average_rating"] >= 4.6
        and metrics["unresolved_disputes"] == 0
    ):
        return "master_artisan"

    # Check Trusted Artisan criteria
    if (
        metrics["completed_orders"] >= 5
        and metrics["review_count"] >= 2
        and metrics["average_rating"] >= 4.0
        and metrics["dispute_rate"] < 5.0
    ):
        return "trusted_artisan"

    # Meets Verified Maker criteria
    return "verified_maker"


def get_tier_details(profile: ArtisanProfile, db: Session) -> Dict[str, Any]:
    metrics = calculate_metrics(profile, db)
    calculated_tier = compute_trust_tier(profile, db)
    effective_tier = profile.manual_tier_override or profile.trust_tier or calculated_tier

    if effective_tier not in TIER_DEFINITIONS:
        effective_tier = "new_artisan"

    tier_info = TIER_DEFINITIONS[effective_tier]

    # Calculate next tier and progress
    levels = ["new_artisan", "verified_maker", "trusted_artisan", "master_artisan"]
    curr_idx = levels.index(effective_tier) if effective_tier in levels else 0
    next_tier_info = TIER_DEFINITIONS[levels[curr_idx + 1]] if curr_idx < len(levels) - 1 else None

    # Audit history
    audits = [
        {
            "id": a.id,
            "old_tier": a.old_tier,
            "new_tier": a.new_tier,
            "change_type": a.change_type,
            "reason": a.reason,
            "admin_name": a.admin.name if a.admin else "System (Automatic)",
            "created_at": a.created_at.isoformat(),
        }
        for a in profile.tier_audits
    ]

    return {
        "artisan_id": profile.user_id,
        "current_tier": effective_tier,
        "tier_name": tier_info["name"],
        "badge": tier_info["badge"],
        "level": tier_info["level"],
        "description": tier_info["description"],
        "is_manual_override": bool(profile.manual_tier_override),
        "override_reason": profile.override_reason,
        "metrics": metrics,
        "tier_requirements": tier_info["requirements"],
        "next_tier": next_tier_info,
        "all_tiers": list(TIER_DEFINITIONS.values()),
        "audit_trail": audits,
        "disclaimer": "Trust tiers are based strictly on transparent order metrics, verification, and verified buyer reviews. AI advisory results are NEVER used in trust tier decisions.",
    }


def record_tier_change(
    profile: ArtisanProfile,
    new_tier: str,
    change_type: str,
    reason: str,
    db: Session,
    admin_id: Optional[int] = None,
) -> TrustTierAudit:
    old_tier = profile.trust_tier or "new_artisan"
    profile.trust_tier = new_tier

    audit = TrustTierAudit(
        artisan_profile_id=profile.id,
        old_tier=old_tier,
        new_tier=new_tier,
        change_type=change_type,
        reason=reason.strip(),
        admin_id=admin_id,
        created_at=utcnow(),
    )
    db.add(audit)
    return audit
