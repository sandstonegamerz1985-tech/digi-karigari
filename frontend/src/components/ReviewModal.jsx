import { useState } from "react";
import { api } from "../api";

export default function ReviewModal({ item, onClose, onSuccess }) {
  const [rating, setRating] = useState(5);
  const [hoverRating, setHoverRating] = useState(0);
  const [title, setTitle] = useState("");
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !comment.trim()) {
      setError("Please fill out both the review title and your comments.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await api.createReview({
        order_item_id: item.id,
        rating,
        title: title.trim(),
        comment: comment.trim(),
      });
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || "Failed to submit review.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" style={{ width: "min(520px, 100%)", textAlign: "left" }} onClick={(e) => e.stopPropagation()}>
        <h3>Write a Verified Review</h3>
        <p className="muted small" style={{ margin: "0 0 1rem" }}>
          For <strong>{item.title}</strong> (Order #{item.order_id || ""})
        </p>

        {error && <div className="alert alert-error small">{error}</div>}

        <form onSubmit={handleSubmit} className="form">
          <div>
            <label style={{ marginBottom: "0.3rem" }}>Rating</label>
            <div className="stars" style={{ gap: "0.25rem" }}>
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  type="button"
                  key={star}
                  className={`star-btn ${(hoverRating || rating) >= star ? "active" : ""}`}
                  onMouseEnter={() => setHoverRating(star)}
                  onMouseLeave={() => setHoverRating(0)}
                  onClick={() => setRating(star)}
                  aria-label={`${star} star`}
                >
                  ★
                </button>
              ))}
              <span className="small muted" style={{ marginLeft: "0.5rem" }}>
                {rating === 5 && "Excellent"}
                {rating === 4 && "Very Good"}
                {rating === 3 && "Average"}
                {rating === 2 && "Below Average"}
                {rating === 1 && "Poor"}
              </span>
            </div>
          </div>

          <label>
            Review Headline
            <input
              type="text"
              placeholder="e.g. Beautiful artisanal craftsmanship, arrived safe"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={120}
              required
            />
          </label>

          <label>
            Detailed Feedback
            <textarea
              rows={4}
              placeholder="Describe the quality, texture, material finish, and delivery of this handmade item..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              maxLength={1000}
              required
            />
          </label>

          <div className="between" style={{ marginTop: "1rem" }}>
            <button type="button" className="btn btn-outline btn-small" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-small" disabled={submitting}>
              {submitting ? "Submitting..." : "Submit Verified Review"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
