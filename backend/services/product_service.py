from pathlib import Path
from typing import Any
import uuid

from backend.models import database
from backend.services import ai_service, market_service


INITIAL_STOCK = 20


def publish_product(image_bytes: bytes, filename: str, price_rupees: int) -> dict[str, Any]:
    if not 1 <= price_rupees <= 10_000_000:
        raise ValueError("Price must be between 1 and 10,000,000 rupees")
    metadata = ai_service.process_product_image(image_bytes, filename)
    try:
        return database.create_product(
            {
                "id": uuid.uuid4().hex,
                "artisan_id": "artisan-demo",
                **metadata,
                "tags": "|".join(metadata["tags"]),
                "price_paise": price_rupees * 100,
                "stock": INITIAL_STOCK,
            }
        )
    except Exception:
        (ai_service.UPLOAD_DIR / Path(metadata["image_url"]).name).unlink(missing_ok=True)
        raise


def get_market_products(buyer_type: str) -> list[dict[str, Any]]:
    return market_service.match_products(database.list_products(), buyer_type)