"""AI Advisory Checks for Product Photos and Category Consistency.

Provides advisory-only feedback on image quality (blur, lighting, dimensions)
and category match.
Strictly advisory:
- Disclaimers that results are suggestions only.
- Never automatically publishes or rejects listings.
- Admin makes the final review decision.
- Separated provider interface with Pillow-based local validation fallback.
"""
import io
import math
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from PIL import Image, ImageFilter, ImageStat

from ..constants import CATEGORIES


CATEGORY_INDICATORS = {
    "Pottery": ["pot", "clay", "terracotta", "ceramic", "vase", "mug", "cup", "jug", "surahi", "planter", "bowl"],
    "Textiles": ["saree", "sari", "fabric", "weave", "woven", "cotton", "silk", "shawl", "scarf", "dupatta", "handloom", "kurta", "embroidery", "chikankari", "runner", "stole", "cushion"],
    "Jewellery": ["necklace", "earring", "earrings", "ring", "bangle", "silver", "beads", "jewellery", "jewelry", "pendant"],
    "Woodwork": ["wood", "wooden", "carved", "carving", "sheesham", "teak", "rosewood", "tray", "coaster", "elephant"],
    "Paintings": ["painting", "madhubani", "warli", "canvas", "pattachitra", "kalamkari", "miniature", "artwork", "wall art"],
    "Metalcraft": ["brass", "copper", "dhokra", "bidri", "metal", "bell", "bronze", "diya", "thali"],
    "Leather": ["leather", "jutti", "mojari", "wallet", "card holder", "passport"],
    "Bamboo & Cane": ["bamboo", "cane", "basket", "jute", "wicker", "table mat"],
    "Home Decor": ["decor", "wall", "diya", "cushion", "runner", "candle", "lamp", "hanging"],
}


class BaseAdvisoryProvider(ABC):
    @abstractmethod
    def run_advisory_check(
        self,
        image_bytes: Optional[bytes],
        selected_category: str,
        title: str,
        description: str,
        artisan_notes: str = "",
    ) -> Dict[str, Any]:
        pass


class LocalAdvisoryProvider(BaseAdvisoryProvider):
    """Local inspection fallback using Pillow image analysis and textual heuristics."""

    def run_advisory_check(
        self,
        image_bytes: Optional[bytes],
        selected_category: str,
        title: str,
        description: str,
        artisan_notes: str = "",
    ) -> Dict[str, Any]:
        checks: List[Dict[str, Any]] = []
        full_text = f"{title} {description} {artisan_notes}".lower()

        # 1. Image Quality Checks
        if image_bytes and len(image_bytes) > 0:
            try:
                img = Image.open(io.BytesIO(image_bytes))
                width, height = img.size

                # Resolution check
                if width < 300 or height < 300:
                    checks.append({
                        "name": "Resolution",
                        "status": "advisory",
                        "severity": "medium",
                        "message": f"Image resolution is low ({width}x{height}px).",
                        "suggestion": "We recommend uploading photos that are at least 600x600px so buyers can zoom in to see artisanal details.",
                    })
                else:
                    checks.append({
                        "name": "Resolution",
                        "status": "pass",
                        "severity": "none",
                        "message": f"Good resolution ({width}x{height}px).",
                        "suggestion": "Resolution is clear for marketplace display.",
                    })

                # Aspect ratio check
                ratio = max(width / max(1, height), height / max(1, width))
                if ratio > 2.5:
                    checks.append({
                        "name": "Aspect Ratio",
                        "status": "advisory",
                        "severity": "low",
                        "message": f"Unusual photo proportions ({width}x{height}).",
                        "suggestion": "Square (1:1) or 4:3 aspect ratios work best on product cards.",
                    })
                else:
                    checks.append({
                        "name": "Aspect Ratio",
                        "status": "pass",
                        "severity": "none",
                        "message": "Balanced aspect ratio.",
                        "suggestion": "Fits well in product displays.",
                    })

                # Lighting / Exposure check
                gray = img.convert("L")
                stat = ImageStat.Stat(gray)
                mean_brightness = stat.mean[0]
                std_dev = stat.stddev[0]

                if mean_brightness < 50:
                    checks.append({
                        "name": "Lighting & Brightness",
                        "status": "advisory",
                        "severity": "high",
                        "message": "Photo appears dark or underexposed.",
                        "suggestion": "Photograph your handmade item near indirect daylight or a well-lit lamp to show natural colors.",
                    })
                elif mean_brightness > 235:
                    checks.append({
                        "name": "Lighting & Brightness",
                        "status": "advisory",
                        "severity": "medium",
                        "message": "Photo appears very bright or overexposed.",
                        "suggestion": "Avoid direct flash reflections which may wash out intricate handcrafted textures.",
                    })
                else:
                    checks.append({
                        "name": "Lighting & Brightness",
                        "status": "pass",
                        "severity": "none",
                        "message": f"Even lighting (brightness score {int(mean_brightness)}/255).",
                        "suggestion": "Craft textures and colors are well exposed.",
                    })

                # Sharpness / Blur estimation
                # Using Laplacian-like edge difference filter
                edges = gray.filter(ImageFilter.FIND_EDGES)
                edge_stat = ImageStat.Stat(edges)
                edge_variance = edge_stat.var[0] if edge_stat.var else 0.0

                if edge_variance < 15.0 and std_dev < 25.0:
                    checks.append({
                        "name": "Clarity & Focus",
                        "status": "advisory",
                        "severity": "medium",
                        "message": "Photo has low edge detail and may be soft or slightly blurry.",
                        "suggestion": "Hold camera steady or rest it on a surface to take a sharp, crisp shot.",
                    })
                else:
                    checks.append({
                        "name": "Clarity & Focus",
                        "status": "pass",
                        "severity": "none",
                        "message": "Good clarity and edge sharpness.",
                        "suggestion": "Product contours are well defined.",
                    })

            except Exception:
                checks.append({
                    "name": "Image Inspection",
                    "status": "advisory",
                    "severity": "low",
                    "message": "Could not inspect image metadata (format not fully decoded).",
                    "suggestion": "Please review the image clarity manually.",
                })
        else:
            checks.append({
                "name": "Photo Upload",
                "status": "advisory",
                "severity": "high",
                "message": "No photo file provided for visual advisory check.",
                "suggestion": "Attach a photo of your handmade product.",
            })

        # 2. Category Match & Consistency Check
        category_scores: Dict[str, int] = {}
        for cat, keywords in CATEGORY_INDICATORS.items():
            count = sum(1 for kw in keywords if kw in full_text)
            if count > 0:
                category_scores[cat] = count

        suggested_category = selected_category
        confidence = "low"
        is_consistent = True
        category_message = f"Selected category '{selected_category}' appears consistent with your listing details."

        if category_scores:
            best_cat = max(category_scores.items(), key=lambda x: x[1])[0]
            if best_cat != selected_category and category_scores[best_cat] >= 2:
                suggested_category = best_cat
                is_consistent = False
                confidence = "medium"
                category_message = (
                    f"Your listing mentions terms related to '{best_cat}'. "
                    f"Consider if '{best_cat}' is a more accurate category than '{selected_category}'."
                )
            elif best_cat == selected_category:
                confidence = "high"
                category_message = f"Listing keywords strongly confirm '{selected_category}' as an appropriate category."

        category_check = {
            "name": "Category Match",
            "status": "pass" if is_consistent else "advisory",
            "severity": "none" if is_consistent else "medium",
            "is_consistent": is_consistent,
            "selected_category": selected_category,
            "suggested_category": suggested_category,
            "confidence": confidence,
            "message": category_message,
            "suggestion": (
                "Accurate categories help buyers discover your work through filters and recommendations."
                if not is_consistent
                else "Matches buyer expectations."
            ),
        }
        checks.append(category_check)

        advisory_count = sum(1 for c in checks if c["status"] == "advisory")

        return {
            "provider": "local_image_advisory_heuristic",
            "is_ai_powered": False,
            "disclaimer": (
                "Advisory suggestion only. This analysis is an automated helper for the artisan. "
                "Listing publication or rejection is NEVER automated and requires explicit human admin review."
            ),
            "overall_status": "advisory_attention" if advisory_count > 1 else "ready_for_review",
            "advisory_count": advisory_count,
            "checks": checks,
            "category_summary": {
                "selected": selected_category,
                "suggested": suggested_category,
                "is_match": is_consistent,
            },
        }


def get_advisory_provider() -> BaseAdvisoryProvider:
    return LocalAdvisoryProvider()
