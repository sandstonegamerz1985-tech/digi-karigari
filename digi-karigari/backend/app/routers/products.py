from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..constants import CATEGORIES, MAX_IMAGES_PER_PRODUCT
from ..database import get_db
from ..deps import get_optional_user, require_approved_artisan, require_roles
from ..models import ArtisanProfile, OrderItem, Product, ProductImage, User
from ..serializers import serialize_product
from ..uploads import delete_image_file, save_image

router = APIRouter(prefix="/products", tags=["products"])


def _check_category(category: str) -> str:
    if category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Category must be one of: {', '.join(CATEGORIES)}.")
    return category


# NOTE: fixed paths like /categories and /mine must be declared BEFORE /{product_id}.
@router.get("/categories")
def list_categories():
    return CATEGORIES


@router.get("/mine")
def my_products(user: User = Depends(require_roles("artisan")), db: Session = Depends(get_db)):
    rows = db.scalars(select(Product).where(Product.artisan_id == user.id).order_by(Product.id.desc())).all()
    return [serialize_product(p) for p in rows]


@router.get("")
def list_products(
    q: Optional[str] = Query(default=None, max_length=100, description="keyword search in title/description"),
    category: Optional[str] = Query(default=None, max_length=40),
    min_price: Optional[int] = Query(default=None, ge=0),
    max_price: Optional[int] = Query(default=None, ge=0),
    artisan_id: Optional[int] = None,
    sort: Literal["newest", "price_asc", "price_desc"] = "newest",
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Public catalog. Only products from APPROVED artisans are shown."""
    stmt = (
        select(Product)
        .join(ArtisanProfile, ArtisanProfile.user_id == Product.artisan_id)
        .where(ArtisanProfile.status == "approved")
    )
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(Product.title.ilike(like) | Product.description.ilike(like))
    if category:
        stmt = stmt.where(Product.category == category)
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)
    if artisan_id is not None:
        stmt = stmt.where(Product.artisan_id == artisan_id)
    order = {
        "newest": Product.id.desc(),
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
    }[sort]
    rows = db.scalars(stmt.order_by(order).limit(limit).offset(offset)).all()
    return [serialize_product(p) for p in rows]


def _get_visible_product(product_id: int, db: Session, viewer: Optional[User]) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    profile = product.artisan.artisan_profile
    is_public = bool(profile and profile.status == "approved")
    is_owner_or_admin = viewer is not None and (viewer.id == product.artisan_id or viewer.role == "admin")
    if not (is_public or is_owner_or_admin):
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db), viewer: Optional[User] = Depends(get_optional_user)):
    return serialize_product(_get_visible_product(product_id, db, viewer))


@router.get("/{product_id}/similar")
def similar_products(product_id: int, db: Session = Depends(get_db), viewer: Optional[User] = Depends(get_optional_user)):
    """DEMO-ONLY recommendations: same category, newest first. Real AI/semantic similarity is planned."""
    product = _get_visible_product(product_id, db, viewer)
    rows = db.scalars(
        select(Product)
        .join(ArtisanProfile, ArtisanProfile.user_id == Product.artisan_id)
        .where(ArtisanProfile.status == "approved", Product.category == product.category, Product.id != product.id)
        .order_by(Product.id.desc())
        .limit(4)
    ).all()
    return {"method": "same-category (demo-only)", "items": [serialize_product(p) for p in rows]}


@router.post("", status_code=201)
def create_product(
    title: str = Form(..., min_length=3, max_length=120),
    description: str = Form(..., min_length=10, max_length=2000),
    category: str = Form(...),
    price: int = Form(..., ge=1, le=1_000_000),
    stock: int = Form(..., ge=0, le=10_000),
    shipping_fee: int = Form(0, ge=0, le=5_000),
    ai_assisted: bool = Form(False),
    images: List[UploadFile] = File(default=[]),
    user: User = Depends(require_approved_artisan),
    db: Session = Depends(get_db),
):
    _check_category(category)
    if not images:
        raise HTTPException(status_code=400, detail="Please add at least one product photo.")
    if len(images) > MAX_IMAGES_PER_PRODUCT:
        raise HTTPException(status_code=400, detail=f"You can upload at most {MAX_IMAGES_PER_PRODUCT} photos.")

    saved: list[str] = []
    try:
        for up in images:
            saved.append(save_image(up))
    except HTTPException:
        for path in saved:  # do not leave half-uploaded files behind
            delete_image_file(path)
        raise

    product = Product(
        artisan_id=user.id,
        title=title.strip(),
        description=description.strip(),
        category=category,
        price=price,
        stock=stock,
        shipping_fee=shipping_fee,
        ai_assisted=ai_assisted,
    )
    product.images = [ProductImage(filename=path, position=i) for i, path in enumerate(saved)]
    db.add(product)
    db.commit()
    db.refresh(product)
    return serialize_product(product)


def _owned_product(product_id: int, user: User, db: Session) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    if product.artisan_id != user.id:
        raise HTTPException(status_code=403, detail="You can only change your own listings.")
    return product


@router.put("/{product_id}")
def update_product(
    product_id: int,
    title: str = Form(..., min_length=3, max_length=120),
    description: str = Form(..., min_length=10, max_length=2000),
    category: str = Form(...),
    price: int = Form(..., ge=1, le=1_000_000),
    stock: int = Form(..., ge=0, le=10_000),
    shipping_fee: int = Form(0, ge=0, le=5_000),
    ai_assisted: bool = Form(False),
    images: List[UploadFile] = File(default=[]),  # NEW photos to add (optional)
    user: User = Depends(require_approved_artisan),
    db: Session = Depends(get_db),
):
    product = _owned_product(product_id, user, db)
    _check_category(category)
    if len(product.images) + len(images) > MAX_IMAGES_PER_PRODUCT:
        raise HTTPException(
            status_code=400,
            detail=f"A listing can have at most {MAX_IMAGES_PER_PRODUCT} photos. Remove some first.",
        )
    saved: list[str] = []
    try:
        for up in images:
            saved.append(save_image(up))
    except HTTPException:
        for path in saved:
            delete_image_file(path)
        raise

    product.title = title.strip()
    product.description = description.strip()
    product.category = category
    product.price = price
    product.stock = stock
    product.shipping_fee = shipping_fee
    product.ai_assisted = ai_assisted
    start = max([i.position for i in product.images], default=-1) + 1
    for offset, path in enumerate(saved):
        product.images.append(ProductImage(filename=path, position=start + offset))
    db.commit()
    db.refresh(product)
    return serialize_product(product)


@router.delete("/{product_id}/images/{image_id}")
def delete_product_image(
    product_id: int,
    image_id: int,
    user: User = Depends(require_roles("artisan")),
    db: Session = Depends(get_db),
):
    product = _owned_product(product_id, user, db)
    image = next((i for i in product.images if i.id == image_id), None)
    if not image:
        raise HTTPException(status_code=404, detail="Photo not found.")
    if len(product.images) <= 1:
        raise HTTPException(status_code=400, detail="A listing needs at least one photo.")
    path = image.filename
    product.images.remove(image)
    db.commit()
    delete_image_file(path)
    return serialize_product(product)


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    user: User = Depends(require_roles("artisan", "admin")),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    if user.role != "admin" and product.artisan_id != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own listings.")
    # Old orders keep their copied title/price; just detach them from the deleted product.
    db.execute(update(OrderItem).where(OrderItem.product_id == product.id).values(product_id=None))
    paths = [i.filename for i in product.images]
    db.delete(product)
    db.commit()
    for path in paths:
        delete_image_file(path)
    return None
