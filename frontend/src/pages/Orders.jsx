import { useState } from "react";
import { useLocation } from "react-router-dom";
import { api, assetUrl } from "../api";
import { EmptyState, ErrorBox, Loading, Notice } from "../components/States";
import { useAuth } from "../context/AuthContext";
import { useFetch } from "../hooks";
import { useLang } from "../i18n";
import { formatDate, formatINR } from "../utils";

// What the next status can be, for the artisan's update form.
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
    if (!/^[A-Za-z0-9\-/ ]*$/.test(tracking)) return setError("Tracking ID can only contain letters, numbers, spaces, - and /.");
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
    <form className="ship-form" onSubmit={submit}>
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

// Shows a list of orders. Buyers see their own, artisans see orders with their items, admins see all.
export function OrdersView({ placedId }) {
  const { user } = useAuth();
  const { t } = useLang();
  const { data, loading, error, reload } = useFetch(() => api.orders(), []);
  const isArtisan = user.role === "artisan";

  if (loading) return <Loading />;
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
      {placedId && <Notice kind="success">Order #{placedId} placed (test payment). Thank you!</Notice>}
      {data.map((o) => (
        <div key={o.id} className="card card-body order">
          <div className="between wrap">
            <strong>Order #{o.id}</strong>
            <span className={`status status-${o.status}`}>{t(`status.${o.status}`)}</span>
          </div>
          <p className="small muted">
            {t("orders.placedOn")} {formatDate(o.created_at)} · {o.payment_note}
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
                <strong>{i.title}</strong> × {i.quantity}
                <p className="small muted">
                  {t("common.by")} {i.artisan_name} · {formatINR(i.price * i.quantity)} + {t("product.shipping")} {formatINR(i.shipping_fee)}
                </p>
                <p className="small">
                  <span className={`status status-${i.status}`}>{t(`status.${i.status}`)}</span>
                  {i.courier_name && (
                    <>
                      {" "}
                      · {t("orders.courier")}: {i.courier_name} · {t("orders.tracking")}: {i.tracking_id}
                    </>
                  )}
                </p>
                {isArtisan && <ShipmentForm item={i} onDone={reload} />}
              </div>
            </div>
          ))}
          <p className="between total">
            <span>{t("cart.total")}</span> <span>{formatINR(o.total)}</span>
          </p>
        </div>
      ))}
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
