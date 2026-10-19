import json, os, re
from io import BytesIO
from PIL import Image

FALLBACK = {"title":"Handcrafted Indian Craft", "story":"A thoughtfully made craft piece created by an artisan using traditional skills. Each item reflects local knowledge and careful handwork.", "materials":["Materials to be confirmed by artisan"], "category":"Handicrafts", "tags":["handmade", "artisan", "traditional"]}

def extract_craft_details(image_bytes: bytes) -> dict:
    """Use Gemini Vision when configured; fallback is clearly generic, not an asserted material identification."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return dict(FALLBACK)
    try:
        import google.generativeai as genai
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = '''Analyze this Indian craft product photo. Return ONLY valid JSON with exactly these keys: title (3-8 words), story (2-3 sentences, avoid inventing regional origin or claims not visible), materials (array of likely materials, mark uncertain items as "confirm with artisan"), category (short category), tags (array of 3-6 lowercase tags). Do not infer authenticity, artisan identity, or provenance from the image.'''
        response = model.generate_content([prompt, image])
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.text.strip(), flags=re.I)
        data = json.loads(raw)
        return {"title":str(data.get("title") or FALLBACK["title"])[:180], "story":str(data.get("story") or FALLBACK["story"])[:3000], "materials":data.get("materials") if isinstance(data.get("materials"), list) else FALLBACK["materials"], "category":str(data.get("category") or FALLBACK["category"])[:80], "tags":data.get("tags") if isinstance(data.get("tags"), list) else FALLBACK["tags"]}
    except Exception:
        return dict(FALLBACK)
