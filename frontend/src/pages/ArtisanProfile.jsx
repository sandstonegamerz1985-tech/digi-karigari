import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import MessageModal from "../components/MessageModal";
import ProductCard from "../components/ProductCard";
import { EmptyState, ErrorBox, Loading } from "../components/States";
import TrustTierBadge from "../components/TrustTierBadge";
import { useAuth } from "../context/AuthContext";
import { useFetch } from "../hooks";

export default function ArtisanProfile() {
  const { id } = useParams();
  const { user } = useAuth();
  const { data: a, loading, error, reload } = useFetch(() => api.artisan(id), [id]);
  const trustData = useFetch(() => api.artisanTrustTier(id), [id]);
  const reviewsData = useFetch(() => api.artisanReviews(id), [id]);

  const [showTierDetails, setShowTierDetails] = useState(false);
  const [showMessageModal, setShowMessageModal] = useState(false);

  if (loading) return <Loading text="Loading artisan profile..." />;
  if (error)
    return (
      <div className="container section">
        <ErrorBox message={error} onRetry={reload} />
        <Link to="/artisans">&larr; Back to Artisans</Link>
      </div>
    );

  const tierInfo = trustData.data;
  const metrics = tierInfo?.metrics;
  const reviews = reviewsData.data?.reviews || [];
  const avgRating = reviewsData.data?.average_rating || 0;
  const totalReviews = reviewsData.data?.total_reviews || 0;

  return (
    <div className="container section">
      <Link to="/artisans">&larr; Back to Artisans Directory</Link>

      <div className="profile-head" style={{ alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", gap: "1.25rem", alignItems: "center", flexWrap: "wrap" }}>
          <div className="avatar avatar-lg">{a.name[0]}</div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
              <h1 style={{ margin: 0 }}>{a.name}</h1>
              {tierInfo?.current_tier && <TrustTierBadge tier={tierInfo.current_tier} />}
            </div>
            <p className="muted" style={{ margin: "0.2rem 0" }}>
              {a.craft} · {a.city}, {a.state}
            </p>
            <p className="pre" style={{ maxWidth: "60ch", margin: "0.4rem 0 0" }}>{a.bio}</p>
          </div>
        </div>

        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.5rem" }}>
          <button
            type="button"
            className="btn btn-outline btn-small"
            onClick={() => setShowTierDetails(!showTierDetails)}
          >
            🛡️ Trust Tier Criteria
          </button>
          {user?.id !== a.id && (
            <button
              type="button"
              className="btn btn-small"
              onClick={() => setShowMessageModal(true)}
            >
              💬 Message Artisan
            </button>
          )}
        </div>
      </div>

      {/* Trust Tier Criteria Breakdown Drawer / Panel */}
      {showTierDetails && tierInfo && (
        <div className="card card-body" style={{ background: "#f8fafc", border: "1px solid #cbd5e1", margin: "1.25rem 0" }}>
          <div className="between">
            <h3 style={{ margin: 0 }}>
              Trust Tier: {tierInfo.tier_name} ({tierInfo.badge})
            </h3>
            <button className="linklike small" onClick={() => setShowTierDetails(false)}>
              Close ✕
            </button>
          </div>
          <p className="small muted" style={{ margin: "0.2rem 0 0.8rem" }}>
            {tierInfo.description}
          </p>

          <div className="grid-3" style={{ gap: "0.75rem", marginBottom: "1rem" }}>
            <div className="card card-body" style={{ background: "#fff", padding: "0.75rem" }}>
              <span className="small muted">Profile Verification</span>
              <strong style={{ display: "block", color: metrics?.is_verified ? "#15803d" : "#b45309" }}>
                {metrics?.is_verified ? "✓ Verified Authentic" : "Pending Admin Review"}
              </strong>
            </div>
            <div className="card card-body" style={{ background: "#fff", padding: "0.75rem" }}>
              <span className="small muted">Completed Orders</span>
              <strong style={{ display: "block" }}>{metrics?.completed_orders || 0} orders</strong>
            </div>
            <div className="card card-body" style={{ background: "#fff", padding: "0.75rem" }}>
              <span className="small muted">Buyer Rating</span>
              <strong style={{ display: "block", color: "#d97706" }}>
                ★ {metrics?.average_rating || "0.0"} ({metrics?.review_count || 0} reviews)
              </strong>
            </div>
            <div className="card card-body" style={{ background: "#fff", padding: "0.75rem" }}>
              <span className="small muted">Dispute History</span>
              <strong style={{ display: "block", color: (metrics?.dispute_rate || 0) < 5 ? "#15803d" : "#b91c1c" }}>
                {metrics?.dispute_rate || 0}% dispute rate ({metrics?.total_disputes || 0} cases)
              </strong>
            </div>
          </div>

          <div className="alert alert-info small" style={{ margin: 0 }}>
            {tierInfo.disclaimer}
          </div>
        </div>
      )}

      {/* Artisan Listings */}
      <div style={{ marginTop: "2rem" }}>
        <h2>Artisanal Creations by {a.name}</h2>
        {a.products.length === 0 && <EmptyState title="No listings available at the moment" />}
        <div className="grid">
          {a.products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      </div>

      {/* Artisan Reviews */}
      <div style={{ marginTop: "2.5rem", borderTop: "1px solid var(--border)", paddingTop: "1.5rem" }}>
        <div className="between" style={{ marginBottom: "1rem" }}>
          <div>
            <h2>Community Reviews for {a.name}</h2>
            <p className="muted small">Feedback across all creations handcrafted by this artisan.</p>
          </div>
          {totalReviews > 0 && (
            <div style={{ textAlign: "right" }}>
              <span style={{ fontSize: "1.5rem", fontWeight: 800, color: "#d97706" }}>★ {avgRating}</span>
              <div className="small muted">({totalReviews} reviews)</div>
            </div>
          )}
        </div>

        {reviews.length === 0 ? (
          <div className="card card-body" style={{ textAlign: "center", color: "var(--muted)", padding: "1.5rem" }}>
            No buyer reviews recorded yet for this artisan.
          </div>
        ) : (
          <div style={{ display: "grid", gap: "0.75rem" }}>
            {reviews.map((r) => (
              <div key={r.id} className="card card-body">
                <div className="between">
                  <div>
                    <span className="stars">{"★".repeat(r.rating)}{"☆".repeat(5 - r.rating)}</span>
                    <strong style={{ marginLeft: "0.5rem" }}>{r.title}</strong>
                    {r.product && (
                      <span className="small muted" style={{ marginLeft: "0.5rem" }}>
                        on <em>{r.product.title}</em>
                      </span>
                    )}
                  </div>
                  <span className="small muted">
                    {new Date(r.created_at).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" })}
                  </span>
                </div>
                <div className="small" style={{ color: "#15803d", fontWeight: 600, margin: "0.2rem 0" }}>
                  ✓ {r.buyer?.name}
                </div>
                <p className="pre" style={{ margin: "0.2rem 0" }}>{r.comment}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {showMessageModal && (
        <MessageModal
          artisan={a}
          product={null}
          onClose={() => setShowMessageModal(false)}
        />
      )}
    </div>
  );
}
