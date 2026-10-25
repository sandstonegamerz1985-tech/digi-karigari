"""Turns database objects into plain dictionaries (JSON) for the API.

Keeping every response shape in ONE file helps the frontend and backend stay in agreement.
"""
from typing import Optional

from .models import Order, OrderItem, Product, User


def image_url(relative_path: Optional[str]) -> Optional[str]:
    return f"/uploads/{relative_path}" if relative_path else None


def serialize_artisan_brief(user: User) -> dict:
    p = user.artisan_profile
    return {
        "id": user.id,
        "name": user.name,
        "craft": p.craft if p else None,
        "city": p.city if p else None,
        "state": p.state if p else None,
        "verified": bool(p and p.status == "approved"),
    }


def serialize_user(user: User) -> dict:
    p = user.artisan_profile
    data = {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "artisan": None}
    if p:
        data["artisan"] = {
            "status": p.status,
            "verified": p.status == "approved",
            "reject_reason": p.reject_reason or "",
            "craft": p.craft,
            "bio": p.bio,
            "city": p.city,
            "state": p.state,
        }
    return data


def serialize_product(product: Product) -> dict:
    images = sorted(product.images, key=lambda i: i.position)
    return {
        "id": product.id,
        "title": product.title,
        "description": product.description,
        "category": product.category,
        "price": product.price,
        "stock": product.stock,
        "shipping_fee": product.shipping_fee,
        "ai_assisted": product.ai_assisted,
        "images": [{"id": i.id, "url": image_url(i.filename)} for i in images],
        "image_url": image_url(images[0].filename) if images else None,
        "artisan": serialize_artisan_brief(product.artisan),
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }


def serialize_artisan_row(user: User, product_count: int = 0) -> dict:
    """Used by the public artisan pages and by the admin approval list."""
    p = user.artisan_profile
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "craft": p.craft,
        "bio": p.bio,
        "city": p.city,
        "state": p.state,
        "status": p.status,
        "verified": p.status == "approved",
        "reject_reason": p.reject_reason or "",
        "product_count": product_count,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def order_status(items: list[OrderItem]) -> str:
    """Works out one overall status from the statuses of the items."""
    statuses = {i.status for i in items}
    if not statuses:
        return "placed"
    if statuses == {"delivered"}:
        return "delivered"
    if statuses <= {"shipped", "delivered"}:
        return "shipped"
    if statuses & {"shipped", "delivered"}:
        return "partially_shipped"
    if statuses == {"packed"}:
        return "packed"
    if "packed" in statuses:
        return "processing"
    return "placed"


def serialize_order_item(item: OrderItem) -> dict:
    return {
        "id": item.id,
        "product_id": item.product_id,
        "title": item.title,
        "price": item.price,
        "shipping_fee": item.shipping_fee,
        "quantity": item.quantity,
        "line_total": item.price * item.quantity + item.shipping_fee,
        "image_url": image_url(item.image),
        "artisan_id": item.artisan_id,
        "artisan_name": item.artisan.name if item.artisan else "",
        "status": item.status,
        "courier_name": item.courier_name,
        "tracking_id": item.tracking_id,
    }


def serialize_order(order: Order, only_artisan_id: Optional[int] = None, include_buyer: bool = False) -> dict:
    """If only_artisan_id is given, only that artisan's items (and their totals) are shown."""
    items = [i for i in order.items if only_artisan_id is None or i.artisan_id == only_artisan_id]
    subtotal = sum(i.price * i.quantity for i in items)
    shipping_total = sum(i.shipping_fee for i in items)
    data = {
        "id": order.id,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "status": order_status(items),
        "payment_status": order.payment_status,
        "payment_note": "TEST payment only - no real money was charged.",
        "shipping": {
            "name": order.shipping_name,
            "address": order.shipping_address,
            "city": order.city,
            "pincode": order.pincode,
            "phone": order.phone,
        },
        "subtotal": subtotal,
        "shipping_total": shipping_total,
        "total": subtotal + shipping_total,
        "items": [serialize_order_item(i) for i in items],
    }
    if include_buyer:
        data["buyer"] = {"id": order.buyer.id, "name": order.buyer.name, "email": order.buyer.email}
    return data
