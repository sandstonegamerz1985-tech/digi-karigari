import google.generativeai as genai
from PIL import Image
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_listing_details(image_path: str, price: str = "") -> dict:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set!")

    # Open image directly from the file on disk
    img = Image.open(image_path)
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = "Look at this handcrafted product photo. Write a title and a short story/description for it."
    
    response = model.generate_content([prompt, img])
    
    return {
        "title": "Handcrafted Item",
        "description": response.text.strip()
    }
