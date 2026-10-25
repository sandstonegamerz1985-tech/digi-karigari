"""Safe image upload handling.

Safety rules used here:
1. We never trust the file name or the "Content-Type" sent by the browser.
2. We look at the first bytes of the file ("magic bytes") to confirm it is really JPEG/PNG/WEBP.
3. We limit the file size.
4. We save under a random name (uuid), so nobody can overwrite files or use "../" tricks.
"""
import uuid
from pathlib import Path
from typing import Optional, Tuple

from fastapi import HTTPException, UploadFile

from .config import settings


def detect_image_type(data: bytes) -> Optional[Tuple[str, str]]:
    """Returns (file_extension, media_type) or None if it is not an allowed image."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg", "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp", "image/webp"
    return None


def read_validated_image(upload: UploadFile) -> Tuple[bytes, str, str]:
    """Reads an upload fully into memory (max size enforced) and validates it.
    Returns (bytes, extension, media_type)."""
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    data = upload.file.read(max_bytes + 1)
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413, detail=f"Image is too large. Maximum size is {settings.MAX_UPLOAD_MB} MB."
        )
    kind = detect_image_type(data)
    if not kind:
        raise HTTPException(status_code=400, detail="Only JPG, PNG or WEBP images are allowed.")
    return data, kind[0], kind[1]


def save_image(upload: UploadFile, subdir: str = "products") -> str:
    """Validates and stores an image. Returns its path relative to the uploads folder."""
    data, ext, _ = read_validated_image(upload)
    folder = settings.UPLOAD_DIR / subdir
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{ext}"
    (folder / name).write_bytes(data)
    return f"{subdir}/{name}"


def delete_image_file(relative_path: str) -> None:
    """Deletes a user-uploaded file. Only files inside uploads/products can be deleted
    (seed sample images are left alone)."""
    try:
        target = (settings.UPLOAD_DIR / relative_path).resolve()
        allowed = (settings.UPLOAD_DIR / "products").resolve()
        if allowed in target.parents and target.is_file():
            target.unlink()
    except OSError:
        pass  # a missing file should never crash a request
