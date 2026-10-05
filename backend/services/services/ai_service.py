import io
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, UnidentifiedImageError


BACKEND_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BACKEND_DIR / "uploads"
MAX_IMAGE_PIXELS = 25_000_000


def process_product_image(image_bytes: bytes, original_name: str) -> dict[str, Any]:
    if not image_bytes:
        raise ValueError("The uploaded image is empty")

    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise ValueError("The image dimensions are too large")
            source.verify()
        with Image.open(io.BytesIO(image_bytes)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError("The image dimensions are too large")
            cropped = ImageOps.fit(image, (1024, 1024), method=Image.Resampling.LANCZOS)
    except (UnidentifiedImageError, OSError) as error:
        raise ValueError("Please upload a valid JPEG, PNG, or WebP image") from error

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.webp"
    destination = UPLOAD_DIR / filename
    cropped.save(destination, format="WEBP", quality=86, method=6)

    metadata = _generate_metadata(cropped, original_name)
    return {**metadata, "image_url": f"/uploads/{filename}"}


def _generate_metadata(image: Image.Image, original_name: str) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
                contents=[
                    "Describe this handmade product for a small artisan marketplace. "
                    "Return only JSON with title (max 70 characters), category (max 40), "
                    "tags (array of 3-6 short strings), and description (max 240 characters). "
                    "Do not guess materials or origin unless visible.",
                    image,
                ],
            )
            parsed = json.loads(_strip_json_fence(response.text or ""))
            return _validate_metadata(parsed)
        except Exception:
            # Keep the upload usable if the optional model is unavailable or returns invalid data.
            pass

    stem = Path(original_name or "handmade craft").stem
    title = re.sub(r"[_-]+", " ", stem).strip()
    title = re.sub(r"\s+", " ", title)[:70].title() or "Handmade Craft"
    return {
        "title": title,
        "category": "Handmade craft",
        "tags": ["handmade", "artisan made", "unique"],
        "description": "A handmade piece, crafted with care. Add details about its materials and story before publishing.",
    }


def _strip_json_fence(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def _validate_metadata(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("AI response must be a JSON object")
    title = str(value.get("title", "Handmade Craft")).strip()[:70] or "Handmade Craft"
    category = str(value.get("category", "Handmade craft")).strip()[:40] or "Handmade craft"
    description = str(value.get("description", "Handmade with care.")).strip()[:240]
    raw_tags = value.get("tags", [])
    if isinstance(raw_tags, str):
        raw_tags = raw_tags.split(",")
    tags = list(dict.fromkeys(str(tag).strip()[:30] for tag in raw_tags if str(tag).strip()))
    return {"title": title, "category": category, "tags": tags[:6], "description": description}