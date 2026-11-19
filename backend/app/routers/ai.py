from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile

from .. import ai_service
from ..deps import require_approved_artisan
from ..models import User
from ..services.advisory_service import get_advisory_provider
from ..uploads import read_validated_image

router = APIRouter(prefix="/ai", tags=["ai-listing-assistant"])


@router.get("/status")
def status():
    """Tells the frontend whether AI is in DEMO or LIVE mode (no secrets are included)."""
    return ai_service.ai_status()


@router.post("/listing-assist")
def listing_assist(
    image: UploadFile = File(...),
    notes: str = Form("", max_length=1000),
    user: User = Depends(require_approved_artisan),
):
    """Analyses ONE photo + notes and returns SUGGESTIONS only.
    Nothing is saved or published here; the artisan reviews and submits the listing form themselves.
    The photo is analysed in memory and not stored by this endpoint."""
    data, _ext, media_type = read_validated_image(image)
    return ai_service.analyze_listing(data, media_type, notes, filename=image.filename or "")


@router.post("/advisory-check")
def advisory_check(
    category: str = Form(..., min_length=2, max_length=50),
    title: str = Form(..., min_length=2, max_length=150),
    description: str = Form("", max_length=3000),
    notes: str = Form("", max_length=1000),
    image: Optional[UploadFile] = File(default=None),
    user: User = Depends(require_approved_artisan),
):
    """Advisory checks for product photo quality and category consistency.

    Returns suggestions for blur, lighting, resolution, and category match.
    Strictly advisory:
    - Never auto-publishes or auto-rejects.
    - Final approval is made by an admin.
    """
    image_bytes = None
    if image is not None and image.filename:
        image_bytes, _ext, _mime = read_validated_image(image)

    provider = get_advisory_provider()
    return provider.run_advisory_check(
        image_bytes=image_bytes,
        selected_category=category.strip(),
        title=title.strip(),
        description=description.strip(),
        artisan_notes=notes.strip(),
    )
