"""Honest scaffolding for features that are NOT built yet.

- GET /api/features returns the status of every feature (implemented / demo-only / planned).
  The frontend "Features" page shows this list, so the demo never pretends to do more than it does.
- The stub endpoints below answer "501 Not Implemented" on purpose. They show where future code
  will go without faking any behaviour.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["planned-features"])

FEATURES = [
    # ---- implemented -----------------------------------------------------
    {"key": "catalog", "name": "Home, catalog, product pages, artisan profiles", "status": "implemented", "note": ""},
    {"key": "auth", "name": "Buyer / artisan / admin accounts (simple demo login)", "status": "implemented", "note": "Fine for a demo; not hardened for production."},
    {"key": "listings", "name": "Create, edit, delete listings with photos", "status": "implemented", "note": "Photos are stored on local disk."},
    {"key": "admin-approval", "name": "Admin approves / rejects artisans (Verified badge)", "status": "implemented", "note": ""},
    {"key": "cart-checkout", "name": "Cart and checkout", "status": "implemented", "note": "Payment is simulated (see below)."},
    {"key": "orders", "name": "Order history, status tracking, manual courier + tracking ID", "status": "implemented", "note": "Artisans type courier details by hand; no courier API."},
    {"key": "search-filters", "name": "Keyword search and category / price filters", "status": "implemented", "note": "Simple text matching (SQL LIKE)."},
    # ---- demo-only -------------------------------------------------------
    {"key": "ai-listing", "name": "AI listing assistant", "status": "demo-only", "note": "Runs in DEMO mode (keyword rules, photo not analysed) unless an API key is set in backend/.env. Suggestions are never auto-published."},
    {"key": "test-payment", "name": "Payment", "status": "demo-only", "note": "Simulated success/failure switch. No card data, no real money."},
    {"key": "similar", "name": "Similar-product suggestions", "status": "demo-only", "note": "Just 'same category'. Smarter recommendations are planned."},
    {"key": "i18n", "name": "English / Hindi labels", "status": "demo-only", "note": "Menus, buttons, headings and form labels switch between English and Hindi. Seller-written text, AI suggestions, server error messages and policy pages stay in English."},
    {"key": "admin-stats", "name": "Admin basic counts", "status": "demo-only", "note": "A few totals only; full analytics dashboard is planned."},
    {"key": "policies", "name": "Terms, privacy, shipping and refund pages", "status": "demo-only", "note": "Placeholder text for the demo. Not legal advice; have them reviewed before launch."},
    # ---- planned ---------------------------------------------------------
    {"key": "semantic-search", "name": "Semantic (meaning-based) search", "status": "planned", "note": ""},
    {"key": "recommendations", "name": "AI-powered similar-product recommendations", "status": "planned", "note": ""},
    {"key": "ai-photo-check", "name": "AI advisory checks for photo quality / category match", "status": "planned", "note": "Advice only; an admin makes the final decision."},
    {"key": "messaging", "name": "Buyer-artisan messaging and notifications", "status": "planned", "note": ""},
    {"key": "reviews", "name": "Reviews", "status": "planned", "note": ""},
    {"key": "disputes-refunds", "name": "Disputes and refunds", "status": "planned", "note": ""},
    {"key": "trust-tiers", "name": "Seller trust tiers", "status": "planned", "note": ""},
    {"key": "admin-dashboard", "name": "Full admin dashboard and analytics", "status": "planned", "note": ""},
]


@router.get("/features")
def list_features():
    return FEATURES


def _not_built(name: str):
    raise HTTPException(status_code=501, detail=f"{name} is a planned feature and is not implemented yet.")


@router.get("/planned/search/semantic")
def semantic_search():
    _not_built("Semantic search")


@router.get("/planned/messages")
def messages():
    _not_built("Buyer-artisan messaging")


@router.get("/planned/notifications")
def notifications():
    _not_built("Notifications")


@router.get("/planned/reviews")
def reviews():
    _not_built("Reviews")


@router.get("/planned/disputes")
def disputes():
    _not_built("Disputes and refunds")
