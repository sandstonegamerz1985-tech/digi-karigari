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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="artisan_profile")


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    artisan: Mapped["User"] = relationship(back_populates="products")
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.position"
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
