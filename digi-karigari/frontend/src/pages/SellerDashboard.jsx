import { useState } from "react";
import { Link } from "react-router-dom";
import { api, assetUrl } from "../api";
import { EmptyState, ErrorBox, Loading, Notice } from "../components/States";
import { VerifiedBadge } from "../components/Tag";
import { useAuth } from "../context/AuthContext";
import { useFetch } from "../hooks";
import { useLang } from "../i18n";
import { formatINR } from "../utils";
import { OrdersView } from "./Orders";

export default function SellerDashboard() {
  const { user } = useAuth();
  const { t } = useLang();
  const [tab, setTab] = useState("listings");
  const [actionError, setActionError] = useState("");
  const { data, loading, error, reload } = useFetch(() => api.myProducts(), []);

  const profile = user.artisan;
  const approved = profile?.status === "approved";

  const remove = async (p) => {
    if (!window.confirm(`Delete "${p.title}"? This cannot be undone.`)) return;
    setActionError("");
    try {
      await api.deleteProduct(p.id);
      reload();
    } catch (err) {
      setActionError(err.message);
    }
  };

  return (
    <div className="container section">
      <div className="between wrap">
        <h1>
          {t("seller.title")} <VerifiedBadge verified={approved} />
        </h1>
        {approved ? (
          <Link className="btn" to="/seller/new">
            {t("seller.newListing")}
          </Link>
        ) : (
          <button className="btn" disabled>
            {t("seller.newListing")}
          </button>
        )}
      </div>

      {profile?.status === "pending" && (
        <Notice kind="warn">Your account is waiting for admin approval. You can add listings once you are approved and get the Verified badge.</Notice>
      )}
      {profile?.status === "rejected" && (
        <Notice kind="error">Your application was rejected. Reason: {profile.reject_reason || "not given"}</Notice>
      )}

      <div className="tabs">
        <button className={tab === "listings" ? "tab active" : "tab"} onClick={() => setTab("listings")}>
          {t("seller.listingsTab")}
        </button>
        <button className={tab === "orders" ? "tab active" : "tab"} onClick={() => setTab("orders")}>
          {t("seller.ordersTab")}
        </button>
      </div>

      {tab === "orders" && <OrdersView />}

      {tab === "listings" && (
        <>
          <ErrorBox message={actionError} />
          {loading && <Loading />}
          <ErrorBox message={error} onRetry={reload} />
          {!loading && !error && data.length === 0 && (
            <EmptyState
              title={t("seller.noListings")}
              text={approved ? "" : "You can create listings after an admin approves your account."}
              actionTo={approved ? "/seller/new" : undefined}
              actionLabel={t("seller.newListing")}
            />
          )}
          {data &&
            data.map((p) => (
              <div key={p.id} className="card cart-row">
                <img src={assetUrl(p.image_url)} alt={p.title} />
                <div className="grow">
                  <Link to={`/product/${p.id}`}>
                    <strong>{p.title}</strong>
                  </Link>
                  <p className="muted small">
                    {p.category} · {formatINR(p.price)} · {t("listing.stock")}: {p.stock}
                  </p>
                </div>
                <div className="row">
                  {approved && (
                    <Link className="btn btn-small btn-outline" to={`/seller/edit/${p.id}`}>
                      {t("seller.edit")}
                    </Link>
                  )}
                  <button className="btn btn-small btn-danger" onClick={() => remove(p)}>
                    {t("seller.delete")}
                  </button>
                </div>
              </div>
            ))}
        </>
      )}
    </div>
  );
}
