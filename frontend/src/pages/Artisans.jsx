import { Link } from "react-router-dom";
import { api } from "../api";
import { EmptyState, ErrorBox, Loading } from "../components/States";
import { VerifiedBadge } from "../components/Tag";
import { useFetch } from "../hooks";
import { useLang } from "../i18n";

export default function Artisans() {
  const { t } = useLang();
  const { data, loading, error, reload } = useFetch(() => api.artisans(), []);
  return (
    <div className="container section">
      <h1>{t("artisans.title")}</h1>
      {loading && <Loading />}
      <ErrorBox message={error} onRetry={reload} />
      {!loading && !error && data.length === 0 && <EmptyState title="No verified artisans yet" text="An admin has to approve artisan accounts first." />}
      <div className="grid grid-3">
        {data &&
          data.map((a) => (
            <Link key={a.id} to={`/artisan/${a.id}`} className="card card-body artisan-card">
              <div className="avatar">{a.name[0]}</div>
              <h3>
                {a.name} <VerifiedBadge verified={a.verified} />
              </h3>
              <p className="muted">
                {a.craft} · {a.city}, {a.state}
              </p>
              <p className="small">
                {a.product_count} {t("artisans.products")}
              </p>
            </Link>
          ))}
      </div>
    </div>
  );
}
