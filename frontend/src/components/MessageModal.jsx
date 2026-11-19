import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function MessageModal({ artisan, product, onClose }) {
  const navigate = useNavigate();
  const [subject, setSubject] = useState(product ? `Inquiry regarding ${product.title}` : `Inquiry for ${artisan.name}`);
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) {
      setError("Please write a message to start the conversation.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const convo = await api.startConversation({
        artisan_id: artisan.id,
        product_id: product ? product.id : null,
        subject: subject.trim(),
        initial_message: message.trim(),
      });
      onClose();
      navigate(`/messages?convo=${convo.id}`);
    } catch (err) {
      setError(err.message || "Failed to send message.");
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" style={{ width: "min(500px, 100%)", textAlign: "left" }} onClick={(e) => e.stopPropagation()}>
        <h3>Send Message to {artisan.name}</h3>
        {product && (
          <p className="muted small" style={{ margin: "0.2rem 0 1rem" }}>
            Regarding: <strong>{product.title}</strong> (₹{product.price.toLocaleString("en-IN")})
          </p>
        )}

        {error && <div className="alert alert-error small">{error}</div>}

        <form onSubmit={handleSubmit} className="form">
          <label>
            Subject
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              maxLength={140}
              required
            />
          </label>

          <label>
            Your Message
            <textarea
              rows={4}
              placeholder="Ask about dimensions, materials, care instructions, or customization..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              required
            />
          </label>

          <div className="between" style={{ marginTop: "0.75rem" }}>
            <button type="button" className="btn btn-outline btn-small" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-small" disabled={submitting}>
              {submitting ? "Sending..." : "Send Message"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
