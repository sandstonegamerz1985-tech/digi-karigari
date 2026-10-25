import { useState } from "react";
import { api } from "../api";
import { EmptyState, ErrorBox, Loading } from "../components/States";
import { FeatureTag, VerifiedBadge } from "../components/Tag";
import { useFetch } from "../hooks";
import { useLang } from "../i18n";
import { formatINR } from "../utils";

export default function AdminPanel() {
  const { t } = useLang();
  const [status, setStatus] = useState("pending");
  const [actionError, setActionError] = useState("");
  const [rejecting, setRejecting] = useState(null); // user id we are writing a reason for
  const [reason, setReason] = useState("");

  const stats = useFetch(() => api.adminStats(), []);
  const list = useFetch(() => api.adminArtisans(status), [status]);

  const refresh = () => {
    list.reload();
    stats.reload();
  };

  const approve = async (a) => {
    setActionError("");
    try {
      await api.approveArtisan(a.id);
      refresh();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const reject = async (a) => {
    if (reason.trim().length < 3) return setActionError("Please write a short reason (at least 3 characters).");
    setActionError("");
    try {
      await api.rejectArtisan(a.id, reason.trim());
      setRejecting(null);
      setReason("");
      refresh();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const tabs = [
    ["pending", t("admin.pending")],
    ["approved", t("admin.approved")],
    ["rejected", t("admin.rejected")],
    ["all", t("admin.all")],
  ];

  return (
    <div className="container section">
      <h1>{t("admin.title")}</h1>

      {stats.data && (
        <>
          <div className="grid grid-4">
            {[
              ["Users", stats.data.users],
              ["Pending artisans", stats.data.pending_artisans],
              ["Products", stats.data.products],
              ["Orders", stats.data.orders],
            ].map(([label, value]) => (
              <div key={label} className="card card-body stat">
                <span className="muted small">{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
          <p className="small muted">
            <FeatureTag status="demo-only" /> Basic counts only (test sales so far: {formatINR(stats.data.test_sales_total)}). A full analytics dashboard is planned.
          </p>
        </>
      )}

      <div className="tabs">
        {tabs.map(([key, label]) => (
          <button key={key} className={status === key ? "tab active" : "tab"} onClick={() => setStatus(key)}>
            {label}
          </button>
        ))}
      </div>

      <ErrorBox message={actionError} />
      {list.loading && <Loading />}
      <ErrorBox message={list.error} onRetry={list.reload} />
      {!list.loading && !list.error && list.data.length === 0 && <EmptyState title={t("admin.none")} />}

      {list.data &&
        list.data.map((a) => (
          <div key={a.id} className="card card-body">
            <div className="between wrap">
              <div>
                <strong>{a.name}</strong> <VerifiedBadge verified={a.verified} />
                <span className={`status status-${a.status}`}>{a.status}</span>
                <p className="muted small">
                  {a.email} · {a.craft} · {a.city}, {a.state} · {a.product_count} products
                </p>
              </div>
              <div className="row">
                {a.status !== "approved" && (
                  <button className="btn btn-small" onClick={() => approve(a)}>
                    {t("admin.approve")}
                  </button>
                )}
                {a.status !== "rejected" && (
                  <button className="btn btn-small btn-danger" onClick={() => setRejecting(rejecting === a.id ? null : a.id)}>
                    {t("admin.reject")}
                  </button>
                )}
              </div>
            </div>
            <p className="pre small">{a.bio}</p>
            {a.reject_reason && <p className="small">Rejection reason: {a.reject_reason}</p>}
            {rejecting === a.id && (
              <div className="row wrap">
                <input className="grow" placeholder={t("admin.reason")} value={reason} onChange={(e) => setReason(e.target.value)} maxLength={300} />
                <button className="btn btn-small btn-danger" onClick={() => reject(a)}>
                  {t("admin.reject")}
                </button>
              </div>
            )}
          </div>
        ))}
    </div>
  );
}
