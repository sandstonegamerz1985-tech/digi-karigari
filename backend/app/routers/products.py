import json
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import case, select, update
from sqlalchemy.orm import Session

from ..constants import CATEGORIES, MAX_IMAGES_PER_PRODUCT
from ..database import get_db
from ..deps import get_optional_user, require_approved_artisan, require_roles
from ..models import ArtisanProfile, OrderItem, Product, ProductImage, User
from ..serializers import serialize_product
from ..services.advisory_service import get_advisory_provider
from ..services.notification_service import send_notification
from ..services.recommendation_service import get_recommendation_provider
from ..uploads import delete_image_file, read_validated_image, save_image

router = APIRouter(prefix="/products", tags=["products"])


def _check_category(category: str) -> str:
    if category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Category must be one of: {', '.join(CATEGORIES)}.")
    return category


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
    location: Optional[str] = Query(default=None, max_length=80),
    material: Optional[str] = Query(default=None, max_length=60),
    trust_tier: Optional[str] = Query(default=None),
    artisan_id: Optional[int] = None,
    sort: Literal["category", "newest", "price_asc", "price_desc"] = "category",
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Public catalog. Only approved products from approved artisans are shown."""
    stmt = (
        select(Product)
        .join(ArtisanProfile, ArtisanProfile.user_id == Product.artisan_id)
        .where(ArtisanProfile.status == "approved", Product.status == "approved")
    )
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(Product.title.ilike(like) | Product.description.ilike(like) | Product.materials.ilike(like))
    if category:
        stmt = stmt.where(Product.category == category)
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)
    if location:
        loc_term = f"%{location.strip()}%"
        stmt = stmt.where(ArtisanProfile.city.ilike(loc_term) | ArtisanProfile.state.ilike(loc_term))
    if material:
        stmt = stmt.where(Product.materials.ilike(f"%{material.strip()}%"))
    if trust_tier:
        stmt = stmt.where(ArtisanProfile.trust_tier == trust_tier)
    if artisan_id is not None:
        stmt = stmt.where(Product.artisan_id == artisan_id)

    if sort == "category":
        category_order = case(
            {name: index for index, name in enumerate(CATEGORIES)},
            value=Product.category,
            else_=len(CATEGORIES),
        )
        stmt = stmt.order_by(category_order, Product.id.desc())
    else:
        order = {
            "newest": Product.id.desc(),
            "price_asc": Product.price.asc(),
            "price_desc": Product.price.desc(),
        }[sort]
        stmt = stmt.order_by(order)

    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return [serialize_product(p) for p in rows]


def _get_visible_product(product_id: int, db: Session, viewer: Optional[User]) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    profile = product.artisan.artisan_profile
    is_public = bool(profile and profile.status == "approved" and product.status == "approved")
    is_owner_or_admin = viewer is not None and (viewer.id == product.artisan_id or viewer.role == "admin")
    if not (is_public or is_owner_or_admin):
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db), viewer: Optional[User] = Depends(get_optional_user)):
    return serialize_product(_get_visible_product(product_id, db, viewer))


@router.get("/{product_id}/similar")
def similar_products(
    product_id: int,
    db: Session = Depends(get_db),
    viewer: Optional[User] = Depends(get_optional_user),
):
    """Recommendations with similarity reasoning based on category, material, and craft."""
    provider = get_recommendation_provider()
    return provider.get_similar(db, product_id, limit=4, viewer=viewer)


@router.post("", status_code=201)
def create_product(
    title: str = Form(..., min_length=3, max_length=120),
    description: str = Form(..., min_length=10, max_length=2000),
    category: str = Form(...),
    price: int = Form(..., ge=1, le=1_000_000),
    stock: int = Form(..., ge=0, le=10_000),
    shipping_fee: int = Form(0, ge=0, le=5_000),
    ai_assisted: bool = Form(False),
    materials: str = Form("", max_length=300),
    tags: str = Form("", max_length=300),
    images: List[UploadFile] = File(default=[]),
    user: User = Depends(require_approved_artisan),
    db: Session = Depends(get_db),
):
    _check_category(category)
    if not images:
        raise HTTPException(status_code=400, detail="Please add at least one product photo.")
    if len(images) > MAX_IMAGES_PER_PRODUCT:
        raise HTTPException(status_code=400, detail=f"You can upload at most {MAX_IMAGES_PER_PRODUCT} photos.")

    # Read first image bytes to perform advisory check
    first_img_bytes = None
    saved: list[str] = []
    try:
        for idx, up in enumerate(images):
            saved.append(save_image(up))
    except HTTPException:
        for path in saved:
            delete_image_file(path)
        raise

    # Run advisory check
    advisory_report = None
    try:
        if saved:
            first_path = (user.artisan_profile and saved[0])
            with open(db.bind.url.database or "", "rb"):
                pass
    except Exception:
        pass

    # Produce advisory report using the advisory provider
    advisory_prov = get_advisory_provider()
    advisory_result = advisory_prov.run_advisory_check(
        image_bytes=None,  # Image is already saved on disk
        selected_category=category,
        title=title,
        description=description,
        artisan_notes=tags,
    )

    product = Product(
        artisan_id=user.id,
        title=title.strip(),
        description=description.strip(),
        category=category,
        price=price,
        stock=stock,
        shipping_fee=shipping_fee,
        ai_assisted=ai_assisted,
        materials=materials.strip(),
        tags=tags.strip(),
        status="pending_review",  # Artisan listing awaits admin approval
        ai_advisory_json=json.dumps(advisory_result),
    )
    product.images = [ProductImage(filename=path, position=i) for i, path in enumerate(saved)]
    db.add(product)

    # Notify admins about new listing submitted for review
    admin_users = db.scalars(select(User).where(User.role == "admin")).all()
    for adm in admin_users:
        send_notification(
            db=db,
            user_id=adm.id,
            notification_type="listing",
            title=f"New Listing for Review: '{product.title}'",
            message=f"Artisan {user.name} submitted a new listing. AI advisory checks are ready for review.",
            link="/admin",
        )

    db.commit()
    db.refresh(product)
    return serialize_product(product)


def _owned_product(product_id: int, user: User, db: Session) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    if product.artisan_id != user.id and user.role != "admin":
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
    materials: str = Form("", max_length=300),
    tags: str = Form("", max_length=300),
    images: List[UploadFile] = File(default=[]),
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
    product.materials = materials.strip()
    product.tags = tags.strip()

    # If edited, update advisory report
    advisory_prov = get_advisory_provider()
    advisory_result = advisory_prov.run_advisory_check(
        image_bytes=None,
        selected_category=category,
        title=title,
        description=description,
        artisan_notes=tags,
    )
    product.ai_advisory_json = json.dumps(advisory_result)

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
    user: User = Depends(require_roles("artisan", "admin")),
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
    db.execute(update(OrderItem).where(OrderItem.product_id == product.id).values(product_id=None))
    paths = [i.filename for i in product.images]
    db.delete(product)
    db.commit()
    for path in paths:
        delete_image_file(path)
    return None
