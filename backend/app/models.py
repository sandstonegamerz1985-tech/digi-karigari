"""Database tables (SQLAlchemy 2.0 style). Written to work on SQLite and PostgreSQL."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="buyer")  # buyer | artisan | admin
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    artisan_profile: Mapped[Optional["ArtisanProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    products: Mapped[list["Product"]] = relationship(back_populates="artisan")
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", order_by="Notification.id.desc()"
    )


class ArtisanProfile(Base):
    __tablename__ = "artisan_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    craft: Mapped[str] = mapped_column(String(80))
    bio: Mapped[str] = mapped_column(Text, default="")
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80), default="")
    # pending -> approved (Verified badge) or rejected. Only an admin can change this.
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reject_reason: Mapped[str] = mapped_column(String(300), default="")
    # Seller Trust Tiers: new_artisan | verified_maker | trusted_artisan | master_artisan
    trust_tier: Mapped[str] = mapped_column(String(30), default="new_artisan")
    manual_tier_override: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    override_reason: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="artisan_profile")
    tier_audits: Mapped[list["TrustTierAudit"]] = relationship(
        back_populates="artisan_profile", cascade="all, delete-orphan", order_by="TrustTierAudit.id.desc()"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    artisan_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(40), index=True)
    price: Mapped[int] = mapped_column(Integer)  # whole rupees
    stock: Mapped[int] = mapped_column(Integer, default=0)
    shipping_fee: Mapped[int] = mapped_column(Integer, default=0)  # whole rupees
    ai_assisted: Mapped[bool] = mapped_column(Boolean, default=False)
    # Listing moderation status: approved | pending_review | rejected
    status: Mapped[str] = mapped_column(String(20), default="approved", index=True)
    reject_reason: Mapped[str] = mapped_column(String(300), default="")
    materials: Mapped[str] = mapped_column(String(300), default="")
    tags: Mapped[str] = mapped_column(String(300), default="")
    ai_advisory_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    artisan: Mapped["User"] = relationship(back_populates="products")
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.position"
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="Review.id.desc()"
    )


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    filename: Mapped[str] = mapped_column(String(200))  # path relative to the uploads folder
    position: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped["Product"] = relationship(back_populates="images")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    shipping_name: Mapped[str] = mapped_column(String(80))
    shipping_address: Mapped[str] = mapped_column(String(300))
    city: Mapped[str] = mapped_column(String(80))
    pincode: Mapped[str] = mapped_column(String(10))
    phone: Mapped[str] = mapped_column(String(15))
    payment_status: Mapped[str] = mapped_column(String(20), default="paid_test")  # TEST payment only
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id])
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderItem.id"
    )
    disputes: Mapped[list["Dispute"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """One product line inside an order. Title and price are copied ("snapshot") so that
    old orders stay correct even if the artisan later edits or deletes the listing."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    artisan_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    price: Mapped[int] = mapped_column(Integer)
    shipping_fee: Mapped[int] = mapped_column(Integer, default=0)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    image: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="placed")
    courier_name: Mapped[str] = mapped_column(String(60), default="")
    tracking_id: Mapped[str] = mapped_column(String(40), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    order: Mapped["Order"] = relationship(back_populates="items")
    artisan: Mapped["User"] = relationship(foreign_keys=[artisan_id])
    product: Mapped[Optional["Product"]] = relationship(foreign_keys=[product_id])
    review: Mapped[Optional["Review"]] = relationship(back_populates="order_item", uselist=False)
    disputes: Mapped[list["Dispute"]] = relationship(back_populates="order_item")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    artisan_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    subject: Mapped[str] = mapped_column(String(140), default="")
    last_message_text: Mapped[str] = mapped_column(String(300), default="")
    last_message_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id])
    artisan: Mapped["User"] = relationship(foreign_keys=[artisan_id])
    product: Mapped[Optional["Product"]] = relationship(foreign_keys=[product_id])
    order: Mapped[Optional["Order"]] = relationship(foreign_keys=[order_id])
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.id.asc()"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(foreign_keys=[sender_id])


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(40))  # message | order | dispute | listing | review | tier
    title: Mapped[str] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(Text)
    link: Mapped[str] = mapped_column(String(200), default="")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="notifications")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"), unique=True, index=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    artisan_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer)  # 1 to 5
    title: Mapped[str] = mapped_column(String(120))
    comment: Mapped[str] = mapped_column(Text)
    # published | hidden_by_admin | flagged
    status: Mapped[str] = mapped_column(String(20), default="published", index=True)
    moderation_note: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    product: Mapped["Product"] = relationship(back_populates="reviews")
    order: Mapped["Order"] = relationship(foreign_keys=[order_id])
    order_item: Mapped["OrderItem"] = relationship(back_populates="review")
    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id])
    artisan: Mapped["User"] = relationship(foreign_keys=[artisan_id])


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    order_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("order_items.id"), nullable=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    artisan_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reason: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    requested_resolution: Mapped[str] = mapped_column(String(40), default="full_refund")
    requested_amount: Mapped[int] = mapped_column(Integer, default=0)
    # open | artisan_replied | under_review | resolved_refunded | resolved_rejected | closed
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    resolution_decision: Mapped[str] = mapped_column(String(40), default="")
    refunded_amount: Mapped[int] = mapped_column(Integer, default=0)
    refund_reference: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    order: Mapped["Order"] = relationship(back_populates="disputes")
    order_item: Mapped[Optional["OrderItem"]] = relationship(back_populates="disputes")
    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id])
    artisan: Mapped["User"] = relationship(foreign_keys=[artisan_id])
    messages: Mapped[list["DisputeMessage"]] = relationship(
        back_populates="dispute", cascade="all, delete-orphan", order_by="DisputeMessage.id.asc()"
    )
    audits: Mapped[list["DisputeAudit"]] = relationship(
        back_populates="dispute", cascade="all, delete-orphan", order_by="DisputeAudit.id.asc()"
    )


class DisputeMessage(Base):
    __tablename__ = "dispute_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    dispute_id: Mapped[int] = mapped_column(ForeignKey("disputes.id"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    sender_role: Mapped[str] = mapped_column(String(20))  # buyer | artisan | admin
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    dispute: Mapped["Dispute"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(foreign_keys=[sender_id])


class DisputeAudit(Base):
    __tablename__ = "dispute_audits"

    id: Mapped[int] = mapped_column(primary_key=True)
    dispute_id: Mapped[int] = mapped_column(ForeignKey("disputes.id"), index=True)
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor_role: Mapped[str] = mapped_column(String(20))  # buyer | artisan | admin | system
    action: Mapped[str] = mapped_column(String(60))
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    dispute: Mapped["Dispute"] = relationship(back_populates="audits")
    actor: Mapped[Optional["User"]] = relationship(foreign_keys=[actor_id])


class TrustTierAudit(Base):
    __tablename__ = "trust_tier_audits"

    id: Mapped[int] = mapped_column(primary_key=True)
    artisan_profile_id: Mapped[int] = mapped_column(ForeignKey("artisan_profiles.id"), index=True)
    old_tier: Mapped[str] = mapped_column(String(30))
    new_tier: Mapped[str] = mapped_column(String(30))
    change_type: Mapped[str] = mapped_column(String(40))  # automatic_recalculation | admin_override
    reason: Mapped[str] = mapped_column(String(300))
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    artisan_profile: Mapped["ArtisanProfile"] = relationship(back_populates="tier_audits")
    admin: Mapped[Optional["User"]] = relationship(foreign_keys=[admin_id])
