import { useState } from "react";
import { Link } from "react-router-dom";
import { api, assetUrl } from "../api";
import { EmptyState, ErrorBox, Loading } from "../components/States";
import TrustTierBadge from "../components/TrustTierBadge";
import { useFetch } from "../hooks";
import { formatINR } from "../utils";

export default function AdminPanel() {
  const [tab, setTab] = useState("analytics");
  const [actionError, setActionError] = useState("");
  const [actionSuccess, setActionSuccess] = useState("");

  // Analytics filters
  const [range, setRange] = useState("30d");
  const [selectedCat, setSelectedCat] = useState("");

  // Listings filter
  const [listingStatus, setListingStatus] = useState("all");
  const [rejectingListing, setRejectingListing] = useState(null);
  const [listingRejectReason, setListingRejectReason] = useState("");

  // Artisans filter
  const [artisanStatus, setArtisanStatus] = useState("pending");
  const [rejectingArtisan, setRejectingArtisan] = useState(null);
  const [artisanRejectReason, setArtisanRejectReason] = useState("");

  // Trust tier modal
  const [tierModalArtisan, setTierModalArtisan] = useState(null);
  const [overrideTier, setOverrideTier] = useState("trusted_artisan");
  const [overrideReason, setOverrideReason] = useState("");

  // Dispute resolution modal
  const [resolvingDispute, setResolvingDispute] = useState(null);
  const [disputeDecision, setDisputeDecision] = useState("refund_approved");
  const [refundAmount, setRefundAmount] = useState(0);
  const [disputeNotes, setDisputeNotes] = useState("");

  // Data queries
  const stats = useFetch(() => api.adminStats(), []);
  const analytics = useFetch(() => api.adminAnalytics({ range, category: selectedCat || undefined }), [range, selectedCat]);
  const listings = useFetch(() => api.adminListings(listingStatus), [listingStatus]);
  const artisansList = useFetch(() => api.adminArtisans(artisanStatus), [artisanStatus]);
  const disputesList = useFetch(() => api.disputes(), []);
  const reviewsList = useFetch(() => api.adminReviews("all"), []);
  const usersList = useFetch(() => api.adminUsers("all"), []);
  const categories = useFetch(() => api.categories(), []);

  const refreshAll = () => {
    stats.reload();
    analytics.reload();
    listings.reload();
    artisansList.reload();
    disputesList.reload();
    reviewsList.reload();
    usersList.reload();
  };

  // --- Handlers ---
  const handleApproveListing = async (productId) => {
    setActionError("");
    try {
      await api.adminApproveListing(productId);
      setActionSuccess("Listing approved and published to catalog!");
      listings.reload();
      stats.reload();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const handleRejectListing = async (e) => {
    e.preventDefault();
    if (!listingRejectReason.trim()) return;
    setActionError("");
    try {
      await api.adminRejectListing(rejectingListing.id, listingRejectReason.trim());
      setActionSuccess("Listing rejected with artisan feedback recorded.");
      setRejectingListing(null);
      setListingRejectReason("");
      listings.reload();
      stats.reload();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const handleApproveArtisan = async (userId) => {
    setActionError("");
    try {
      await api.approveArtisan(userId);
      setActionSuccess("Artisan profile verified!");
      artisansList.reload();
      stats.reload();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const handleRejectArtisan = async (e) => {
    e.preventDefault();
    if (!artisanRejectReason.trim()) return;
    setActionError("");
    try {
      await api.rejectArtisan(rejectingArtisan.id, artisanRejectReason.trim());
      setActionSuccess("Artisan application rejected.");
      setRejectingArtisan(null);
      setArtisanRejectReason("");
      artisansList.reload();
      stats.reload();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const handleTierOverride = async (e) => {
    e.preventDefault();
    if (!overrideReason.trim()) return;
    setActionError("");
    try {
      await api.adminOverrideTrustTier(tierModalArtisan.artisan_id || tierModalArtisan.id, {
        new_tier: overrideTier,
        reason: overrideReason.trim(),
      });
      setActionSuccess("Artisan trust tier updated with audit record.");
      setTierModalArtisan(null);
      setOverrideReason("");
      artisansList.reload();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const handleResolveDispute = async (e) => {
    e.preventDefault();
    if (!disputeNotes.trim()) return;
    setActionError("");
    try {
      await api.adminResolveDispute(resolvingDispute.id, {
        decision: disputeDecision,
        refund_amount: Number(refundAmount),
        resolution_notes: disputeNotes.trim(),
      });
      setActionSuccess("Dispute case resolved and mock refund gateway transaction recorded.");
      setResolvingDispute(null);
      setDisputeNotes("");
      disputesList.reload();
      stats.reload();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const handleModerateReview = async (reviewId, newStatus) => {
    setActionError("");
    try {
      await api.adminModerateReview(reviewId, {
        status: newStatus,
        moderation_note: `Admin marked as ${newStatus}`,
      });
      setActionSuccess(`Review updated to ${newStatus}.`);
      reviewsList.reload();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const an = analytics.data;

  return (
    <div className="container section">
      <div className="between wrap" style={{ marginBottom: "1rem" }}>
        <div>
          <h1>Marketplace Administration & Analytics</h1>
          <p className="muted small">Role-protected administrative oversight, listing quality review, trust, and dispute resolution.</p>
        </div>
        <button className="btn btn-outline btn-small" onClick={refreshAll}>
          🔄 Refresh Data
        </button>
      </div>

      {actionError && <div className="alert alert-error">{actionError}</div>}
      {actionSuccess && (
        <div className="alert alert-success">
          {actionSuccess}
          <button className="linklike small" onClick={() => setActionSuccess("")} style={{ marginLeft: "1rem" }}>✕</button>
        </div>
      )}

      {/* Main Admin Navigation Tabs */}
      <div className="tabs">
        <button className={tab === "analytics" ? "tab active" : "tab"} onClick={() => setTab("analytics")}>
          📊 Analytics & Metrics
        </button>
        <button className={tab === "listings" ? "tab active" : "tab"} onClick={() => setTab("listings")}>
          🎨 Listing Review Queue ({stats.data?.pending_listings || 0} pending)
        </button>
        <button className={tab === "artisans" ? "tab active" : "tab"} onClick={() => setTab("artisans")}>
          🛡️ Artisans & Trust Tiers ({stats.data?.pending_artisans || 0} pending)
        </button>
        <button className={tab === "disputes" ? "tab active" : "tab"} onClick={() => setTab("disputes")}>
          ⚠️ Disputes & Refunds ({disputesList.data?.filter((d) => d.status === "open" || d.status === "under_review").length || 0})
        </button>
        <button className={tab === "reviews" ? "tab active" : "tab"} onClick={() => setTab("reviews")}>
          ⭐ Review Moderation
        </button>
        <button className={tab === "users" ? "tab active" : "tab"} onClick={() => setTab("users")}>
          👥 User Directory ({stats.data?.users || 0})
        </button>
      </div>

      {/* ---------------- 1. Analytics & Metrics Tab ---------------- */}
      {tab === "analytics" && (
        <div>
          <div className="filter-card">
            <div className="filters">
              <label>
                Date Range Filter
                <select value={range} onChange={(e) => setRange(e.target.value)}>
                  <option value="7d">Last 7 Days</option>
                  <option value="30d">Last 30 Days</option>
                  <option value="90d">Last 90 Days</option>
                  <option value="all">All Time</option>
                </select>
              </label>

              <label>
                Category Filter
                <select value={selectedCat} onChange={(e) => setSelectedCat(e.target.value)}>
                  <option value="">All Categories</option>
                  {(categories.data || []).map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          {analytics.loading && <Loading text="Aggregating marketplace metrics..." />}
          {analytics.error && <ErrorBox message={analytics.error} />}

          {an && (
            <>
              {!an.has_enough_data && (
                <div className="alert alert-info">
                  {an.empty_state_note || "Not enough transactions in this selected range."}
                </div>
              )}

              {/* Metric KPI Cards */}
              <div className="analytics-grid">
                <div className="metric-card">
                  <h4>Test Sales Volume</h4>
                  <div className="metric-val">{formatINR(an.summary.total_sales)}</div>
                  <div className="small muted">Simulated checkout volume</div>
                </div>

                <div className="metric-card">
                  <h4>Order Items</h4>
                  <div className="metric-val">{an.summary.order_volume}</div>
                  <div className="small muted">Items fulfilled or in transit</div>
                </div>

                <div className="metric-card">
                  <h4>Active Buyers</h4>
                  <div className="metric-val">{an.summary.active_buyers}</div>
                  <div className="small muted">Purchased in range</div>
                </div>

                <div className="metric-card">
                  <h4>Active Artisans</h4>
                  <div className="metric-val">{an.summary.active_sellers}</div>
                  <div className="small muted">Sellers with order activity</div>
                </div>

                <div className="metric-card">
                  <h4>Buyer Conversion Rate</h4>
                  <div className="metric-val">{an.summary.conversion_rate_percent}%</div>
                  <div className="small muted">Registered buyer to purchaser</div>
                </div>

                <div className="metric-card">
                  <h4>Dispute Rate</h4>
                  <div className="metric-val" style={{ color: an.summary.dispute_rate_percent > 5 ? "#dc2626" : "var(--indigo)" }}>
                    {an.summary.dispute_rate_percent}%
                  </div>
                  <div className="small muted">{an.dispute_metrics.total} total cases</div>
                </div>

                <div className="metric-card">
                  <h4>Average Buyer Rating</h4>
                  <div className="metric-val" style={{ color: "#d97706" }}>
                    ★ {an.summary.average_rating}
                  </div>
                  <div className="small muted">{an.summary.total_reviews} verified reviews</div>
                </div>
              </div>

              {/* Popular Categories & Order Status */}
              <div className="detail" style={{ marginTop: "1rem" }}>
                <div className="card card-body">
                  <h3>Popular Craft Categories</h3>
                  <p className="small muted">Share of total sales across artisanal specialties</p>
                  {an.popular_categories.length === 0 ? (
                    <p className="small muted">No category sales recorded yet.</p>
                  ) : (
                    an.popular_categories.map((cat, idx) => (
                      <div key={idx} style={{ marginBottom: "0.6rem" }}>
                        <div className="between small">
                          <strong>{cat.category}</strong>
                          <span>{formatINR(cat.sales)} ({cat.share_pct}%)</span>
                        </div>
                        <div className="rating-bar-bg" style={{ marginTop: "0.25rem", height: "10px" }}>
                          <div className="rating-bar-fill" style={{ width: `${cat.share_pct}%`, background: "var(--saffron)" }} />
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <div className="card card-body">
                  <h3>Fulfillment Status Pipeline</h3>
                  <p className="small muted">Current status of items ordered</p>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1rem" }}>
                    <div style={{ padding: "0.75rem", background: "#f8fafc", borderRadius: "8px" }}>
                      <span className="small muted">Placed</span>
                      <strong style={{ fontSize: "1.4rem", display: "block" }}>{an.order_status_distribution.placed || 0}</strong>
                    </div>
                    <div style={{ padding: "0.75rem", background: "#fefce8", borderRadius: "8px" }}>
                      <span className="small muted">Packed</span>
                      <strong style={{ fontSize: "1.4rem", display: "block" }}>{an.order_status_distribution.packed || 0}</strong>
                    </div>
                    <div style={{ padding: "0.75rem", background: "#eff6ff", borderRadius: "8px" }}>
                      <span className="small muted">Shipped</span>
                      <strong style={{ fontSize: "1.4rem", display: "block" }}>{an.order_status_distribution.shipped || 0}</strong>
                    </div>
                    <div style={{ padding: "0.75rem", background: "#f0fdf4", borderRadius: "8px" }}>
                      <span className="small muted">Delivered</span>
                      <strong style={{ fontSize: "1.4rem", display: "block", color: "#16a34a" }}>
                        {an.order_status_distribution.delivered || 0}
                      </strong>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* ---------------- 2. Listings Review Queue Tab ---------------- */}
      {tab === "listings" && (
        <div>
          <div className="between" style={{ marginBottom: "1rem" }}>
            <div>
              <h3>Artisan Listing Review & Quality Assurance</h3>
              <p className="small muted">
                Review photos, materials, and automated AI advisory checks before publishing. Final decision is explicitly made by an admin.
              </p>
            </div>
            <div className="row">
              {["all", "pending_review", "approved", "rejected"].map((st) => (
                <button
                  key={st}
                  className={`btn btn-small ${listingStatus === st ? "btn" : "btn-outline"}`}
                  onClick={() => setListingStatus(st)}
                >
                  {st.replace("_", " ").toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {listings.loading && <Loading text="Loading listings..." />}
          {listings.data?.length === 0 && <EmptyState title="No listings found for this filter" />}

          {listings.data?.map((p) => {
            const adv = p.ai_advisory;
            return (
              <div key={p.id} className="review-queue-card">
                <div className="review-queue-grid">
                  <img
                    src={assetUrl(p.image_url)}
                    alt={p.title}
                    style={{ width: "100%", aspectRatio: "1", objectFit: "cover", borderRadius: "8px" }}
                  />

                  <div>
                    <div className="between">
                      <h3 style={{ margin: 0 }}>{p.title}</h3>
                      <span className={`status status-${p.status || "approved"}`}>
                        {p.status || "approved"}
                      </span>
                    </div>

                    <p className="small muted" style={{ margin: "0.2rem 0" }}>
                      Category: <strong>{p.category}</strong> · Price: <strong>{formatINR(p.price)}</strong> · Stock: {p.stock}
                      <br />
                      Artisan: <Link to={`/artisan/${p.artisan?.id}`}>{p.artisan?.name}</Link> ({p.artisan?.craft})
                    </p>

                    <p className="small pre" style={{ margin: "0.4rem 0" }}>{p.description}</p>
                    {p.materials && <p className="small"><strong>Materials:</strong> {p.materials}</p>}

                    {/* AI Advisory Report Section */}
                    {adv && (
                      <div className="card card-body" style={{ background: "#fffaf0", border: "1px solid #fed7aa", padding: "0.75rem", marginTop: "0.6rem" }}>
                        <div className="between">
                          <strong style={{ fontSize: "0.85rem", color: "#9a3412" }}>
                            🔍 AI Advisory Quality Inspection ({adv.overall_status})
                          </strong>
                          <span className="small muted">Suggestions Only</span>
                        </div>
                        {adv.checks?.map((chk, idx) => (
                          <div key={idx} className="small" style={{ margin: "0.2rem 0" }}>
                            <span style={{ color: chk.status === "pass" ? "#16a34a" : "#ea580c", fontWeight: 700 }}>
                              {chk.status === "pass" ? "✓" : "⚠️"} {chk.name}:
                            </span>{" "}
                            {chk.message}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {p.status !== "approved" && (
                      <button
                        type="button"
                        className="btn btn-small"
                        style={{ background: "#15803d", borderColor: "#15803d" }}
                        onClick={() => handleApproveListing(p.id)}
                      >
                        ✓ Approve Listing
                      </button>
                    )}
                    {p.status !== "rejected" && (
                      <button
                        type="button"
                        className="btn btn-small btn-danger"
                        onClick={() => setRejectingListing(p)}
                      >
                        ✕ Reject Listing
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Reject Listing Modal */}
          {rejectingListing && (
            <div className="modal-backdrop" onClick={() => setRejectingListing(null)}>
              <div className="modal" style={{ textAlign: "left" }} onClick={(e) => e.stopPropagation()}>
                <h3>Reject Listing: {rejectingListing.title}</h3>
                <p className="small muted">Explain what needs correction (e.g. clearer photo, accurate craft category, detailed description):</p>
                <form onSubmit={handleRejectListing} className="form">
                  <textarea
                    rows={4}
                    placeholder="Enter reason for rejection..."
                    value={listingRejectReason}
                    onChange={(e) => setListingRejectReason(e.target.value)}
                    required
                  />
                  <div className="between">
                    <button type="button" className="btn btn-outline btn-small" onClick={() => setRejectingListing(null)}>
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-small btn-danger">
                      Reject Listing
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ---------------- 3. Artisans & Trust Tiers Tab ---------------- */}
      {tab === "artisans" && (
        <div>
          <div className="between wrap" style={{ marginBottom: "1rem" }}>
            <div>
              <h3>Artisan Verification & Trust Tiers</h3>
              <p className="small muted">
                Transparent 4-tier seller progression derived from order completions, ratings, and disputes. Full audit logging for manual overrides.
              </p>
            </div>
            <div className="row">
              {["pending", "approved", "rejected", "all"].map((st) => (
                <button
                  key={st}
                  className={`btn btn-small ${artisanStatus === st ? "btn" : "btn-outline"}`}
                  onClick={() => setArtisanStatus(st)}
                >
                  {st.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {artisansList.loading && <Loading text="Loading artisans..." />}
          {artisansList.data?.map((a) => (
            <div key={a.id} className="card card-body" style={{ marginBottom: "0.75rem" }}>
              <div className="between wrap">
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <strong>{a.name}</strong>
                    <TrustTierBadge tier={a.trust_tier} />
                    <span className={`status status-${a.status}`}>{a.status}</span>
                  </div>
                  <p className="small muted" style={{ margin: "0.2rem 0" }}>
                    {a.email} · Craft: {a.craft} · Location: {a.city}, {a.state} · Listings: {a.product_count}
                  </p>
                  <p className="small pre" style={{ margin: "0.2rem 0" }}>{a.bio}</p>
                </div>

                <div className="row wrap" style={{ gap: "0.5rem" }}>
                  {a.status !== "approved" && (
                    <button
                      type="button"
                      className="btn btn-small"
                      style={{ background: "#15803d", borderColor: "#15803d" }}
                      onClick={() => handleApproveArtisan(a.id)}
                    >
                      ✓ Verify Artisan
                    </button>
                  )}
                  {a.status !== "rejected" && (
                    <button
                      type="button"
                      className="btn btn-small btn-danger"
                      onClick={() => setRejectingArtisan(a)}
                    >
                      ✕ Reject
                    </button>
                  )}
                  <button
                    type="button"
                    className="btn btn-outline btn-small"
                    onClick={async () => {
                      const tierDetails = await api.artisanTrustTier(a.id);
                      setTierModalArtisan(tierDetails);
                      setOverrideTier(tierDetails.current_tier);
                    }}
                  >
                    🛡️ Trust Tier Audit
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* Artisan Reject Modal */}
          {rejectingArtisan && (
            <div className="modal-backdrop" onClick={() => setRejectingArtisan(null)}>
              <div className="modal" style={{ textAlign: "left" }} onClick={(e) => e.stopPropagation()}>
                <h3>Reject Artisan Application</h3>
                <p className="small muted">Reason for rejecting {rejectingArtisan.name}:</p>
                <form onSubmit={handleRejectArtisan} className="form">
                  <textarea
                    rows={3}
                    placeholder="Provide reason for rejection..."
                    value={artisanRejectReason}
                    onChange={(e) => setArtisanRejectReason(e.target.value)}
                    required
                  />
                  <div className="between">
                    <button type="button" className="btn btn-outline btn-small" onClick={() => setRejectingArtisan(null)}>
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-small btn-danger">
                      Reject Application
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Trust Tier Override & Audit Modal */}
          {tierModalArtisan && (
            <div className="modal-backdrop" onClick={() => setTierModalArtisan(null)}>
              <div className="modal" style={{ width: "min(600px, 100%)", textAlign: "left" }} onClick={(e) => e.stopPropagation()}>
                <h3>Trust Tier Management & Audit</h3>
                <p className="small muted">
                  Current Tier: <strong>{tierModalArtisan.tier_name} ({tierModalArtisan.badge})</strong>
                </p>

                <div className="grid-3" style={{ gap: "0.5rem", margin: "0.75rem 0" }}>
                  <div style={{ background: "#f8fafc", padding: "0.5rem", borderRadius: "6px" }} className="small">
                    Orders: <strong>{tierModalArtisan.metrics?.completed_orders || 0}</strong>
                  </div>
                  <div style={{ background: "#f8fafc", padding: "0.5rem", borderRadius: "6px" }} className="small">
                    Rating: <strong>★ {tierModalArtisan.metrics?.average_rating || 0}</strong>
                  </div>
                  <div style={{ background: "#f8fafc", padding: "0.5rem", borderRadius: "6px" }} className="small">
                    Disputes: <strong>{tierModalArtisan.metrics?.dispute_rate || 0}%</strong>
                  </div>
                </div>

                <form onSubmit={handleTierOverride} className="form" style={{ marginTop: "1rem" }}>
                  <label>
                    Assign / Override Tier
                    <select value={overrideTier} onChange={(e) => setOverrideTier(e.target.value)}>
                      <option value="new_artisan">🪴 New Artisan</option>
                      <option value="verified_maker">🛡️ Verified Maker</option>
                      <option value="trusted_artisan">⭐ Trusted Artisan</option>
                      <option value="master_artisan">👑 Master Heritage Artisan</option>
                      <option value="auto">↺ Revert to Automatic Metric Calculation</option>
                    </select>
                  </label>

                  <label>
                    Administrative Justification / Reason *
                    <textarea
                      rows={3}
                      placeholder="Required audit explanation for manual tier change..."
                      value={overrideReason}
                      onChange={(e) => setOverrideReason(e.target.value)}
                      required
                    />
                  </label>

                  <div className="between">
                    <button type="button" className="btn btn-outline btn-small" onClick={() => setTierModalArtisan(null)}>
                      Close
                    </button>
                    <button type="submit" className="btn btn-small">
                      Save Tier with Audit Record
                    </button>
                  </div>
                </form>

                {tierModalArtisan.audit_trail?.length > 0 && (
                  <div style={{ marginTop: "1rem", borderTop: "1px solid var(--border)", paddingTop: "0.75rem" }}>
                    <strong className="small">Audit History:</strong>
                    <div className="audit-timeline" style={{ maxHeight: "150px", overflowY: "auto" }}>
                      {tierModalArtisan.audit_trail.map((a) => (
                        <div key={a.id} className="audit-node">
                          <strong>{a.new_tier}</strong> ({a.change_type}) by {a.admin_name}: {a.reason}
                          <div className="small muted">{a.created_at}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ---------------- 4. Disputes & Refunds Tab ---------------- */}
      {tab === "disputes" && (
        <div>
          <h3>Marketplace Disputes & Refund Outcomes</h3>
          <p className="small muted">
            Review claims, evidence, and issue mock refunds. Refund outcomes require payment provider confirmation.
          </p>

          {disputesList.loading && <Loading text="Loading disputes..." />}
          {disputesList.data?.length === 0 && <EmptyState title="No customer dispute cases filed" />}

          {disputesList.data?.map((d) => (
            <div key={d.id} className="card card-body" style={{ marginBottom: "1rem" }}>
              <div className="between wrap">
                <div>
                  <strong>Case #{d.id}: {d.reason}</strong>
                  <div className="small muted">
                    Order #{d.order_id} · Buyer: {d.buyer?.name} · Artisan: {d.artisan?.name}
                  </div>
                </div>
                <span className={`status status-${d.status}`}>
                  {d.status.replace("_", " ").toUpperCase()}
                </span>
              </div>

              <p className="small pre" style={{ margin: "0.4rem 0", background: "#f8fafc", padding: "0.6rem", borderRadius: "6px" }}>
                {d.description}
              </p>

              <div className="between wrap">
                <span className="small muted">
                  Requested: {d.requested_resolution.replace("_", " ")} (₹{d.requested_amount})
                  {d.refund_reference && ` · Confirmed Refund: ₹${d.refunded_amount} (Ref: ${d.refund_reference})`}
                </span>
                <button
                  type="button"
                  className="btn btn-small"
                  onClick={() => {
                    setResolvingDispute(d);
                    setRefundAmount(d.requested_amount);
                  }}
                >
                  Review & Record Decision
                </button>
              </div>
            </div>
          ))}

          {/* Resolve Dispute Modal */}
          {resolvingDispute && (
            <div className="modal-backdrop" onClick={() => setResolvingDispute(null)}>
              <div className="modal" style={{ width: "min(560px, 100%)", textAlign: "left" }} onClick={(e) => e.stopPropagation()}>
                <h3>Resolve Dispute #{resolvingDispute.id}</h3>
                <p className="small muted">Order #{resolvingDispute.order_id} · Claim: {resolvingDispute.reason}</p>

                <form onSubmit={handleResolveDispute} className="form">
                  <label>
                    Decision Outcome
                    <select value={disputeDecision} onChange={(e) => setDisputeDecision(e.target.value)}>
                      <option value="refund_approved">Approve Refund (Full or Partial)</option>
                      <option value="refund_rejected">Reject Dispute Claim</option>
                      <option value="settled_mutual">Mutual Settlement without Monetary Refund</option>
                    </select>
                  </label>

                  {disputeDecision === "refund_approved" && (
                    <label>
                      Refund Amount (₹)
                      <input
                        type="number"
                        min="1"
                        value={refundAmount}
                        onChange={(e) => setRefundAmount(e.target.value)}
                        required
                      />
                    </label>
                  )}

                  <label>
                    Decision Justification & Audit Notes *
                    <textarea
                      rows={4}
                      placeholder="Explain findings, evidence evaluated, and decision..."
                      value={disputeNotes}
                      onChange={(e) => setDisputeNotes(e.target.value)}
                      required
                    />
                  </label>

                  <div className="alert alert-info small">
                    Provider confirmation: Mock payment provider records transaction reference and updates auditable case history.
                  </div>

                  <div className="between">
                    <button type="button" className="btn btn-outline btn-small" onClick={() => setResolvingDispute(null)}>
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-small">
                      Finalize Decision
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ---------------- 5. Review Moderation Tab ---------------- */}
      {tab === "reviews" && (
        <div>
          <h3>Review Moderation & Trust Controls</h3>
          <p className="small muted">Inspect buyer reviews. Flag, hide, or restore reviews as appropriate.</p>

          {reviewsList.loading && <Loading text="Loading reviews..." />}
          {reviewsList.data?.map((r) => (
            <div key={r.id} className="card card-body" style={{ marginBottom: "0.75rem" }}>
              <div className="between wrap">
                <div>
                  <span className="stars">{"★".repeat(r.rating)}{"☆".repeat(5 - r.rating)}</span>
                  <strong style={{ marginLeft: "0.5rem" }}>{r.title}</strong>
                  <span className={`status status-${r.status}`} style={{ marginLeft: "0.5rem" }}>
                    {r.status}
                  </span>
                  <div className="small muted">
                    By {r.buyer?.name} on {r.product?.title || "Product"} · {r.created_at}
                  </div>
                </div>

                <div className="row" style={{ gap: "0.4rem" }}>
                  {r.status === "published" ? (
                    <button
                      type="button"
                      className="btn btn-small btn-danger"
                      onClick={() => handleModerateReview(r.id, "hidden_by_admin")}
                    >
                      Hide Review
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="btn btn-small"
                      style={{ background: "#15803d", borderColor: "#15803d" }}
                      onClick={() => handleModerateReview(r.id, "published")}
                    >
                      Publish Review
                    </button>
                  )}
                </div>
              </div>
              <p className="small pre" style={{ margin: "0.4rem 0" }}>{r.comment}</p>
            </div>
          ))}
        </div>
      )}

      {/* ---------------- 6. User Directory Tab ---------------- */}
      {tab === "users" && (
        <div>
          <h3>User Directory & Marketplace Roles</h3>
          <p className="small muted">List of registered buyers, artisans, and platform administrators.</p>

          {usersList.loading && <Loading text="Loading users..." />}
          <div className="grid">
            {usersList.data?.map((u) => (
              <div key={u.id} className="card card-body">
                <strong>{u.name}</strong>
                <div className="small muted">{u.email}</div>
                <div className="small" style={{ marginTop: "0.4rem" }}>
                  Role: <strong>{u.role.toUpperCase()}</strong>
                </div>
                {u.artisan_status && (
                  <div className="small">
                    Artisan Status: <span className={`status status-${u.artisan_status}`}>{u.artisan_status}</span>
                  </div>
                )}
                {u.trust_tier && (
                  <div style={{ marginTop: "0.3rem" }}>
                    <TrustTierBadge tier={u.trust_tier} />
                  </div>
                )}
                <div className="small muted" style={{ marginTop: "0.4rem" }}>
                  Orders: {u.order_count}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
