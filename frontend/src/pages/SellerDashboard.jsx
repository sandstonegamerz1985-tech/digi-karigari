import { useState } from "react";
import { Link } from "react-router-dom";
import { api, assetUrl } from "../api";
import { EmptyState, ErrorBox, Loading, Notice } from "../components/States";
import TrustTierBadge from "../components/TrustTierBadge";
import { useAuth } from "../context/AuthContext";
import { useFetch } from "../hooks";
import { useLang } from "../i18n";
import { formatINR } from "../utils";
import { OrdersView } from "./Orders";

export default function SellerDashboard() {
  const { user } = useAuth();
  const { t } = useLang();
  const [tab, setTab] = useState("listings");
  const [actionError, setActionError] = useState("");
  const { data, loading, error, reload } = useFetch(() => api.myProducts(), []);
  const trustData = useFetch(() => api.artisanTrustTier(user.id), [user.id]);
  const disputesData = useFetch(() => api.disputes(), []);

  const [activeDispute, setActiveDispute] = useState(null);
  const [disputeReplyText, setDisputeReplyText] = useState("");
  const [sendingReply, setSendingReply] = useState(false);

  const profile = user.artisan;
  const approved = profile?.status === "approved";
  const tierInfo = trustData.data;

  const remove = async (p) => {
    if (!window.confirm(`Delete "${p.title}"? This cannot be undone.`)) return;
    setActionError("");
    try {
      await api.deleteProduct(p.id);
      reload();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const handleSendDisputeReply = async (e) => {
    e.preventDefault();
    if (!disputeReplyText.trim() || !activeDispute) return;
    setSendingReply(true);
    try {
      const updated = await api.sendDisputeMessage(activeDispute.id, disputeReplyText.trim());
      setActiveDispute(updated);
      setDisputeReplyText("");
      disputesData.reload();
    } catch (err) {
      alert(err.message || "Failed to send dispute reply.");
    } finally {
      setSendingReply(false);
    }
  };

  return (
    <div className="container section">
      <div className="between wrap">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <h1>{t("seller.title")}</h1>
          {tierInfo?.current_tier && <TrustTierBadge tier={tierInfo.current_tier} />}
        </div>
        {approved ? (
          <Link className="btn" to="/seller/new">
            {t("seller.newListing")}
          </Link>
        ) : (
          <button className="btn" disabled>
            {t("seller.newListing")}
          </button>
        )}
      </div>

      {profile?.status === "pending" && (
        <Notice kind="warn">
          Your artisan application is currently pending admin review. You can create listings once verified.
        </Notice>
      )}
      {profile?.status === "rejected" && (
        <Notice kind="error">Your application was rejected. Reason: {profile.reject_reason || "not specified"}</Notice>
      )}

      {/* Trust Tier Card */}
      {tierInfo && (
        <div className="card card-body" style={{ background: "#f8fafc", border: "1px solid #cbd5e1", margin: "1rem 0" }}>
          <div className="between wrap">
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <span style={{ fontSize: "1.4rem" }}>{tierInfo.badge.split(" ")[0]}</span>
                <strong style={{ fontSize: "1.1rem" }}>{tierInfo.tier_name}</strong>
                <span className="small muted">· Level {tierInfo.level} of 4</span>
              </div>
              <p className="small muted" style={{ margin: "0.2rem 0" }}>{tierInfo.description}</p>
            </div>

            {tierInfo.next_tier && (
              <div style={{ textAlign: "right" }}>
                <span className="small muted">Next Tier:</span>{" "}
                <strong>{tierInfo.next_tier.name}</strong>
              </div>
            )}
          </div>

          <div className="grid-3" style={{ gap: "0.75rem", marginTop: "0.75rem" }}>
            <div className="card card-body" style={{ background: "#fff", padding: "0.6rem" }}>
              <span className="small muted">Completed Orders:</span>{" "}
              <strong>{tierInfo.metrics?.completed_orders || 0}</strong>
            </div>
            <div className="card card-body" style={{ background: "#fff", padding: "0.6rem" }}>
              <span className="small muted">Avg Rating:</span>{" "}
              <strong style={{ color: "#d97706" }}>★ {tierInfo.metrics?.average_rating || "0.0"}</strong>
            </div>
            <div className="card card-body" style={{ background: "#fff", padding: "0.6rem" }}>
              <span className="small muted">Dispute Rate:</span>{" "}
              <strong>{tierInfo.metrics?.dispute_rate || 0}%</strong>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="tabs">
        <button className={tab === "listings" ? "tab active" : "tab"} onClick={() => setTab("listings")}>
          {t("seller.listingsTab")} ({data?.length || 0})
        </button>
        <button className={tab === "orders" ? "tab active" : "tab"} onClick={() => setTab("orders")}>
          {t("seller.ordersTab")}
        </button>
        <button className={tab === "disputes" ? "tab active" : "tab"} onClick={() => setTab("disputes")}>
          Disputes & Help Cases ({disputesData.data?.length || 0})
        </button>
      </div>

      {tab === "orders" && <OrdersView />}

      {tab === "disputes" && (
        <div>
          {disputesData.loading && <Loading text="Loading disputes..." />}
          {disputesData.data?.length === 0 && (
            <EmptyState
              title="No customer disputes"
              text="You have no open dispute cases from buyers. Keep up the high standard of craftsmanship and fulfillment!"
            />
          )}

          {disputesData.data?.map((d) => (
            <div key={d.id} className="card card-body" style={{ marginBottom: "1rem" }}>
              <div className="between">
                <div>
                  <strong>Case #{d.id}: {d.reason}</strong>
                  <div className="small muted">
                    Order #{d.order_id} · Buyer: {d.buyer?.name} ({d.buyer?.email})
                  </div>
                </div>
                <span className={`status status-${d.status}`}>
                  {d.status.replace("_", " ").toUpperCase()}
                </span>
              </div>

              <p className="pre small" style={{ margin: "0.5rem 0", background: "#fdf8f6", padding: "0.5rem", borderRadius: "6px" }}>
                {d.description}
              </p>

              <div className="between">
                <span className="small muted">
                  Requested: {d.requested_resolution.replace("_", " ")} (₹{d.requested_amount})
                </span>
                <button
                  type="button"
                  className="btn btn-outline btn-small"
                  onClick={() => setActiveDispute(d)}
                >
                  View Case & Reply
                </button>
              </div>
            </div>
          ))}

          {/* Dispute Reply Modal */}
          {activeDispute && (
            <div className="modal-backdrop" onClick={() => setActiveDispute(null)}>
              <div className="modal" style={{ width: "min(560px, 100%)", textAlign: "left" }} onClick={(e) => e.stopPropagation()}>
                <div className="between">
                  <h3>Customer Dispute #{activeDispute.id}</h3>
                  <button className="linklike small" onClick={() => setActiveDispute(null)}>✕</button>
                </div>
                <p className="small muted">{activeDispute.reason} · Buyer: {activeDispute.buyer?.name}</p>

                <div className="card card-body" style={{ background: "#f8fafc", padding: "0.75rem", margin: "0.5rem 0" }}>
                  <strong>Buyer Claim:</strong>
                  <p className="small pre" style={{ margin: "0.2rem 0" }}>{activeDispute.description}</p>
                </div>

                <div style={{ marginTop: "1rem" }}>
                  <strong>Messages & Timeline</strong>
                  <div className="audit-timeline" style={{ maxHeight: "200px", overflowY: "auto" }}>
                    {activeDispute.messages?.map((m) => (
                      <div key={m.id} className="audit-node">
                        <strong>{m.sender_name} ({m.sender_role}):</strong> {m.message}
                        <div className="small muted">
                          {new Date(m.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <form onSubmit={handleSendDisputeReply} style={{ marginTop: "1rem" }}>
                  <label>
                    Respond to Buyer & Admin
                    <textarea
                      rows={3}
                      placeholder="Explain the situation or offer a resolution to the customer..."
                      value={disputeReplyText}
                      onChange={(e) => setDisputeReplyText(e.target.value)}
                      required
                    />
                  </label>
                  <div className="between" style={{ marginTop: "0.5rem" }}>
                    <button type="button" className="btn btn-outline btn-small" onClick={() => setActiveDispute(null)}>
                      Close
                    </button>
                    <button type="submit" className="btn btn-small" disabled={sendingReply || !disputeReplyText.trim()}>
                      {sendingReply ? "Sending..." : "Send Response"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === "listings" && (
        <>
          <ErrorBox message={actionError} />
          {loading && <Loading />}
          <ErrorBox message={error} onRetry={reload} />
          {!loading && !error && data?.length === 0 && (
            <EmptyState
              title={t("seller.noListings")}
              text={approved ? "" : "You can create listings after an admin approves your account."}
              actionTo={approved ? "/seller/new" : undefined}
              actionLabel={t("seller.newListing")}
            />
          )}
          {data &&
            data.map((p) => (
              <div key={p.id} className="card cart-row">
                <img src={assetUrl(p.image_url)} alt={p.title} />
                <div className="grow">
                  <div className="between">
                    <Link to={`/product/${p.id}`}>
                      <strong>{p.title}</strong>
                    </Link>
                    <span className={`status status-${p.status || "approved"}`}>
                      {p.status === "pending_review" ? "Pending Review" : p.status ? p.status.toUpperCase() : "LIVE"}
                    </span>
                  </div>

                  <p className="muted small">
                    {p.category} · {formatINR(p.price)} · {t("listing.stock")}: {p.stock}
                  </p>

                  {p.materials && (
                    <div className="small muted">Materials: {p.materials}</div>
                  )}

                  {p.status === "pending_review" && (
                    <div className="small" style={{ color: "#b45309", marginTop: "0.2rem" }}>
                      ⏳ Submitted for admin quality review. Live in shop once approved.
                    </div>
                  )}
                  {p.status === "rejected" && (
                    <div className="small" style={{ color: "#b91c1c", marginTop: "0.2rem" }}>
                      Feedback: {p.reject_reason || "Admin requested revisions."}
                    </div>
                  )}
                </div>
                <div className="row">
                  {approved && (
                    <Link className="btn btn-small btn-outline" to={`/seller/edit/${p.id}`}>
                      {t("seller.edit")}
                    </Link>
                  )}
                  <button className="btn btn-small btn-danger" onClick={() => remove(p)}>
                    {t("seller.delete")}
                  </button>
                </div>
              </div>
            ))}
        </>
      )}
    </div>
  );
}
