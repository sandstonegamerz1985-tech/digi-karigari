import uuid
from typing import Any

from models import database
from services.market_service import quote_order


def place_order(
    product_id: str,
    quantity: int,
    buyer_name: str,
    buyer_type: str,
) -> dict[str, Any]:
    product = database.get_product(product_id)
    if product is None:
        raise LookupError("Product not found")
    quote = quote_order(product["price_paise"], quantity, buyer_type)

    # This integration is intentionally simulated; it does not move real money.
    payment_reference = f"mock-upi-{uuid.uuid4().hex[:12]}"
    tracking_reference = f"DEMO-{uuid.uuid4().hex[:10].upper()}"
    return database.create_order(
        {
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "quantity": quantity,
            "unit_price_paise": quote["unit_price_paise"],
            "total_paise": quote["total_paise"],
            "buyer_name": buyer_name,
            "buyer_type": buyer_type,
            "payment_reference": payment_reference,
            "tracking_reference": tracking_reference,
            "status": "paid",
        }
    )