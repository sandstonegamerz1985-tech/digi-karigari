"""Turns database objects into plain dictionaries (JSON) for the API.

Keeping every response shape in ONE file helps the frontend and backend stay in agreement.
"""
import json
from typing import Optional

from .models import (
    ArtisanProfile,
    Conversation,
    Dispute,
    DisputeAudit,
    DisputeMessage,
    Message,
    Notification,
    Order,
    OrderItem,
    Product,
    Review,
    TrustTierAudit,
    User,
)
from .services.trust_tier_service import TIER_DEFINITIONS


def image_url(relative_path: Optional[str]) -> Optional[str]:
    return f"/uploads/{relative_path}" if relative_path else None


def get_trust_badge(tier_key: str) -> str:
    return TIER_DEFINITIONS.get(tier_key, {}).get("badge", "🪴 New Maker")


def get_trust_name(tier_key: str) -> str:
    return TIER_DEFINITIONS.get(tier_key, {}).get("name", "New Artisan")


def serialize_artisan_brief(user: User) -> dict:
    p = user.artisan_profile
    tier = p.trust_tier if p else "new_artisan"
    return {
        "id": user.id,
        "name": user.name,
        "craft": p.craft if p else None,
        "city": p.city if p else None,
        "state": p.state if p else None,
        "verified": bool(p and p.status == "approved"),
        "trust_tier": tier,
        "trust_badge": get_trust_badge(tier),
        "trust_name": get_trust_name(tier),
    }


def serialize_user(user: User) -> dict:
    p = user.artisan_profile
    data = {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "artisan": None}
    if p:
        tier = p.trust_tier or "new_artisan"
        data["artisan"] = {
            "status": p.status,
            "verified": p.status == "approved",
            "reject_reason": p.reject_reason or "",
            "craft": p.craft,
            "bio": p.bio,
            "city": p.city,
            "state": p.state,
            "trust_tier": tier,
            "trust_badge": get_trust_badge(tier),
            "trust_name": get_trust_name(tier),
            "is_manual_override": bool(p.manual_tier_override),
        }
    return data


def serialize_product(product: Product) -> dict:
    images = sorted(product.images, key=lambda i: i.position)
    advisory_report = None
    if product.ai_advisory_json:
        try:
            advisory_report = json.loads(product.ai_advisory_json)
        except Exception:
            advisory_report = None

    # Calculate review summary if reviews exist
    avg_rating = 0.0
    published_reviews = [r for r in product.reviews if r.status == "published"]
    if published_reviews:
        avg_rating = round(sum(r.rating for r in published_reviews) / len(published_reviews), 1)

    return {
        "id": product.id,
        "title": product.title,
        "description": product.description,
        "category": product.category,
        "price": product.price,
        "stock": product.stock,
        "shipping_fee": product.shipping_fee,
        "ai_assisted": product.ai_assisted,
        "status": product.status,
        "reject_reason": product.reject_reason or "",
        "materials": product.materials or "",
        "tags": [t.strip() for t in product.tags.split(",") if t.strip()] if product.tags else [],
        "ai_advisory": advisory_report,
        "rating": avg_rating,
        "review_count": len(published_reviews),
        "images": [{"id": i.id, "url": image_url(i.filename)} for i in images],
        "image_url": image_url(images[0].filename) if images else None,
        "artisan": serialize_artisan_brief(product.artisan) if product.artisan else None,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }


def serialize_artisan_row(user: User, product_count: int = 0) -> dict:
    """Used by public artisan directory and admin lists."""
    p = user.artisan_profile
    tier = p.trust_tier if p else "new_artisan"
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "craft": p.craft if p else "",
        "bio": p.bio if p else "",
        "city": p.city if p else "",
        "state": p.state if p else "",
        "status": p.status if p else "pending",
        "verified": bool(p and p.status == "approved"),
        "reject_reason": p.reject_reason or "" if p else "",
        "trust_tier": tier,
        "trust_badge": get_trust_badge(tier),
        "trust_name": get_trust_name(tier),
        "is_manual_override": bool(p and p.manual_tier_override),
        "product_count": product_count,
        "created_at": p.created_at.isoformat() if p and p.created_at else None,
    }


def order_status(items: list[OrderItem]) -> str:
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
        "has_reviewed": bool(item.review is not None),
        "review_id": item.review.id if item.review else None,
        "has_dispute": bool(item.disputes and len(item.disputes) > 0),
        "dispute_id": item.disputes[0].id if item.disputes else None,
    }


def serialize_order(order: Order, only_artisan_id: Optional[int] = None, include_buyer: bool = False) -> dict:
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


def serialize_message(msg: Message) -> dict:
    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "sender_id": msg.sender_id,
        "sender_name": msg.sender.name if msg.sender else "",
        "text": msg.text,
        "read_at": msg.read_at.isoformat() if msg.read_at else None,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


def serialize_conversation(convo: Conversation, viewer_user_id: int) -> dict:
    other_party = convo.artisan if viewer_user_id == convo.buyer_id else convo.buyer
    unread_count = sum(1 for m in convo.messages if m.sender_id != viewer_user_id and m.read_at is None)

    product_brief = None
    if convo.product:
        product_brief = {
            "id": convo.product.id,
            "title": convo.product.title,
            "price": convo.product.price,
            "image_url": image_url(convo.product.images[0].filename) if convo.product.images else None,
        }

    return {
        "id": convo.id,
        "subject": convo.subject or (f"Inquiry regarding {convo.product.title}" if convo.product else "Direct Inquiry"),
        "buyer_id": convo.buyer_id,
        "artisan_id": convo.artisan_id,
        "other_user": {
            "id": other_party.id if other_party else 0,
            "name": other_party.name if other_party else "Marketplace User",
            "role": other_party.role if other_party else "user",
            "craft": other_party.artisan_profile.craft if other_party and other_party.artisan_profile else None,
        },
        "product": product_brief,
        "order_id": convo.order_id,
        "last_message_text": convo.last_message_text or "",
        "last_message_at": convo.last_message_at.isoformat() if convo.last_message_at else convo.created_at.isoformat(),
        "unread_count": unread_count,
        "created_at": convo.created_at.isoformat() if convo.created_at else None,
    }


def serialize_notification(n: Notification) -> dict:
    return {
        "id": n.id,
        "type": n.type,
        "title": n.title,
        "message": n.message,
        "link": n.link or "",
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


def serialize_review(r: Review, include_product: bool = False) -> dict:
    data = {
        "id": r.id,
        "product_id": r.product_id,
        "order_id": r.order_id,
        "rating": r.rating,
        "title": r.title,
        "comment": r.comment,
        "status": r.status,
        "moderation_note": r.moderation_note or "",
        "buyer": {
            "id": r.buyer.id if r.buyer else 0,
            "name": r.buyer.name if r.buyer else "Verified Buyer",
        },
        "artisan_id": r.artisan_id,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
    if include_product and r.product:
        data["product"] = {
            "id": r.product.id,
            "title": r.product.title,
            "image_url": image_url(r.product.images[0].filename) if r.product.images else None,
        }
    return data


def serialize_dispute(d: Dispute) -> dict:
    return {
        "id": d.id,
        "order_id": d.order_id,
        "order_item_id": d.order_item_id,
        "reason": d.reason,
        "description": d.description,
        "requested_resolution": d.requested_resolution,
        "requested_amount": d.requested_amount,
        "status": d.status,
        "resolution_decision": d.resolution_decision,
        "refunded_amount": d.refunded_amount,
        "refund_reference": d.refund_reference,
        "buyer": {
            "id": d.buyer.id if d.buyer else 0,
            "name": d.buyer.name if d.buyer else "Buyer",
            "email": d.buyer.email if d.buyer else "",
        },
        "artisan": {
            "id": d.artisan.id if d.artisan else 0,
            "name": d.artisan.name if d.artisan else "Artisan",
        },
        "item_title": d.order_item.title if d.order_item else (d.order.items[0].title if d.order and d.order.items else "Order items"),
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "sender_name": m.sender.name if m.sender else "",
                "sender_role": m.sender_role,
                "message": m.message,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in d.messages
        ],
        "audits": [
            {
                "id": a.id,
                "actor_id": a.actor_id,
                "actor_name": a.actor.name if a.actor else "System",
                "actor_role": a.actor_role,
                "action": a.action,
                "notes": a.notes,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in d.audits
        ],
    }
