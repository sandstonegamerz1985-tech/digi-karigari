"""Digi-Karigari FastAPI application. Demo payments and verification are explicitly non-production."""
from __future__ import annotations
import hashlib, os, re, secrets, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import quote

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import inspect, or_, select, text
from sqlalchemy.orm import Session, joinedload

from core.database import Base, engine, get_db
from core.models import Artisan, Product, Order
from core.ai import extract_craft_details

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CORS_ORIGINS = [x.strip().rstrip("/") for x in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if x.strip()]
TRUST_PROXY_HTTPS = os.getenv("TRUST_PROXY_HTTPS", "false").lower() == "true"

app = FastAPI(title="Digi Karigari Marketplace API", version="2.0.0", description="Artisan marketplace APIs; demo payment and identity flows are clearly marked.")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Authorization", "Content-Type"], max_age=600)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'"
    if request.url.scheme == "https" or TRUST_PROXY_HTTPS:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.on_event("startup")
def startup():
    # Preserve the user's original prototype DB while allowing the expanded SQLAlchemy schema.
    # Older versions used price_paise/description and a smaller artisans table.
    if engine.url.get_backend_name() == "sqlite":
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        if "artisans" in tables and "wallet_address" not in {c["name"] for c in inspector.get_columns("artisans")}:
            with engine.begin() as conn:
                for table in ("orders", "products", "artisans"):
                    if table in tables and f"legacy_{table}" not in tables:
                        conn.execute(text(f"ALTER TABLE {table} RENAME TO legacy_{table}"))
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        if not db.get(Artisan, "artisan-demo"):
            db.add(Artisan(id="artisan-demo", name="Meera Devi", wallet_address=None, cluster_info="Rural artisan collective"))
            db.commit()
        # Import products from the original SQLite prototype without claiming old demo payments were real.
        if engine.url.get_backend_name() == "sqlite":
            tables = set(inspect(engine).get_table_names())
            if "legacy_artisans" in tables:
                for row in db.connection().execute(text("SELECT * FROM legacy_artisans")).mappings():
                    if not db.get(Artisan, row["id"]):
                        db.add(Artisan(id=row["id"], name=row.get("name") or "Digi Karigari Artisan", cluster_info=row.get("community") or "Independent artisan", is_verified=False, verification_status="not_submitted"))
                db.commit()
            if "legacy_products" in tables and db.scalar(select(Product.id).limit(1)) is None:
                import json
                for row in db.connection().execute(text("SELECT * FROM legacy_products")).mappings():
                    if not db.get(Product, row["id"]):
                        old_tags = row.get("tags") or "handmade|artisan"
                        tag_list = old_tags.split("|") if isinstance(old_tags, str) else ["handmade", "artisan"]
                        artisan = db.get(Artisan, row["artisan_id"]) or db.get(Artisan, "artisan-demo")
                        db.add(Product(id=row["id"], artisan_id=artisan.id, title=row["title"], story=row.get("description") or "Handcrafted by an artisan.", materials=json.dumps(["Please confirm materials with the artisan"]), price=max(1, round(int(row.get("price_paise") or 100) / 100)), stock=max(0, int(row.get("stock") or 0)), category=row.get("category") or "Handicrafts", tags=json.dumps(tag_list), image_url=row.get("image_url") or "", location=artisan.cluster_info))
                db.commit()
            if "legacy_orders" in tables and db.scalar(select(Order.id).limit(1)) is None:
                for row in db.connection().execute(text("SELECT * FROM legacy_orders")).mappings():
                    if not db.get(Order, row["id"]) and db.get(Product, row["product_id"]):
                        product = db.get(Product, row["product_id"])
                        db.add(Order(id=row["id"], product_id=row["product_id"], artisan_id=product.artisan_id, buyer_address="legacy-demo", buyer_name=row.get("buyer_name") or "Marketplace buyer", quantity=int(row.get("quantity") or 1), escrow_amount=max(0, round(int(row.get("total_paise") or 0) / 100)), status="demo_payment", payment_method="demo_upi", courier_name=None, tracking_id=row.get("tracking_reference")))
                db.commit()

@app.get("/api/health")
def health():
    return {"status":"ok", "service":"digi-karigari", "mode":"demo-ready"}

def product_payload(p: Product) -> dict:
    artisan = p.artisan
    return {"id":p.id, "artisan_id":p.artisan_id, "title":p.title, "story":p.story, "description":p.story, "materials":_json_list(p.materials), "price":p.price, "price_rupees":p.price, "stock":p.stock, "category":p.category, "tags":_json_list(p.tags), "image_url":p.image_url, "token_id":p.token_id, "location":p.location, "artisan_name":artisan.name if artisan else "Digi Karigari artisan", "cluster_info":artisan.cluster_info if artisan else p.location, "is_verified":bool(artisan and artisan.is_verified), "artisan_wallet_address":artisan.wallet_address if artisan else None, "verification_status":artisan.verification_status if artisan else "unknown", "created_at":p.created_at.isoformat() if p.created_at else None}

def _json_list(value: str):
    import json
    try:
        out = json.loads(value or "[]")
        return out if isinstance(out, list) else []
    except Exception:
        return []

@app.get("/api/products")
def list_products(search: str = Query(default="", max_length=100), category: str = Query(default="", max_length=80), location: str = Query(default="", max_length=120), buyer_type: Literal["retail", "wholesale"] = "retail", db: Session = Depends(get_db)):
    stmt = select(Product).options(joinedload(Product.artisan)).where(Product.stock > 0)
    if search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(or_(Product.title.ilike(term), Product.story.ilike(term), Product.category.ilike(term), Product.tags.ilike(term)))
    if category.strip(): stmt = stmt.where(Product.category.ilike(f"%{category.strip()}%"))
    if location.strip(): stmt = stmt.where(Product.location.ilike(f"%{location.strip()}%"))
    items = db.scalars(stmt.order_by(Product.created_at.desc())).unique().all()
    result = [product_payload(p) for p in items]
    if buyer_type == "wholesale":
        for item in result: item["display_price"] = round(item["price"] * 0.9, 2) if item["price"] >= 1000 else item["price"]
    else:
        for item in result: item["display_price"] = item["price"]
    return result

@app.get("/api/products/{product_id}")
def product_detail(product_id: str, db: Session = Depends(get_db)):
    p = db.scalar(select(Product).options(joinedload(Product.artisan)).where(Product.id == product_id))
    if not p: raise HTTPException(404, "Product not found")
    result = product_payload(p)
    result["delivery_estimate"] = "Typically 4–8 business days; confirm serviceability with the courier."
    result["certificate"] = {"token_id":p.token_id, "status":"not_minted" if not p.token_id else "token_reference_recorded", "note":"On-chain status must be independently verified on the selected network."}
    return result

@app.post("/api/products", status_code=201)
async def publish_product(request: Request, image: UploadFile = File(...), price_rupees: int = Form(..., ge=1, le=10000000), stock: int = Form(default=1, ge=0, le=100000), artisan_id: str = Form(default="artisan-demo"), location: str = Form(default="India", max_length=120), title_override: str = Form(default="", max_length=180), db: Session = Depends(get_db)):
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(415, "Upload a JPEG, PNG, or WebP image")
    content = await image.read(8 * 1024 * 1024 + 1)
    if len(content) > 8 * 1024 * 1024: raise HTTPException(413, "Image must be 8 MB or smaller")
    if not content: raise HTTPException(400, "Uploaded image is empty")
    try:
        from PIL import Image
        from io import BytesIO
        Image.open(BytesIO(content)).verify()
    except Exception as exc:
        raise HTTPException(415, "The uploaded file is not a valid image") from exc
    artisan = db.get(Artisan, artisan_id)
    if not artisan: raise HTTPException(404, "Artisan profile not found")
    ai = extract_craft_details(content)
    suffix = {"image/jpeg":".jpg", "image/png":".png", "image/webp":".webp"}[image.content_type]
    filename = f"{uuid.uuid4().hex}{suffix}"
    (UPLOAD_DIR / filename).write_bytes(content)
    import json
    p = Product(id=uuid.uuid4().hex, artisan_id=artisan_id, title=title_override.strip() or ai["title"], story=ai["story"], materials=json.dumps(ai["materials"]), price=price_rupees, stock=stock, category=ai["category"], tags=json.dumps(ai["tags"]), image_url=f"{str(request.base_url).rstrip('/')}/uploads/{filename}", location=location.strip() or "India")
    try:
        db.add(p); db.commit(); db.refresh(p)
        p.artisan = artisan
        payload = product_payload(p); payload["ai_preview"] = ai; payload["ai_provider"] = "Gemini 1.5 Flash" if os.getenv("GEMINI_API_KEY") else "fallback (configure GEMINI_API_KEY)"
        return payload
    except Exception:
        db.rollback(); (UPLOAD_DIR / filename).unlink(missing_ok=True); raise

class VerifyRequest(BaseModel):
    artisan_id: str = "artisan-demo"
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=24)
    govt_id_number: str = Field(min_length=4, max_length=80)
    wallet_address: str | None = Field(default=None, max_length=100)
    cluster_info: str = Field(default="Independent artisan", max_length=180)
    @field_validator("wallet_address")
    @classmethod
    def valid_wallet(cls, value):
        if value and not re.fullmatch(r"0x[a-fA-F0-9]{40}", value): raise ValueError("Wallet must be a valid EVM address")
        return value

@app.post("/api/artisan/verify", status_code=202)
def request_verification(body: VerifyRequest, db: Session = Depends(get_db)):
    artisan = db.get(Artisan, body.artisan_id)
    if not artisan: artisan = Artisan(id=body.artisan_id)
    artisan.name = body.name.strip(); artisan.phone = body.phone.strip(); artisan.govt_id_number = body.govt_id_number.strip(); artisan.wallet_address = body.wallet_address; artisan.cluster_info = body.cluster_info.strip(); artisan.verification_status = "pending_review"; artisan.is_verified = False
    db.add(artisan); db.commit()
    return {"artisan_id":artisan.id, "status":"pending_review", "badge":None, "message":"Request submitted for authorised human review. This demo does not verify government ID or mint a blockchain credential."}

class OrderRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=64)
    quantity: int = Field(ge=1, le=1000)
    buyer_name: str = Field(default="Marketplace buyer", min_length=1, max_length=100)
    buyer_address: str = Field(default="demo-buyer", min_length=1, max_length=180)
    payment_method: Literal["demo_upi", "demo_card", "wallet"] = "demo_upi"
    payment_tx_hash: str | None = Field(default=None, max_length=100)

@app.post("/api/orders", status_code=201)
def create_order(body: OrderRequest, db: Session = Depends(get_db)):
    p = db.scalar(select(Product).options(joinedload(Product.artisan)).where(Product.id == body.product_id))
    if not p: raise HTTPException(404, "Product not found")
    if p.stock < body.quantity: raise HTTPException(409, "Not enough stock available")
    # This prototype never treats a client-provided transaction hash as proof of payment.
    order = Order(id=uuid.uuid4().hex, product_id=p.id, artisan_id=p.artisan_id, buyer_address=body.buyer_address.strip(), buyer_name=body.buyer_name.strip(), quantity=body.quantity, escrow_amount=p.price * body.quantity, status="payment_pending" if body.payment_method == "wallet" else "demo_payment", payment_method=body.payment_method)
    p.stock -= body.quantity
    db.add(order); db.commit(); db.refresh(order)
    return {"id":order.id, "product_id":p.id, "product_title":p.title, "quantity":order.quantity, "escrow_amount":order.escrow_amount, "currency":"INR", "status":order.status, "payment_method":order.payment_method, "tracking_id":None, "message":"Demo order created. No real payment was collected or escrow locked."}

COURIER_URLS = {"India Post":"https://www.indiapost.gov.in/", "Delhivery":"https://www.delhivery.com/", "Porter":"https://porter.in/"}
class ShipRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=64)
    courier_name: Literal["India Post", "Delhivery", "Porter"]
    tracking_id: str = Field(min_length=3, max_length=100)

@app.patch("/api/orders/ship")
def dispatch_order(body: ShipRequest, db: Session = Depends(get_db)):
    order = db.get(Order, body.order_id)
    if not order: raise HTTPException(404, "Order not found")
    if order.status == "cancelled": raise HTTPException(409, "Cancelled order cannot be dispatched")
    order.courier_name = body.courier_name; order.tracking_id = body.tracking_id.strip(); order.external_tracking_url = COURIER_URLS[body.courier_name]; order.dispatch_at = datetime.now(timezone.utc); order.status = "dispatched"
    db.commit(); db.refresh(order)
    return {"order_id":order.id, "status":order.status, "courier_name":order.courier_name, "tracking_id":order.tracking_id, "external_tracking_url":order.external_tracking_url, "dispatch_at":order.dispatch_at.isoformat(), "note":"Dispatch is recorded in this marketplace. Courier status is not live unless a courier API is integrated."}

@app.get("/api/orders/track")
def track_order(reference: str = Query(min_length=1, max_length=100), db: Session = Depends(get_db)):
    order = db.scalar(select(Order).options(joinedload(Order.product)).where(or_(Order.id == reference, Order.tracking_id == reference)))
    if not order: raise HTTPException(404, "No order found for that order ID or tracking ID")
    return {"order_id":order.id, "product_title":order.product.title if order.product else "Marketplace item", "status":order.status, "courier_name":order.courier_name, "tracking_id":order.tracking_id, "external_tracking_url":order.external_tracking_url, "dispatch_at":order.dispatch_at.isoformat() if order.dispatch_at else None, "timeline":[{"label":"Order created", "complete":True, "at":order.created_at.isoformat() if order.created_at else None}, {"label":"Dispatch confirmed", "complete":order.dispatch_at is not None, "at":order.dispatch_at.isoformat() if order.dispatch_at else None}, {"label":"Delivered", "complete":order.status == "delivered", "at":None}], "tracking_note":"Courier updates are not live in this demo; use the courier link for external tracking."}

@app.get("/api/artisan/orders")
def artisan_orders(artisan_id: str = Query(default="artisan-demo"), db: Session = Depends(get_db)):
    orders = db.scalars(select(Order).options(joinedload(Order.product)).where(Order.artisan_id == artisan_id).order_by(Order.created_at.desc())).unique().all()
    return [{"id":o.id, "product_id":o.product_id, "product_title":o.product.title if o.product else "Item", "quantity":o.quantity, "buyer_name":o.buyer_name, "buyer_address":o.buyer_address, "escrow_amount":o.escrow_amount, "status":o.status, "courier_name":o.courier_name, "tracking_id":o.tracking_id} for o in orders]

@app.post("/api/auth/mobile-otp")
def mobile_otp(phone: str = Form(...)):
    cleaned = re.sub(r"\D", "", phone)
    if len(cleaned) not in range(10, 14): raise HTTPException(422, "Enter a valid mobile number")
    return {"status":"stub", "message":"OTP delivery is not configured. No OTP was sent.", "phone_masked":"*" * max(0, len(cleaned)-4) + cleaned[-4:]}

class GoogleTokenRequest(BaseModel):
    id_token: str = Field(min_length=20, max_length=5000)

@app.post("/api/auth/google")
async def google_auth(body: GoogleTokenRequest):
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not client_id: raise HTTPException(503, "Google OAuth is not configured")
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get("https://oauth2.googleapis.com/tokeninfo", params={"id_token":body.id_token})
        if response.status_code != 200: raise ValueError("Token rejected")
        claims = response.json()
        if claims.get("aud") != client_id or claims.get("email_verified") not in (True, "true"): raise ValueError("Token audience or email verification invalid")
        return {"status":"verified", "subject":claims.get("sub"), "email":claims.get("email"), "name":claims.get("name")}
    except Exception as exc:
        raise HTTPException(401, "Google ID token could not be verified") from exc

@app.get("/api/support")
def support():
    return {"service":"Digi-Karigari Customer Care", "phone":os.getenv("SUPPORT_PHONE", "Configure a real support number"), "channels":[{"name":"Support desk", "status":"configuration_required"}], "ticketing":"A ticketing provider is not configured; do not treat this as a live helpdesk."}

@app.get("/api/artisan/{artisan_id}")
def artisan_profile(artisan_id: str, db: Session = Depends(get_db)):
    artisan = db.get(Artisan, artisan_id)
    if not artisan: raise HTTPException(404, "Artisan not found")
    return {"id":artisan.id, "name":artisan.name, "wallet_address":artisan.wallet_address, "is_verified":artisan.is_verified, "verification_status":artisan.verification_status, "cluster_info":artisan.cluster_info, "created_at":artisan.created_at.isoformat() if artisan.created_at else None}

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
