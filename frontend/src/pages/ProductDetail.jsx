import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, assetUrl } from "../api";
import MessageModal from "../components/MessageModal";
import ProductCard from "../components/ProductCard";
import { ErrorBox, Loading, Notice } from "../components/States";
import TrustTierBadge from "../components/TrustTierBadge";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { useFetch } from "../hooks";
import { useLang } from "../i18n";
import { formatINR } from "../utils";

export default function ProductDetail() {
  const { id } = useParams();
  const { t } = useLang();
  const { user } = useAuth();
  const cart = useCart();

  const { data: product, loading, error, reload } = useFetch(() => api.product(id), [id]);
  const similar = useFetch(() => api.similarRecommendations(id, 4), [id]);
  const reviewsData = useFetch(() => api.productReviews(id), [id]);

  const [qty, setQty] = useState(1);
  const [imgIndex, setImgIndex] = useState(0);
  const [added, setAdded] = useState(false);
  const [showMessageModal, setShowMessageModal] = useState(false);

  useEffect(() => {
    setQty(1);
    setImgIndex(0);
    setAdded(false);
  }, [id]);

  if (loading) return <Loading />;
  if (error)
    return (
      <div className="container section">
        <ErrorBox message={error} onRetry={reload} />
        <Link to="/shop">&larr; {t("nav.shop")}</Link>
      </div>
    );

  const canBuy = !user || user.role === "buyer";
  const maxQty = Math.min(product.stock, 10);
  const main = product.images[imgIndex] || product.images[0];
  const reviews = reviewsData.data?.reviews || [];
  const avgRating = reviewsData.data?.average_rating || 0;
  const totalReviews = reviewsData.data?.total_reviews || 0;
  const breakdown = reviewsData.data?.rating_breakdown || {};

  return (
    <div className="container section">
      <Link to="/shop">&larr; Back to Catalog</Link>

      <div className="detail">
        {/* Left: Product Images */}
        <div>
          <img className="detail-img" src={assetUrl(main && main.url)} alt={product.title} />
          {product.images.length > 1 && (
            <div className="thumbs">
              {product.images.map((im, i) => (
                <button
                  key={im.id}
                  className={i === imgIndex ? "thumb active" : "thumb"}
                  onClick={() => setImgIndex(i)}
                >
                  <img src={assetUrl(im.url)} alt={`${product.title} ${i + 1}`} />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Product Details & Purchase */}
        <div>
          <div className="between">
            <span className="muted small">{product.category}</span>
            {totalReviews > 0 && (
              <span className="small" style={{ color: "#d97706", fontWeight: 700 }}>
                ★ {avgRating} ({totalReviews} {totalReviews === 1 ? "review" : "reviews"})
              </span>
            )}
          </div>

          <h1>{product.title}</h1>
          <p className="price big">{formatINR(product.price)}</p>
          <p className="muted">
            {t("product.shipping")}: {formatINR(product.shipping_fee)} ·{" "}
            {product.stock > 0 ? `${product.stock} ${t("product.inStock")}` : t("product.soldOut")}
          </p>

          <p className="pre">{product.description}</p>

          {product.materials && (
            <p className="small">
              <strong>Artisanal Materials:</strong> {product.materials}
            </p>
          )}

          {product.tags && product.tags.length > 0 && (
            <div style={{ margin: "0.5rem 0" }}>
              {product.tags.map((tag, idx) => (
                <span key={idx} className="semantic-tag">#{tag}</span>
              ))}
            </div>
          )}

          {/* Artisan Card */}
          <div
            style={{
              background: "#fff",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              padding: "0.85rem 1rem",
              margin: "1rem 0",
            }}
          >
            <div className="between">
              <div>
                <span className="small muted">Handcrafted by</span>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.15rem" }}>
                  <Link to={`/artisan/${product.artisan?.id}`} style={{ fontWeight: 700, fontSize: "1.05rem" }}>
                    {product.artisan?.name}
                  </Link>
                  {product.artisan?.trust_tier && (
                    <TrustTierBadge tier={product.artisan.trust_tier} />
                  )}
                </div>
                <div className="muted small">
                  {product.artisan?.craft} · {product.artisan?.city}, {product.artisan?.state}
                </div>
              </div>

              {user?.id !== product.artisan?.id && (
                <button
                  type="button"
                  className="btn btn-outline btn-small"
                  onClick={() => setShowMessageModal(true)}
                >
                  💬 Message Artisan
                </button>
              )}
            </div>
          </div>

          {canBuy ? (
            <div className="row wrap">
              <label className="inline">
                {t("product.quantity")}
                <select
                  value={qty}
                  onChange={(e) => setQty(Number(e.target.value))}
                  disabled={product.stock === 0}
                >
                  {Array.from({ length: Math.max(maxQty, 1) }, (_, i) => i + 1).map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="btn"
                disabled={product.stock === 0}
                onClick={() => {
                  cart.add(product, qty);
                  setAdded(true);
                }}
              >
                {t("product.addToCart")}
              </button>
              {added && (
                <Link to="/cart" className="small" style={{ marginLeft: "0.5rem" }}>
                  Added to Cart! View Cart &rarr;
                </Link>
              )}
            </div>
          ) : (
            <Notice>{t("product.loginToBuy")}</Notice>
          )}
        </div>
      </div>

      {/* Customer Reviews Section */}
      <section className="section" style={{ marginTop: "2rem", borderTop: "1px solid var(--border)" }}>
        <div className="between" style={{ marginBottom: "1rem" }}>
          <div>
            <h2>Verified Customer Reviews</h2>
            <p className="muted small">Reviews submitted exclusively by verified buyers of this handmade craft.</p>
          </div>
          {totalReviews > 0 && (
            <div style={{ textAlign: "right" }}>
              <span style={{ fontSize: "1.8rem", fontWeight: 800, color: "#d97706" }}>★ {avgRating}</span>
              <div className="small muted">out of 5 stars ({totalReviews} verified reviews)</div>
            </div>
          )}
        </div>

        {totalReviews > 0 && (
          <div
            style={{
              maxWidth: "360px",
              background: "#fff",
              padding: "0.85rem 1rem",
              borderRadius: "var(--radius)",
              border: "1px solid var(--border)",
              marginBottom: "1.5rem",
            }}
          >
            {[5, 4, 3, 2, 1].map((star) => {
              const count = breakdown[star] || 0;
              const pct = totalReviews > 0 ? (count / totalReviews) * 100 : 0;
              return (
                <div key={star} className="rating-bar-row">
                  <span style={{ minWidth: "40px" }}>{star} ★</span>
                  <div className="rating-bar-bg">
                    <div className="rating-bar-fill" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="small muted" style={{ minWidth: "30px", textAlign: "right" }}>
                    {count}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {reviews.length === 0 ? (
          <div className="card card-body" style={{ textAlign: "center", color: "var(--muted)", padding: "2rem 1rem" }}>
            No reviews written for this product yet. Verified buyers can submit a review after purchasing!
          </div>
        ) : (
          <div style={{ display: "grid", gap: "1rem" }}>
            {reviews.map((r) => (
              <div key={r.id} className="card card-body">
                <div className="between">
                  <div>
                    <span className="stars">{"★".repeat(r.rating)}{"☆".repeat(5 - r.rating)}</span>
                    <strong style={{ marginLeft: "0.5rem", fontSize: "1rem" }}>{r.title}</strong>
                  </div>
                  <span className="small muted">
                    {new Date(r.created_at).toLocaleDateString("en-IN", { year: "numeric", month: "short", day: "numeric" })}
                  </span>
                </div>
                <div className="small" style={{ color: "#15803d", fontWeight: 600, margin: "0.2rem 0 0.4rem" }}>
                  ✓ Verified Buyer ({r.buyer?.name})
                </div>
                <p className="pre" style={{ margin: "0.3rem 0" }}>{r.comment}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Similar-Product Recommendations with Reason */}
      {similar.data?.items && similar.data.items.length > 0 && (
        <section className="section" style={{ marginTop: "1rem", borderTop: "1px solid var(--border)" }}>
          <div className="section-head">
            <div>
              <h2>Similar Handmade Products</h2>
              <p className="small muted">
                Recommendations matched on craft category, natural materials, and artisan technique.
              </p>
            </div>
          </div>
          <div className="grid">
            {similar.data.items.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}

      {/* Message Artisan Modal */}
      {showMessageModal && (
        <MessageModal
          artisan={product.artisan}
          product={product}
          onClose={() => setShowMessageModal(false)}
        />
      )}
    </div>
  );
}
