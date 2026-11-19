from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_optional_user
from ..models import User
from ..services.recommendation_service import get_recommendation_provider

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/similar/{product_id}")
def similar_recommendations(
    product_id: int,
    limit: int = Query(default=4, ge=1, le=12),
    db: Session = Depends(get_db),
    viewer: User = Depends(get_optional_user),
):
    """Returns similar artisanal items with human-readable similarity reasons."""
    provider = get_recommendation_provider()
    return provider.get_similar(db, product_id, limit=limit, viewer=viewer)


@router.get("/for-you")
def for_you_recommendations(
    limit: int = Query(default=6, ge=1, le=12),
    db: Session = Depends(get_db),
    viewer: User = Depends(get_optional_user),
):
    """Personalized craft discovery recommendations."""
    provider = get_recommendation_provider()
    if viewer:
        return provider.get_for_you(db, viewer, limit=limit)
    # Generic popular picks if not logged in
    from ..models import Product, ArtisanProfile
    from ..serializers import serialize_product
    from sqlalchemy import select
    products = db.scalars(
        select(Product)
        .join(ArtisanProfile, ArtisanProfile.user_id == Product.artisan_id)
        .where(ArtisanProfile.status == "approved", Product.status == "approved")
        .order_by(Product.id.desc())
        .limit(limit)
    ).all()
    items = []
    for p in products:
        d = serialize_product(p)
        d["recommendation_reason"] = "Featured handcrafted piece"
        items.append(d)
    return {
        "provider": "catalog_featured",
        "is_ai": False,
        "items": items,
    }
