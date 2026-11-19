"""Feature status directory.

- GET /api/features returns the status of every feature (implemented / demo-only / planned).
  The frontend "Features" page shows this list, so users and evaluators see honest statuses.
"""
from fastapi import APIRouter

router = APIRouter(tags=["marketplace-features"])

FEATURES = [
    # ---- Core Marketplace Features -----------------------------------------------------
    {"key": "catalog", "name": "Home, catalog, product pages, artisan profiles", "status": "implemented", "note": "Responsive artisan-focused catalog."},
    {"key": "auth", "name": "Buyer / artisan / admin accounts (demo auth)", "status": "implemented", "note": "Role-based token authentication."},
    {"key": "listings", "name": "Create, edit, delete listings with photos", "status": "implemented", "note": "Full lifecycle with image uploads and tags."},
    {"key": "admin-approval", "name": "Admin approves / rejects artisans (Verified badge)", "status": "implemented", "note": "Verification workflow with rejection feedback."},
    {"key": "cart-checkout", "name": "Cart and checkout", "status": "implemented", "note": "Full cart management and multi-item checkout."},
    {"key": "orders", "name": "Order history, status tracking, manual courier + tracking ID", "status": "implemented", "note": "Tracking and status lifecycle."},
    {"key": "search-filters", "name": "Keyword search and category / price / trust filters", "status": "implemented", "note": "Multi-attribute catalog filtering."},

    # ---- Newly Implemented Planned Features ---------------------------------------------
    {"key": "semantic-search", "name": "Semantic (meaning-based) search", "status": "implemented", "note": "Search by use, style, material, occasion, and intent with transparent local heuristic provider interface."},
    {"key": "recommendations", "name": "Similar-product recommendations", "status": "implemented", "note": "Multi-factor craft, material, and category similarity engine with human-readable reasons (e.g. 'Similar material')."},
    {"key": "ai-photo-check", "name": "AI advisory checks for photo quality / category match", "status": "implemented", "note": "Advisory checks for blur, lighting, dimensions, and category consistency. Admin makes final approval decision."},
    {"key": "messaging", "name": "Buyer-artisan messaging and notifications", "status": "implemented", "note": "Conversation inbox, message threads tied to products/orders, unread tracking, and marketplace event notifications."},
    {"key": "reviews", "name": "Verified purchase reviews", "status": "implemented", "note": "1-5 star ratings, duplicate review prevention per purchase, rating summaries, and admin moderation."},
    {"key": "disputes-refunds", "name": "Disputes and refunds", "status": "implemented", "note": "Dispute filing, communication timeline, admin resolution, audit logs, and simulated mock payment refund provider."},
    {"key": "trust-tiers", "name": "Seller trust tiers", "status": "implemented", "note": "4-tier transparent progression (New Maker -> Verified -> Trusted -> Master) from orders and ratings, with admin override audit trail."},
    {"key": "admin-dashboard", "name": "Full admin dashboard and analytics", "status": "implemented", "note": "Marketplace analytics (sales, conversion, disputes, review trends, date/category filters), listing review queue, and moderation."},

    # ---- Honest labels for demo / simulated aspects -------------------------------------
    {"key": "test-payment", "name": "Payment & Refund Processing", "status": "demo-only", "note": "Simulated test payment and mock refund provider with audit trail. No real bank charges or credit card transactions."},
    {"key": "policies", "name": "Terms, privacy, shipping and refund policies", "status": "demo-only", "note": "Demonstration policy text for marketplace terms and conditions."},
]


@router.get("/features")
def list_features():
    return FEATURES
