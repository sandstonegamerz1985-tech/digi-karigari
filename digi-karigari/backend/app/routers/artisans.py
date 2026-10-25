from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ArtisanProfile, Product, User
from ..serializers import serialize_artisan_row, serialize_product

router = APIRouter(prefix="/artisans", tags=["artisans"])


def _public_row(user: User, db: Session) -> dict:
    count = db.scalar(select(func.count(Product.id)).where(Product.artisan_id == user.id)) or 0
    row = serialize_artisan_row(user, count)
    row.pop("email", None)  # never show emails publicly
    row.pop("reject_reason", None)
    return row


@router.get("")
def list_artisans(db: Session = Depends(get_db)):
    """Public list: only APPROVED (Verified) artisans."""
    users = db.scalars(
        select(User)
        .join(ArtisanProfile, ArtisanProfile.user_id == User.id)
        .where(ArtisanProfile.status == "approved")
        .order_by(User.name)
    ).all()
    return [_public_row(u, db) for u in users]


@router.get("/{artisan_id}")
def get_artisan(artisan_id: int, db: Session = Depends(get_db)):
    user = db.get(User, artisan_id)
    if not user or not user.artisan_profile or user.artisan_profile.status != "approved":
        raise HTTPException(status_code=404, detail="Artisan not found.")
    products = db.scalars(select(Product).where(Product.artisan_id == user.id).order_by(Product.id.desc())).all()
    data = _public_row(user, db)
    data["products"] = [serialize_product(p) for p in products]
    return data
