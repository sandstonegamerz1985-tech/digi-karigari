import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import ProductCard from "../components/ProductCard";
import { EmptyState, ErrorBox, Loading } from "../components/States";
import { VerifiedBadge } from "../components/Tag";
import { useFetch } from "../hooks";
import { useLang } from "../i18n";

export default function ArtisanProfile() {
  const { id } = useParams();
  const { t } = useLang();
  const { data: a, loading, error, reload } = useFetch(() => api.artisan(id), [id]);

  if (loading) return <Loading />;
  if (error)
    return (
      <div className="container section">
        <ErrorBox message={error} onRetry={reload} />
        <Link to="/artisans">&larr; {t("nav.artisans")}</Link>
      </div>
    );

  return (
    <div className="container section">
      <Link to="/artisans">&larr; {t("nav.artisans")}</Link>
      <div className="profile-head">
        <div className="avatar avatar-lg">{a.name[0]}</div>
        <div>
          <h1>
            {a.name} <VerifiedBadge verified={a.verified} />
          </h1>
          <p className="muted">
            {a.craft} · {a.city}, {a.state}
          </p>
          <p className="pre">{a.bio}</p>
        </div>
      </div>
      <h2>
        {t("artisans.listingsBy")} {a.name}
      </h2>
      {a.products.length === 0 && <EmptyState title="No listings yet" />}
      <div className="grid">
        {a.products.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </div>
  );
}
