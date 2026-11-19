"""Similar-Product Recommendation Provider Interface and Implementations.

Calculates related items based on category, craft materials, artisanal style,
tags, and buyer context with clear explanations ("Similar material", "Same craft category").
Provides a transparent non-AI content-based fallback when AI services are not configured.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ArtisanProfile, Order, OrderItem, Product, User
from ..serializers import serialize_product


class BaseRecommendationProvider(ABC):
    @abstractmethod
    def get_similar(
        self,
        db: Session,
        product_id: int,
        limit: int = 4,
        viewer: Optional[User] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_for_you(
        self,
        db: Session,
        buyer: User,
        limit: int = 6,
    ) -> Dict[str, Any]:
        pass


class ContentBasedRecommendationProvider(BaseRecommendationProvider):
    """Non-AI multi-attribute similarity engine with explainable recommendation reasons."""

    def get_similar(
        self,
        db: Session,
        product_id: int,
        limit: int = 4,
        viewer: Optional[User] = None,
    ) -> Dict[str, Any]:
        target = db.get(Product, product_id)
        if not target:
            return {"items": [], "provider": "content_based_local", "is_ai": False}

        # Candidate pool: approved products from approved artisans, excluding current product
        stmt = (
            select(Product)
            .join(ArtisanProfile, ArtisanProfile.user_id == Product.artisan_id)
            .where(
                ArtisanProfile.status == "approved",
                Product.status == "approved",
                Product.id != product_id,
            )
        )
        candidates = db.scalars(stmt).all()

        target_text = f"{target.title} {target.description} {target.materials} {target.tags}".lower()
        target_artisan_craft = (
            target.artisan.artisan_profile.craft.lower()
            if target.artisan and target.artisan.artisan_profile
            else ""
        )

        scored = []
        for cand in candidates:
            score = 0
            reason = "Recommended for you"
            cand_text = f"{cand.title} {cand.description} {cand.materials} {cand.tags}".lower()
            cand_craft = (
                cand.artisan.artisan_profile.craft.lower()
                if cand.artisan and cand.artisan.artisan_profile
                else ""
            )

            # Check for same craft category
            if cand.category == target.category:
                score += 30
                reason = f"Same craft category ({target.category})"

            # Check for shared artisan
            if cand.artisan_id == target.artisan_id:
                score += 25
                reason = f"Also handcrafted by {cand.artisan.name}"

            # Check for matching craft tradition
            if target_artisan_craft and target_artisan_craft in cand_craft:
                score += 20
                reason = f"Shared craft tradition: {target.artisan.artisan_profile.craft}"

            # Check for material keywords overlap
            shared_materials = []
            for mat in ["terracotta", "clay", "cotton", "silk", "brass", "wood", "sheesham", "leather", "bamboo", "cane", "beads"]:
                if mat in target_text and mat in cand_text:
                    score += 15
                    shared_materials.append(mat.title())
            if shared_materials:
                reason = f"Similar natural material ({', '.join(shared_materials[:2])})"

            # Price proximity (within 35% range)
            if target.price > 0:
                price_ratio = abs(cand.price - target.price) / target.price
                if price_ratio <= 0.35:
                    score += 8

            if score > 0:
                item_data = serialize_product(cand)
                item_data["recommendation_reason"] = reason
                item_data["similarity_score"] = score
                scored.append((score, item_data))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scored[:limit]]

        return {
            "provider": "content_based_local",
            "is_ai": False,
            "provider_note": "Multi-factor craft and material similarity fallback (non-AI).",
            "items": results,
        }

    def get_for_you(
        self,
        db: Session,
        buyer: User,
        limit: int = 6,
    ) -> Dict[str, Any]:
        # Inspect past orders of buyer
        past_items = db.scalars(
            select(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.buyer_id == buyer.id)
        ).all()

        preferred_categories = set()
        preferred_artisans = set()
        for item in past_items:
            if item.product:
                preferred_categories.add(item.product.category)
            preferred_artisans.add(item.artisan_id)

        stmt = (
            select(Product)
            .join(ArtisanProfile, ArtisanProfile.user_id == Product.artisan_id)
            .where(
                ArtisanProfile.status == "approved",
                Product.status == "approved",
            )
        )
        candidates = db.scalars(stmt).all()

        scored = []
        for cand in candidates:
            score = 0
            reason = "Popular in handmade craft"
            if cand.category in preferred_categories:
                score += 25
                reason = f"Based on your interest in {cand.category}"
            if cand.artisan_id in preferred_artisans:
                score += 20
                reason = f"From an artisan you previously bought from ({cand.artisan.name})"

            if cand.stock > 0:
                score += 5

            item_data = serialize_product(cand)
            item_data["recommendation_reason"] = reason
            scored.append((score, item_data))

        scored.sort(key=lambda x: x[0], reverse=True)
        return {
            "provider": "buyer_history_content_local",
            "is_ai": False,
            "provider_note": "Recommendations based on your order history and craft preferences.",
            "items": [item[1] for item in scored[:limit]],
        }


def get_recommendation_provider() -> BaseRecommendationProvider:
    return ContentBasedRecommendationProvider()
