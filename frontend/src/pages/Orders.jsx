import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, assetUrl } from "../api";
import DisputeModal from "../components/DisputeModal";
import ReviewModal from "../components/ReviewModal";
import { EmptyState, ErrorBox, Loading, Notice } from "../components/States";
import { useAuth } from "../context/AuthContext";
import { useFetch } from "../hooks";
import { useLang } from "../i18n";
import { formatDate, formatINR } from "../utils";

const NEXT = { placed: ["packed", "shipped"], packed: ["shipped"], shipped: ["delivered"], delivered: [] };

function ShipmentForm({ item, onDone }) {
  const { t } = useLang();
  const options = NEXT[item.status] || [];
  const [status, setStatus] = useState(options[0] || "");
  const [courier, setCourier] = useState(item.courier_name || "");
  const [tracking, setTracking] = useState(item.tracking_id || "");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (options.length === 0) return null;

  const submit = async (e) => {
    e.preventDefault();
    if ((status === "shipped" || status === "delivered") && (!courier.trim() || !tracking.trim())) {
      return setError("Enter the courier name and tracking ID before marking as shipped.");
    }
    if (!/^[A-Za-z0-9\-/ ]*$/.test(tracking)) {
      return setError("Tracking ID can only contain letters, numbers, spaces, - and /.");
    }
    setBusy(true);
    setError("");
    try {
      await api.updateItem(item.id, { status, courier_name: courier.trim(), tracking_id: tracking.trim() });
      onDone();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="ship-form" onSubmit={submit} style={{ marginTop: "0.5rem" }}>
      <ErrorBox message={error} />
      <div className="row wrap">
        <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label={t("seller.updateStatus")}>
          {options.map((s) => (
            <option key={s} value={s}>
              {t(`status.${s}`)}
            </option>
          ))}
        </select>
        <input placeholder={t("orders.courier")} value={courier} onChange={(e) => setCourier(e.target.value)} maxLength={60} />
        <input placeholder={t("orders.tracking")} value={tracking} onChange={(e) => setTracking(e.target.value)} maxLength={40} />
        <button className="btn btn-small" disabled={busy}>
          {t("seller.updateStatus")}
        </button>
      </div>
    </form>
  );
}

export function OrdersView({ placedId }) {
  const { user } = useAuth();
  const { t } = useLang();
  const { data, loading, error, reload } = useFetch(() => api.orders(), []);
  const [reviewItem, setReviewItem] = useState(null);
  const [disputeItem, setDisputeItem] = useState(null);
  const [selectedDispute, setSelectedDispute] = useState(null);

  const isBuyer = user?.role === "buyer";
  const isArtisan = user?.role === "artisan";

  if (loading) return <Loading text="Loading order history..." />;
  if (error) return <ErrorBox message={error} onRetry={reload} />;
  if (data.length === 0)
    return (
      <EmptyState
        title={isArtisan ? t("seller.noOrders") : t("orders.emptyTitle")}
        text={isArtisan ? "" : t("orders.emptyText")}
        actionTo={isArtisan ? undefined : "/shop"}
        actionLabel={t("home.cta")}
      />
    );

  return (
    <>
      {placedId && <Notice kind="success">Order #{placedId} placed successfully (simulated demo payment). Thank you!</Notice>}

      {data.map((o) => (
        <div key={o.id} className="card card-body order" style={{ marginBottom: "1.25rem" }}>
          <div className="between wrap">
            <div>
              <strong>Order #{o.id}</strong>
              <span className={`status status-${o.status}`} style={{ marginLeft: "0.5rem" }}>
                {t(`status.${o.status}`)}
              </span>
              {o.payment_status === "refunded_test" && (
                <span className="badge-tier" style={{ background: "#fee2e2", color: "#991b1b", marginLeft: "0.5rem" }}>
                  Refund Processed
                </span>
              )}
            </div>
            <span className="small muted">
              {t("orders.placedOn")} {formatDate(o.created_at)}
            </span>
          </div>

          <p className="small muted" style={{ margin: "0.3rem 0" }}>
            {o.payment_note}
          </p>

          {o.buyer && (
            <p className="small">
              {t("orders.customer")}: {o.buyer.name} · {o.shipping.name}, {o.shipping.address}, {o.shipping.city} {o.shipping.pincode} · {o.shipping.phone}
            </p>
          )}

          {o.items.map((i) => (
            <div key={i.id} className="order-item">
              <img src={assetUrl(i.image_url)} alt="" />
              <div className="grow">
                <div className="between">
                  <strong>{i.title} × {i.quantity}</strong>
                  <span className="price">{formatINR(i.line_total)}</span>
                </div>

                <p className="small muted" style={{ margin: "0.15rem 0" }}>
                  {t("common.by")} {i.artisan_name}
                </p>

                <div className="between wrap" style={{ marginTop: "0.25rem" }}>
                  <p className="small" style={{ margin: 0 }}>
                    Status: <span className={`status status-${i.status}`}>{t(`status.${i.status}`)}</span>
                    {i.courier_name && (
                      <span> · {t("orders.courier")}: {i.courier_name} · Track: {i.tracking_id}</span>
                    )}
                  </p>

                  {/* Actions for buyer */}
                  {isBuyer && (
                    <div className="row" style={{ gap: "0.4rem" }}>
                      {i.has_reviewed ? (
                        <span className="small" style={{ color: "#15803d", fontWeight: 600 }}>
                          ✓ Reviewed
                        </span>
                      ) : (
                        <button
                          type="button"
                          className="btn btn-outline btn-small"
                          onClick={() => setReviewItem({ ...i, order_id: o.id })}
                        >
                          ⭐ Write Review
                        </button>
                      )}

                      {i.has_dispute ? (
                        <button
                          type="button"
                          className="btn btn-outline btn-small"
                          style={{ borderColor: "#ea580c", color: "#c2410c" }}
                          onClick={async () => {
                            const d = await api.dispute(i.dispute_id);
                            setSelectedDispute(d);
                          }}
                        >
                          ⚠️ View Dispute
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="linklike small"
                          style={{ color: "#b45309" }}
                          onClick={() => setDisputeItem({ ...i, order_id: o.id })}
                        >
                          Need Help? Dispute
                        </button>
                      )}
                    </div>
                  )}
                </div>

                {isArtisan && <ShipmentForm item={i} onDone={reload} />}
              </div>
            </div>
          ))}

          <p className="between total" style={{ marginTop: "0.75rem", borderTop: "1px dashed var(--border)", paddingTop: "0.5rem" }}>
            <span>{t("cart.total")}</span> <span>{formatINR(o.total)}</span>
          </p>
        </div>
      ))}

      {/* Review Modal */}
      {reviewItem && (
        <ReviewModal
          item={reviewItem}
          onClose={() => setReviewItem(null)}
          onSuccess={reload}
        />
      )}

      {/* Dispute Modal */}
      {disputeItem && (
        <DisputeModal
          item={disputeItem}
          orderId={disputeItem.order_id}
          onClose={() => setDisputeItem(null)}
          onSuccess={reload}
        />
      )}

      {/* Dispute Details View Modal */}
      {selectedDispute && (
        <div className="modal-backdrop" onClick={() => setSelectedDispute(null)}>
          <div className="modal" style={{ width: "min(560px, 100%)", textAlign: "left" }} onClick={(e) => e.stopPropagation()}>
            <div className="between">
              <h3>Dispute Case #{selectedDispute.id}</h3>
              <span className={`status status-${selectedDispute.status}`}>
                {selectedDispute.status.replace("_", " ").toUpperCase()}
              </span>
            </div>

            <p className="small muted">
              Order #{selectedDispute.order_id} · Reason: <strong>{selectedDispute.reason}</strong>
            </p>

            <div className="card card-body" style={{ background: "#f8fafc", padding: "0.75rem", margin: "0.75rem 0" }}>
              <div className="small"><strong>Buyer Statement:</strong></div>
              <p className="small pre" style={{ margin: "0.2rem 0" }}>{selectedDispute.description}</p>
              <div className="small muted" style={{ marginTop: "0.4rem" }}>
                Requested: {selectedDispute.requested_resolution.replace("_", " ")} (₹{selectedDispute.requested_amount})
              </div>
            </div>

            {selectedDispute.resolution_decision && (
              <div className="alert alert-info small">
                <strong>Case Decision:</strong> {selectedDispute.resolution_decision.replace("_", " ").toUpperCase()}
                {selectedDispute.refunded_amount > 0 && (
                  <div>
                    Refund: ₹{selectedDispute.refunded_amount} (Ref: {selectedDispute.refund_reference})
                  </div>
                )}
              </div>
            )}

            <div style={{ marginTop: "1rem" }}>
              <strong>Case Timeline & Messages</strong>
              <div className="audit-timeline">
                {selectedDispute.messages?.map((m) => (
                  <div key={m.id} className="audit-node">
                    <strong>{m.sender_name} ({m.sender_role}):</strong> {m.message}
                    <div className="small muted">
                      {new Date(m.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ textAlign: "right", marginTop: "1rem" }}>
              <button type="button" className="btn btn-small" onClick={() => setSelectedDispute(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default function Orders() {
  const { t } = useLang();
  const location = useLocation();
  return (
    <div className="container section">
      <h1>{t("orders.title")}</h1>
      <OrdersView placedId={location.state?.placed} />
    </div>
  );
}
