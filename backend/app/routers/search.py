from typing import Literal, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.search_service import get_search_provider

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/semantic")
def semantic_search(
    q: Optional[str] = Query(default=None, max_length=150, description="Natural-language search query"),
    category: Optional[str] = Query(default=None, max_length=50),
    min_price: Optional[int] = Query(default=None, ge=0),
    max_price: Optional[int] = Query(default=None, ge=0),
    location: Optional[str] = Query(default=None, max_length=80),
    material: Optional[str] = Query(default=None, max_length=50),
    in_stock: bool = Query(default=False),
    trust_tier: Optional[str] = Query(default=None),
    sort: Literal["relevance", "newest", "price_asc", "price_desc"] = "relevance",
    limit: int = Query(default=40, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Semantic meaning-based search across artisanal crafts with multi-field filters."""
    provider = get_search_provider()
    return provider.search(
        db=db,
        query=q or "",
        category=category,
        min_price=min_price,
        max_price=max_price,
        location=location,
        material=material,
        in_stock_only=in_stock,
        trust_tier=trust_tier,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get("/suggestions")
def suggested_searches():
    return {
        "suggestions": [
            {"query": "Handmade brass diya for pooja", "category": "Metalcraft", "badge": "Pooja Decor"},
            {"query": "Lightweight chikankari cotton dupatta", "category": "Textiles", "badge": "Handloom"},
            {"query": "Hand-painted blue pottery planter", "category": "Pottery", "badge": "Balcony & Garden"},
            {"query": "Madhubani folk wall painting", "category": "Paintings", "badge": "Mithila Art"},
            {"query": "Hand-carved sheesham wood tray", "category": "Woodwork", "badge": "Dining & Hosting"},
            {"query": "Artisan leather card holder", "category": "Leather", "badge": "Handcrafted Gift"},
            {"query": "Woven cane storage basket", "category": "Bamboo & Cane", "badge": "Natural Home"},
        ]
    }
