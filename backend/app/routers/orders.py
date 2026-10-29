from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..constants import ITEM_STATUS_FLOW
from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import Order, OrderItem, Product, User
from ..serializers import serialize_order

router = APIRouter(prefix="/orders", tags=["orders"])


class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=10)


class OrderIn(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1, max_length=20)
    shipping_name: str = Field(min_length=2, max_length=80)
    shipping_address: str = Field(min_length=5, max_length=300)
    city: str = Field(min_length=2, max_length=80)
    pincode: str = Field(pattern=r"^\d{6}$")
    phone: str = Field(pattern=r"^\d{10}$")
    # SIMULATED payment. No card details are collected anywhere in this app.
    simulate_payment: Literal["success", "fail"] = "success"


@router.post("", status_code=201)
def create_order(data: OrderIn, user: User = Depends(require_roles("buyer")), db: Session = Depends(get_db)):
    # Merge duplicate lines for the same product
    wanted: dict[int, int] = {}
    for line in data.items:
        wanted[line.product_id] = wanted.get(line.product_id, 0) + line.quantity

    # The SERVER looks up prices and stock. We never trust prices sent by the browser.
    products = {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(wanted.keys()))).all()}
    for pid, qty in wanted.items():
        product = products.get(pid)
        profile = product.artisan.artisan_profile if product else None
        if not product or not profile or profile.status != "approved":
            raise HTTPException(status_code=404, detail="One of the products in your cart is no longer available.")
        if qty > product.stock:
            raise HTTPException(
                status_code=409,
                detail=f'Only {product.stock} left of "{product.title}". Please reduce the quantity.',
            )

    if data.simulate_payment == "fail":
        raise HTTPException(
            status_code=402,
            detail="Test payment declined (simulated). No money was charged and nothing was ordered.",
        )

    # Reserve every line with a conditional database update. The earlier stock check
    # gives a friendly error in the usual case; this atomic guard prevents two concurrent
    # checkouts from both consuming the same remaining units.
    for pid, qty in wanted.items():
        result = db.execute(
            update(Product)
            .where(Product.id == pid, Product.stock >= qty)
            .values(stock=Product.stock - qty)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Stock changed during checkout. Please review your cart and try again.",
            )

    order = Order(
        buyer_id=user.id,
        shipping_name=data.shipping_name.strip(),
        shipping_address=data.shipping_address.strip(),
        city=data.city.strip(),
        pincode=data.pincode,
        phone=data.phone,
        payment_status="paid_test",
    )
    for pid, qty in wanted.items():
        product = products[pid]
        first_image = product.images[0].filename if product.images else None
        order.items.append(
            OrderItem(
                product_id=product.id,
                artisan_id=product.artisan_id,
                title=product.title,
                price=product.price,
                shipping_fee=product.shipping_fee,  # charged once per product line
                quantity=qty,
                image=first_image,
                status="placed",
            )
        )
    db.add(order)
    db.commit()
    db.refresh(order)
    return serialize_order(order)


def _orders_for(user: User, db: Session) -> list[Order]:
    stmt = select(Order).order_by(Order.id.desc())
    if user.role == "buyer":
        stmt = stmt.where(Order.buyer_id == user.id)
    elif user.role == "artisan":
        stmt = stmt.where(Order.id.in_(select(OrderItem.order_id).where(OrderItem.artisan_id == user.id)))
    return list(db.scalars(stmt).all())


def _serialize_for(order: Order, user: User) -> dict:
    if user.role == "artisan":
        return serialize_order(order, only_artisan_id=user.id, include_buyer=True)
    return serialize_order(order, include_buyer=(user.role == "admin"))


@router.get("")
def list_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Buyers see their own orders, artisans see orders containing THEIR items, admins see all."""
    return [_serialize_for(o, user) for o in _orders_for(user, db)]


@router.get("/{order_id}")
def get_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    allowed = False
    if order:
        if user.role == "admin":
            allowed = True
        elif user.role == "buyer":
            allowed = order.buyer_id == user.id
        elif user.role == "artisan":
            allowed = any(i.artisan_id == user.id for i in order.items)
    if not order or not allowed:
        raise HTTPException(status_code=404, detail="Order not found.")
    return _serialize_for(order, user)


class ShipmentIn(BaseModel):
    status: Literal["packed", "shipped", "delivered"]
    courier_name: Optional[str] = Field(default=None, max_length=60)
    tracking_id: Optional[str] = Field(default=None, max_length=40, pattern=r"^[A-Za-z0-9\-/ ]*$")


@router.patch("/items/{item_id}")
def update_item_status(
    item_id: int,
    data: ShipmentIn,
    user: User = Depends(require_roles("artisan")),
    db: Session = Depends(get_db),
):
    """The artisan who owns the item updates its status and types the courier + tracking ID by hand.
    (No real courier API is used.)"""
    item = db.get(OrderItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Order item not found.")
    if item.artisan_id != user.id:
        raise HTTPException(status_code=403, detail="You can only update your own order items.")
    if ITEM_STATUS_FLOW.index(data.status) <= ITEM_STATUS_FLOW.index(item.status):
        raise HTTPException(status_code=400, detail="Status can only move forward (placed > packed > shipped > delivered).")

    courier = (data.courier_name if data.courier_name is not None else item.courier_name).strip()
    tracking = (data.tracking_id if data.tracking_id is not None else item.tracking_id).strip()
    if data.status in ("shipped", "delivered") and (not courier or not tracking):
        raise HTTPException(status_code=400, detail="Please enter the courier name and tracking ID before marking as shipped.")

    item.status = data.status
    item.courier_name = courier
    item.tracking_id = tracking
    db.commit()
    db.refresh(item)
    return serialize_order(item.order, only_artisan_id=user.id, include_buyer=True)
