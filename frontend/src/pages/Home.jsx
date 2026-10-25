import { Link } from "react-router-dom";
import { api } from "../api";
import ProductCard from "../components/ProductCard";
import { EmptyState, ErrorBox, Loading } from "../components/States";
import { VerifiedBadge } from "../components/Tag";
import { useFetch } from "../hooks";
import { useLang } from "../i18n";

export default function Home() {
  const { t } = useLang();
  const products = useFetch(() => api.products({ limit: 4 }), []);
  const artisans = useFetch(() => api.artisans(), []);

  return (
    <>
      <section className="hero">
        <div className="container">
          <h1>{t("home.title")}</h1>
          <p>{t("home.subtitle")}</p>
          <Link to="/shop" className="btn btn-light">
            {t("home.cta")}
          </Link>
        </div>
      </section>

      <section className="container section">
        <div className="section-head">
          <h2>{t("home.featured")}</h2>
          <Link to="/shop">{t("home.viewAll")}</Link>
        </div>
        {products.loading && <Loading />}
        <ErrorBox message={products.error} onRetry={products.reload} />
        {!products.loading && !products.error && products.data.length === 0 && (
          <EmptyState title={t("shop.emptyTitle")} text="Run the seed script to add sample products." />
        )}
        <div className="grid">{products.data && products.data.map((p) => <ProductCard key={p.id} product={p} />)}</div>
      </section>

      <section className="container section">
        <div className="section-head">
          <h2>{t("home.artisans")}</h2>
          <Link to="/artisans">{t("home.viewAll")}</Link>
        </div>
        {artisans.loading && <Loading />}
        <ErrorBox message={artisans.error} onRetry={artisans.reload} />
        <div className="grid grid-3">
          {artisans.data &&
            artisans.data.map((a) => (
              <Link key={a.id} to={`/artisan/${a.id}`} className="card card-body artisan-card">
                <div className="avatar">{a.name[0]}</div>
                <h3>
                  {a.name} <VerifiedBadge verified={a.verified} />
                </h3>
                <p className="muted">
                  {a.craft} · {a.city}
                </p>
              </Link>
            ))}
        </div>
      </section>
    </>
  );
}
