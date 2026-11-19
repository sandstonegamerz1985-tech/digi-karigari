import { Link } from "react-router-dom";
import { assetUrl } from "../api";
import { formatINR } from "../utils";
import TrustTierBadge from "./TrustTierBadge";
import { useLang } from "../i18n";

export default function ProductCard({ product }) {
  const { t } = useLang();
  return (
    <Link to={`/product/${product.id}`} className="card product-card">
      <div className="product-img">
        <img src={assetUrl(product.image_url)} alt={product.title} loading="lazy" />
        {product.stock === 0 && <span className="soldout">{t("product.soldOut")}</span>}
      </div>
      <div className="card-body">
        {product.recommendation_reason && (
          <div className="recommend-reason">{product.recommendation_reason}</div>
        )}
        <div className="between" style={{ marginBottom: "0.2rem" }}>
          <span className="muted small">{product.category}</span>
          {product.rating > 0 && (
            <span className="small" style={{ color: "#d97706", fontWeight: 700 }}>
              ★ {product.rating} {product.review_count ? `(${product.review_count})` : ""}
            </span>
          )}
        </div>

        <h3>{product.title}</h3>
        <p className="price">{formatINR(product.price)}</p>

        {product.semantic_highlights && product.semantic_highlights.length > 0 && (
          <div style={{ margin: "0.25rem 0" }}>
            {product.semantic_highlights.map((h, i) => (
              <span key={i} className="semantic-tag">{h}</span>
            ))}
          </div>
        )}

        <div className="small muted" style={{ display: "flex", alignItems: "center", gap: "0.35rem", flexWrap: "wrap", marginTop: "0.35rem" }}>
          <span>{t("common.by")} {product.artisan?.name}</span>
          {product.artisan?.trust_tier && (
            <TrustTierBadge tier={product.artisan.trust_tier} />
          )}
        </div>
      </div>
    </Link>
  );
}
