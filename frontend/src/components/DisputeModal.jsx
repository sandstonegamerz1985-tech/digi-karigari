import { useState } from "react";
import { api } from "../api";

export default function DisputeModal({ item, orderId, onClose, onSuccess }) {
  const [reason, setReason] = useState("Damaged in transit");
  const [description, setDescription] = useState("");
  const [resolution, setResolution] = useState("full_refund");
  const [amount, setAmount] = useState(item ? item.line_total || item.price : 0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!description.trim() || description.length < 10) {
      setError("Please provide at least 10 characters explaining the issue.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await api.openDispute({
        order_id: orderId,
        order_item_id: item ? item.id : null,
        reason,
        description: description.trim(),
        requested_resolution: resolution,
        requested_amount: parseInt(amount, 10) || 0,
      });
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || "Failed to submit dispute.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" style={{ width: "min(540px, 100%)", textAlign: "left" }} onClick={(e) => e.stopPropagation()}>
        <h3>Open an Order Dispute / Request Help</h3>
        <p className="muted small" style={{ margin: "0 0 1rem" }}>
          Order #{orderId} {item ? `· Item: ${item.title}` : ""}
        </p>

        {error && <div className="alert alert-error small">{error}</div>}

        <div className="alert alert-info small" style={{ marginBottom: "1rem" }}>
          🛡️ Our marketplace dispute resolution process ensures fair review between buyers and artisans. Admins review claims and audit logs before decisions are finalized.
        </div>

        <form onSubmit={handleSubmit} className="form">
          <label>
            Dispute Reason
            <select value={reason} onChange={(e) => setReason(e.target.value)}>
              <option value="Damaged in transit">Damaged in transit (Broken/chipped/torn)</option>
              <option value="Item not received">Item not received (Courier tracking issue)</option>
              <option value="Significantly different from listing">Significantly different from listing / description</option>
              <option value="Wrong item delivered">Wrong item received</option>
              <option value="Quality or craft defect">Material or workmanship defect</option>
            </select>
          </label>

          <label>
            Requested Resolution
            <select
              value={resolution}
              onChange={(e) => {
                setResolution(e.target.value);
                if (e.target.value === "full_refund" && item) {
                  setAmount(item.line_total || item.price);
                }
              }}
            >
              <option value="full_refund">Full Refund</option>
              <option value="partial_refund">Partial Refund (e.g. keeping item with compensation)</option>
              <option value="replacement">Artisan Replacement</option>
            </select>
          </label>

          {(resolution === "full_refund" || resolution === "partial_refund") && (
            <label>
              Requested Refund Amount (₹)
              <input
                type="number"
                min={1}
                max={item ? item.line_total || item.price : 50000}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
            </label>
          )}

          <label>
            Problem Description & Evidence
            <textarea
              rows={4}
              placeholder="Describe what occurred, any packaging damage, or differences observed..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
            />
          </label>

          <p className="muted small">
            * Note: Payments and refunds in this demonstration use a verified mock payment gateway.
          </p>

          <div className="between" style={{ marginTop: "0.5rem" }}>
            <button type="button" className="btn btn-outline btn-small" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-small" disabled={submitting}>
              {submitting ? "Opening Case..." : "File Dispute"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
