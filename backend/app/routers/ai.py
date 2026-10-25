from fastapi import APIRouter, Depends, File, Form, UploadFile

from .. import ai_service
from ..deps import require_approved_artisan
from ..models import User
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
