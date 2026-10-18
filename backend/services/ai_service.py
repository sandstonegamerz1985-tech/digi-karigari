import io
import logging
from pathlib import Path
from PIL import Image
import google.generativeai as genai
from config import GEMINI_API_KEY, UPLOAD_FOLDER

logger = logging.getLogger(__name__)

# Define UPLOAD_DIR for app.py to reference
UPLOAD_DIR = Path(UPLOAD_FOLDER)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_listing_details(image_input, price: str = "") -> dict:
    fallback = {
        "title": "Handcrafted Artisan Item",
        "description": "A beautiful handcrafted piece made with care and traditional skill."
    }

    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is missing. Returning fallback details.")
        return fallback

    try:
        # Handle input whether it is raw bytes or a file path string
        if isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input))
        else:
            img = Image.open(image_input)

        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "Look at this handcrafted product photo. "
            "Write an engaging product title and a short story/description for an artisan marketplace."
        )

        response = model.generate_content([prompt, img])

        return {
            "title": "Handcrafted Artisan Item",
            "description": response.text.strip() if response.text else fallback["description"]
        }
    except Exception as e:
        logger.error(f"Gemini AI generation failed: {e}")
        return fallback
