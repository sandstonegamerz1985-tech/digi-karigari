import io
import json
import logging
from PIL import Image
import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_listing_details(image_input, price: str = "") -> dict:
    fallback = {
        "title": "Handcrafted Clay Terracotta Pot",
        "description": "Exquisite traditional clay pottery crafted by master rural artisans using natural clay and age-old pottery wheels.",
        "category": "Pottery",
        "tags": ["pottery", "terracotta", "handmade", "decor"]
    }

    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY missing. Returning fallback details.")
        return fallback

    try:
        if isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input))
        else:
            img = Image.open(image_input)

        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # PROMPT TO STRICTLY SEPARATE TITLE, DESCRIPTION, CATEGORY AND TAGS
        prompt = (
            "Analyze this product photo of an Indian handcrafted craft item. "
            "Return JSON format with the following keys:\n"
            "- 'title': A specific, attractive title for the product (3 to 6 words). DO NOT use terms like 'shopping', 'image', 'photo', or generic labels.\n"
            "- 'description': An engaging 2-sentence description highlighting its traditional craft techniques.\n"
            "- 'category': One suitable category name (e.g. Pottery, Handlooms, Metalware, Woodcraft).\n"
            "- 'tags': A list of 3-4 relevant lower-case tags.\n"
            "Return valid JSON raw text without markdown blocks."
        )

        response = model.generate_content([prompt, img])
        text_content = response.text.strip().replace("```json", "").replace("```", "")
        parsed = json.loads(text_content)

        return {
            "title": parsed.get("title", fallback["title"]),
            "description": parsed.get("description", fallback["description"]),
            "category": parsed.get("category", fallback["category"]),
            "tags": parsed.get("tags", fallback["tags"])
        }

    except Exception as e:
        logger.error(f"Gemini AI parsing failed: {e}")
        return fallback
