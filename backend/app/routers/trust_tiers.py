from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import ArtisanProfile, User
from ..services.trust_tier_service import (
    TIER_DEFINITIONS,
    compute_trust_tier,
    get_tier_details,
    record_tier_change,
)

router = APIRouter(tags=["trust-tiers"])


class TierOverrideIn(BaseModel):
    new_tier: str
    reason: str = Field(min_length=5, max_length=300)


@router.get("/artisans/{user_id}/trust-tier")
def get_artisan_trust_tier(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Returns trust tier, transparent criteria breakdown, and audit trail for an artisan."""
    user = db.get(User, user_id)
    if not user or not user.artisan_profile:
        raise HTTPException(status_code=404, detail="Artisan not found.")

    return get_tier_details(user.artisan_profile, db)


@router.get("/admin/trust-tiers")
def admin_list_trust_tiers(
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    """Admin view of all artisans with their computed criteria and current trust tier."""
    profiles = db.scalars(select(ArtisanProfile).order_by(ArtisanProfile.id.desc())).all()
    results = []
    for p in profiles:
        details = get_tier_details(p, db)
        details["artisan_name"] = p.user.name if p.user else ""
        details["artisan_email"] = p.user.email if p.user else ""
        details["craft"] = p.craft
        results.append(details)
    return results


@router.post("/admin/trust-tiers/{user_id}/override")
def admin_override_trust_tier(
    user_id: int,
    data: TierOverrideIn,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    """Admin manually sets or overrides an artisan's trust tier with required justification."""
    if data.new_tier not in TIER_DEFINITIONS and data.new_tier != "auto":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier. Must be one of: {', '.join(TIER_DEFINITIONS.keys())} or 'auto' to revert to automatic.",
        )

    target = db.get(User, user_id)
    if not target or not target.artisan_profile:
        raise HTTPException(status_code=404, detail="Artisan not found.")

    p = target.artisan_profile
    if data.new_tier == "auto":
        p.manual_tier_override = None
        p.override_reason = ""
        computed = compute_trust_tier(p, db)
        record_tier_change(
            profile=p,
            new_tier=computed,
            change_type="automatic_recalculation",
            reason=f"Admin reverted to automatic metric evaluation: {data.reason}",
            db=db,
            admin_id=user.id,
        )
    else:
        p.manual_tier_override = data.new_tier
        p.override_reason = data.reason.strip()
        record_tier_change(
            profile=p,
            new_tier=data.new_tier,
            change_type="admin_override",
            reason=data.reason.strip(),
            db=db,
            admin_id=user.id,
        )

    db.commit()
    return get_tier_details(p, db)
