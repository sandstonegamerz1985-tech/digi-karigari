import { Link, useNavigate } from "react-router-dom";
import { assetUrl } from "../api";
import { EmptyState, Notice } from "../components/States";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { useLang } from "../i18n";
import { formatINR } from "../utils";

export default function Cart() {
  const { t } = useLang();
  const { user } = useAuth();
  const cart = useCart();
  const navigate = useNavigate();

  if (cart.items.length === 0)
    return (
      <div className="container section">
        <h1>{t("cart.title")}</h1>
        <EmptyState title={t("cart.emptyTitle")} text={t("cart.emptyText")} actionTo="/shop" actionLabel={t("home.cta")} />
      </div>
    );

  const canCheckout = !user || user.role === "buyer";

  return (
    <div className="container section">
      <h1>{t("cart.title")}</h1>
      <div className="cart-layout">
        <div>
          {cart.items.map((i) => (
            <div key={i.product_id} className="card cart-row">
              <img src={assetUrl(i.image_url)} alt={i.title} />
              <div className="grow">
                <Link to={`/product/${i.product_id}`}>
                  <strong>{i.title}</strong>
                </Link>
                <p className="muted small">
                  {formatINR(i.price)} · {t("product.shipping")} {formatINR(i.shipping_fee)}
                </p>
                <div className="row">
                  <select
                    aria-label={t("product.quantity")}
                    value={i.quantity}
                    onChange={(e) => cart.setQuantity(i.product_id, Number(e.target.value))}
                  >
                    {Array.from({ length: Math.max(Math.min(i.stock, 10), 1) }, (_, n) => n + 1).map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                  <button className="linklike" onClick={() => cart.remove(i.product_id)}>
                    {t("cart.remove")}
                  </button>
                </div>
              </div>
              <strong>{formatINR(i.price * i.quantity)}</strong>
            </div>
          ))}
        </div>

        <aside className="card card-body summary">
          <p className="between">
            <span>{t("cart.subtotal")}</span> <span>{formatINR(cart.subtotal)}</span>
          </p>
          <p className="between">
            <span>{t("cart.shipping")}</span> <span>{formatINR(cart.shipping)}</span>
          </p>
          <p className="between total">
            <span>{t("cart.total")}</span> <span>{formatINR(cart.total)}</span>
          </p>
          <p className="small muted">{t("cart.estimate")}</p>
          {canCheckout ? (
            <button className="btn" onClick={() => navigate("/checkout")}>
              {t("cart.checkout")}
            </button>
          ) : (
            <Notice kind="error">Only buyer accounts can place orders. Log in as a buyer.</Notice>
          )}
        </aside>
      </div>
    </div>
  );
}
