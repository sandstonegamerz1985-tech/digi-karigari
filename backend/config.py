import os
from pathlib import Path

# Base directory path
BASE_DIR = Path(__file__).resolve().parent

# Upload directory and database paths
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATABASE_PATH = os.path.join(BASE_DIR, "marketplace.db")

# Load Google Gemini API Key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Ensure the uploads directory exists on server start
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
