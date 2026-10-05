from typing import Any

from backend.models import database


def calculate_impact() -> dict[str, Any]:
    totals = database.get_impact()
    earnings = totals["earnings_paise"]
    marginalized_earnings = totals["marginalized_earnings_paise"]
    return {
        "artisan_earnings_paise": earnings,
        "orders_count": totals["orders_count"],
        "artisans_reached": totals["artisans_reached"],
        "marginalized_artisans_reached": totals["marginalized_artisans_reached"],
        "marginalized_earnings_share_percent": round(marginalized_earnings * 100 / earnings, 1)
        if earnings
        else 0,
        "currency": "INR",
    }