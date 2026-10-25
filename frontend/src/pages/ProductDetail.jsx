import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, assetUrl } from "../api";
import ProductCard from "../components/ProductCard";
import { ErrorBox, Loading, Notice } from "../components/States";
import { FeatureTag, VerifiedBadge } from "../components/Tag";
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
  const similar = useFetch(() => api.similar(id), [id]);
  const [qty, setQty] = useState(1);
  const [imgIndex, setImgIndex] = useState(0);
  const [added, setAdded] = useState(false);

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

  return (
    <div className="container section">
      <Link to="/shop">&larr; {t("nav.shop")}</Link>
      <div className="detail">
        <div>
          <img className="detail-img" src={assetUrl(main && main.url)} alt={product.title} />
          {product.images.length > 1 && (
            <div className="thumbs">
              {product.images.map((im, i) => (
                <button key={im.id} className={i === imgIndex ? "thumb active" : "thumb"} onClick={() => setImgIndex(i)}>
                  <img src={assetUrl(im.url)} alt={`${product.title} ${i + 1}`} />
                </button>
              ))}
            </div>
          )}
        </div>
        <div>
          <span className="muted small">{product.category}</span>
          <h1>{product.title}</h1>
          <p className="price big">{formatINR(product.price)}</p>
          <p className="muted">
            {t("product.shipping")}: {formatINR(product.shipping_fee)} ·{" "}
            {product.stock > 0 ? `${product.stock} ${t("product.inStock")}` : t("product.soldOut")}
          </p>
          <p className="pre">{product.description}</p>
          {product.ai_assisted && (
            <p className="small muted">
              <FeatureTag status="demo-only" /> The artisan used the AI assistant and reviewed this text.
            </p>
          )}

          <p>
            {t("product.soldBy")}{" "}
            <Link to={`/artisan/${product.artisan.id}`}>
              <strong>{product.artisan.name}</strong>
            </Link>{" "}
            <VerifiedBadge verified={product.artisan.verified} />
            <br />
            <span className="muted small">
              {product.artisan.craft} · {product.artisan.city}
            </span>
          </p>

          {canBuy ? (
            <div className="row">
              <label className="inline">
                {t("product.quantity")}
                <select value={qty} onChange={(e) => setQty(Number(e.target.value))} disabled={product.stock === 0}>
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
                <Link to="/cart" className="small">
                  {t("product.added")} {t("nav.cart")} &rarr;
                </Link>
              )}
            </div>
          ) : (
            <Notice>{t("product.loginToBuy")}</Notice>
          )}
        </div>
      </div>

      {similar.data && similar.data.items.length > 0 && (
        <section className="section">
          <h2>{t("product.similar")}</h2>
          <p className="small muted">
            <FeatureTag status="demo-only" /> Currently just products from the same category. Smarter recommendations are planned.
          </p>
          <div className="grid">
            {similar.data.items.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
