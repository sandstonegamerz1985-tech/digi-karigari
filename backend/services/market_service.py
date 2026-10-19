from typing import Any


def match_products(products: list[dict[str, Any]], buyer_type: str) -> list[dict[str, Any]]:
    if buyer_type not in {"retail", "wholesale"}:
        raise ValueError("Buyer type must be retail or wholesale")
    if buyer_type == "wholesale":
        return [product for product in products if product["stock"] >= 5]
    return products


def quote_order(price_paise: int, quantity: int, buyer_type: str) -> dict[str, int]:
    if buyer_type not in {"retail", "wholesale"}:
        raise ValueError("Buyer type must be retail or wholesale")
    if buyer_type == "wholesale" and quantity < 5:
        raise ValueError("Wholesale orders start at 5 pieces")
    unit_price = price_paise * 90 // 100 if buyer_type == "wholesale" else price_paise
    return {"unit_price_paise": unit_price, "total_paise": unit_price * quantity}