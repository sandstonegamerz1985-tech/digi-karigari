"""Semantic Search Provider Interface and Implementations.

Supports natural-language search by use, style, material, occasion, and intent.
Includes a transparent local semantic heuristic provider as fallback when no AI
embedding service is configured, clearly documenting the provider type.
"""
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ArtisanProfile, Product, User
from ..serializers import serialize_product
from ..config import settings


# Concept dictionaries for semantic mapping
OCCASIONS_MAP = {
    "diwali": ["diya", "pooja", "brass", "festive", "lamp", "thali", "decor", "gift"],
    "pooja": ["diya", "brass", "thali", "bell", "incense", "sacred", "metalcraft", "temple"],
    "wedding": ["saree", "dupatta", "jewellery", "silk", "chikankari", "bangle", "gift", "thali"],
    "festive": ["diya", "brass", "painting", "runner", "decor", "madhubani", "bangle"],
    "gift": ["painting", "planter", "tray", "coaster", "box", "wallet", "earrings", "scarf", "jewellery"],
    "dining": ["tray", "coaster", "mug", "cup", "bowl", "runner", "table", "jug", "surahi", "tea set"],
    "summer": ["cotton", "scarf", "stole", "dupatta", "breathable", "lightweight", "chikankari"],
    "winter": ["silk", "shawl", "wood", "warm", "brass"],
    "living room": ["painting", "planter", "wall art", "cushion cover", "table runner", "tray", "elephant"],
    "kitchen": ["jug", "surahi", "cup", "mug", "bowl", "plate", "tray", "pottery"],
    "office": ["card holder", "passport cover", "bookmark", "tray", "organizer", "leather"],
}

MATERIALS_MAP = {
    "clay": ["terracotta", "pottery", "ceramic", "earthen", "surahi"],
    "terracotta": ["clay", "pottery", "planter", "surahi", "diya"],
    "ceramic": ["pottery", "glazed", "blue pottery", "mug", "cup", "planter"],
    "cotton": ["textile", "handloom", "dupatta", "scarf", "stole", "cushion", "runner", "chikankari"],
    "silk": ["textile", "saree", "dupatta", "stole"],
    "brass": ["metalcraft", "metal", "diya", "thali", "bell", "bowl", "bangle", "hammered"],
    "wood": ["woodwork", "sheesham", "teak", "carved", "tray", "coaster", "box", "elephant"],
    "sheesham": ["wood", "woodwork", "carved", "serving tray", "box", "coaster"],
    "leather": ["accessories", "wallet", "card holder", "passport", "bookmark"],
    "cane": ["bamboo", "basket", "woven", "tray"],
    "bamboo": ["cane", "basket", "woven", "mat", "tray"],
    "glass": ["beads", "jewellery", "earrings", "necklace"],
}

STYLES_MAP = {
    "madhubani": ["painting", "mithila", "folk", "handmade paper", "fish", "peacock", "tree of life"],
    "chikankari": ["embroidery", "lucknow", "cotton", "dupatta", "runner", "stole"],
    "blue pottery": ["jaipur", "pottery", "ceramic", "floral", "planter", "cup"],
    "block print": ["woodblock", "cotton", "scarf", "stole", "cushion cover"],
    "folk": ["madhubani", "traditional", "heritage", "rustic"],
    "minimalist": ["clean", "simple", "modern", "natural finish", "smooth"],
    "traditional": ["heritage", "artisan", "handcrafted", "authentic"],
}


class BaseSearchProvider(ABC):
    @abstractmethod
    def search(
        self,
        db: Session,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        location: Optional[str] = None,
        material: Optional[str] = None,
        in_stock_only: bool = False,
        trust_tier: Optional[str] = None,
        sort: str = "relevance",
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Executes search and returns structured results with provider details."""
        pass


class LocalHeuristicSearchProvider(BaseSearchProvider):
    """Local conceptual search fallback.

    Uses natural-language concept extraction (materials, occasions, uses, styles)
    and multi-field scoring. Transparently declares itself as non-AI fallback.
    """

    def _extract_intent(self, text: str) -> Dict[str, List[str]]:
        t = text.lower()
        matched_occasions = [occ for occ, terms in OCCASIONS_MAP.items() if occ in t or any(x in t for x in terms[:2])]
        matched_materials = [mat for mat, terms in MATERIALS_MAP.items() if mat in t or any(x in t for x in terms[:2])]
        matched_styles = [sty for sty, terms in STYLES_MAP.items() if sty in t or any(x in t for x in terms[:2])]

        return {
            "occasions": matched_occasions,
            "materials": matched_materials,
            "styles": matched_styles,
        }

    def search(
        self,
        db: Session,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        location: Optional[str] = None,
        material: Optional[str] = None,
        in_stock_only: bool = False,
        trust_tier: Optional[str] = None,
        sort: str = "relevance",
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        q = (query or "").strip().lower()
        intent = self._extract_intent(q) if q else {"occasions": [], "materials": [], "styles": []}

        # Build base query for approved products from approved artisans
        stmt = (
            select(Product)
            .join(ArtisanProfile, ArtisanProfile.user_id == Product.artisan_id)
            .join(User, User.id == Product.artisan_id)
            .where(ArtisanProfile.status == "approved", Product.status == "approved")
        )

        if category:
            stmt = stmt.where(Product.category == category)
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        if in_stock_only:
            stmt = stmt.where(Product.stock > 0)
        if location:
            loc_term = f"%{location.strip()}%"
            stmt = stmt.where(ArtisanProfile.city.ilike(loc_term) | ArtisanProfile.state.ilike(loc_term))
        if trust_tier:
            stmt = stmt.where(ArtisanProfile.trust_tier == trust_tier)

        products = db.scalars(stmt).all()

        tokens = [tok for tok in re.split(r"\W+", q) if len(tok) >= 2] if q else []

        scored_items = []
        for p in products:
            score = 0.0
            match_reasons = []

            artisan_profile = p.artisan.artisan_profile if p.artisan else None
            p_text = f"{p.title} {p.description} {p.category} {p.materials} {p.tags}".lower()
            artisan_text = f"{artisan_profile.craft if artisan_profile else ''} {artisan_profile.city if artisan_profile else ''}".lower()

            if material and material.lower() in p_text:
                score += 25.0
                match_reasons.append(f"Material match: {material.title()}")

            if not q:
                # No query string, score based on recency or rating
                score = 1.0
            else:
                # 1. Exact phrase match in title
                if q in p.title.lower():
                    score += 50.0
                    match_reasons.append("Exact title match")

                # 2. Token overlap in title and description
                for token in tokens:
                    if token in p.title.lower():
                        score += 15.0
                    elif token in p_text:
                        score += 6.0
                    if token in artisan_text:
                        score += 4.0

                # 3. Semantic Occasion matching
                for occ in intent["occasions"]:
                    occ_terms = OCCASIONS_MAP.get(occ, [])
                    if any(ot in p_text for ot in [occ] + occ_terms):
                        score += 12.0
                        match_reasons.append(f"Suited for {occ.title()}")

                # 4. Semantic Material matching
                for mat in intent["materials"]:
                    mat_terms = MATERIALS_MAP.get(mat, [])
                    if any(mt in p_text for mt in [mat] + mat_terms):
                        score += 14.0
                        match_reasons.append(f"Handcrafted {mat.title()}")

                # 5. Semantic Style matching
                for sty in intent["styles"]:
                    sty_terms = STYLES_MAP.get(sty, [])
                    if any(st in p_text for st in [sty] + sty_terms):
                        score += 16.0
                        match_reasons.append(f"{sty.title()} craft tradition")

                # Trust Tier slight boost (only if query matched)
                if score > 0 and artisan_profile:
                    tier_weights = {
                        "master_artisan": 4.0,
                        "trusted_artisan": 2.5,
                        "verified_maker": 1.0,
                        "new_artisan": 0.0,
                    }
                    score += tier_weights.get(artisan_profile.trust_tier, 0.0)

            if not q or score > 0:
                serialized = serialize_product(p)
                serialized["relevance_score"] = round(score, 1)
                serialized["semantic_highlights"] = match_reasons[:3]
                scored_items.append((score, serialized))

        # Sort results
        if sort == "relevance" and q:
            scored_items.sort(key=lambda x: x[0], reverse=True)
        elif sort == "price_asc":
            scored_items.sort(key=lambda x: x[1]["price"])
        elif sort == "price_desc":
            scored_items.sort(key=lambda x: x[1]["price"], reverse=True)
        elif sort == "newest":
            scored_items.sort(key=lambda x: x[1]["id"], reverse=True)
        else:
            scored_items.sort(key=lambda x: x[0], reverse=True)

        total_count = len(scored_items)
        paginated_items = [item[1] for item in scored_items[offset : offset + limit]]

        suggested_searches = [
            "Handmade brass diya for pooja",
            "Lightweight chikankari cotton dupatta",
            "Hand-painted blue pottery planter for balcony",
            "Madhubani folk wall painting for living room",
            "Hand-carved sheesham wood tray for dining",
            "Artisan leather card holder gift",
            "Bamboo storage basket for home",
        ]

        return {
            "query": query,
            "provider": "local_semantic_heuristic",
            "is_ai_powered": False,
            "provider_note": "Local conceptual matching using semantic rules, material/style graphs, and occasion mapping. Live embedding/vector AI search service is not configured.",
            "detected_intent": intent,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "items": paginated_items,
            "suggested_searches": suggested_searches,
            "available_filters": {
                "categories": [
                    "Pottery", "Textiles", "Jewellery", "Woodwork", "Paintings",
                    "Metalcraft", "Leather", "Bamboo & Cane", "Home Decor",
                ],
                "materials": ["Terracotta", "Cotton", "Brass", "Sheesham Wood", "Leather", "Bamboo", "Glass Beads"],
                "trust_tiers": [
                    {"key": "master_artisan", "label": "Master Artisan"},
                    {"key": "trusted_artisan", "label": "Trusted Artisan"},
                    {"key": "verified_maker", "label": "Verified Maker"},
                ],
            },
        }


def get_search_provider() -> BaseSearchProvider:
    # If a live AI vector / embedding search is configured in the future, return that provider.
    # Currently defaults cleanly to LocalHeuristicSearchProvider with full transparency.
    return LocalHeuristicSearchProvider()
