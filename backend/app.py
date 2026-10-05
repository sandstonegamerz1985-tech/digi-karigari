from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
import logging

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.models import database
from backend.services import ai_service, impact_service, order_service, product_service


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
        return product_service.publish_product(
            image_bytes,
            image.filename or "handmade-craft",
            price_rupees,
        )
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


@app.get("/api/impact")
def impact():
    return impact_service.calculate_impact()


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/uploads", StaticFiles(directory=ai_service.UPLOAD_DIR, check_dir=False), name="uploads")
app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")