import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import ProductCard from "../components/ProductCard";
import { EmptyState, ErrorBox, Loading, Notice } from "../components/States";
import { useFetch } from "../hooks";
import { useLang } from "../i18n";

const EMPTY = { q: "", category: "", min_price: "", max_price: "", sort: "newest" };

export default function Catalog() {
  const { t } = useLang();
  const [params, setParams] = useSearchParams();
  const [form, setForm] = useState({ ...EMPTY, ...Object.fromEntries(params) });
  const [formError, setFormError] = useState("");

  const categories = useFetch(() => api.categories(), []);
  const { data, loading, error, reload } = useFetch(() => api.products(Object.fromEntries(params)), [params.toString()]);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    const min = form.min_price === "" ? null : Number(form.min_price);
    const max = form.max_price === "" ? null : Number(form.max_price);
    if ((min !== null && (!Number.isFinite(min) || min < 0)) || (max !== null && (!Number.isFinite(max) || max < 0))) {
      return setFormError("Prices must be zero or more.");
    }
    if (min !== null && max !== null && min > max) return setFormError("Min price cannot be higher than max price.");
    setFormError("");
    const next = {};
    Object.entries(form).forEach(([k, v]) => {
      if (v !== "" && !(k === "sort" && v === "newest")) next[k] = v;
    });
    setParams(next);
  };

  const clear = () => {
    setForm(EMPTY);
    setFormError("");
    setParams({});
  };

  return (
    <div className="container section">
      <h1>{t("shop.title")}</h1>
      <form className="filters card card-body" onSubmit={submit}>
        <label className="grow">
          {t("shop.search")}
          <input value={form.q} onChange={set("q")} placeholder={t("shop.searchPlaceholder")} maxLength={100} />
        </label>
        <label>
          {t("shop.category")}
          <select value={form.category} onChange={set("category")}>
            <option value="">{t("shop.allCategories")}</option>
            {(categories.data || []).map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("shop.minPrice")}
          <input type="number" min="0" value={form.min_price} onChange={set("min_price")} />
        </label>
        <label>
          {t("shop.maxPrice")}
          <input type="number" min="0" value={form.max_price} onChange={set("max_price")} />
        </label>
        <label>
          {t("shop.sort")}
          <select value={form.sort} onChange={set("sort")}>
            <option value="newest">{t("shop.sortNewest")}</option>
            <option value="price_asc">{t("shop.sortPriceLow")}</option>
            <option value="price_desc">{t("shop.sortPriceHigh")}</option>
          </select>
        </label>
        <div className="row">
          <button className="btn" type="submit">
            {t("shop.apply")}
          </button>
          <button className="btn btn-outline" type="button" onClick={clear}>
            {t("shop.clear")}
          </button>
        </div>
      </form>
      {formError && <Notice kind="error">{formError}</Notice>}

      {loading && <Loading />}
      <ErrorBox message={error} onRetry={reload} />
      {!loading && !error && data.length === 0 && <EmptyState title={t("shop.emptyTitle")} text={t("shop.emptyText")} />}
      <div className="grid">{data && data.map((p) => <ProductCard key={p.id} product={p} />)}</div>
    </div>
  );
}
