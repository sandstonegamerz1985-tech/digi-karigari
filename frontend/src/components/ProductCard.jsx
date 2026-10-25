import { Link } from "react-router-dom";
import { assetUrl } from "../api";
import { formatINR } from "../utils";
import { VerifiedBadge } from "./Tag";
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
        <span className="muted small">{product.category}</span>
        <h3>{product.title}</h3>
        <p className="price">{formatINR(product.price)}</p>
        <p className="small muted">
          {t("common.by")} {product.artisan.name} <VerifiedBadge verified={product.artisan.verified} />
        </p>
      </div>
    </Link>
  );
}
