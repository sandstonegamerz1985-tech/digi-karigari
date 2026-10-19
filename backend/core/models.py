from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Artisan(Base):
    __tablename__ = "artisans"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="Digi Karigari Artisan")
    wallet_address: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(24), nullable=True)
    govt_id_number: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Prefer encrypted storage in production.
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="not_submitted")
    cluster_info: Mapped[str] = mapped_column(String(180), default="Independent artisan")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    products: Mapped[list["Product"]] = relationship(back_populates="artisan")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    artisan_id: Mapped[str] = mapped_column(ForeignKey("artisans.id"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    story: Mapped[str] = mapped_column(Text, default="")
    materials: Mapped[str] = mapped_column(Text, default="[]")
    price: Mapped[int] = mapped_column(Integer)  # whole INR rupees
    stock: Mapped[int] = mapped_column(Integer, default=1)
    category: Mapped[str] = mapped_column(String(80), default="Handicrafts")
    tags: Mapped[str] = mapped_column(Text, default="[]")
    image_url: Mapped[str] = mapped_column(String(500))
    token_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str] = mapped_column(String(120), default="India")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    artisan: Mapped[Artisan] = relationship(back_populates="products")

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    artisan_id: Mapped[str] = mapped_column(ForeignKey("artisans.id"), index=True)
    buyer_address: Mapped[str] = mapped_column(String(180), default="demo-buyer")
    buyer_name: Mapped[str] = mapped_column(String(100), default="Marketplace buyer")
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    escrow_amount: Mapped[int] = mapped_column(Integer, default=0)  # INR rupees, demo state unless chain tx is verified
    status: Mapped[str] = mapped_column(String(32), default="payment_pending")
    payment_method: Mapped[str] = mapped_column(String(32), default="demo")
    courier_name: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tracking_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_tracking_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dispatch_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    product: Mapped["Product"] = relationship()
    artisan: Mapped["Artisan"] = relationship()
