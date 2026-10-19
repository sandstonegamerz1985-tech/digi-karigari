import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import DATABASE_PATH, GEMINI_API_KEY, UPLOAD_FOLDER
from models import database
from services import ai_service, impact_service, order_service, product_service

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_db()
    ai_service.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Karigar Artisan Marketplace",
    version="1.0.0",
    description="A local-first artisan marketplace prototype with demo payments.",
    lifespan=lifespan,
)

# 1. Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust to explicit Vercel domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrderRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=64)
    quantity: int = Field(ge=1, le=1000)
    buyer_name: str = Field(default="Marketplace buyer", min_length=1, max_length=80)
    buyer_type: Literal["retail", "wholesale"] = "retail"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/products")
def products(buyer_type: Literal["retail", "wholesale"] = Query(default="retail")):
    try:
        return product_service.get_market_products(buyer_type)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/products", status_code=201)
async def upload_product(
    request: Request,
    image: UploadFile = File(...),
    price_rupees: int = Query(ge=1, le=10_000_000),
):
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if image.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Choose a JPEG, PNG, or WebP image")

    image_bytes = await image.read(8 * 1024 * 1024 + 1)
    if len(image_bytes) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 8 MB or smaller")

    try:
        # Build base server URL (e.g., https://your-backend.onrender.com)
        base_url = str(request.base_url).rstrip("/")

        result = product_service.publish_product(
            image_bytes,
            image.filename or "handmade-craft",
            price_rupees,
        )

        # Convert relative upload path to full URL for cross-origin frontend access
        if isinstance(result, dict) and "image_url" in result:
            if not result["image_url"].startswith("http"):
                result["image_url"] = f"{base_url}{result['image_url']}"

        return result

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Product upload failed")
        raise HTTPException(status_code=500, detail="Could not save this product") from error
    finally:
        await image.close()


@app.post("/api/orders", status_code=201)
def create_order(request: OrderRequest):
    try:
        return order_service.place_order(
            request.product_id,
            request.quantity,
            request.buyer_name.strip() or "Marketplace buyer",
            request.buyer_type,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/api/orders/track")
def track_order(reference: str = Query(min_length=1, max_length=100)):
    order = database.get_order_by_tracking(reference)
    if order is None:
        raise HTTPException(status_code=404, detail="No order found for that tracking ID")
    # The prototype creates demo references; this is not connected to a courier network.
    order["tracking_note"] = "Demo tracking record. Live courier updates require a courier API integration."
    return order


@app.get("/api/support")
def support():
    return {
        "service": "Digi-Karigari Customer Care",
        "message": "For this prototype, contact details are demo placeholders. Configure a real support number and ticketing service before launch.",
        "channels": [{"name": "Support desk", "status": "demo-only"}],
    }


@app.post("/api/artisan/verify")
def verify_artisan():
    # Identity verification must be reviewed by an authorised operator.
    # This endpoint deliberately does not collect or store government ID documents.
    return {
        "status": "pending_review",
        "badge": None,
        "message": "Verification request noted for demo. No government identity has been verified.",
    }


@app.get("/api/impact")
def impact():
    return impact_service.calculate_impact()


# Mount static uploads
app.mount("/uploads", StaticFiles(directory=ai_service.UPLOAD_DIR, check_dir=False), name="uploads")

# Safely serve frontend assets if available locally
if FRONTEND_DIR.exists():
    @app.get("/")
    def index():
        return FileResponse(FRONTEND_DIR / "index.html")

    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
    app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")
