import uuid
from pathlib import Path
from typing import Any

from models import database
from services import ai_service, market_service

INITIAL_STOCK = 20


def publish_product(image_bytes: bytes, filename: str, price_rupees: int) -> dict[str, Any]:
    if not 1 <= price_rupees <= 10_000_000:
        raise ValueError("Price must be between 1 and 10,000,000 rupees")

    # 1. Save uploaded image file to disk
    file_ext = Path(filename).suffix or ".jpg"
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    image_path = ai_service.UPLOAD_DIR / unique_filename

    ai_service.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with open(image_path, "wb") as f:
        f.write(image_bytes)

    relative_image_url = f"/uploads/{unique_filename}"

    # 2. Get AI-generated listing details safely
    ai_details = ai_service.generate_listing_details(image_bytes)

    title = ai_details.get("title", "Handcrafted Artisan Item")
    description = ai_details.get("description", "A beautiful handcrafted product.")
    category = ai_details.get("category", "Handicrafts")  # Required by SQLite schema
    tags = ai_details.get("tags", ["handmade", "artisan"])

    # Format tags as pipe-separated string for SQLite (e.g., "handmade|artisan")
    tags_str = "|".join(tags) if isinstance(tags, list) else str(tags)

    # 3. Construct payload matching database.py schema
    product_data = {
        "id": uuid.uuid4().hex,
        "artisan_id": "artisan-demo",
        "title": title,
        "category": category,           # FIX: Added required category key
        "tags": tags_str,
        "description": description,
        "image_url": relative_image_url,
        "price_paise": price_rupees * 100,
        "stock": INITIAL_STOCK,
    }

    try:
        return database.create_product(product_data)
    except Exception:
        # Clean up image file if database insertion fails
        image_path.unlink(missing_ok=True)
        raise


def get_market_products(buyer_type: str) -> list[dict[str, Any]]:
    return market_service.match_products(database.list_products(), buyer_type)
