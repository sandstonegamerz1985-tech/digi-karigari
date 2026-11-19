import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security import create_token

client = TestClient(app)


@pytest.fixture
def admin_headers():
    token = create_token(user_id=1, role="admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def buyer_headers():
    token = create_token(user_id=2, role="buyer")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def artisan_headers():
    token = create_token(user_id=4, role="artisan")
    return {"Authorization": f"Bearer {token}"}


# 1. Semantic Search Tests
def test_semantic_search_basic():
    res = client.get("/api/search/semantic?q=handcrafted+brass+diya")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["provider"] == "local_semantic_heuristic"
    assert data["is_ai_powered"] is False
    assert len(data["items"]) > 0
    # Checks relevance score and highlights
    first = data["items"][0]
    assert "relevance_score" in first
    assert "semantic_highlights" in first


def test_semantic_search_filters():
    res = client.get("/api/search/semantic?q=cotton&category=Textiles&min_price=500&max_price=2000")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    for item in data["items"]:
        assert item["category"] == "Textiles"
        assert item["price"] >= 500
        assert item["price"] <= 2000


def test_semantic_search_empty_and_suggestions():
    res = client.get("/api/search/semantic?q=nonexistentcraftqueryxyz")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert len(data["suggested_searches"]) > 0


# 2. Similar-Product Recommendations Tests
def test_similar_recommendations():
    # Fetch first product
    prod_res = client.get("/api/products")
    first_id = prod_res.json()[0]["id"]

    res = client.get(f"/api/recommendations/similar/{first_id}")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) > 0
    for item in data["items"]:
        assert "recommendation_reason" in item
        assert len(item["recommendation_reason"]) > 0


def test_recommendations_for_you(buyer_headers):
    res = client.get("/api/recommendations/for-you", headers=buyer_headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data


# 3. AI Advisory Checks Tests
def test_ai_advisory_check(artisan_headers):
    res = client.post(
        "/api/ai/advisory-check",
        headers=artisan_headers,
        data={
            "category": "Pottery",
            "title": "Terracotta Earthen Planter",
            "description": "Wheel thrown clay pot for balcony garden with drainage hole.",
            "notes": "terracotta, clay, pottery",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "checks" in data
    assert "disclaimer" in data
    assert "Advisory suggestion only" in data["disclaimer"]
    # Check category match result
    assert data["category_summary"]["selected"] == "Pottery"
    assert data["category_summary"]["is_match"] is True


# 4. Messaging & Notifications Tests
def test_messaging_and_notifications(buyer_headers, artisan_headers):
    # Buyer starts conversation with artisan (id=4)
    start_res = client.post(
        "/api/conversations",
        headers=buyer_headers,
        json={
            "artisan_id": 4,
            "subject": "Inquiry about custom piece",
            "initial_message": "Hello, do you accept custom color requests for this design?",
        },
    )
    assert start_res.status_code in (200, 201)
    convo = start_res.json()
    convo_id = convo["id"]

    # Artisan replies in thread
    reply_res = client.post(
        f"/api/conversations/{convo_id}/messages",
        headers=artisan_headers,
        json={"text": "Yes, I can hand-paint it in custom natural dyes!"},
    )
    assert reply_res.status_code == 200

    # Buyer reads thread
    thread_res = client.get(f"/api/conversations/{convo_id}", headers=buyer_headers)
    assert thread_res.status_code == 200
    assert len(thread_res.json()["messages"]) >= 2

    # Check artisan notifications
    notif_res = client.get("/api/notifications", headers=artisan_headers)
    assert notif_res.status_code == 200
    assert "notifications" in notif_res.json()


# 5. Reviews Tests
def test_reviews_eligible_and_public():
    # Get reviews for product 1
    res = client.get("/api/reviews/product/1")
    assert res.status_code == 200
    data = res.json()
    assert "average_rating" in data
    assert "rating_breakdown" in data
    assert "reviews" in data


# 6. Disputes & Refunds Tests
def test_disputes_flow(buyer_headers, admin_headers):
    # Buyer lists disputes
    dispute_list = client.get("/api/disputes", headers=buyer_headers)
    assert dispute_list.status_code == 200
    disputes = dispute_list.json()
    assert len(disputes) > 0
    dispute_id = disputes[0]["id"]

    # Post message in dispute
    msg_res = client.post(
        f"/api/disputes/{dispute_id}/messages",
        headers=buyer_headers,
        json={"message": "Here is additional context about the package."},
    )
    assert msg_res.status_code == 200

    # Admin resolves dispute with mock refund
    resolve_res = client.post(
        f"/api/admin/disputes/{dispute_id}/resolve",
        headers=admin_headers,
        json={
            "decision": "refund_approved",
            "refund_amount": 200,
            "resolution_notes": "Approved partial refund for courier transit damage.",
        },
    )
    assert resolve_res.status_code == 200
    res_data = resolve_res.json()
    assert res_data["status"] == "resolved_refunded"
    assert res_data["refunded_amount"] == 200
    assert "REFUND-" in res_data["refund_reference"]


# 7. Trust Tiers Tests
def test_trust_tier_details():
    res = client.get("/api/artisans/4/trust-tier")
    assert res.status_code == 200
    data = res.json()
    assert "current_tier" in data
    assert "metrics" in data
    assert "tier_requirements" in data
    assert "disclaimer" in data
    assert "AI advisory results are NEVER used" in data["disclaimer"]


def test_trust_tier_admin_override(admin_headers):
    res = client.post(
        "/api/admin/trust-tiers/4/override",
        headers=admin_headers,
        json={
            "new_tier": "master_artisan",
            "reason": "Exemplary 20-year dedication to traditional craft technique.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["current_tier"] == "master_artisan"
    assert data["is_manual_override"] is True
    assert len(data["audit_trail"]) > 0


# 8. Admin Dashboard & Analytics Tests
def test_admin_dashboard_role_protection():
    # Unauthenticated should fail 401
    res = client.get("/api/admin/analytics")
    assert res.status_code == 401

    # Non-admin should fail 403
    buyer_token = create_token(user_id=2, role="buyer")
    res2 = client.get("/api/admin/analytics", headers={"Authorization": f"Bearer {buyer_token}"})
    assert res2.status_code == 403


def test_admin_analytics_with_filters(admin_headers):
    res = client.get("/api/admin/analytics?range=30d", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "order_status_distribution" in data
    assert "popular_categories" in data
    assert "dispute_metrics" in data
    assert "review_metrics" in data


def test_admin_listing_queue_and_actions(admin_headers):
    listings_res = client.get("/api/admin/listings", headers=admin_headers)
    assert listings_res.status_code == 200
    listings = listings_res.json()
    assert len(listings) > 0

    first_prod_id = listings[0]["id"]
    # Explicit admin approve
    app_res = client.post(f"/api/admin/listings/{first_prod_id}/approve", headers=admin_headers)
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "approved"
