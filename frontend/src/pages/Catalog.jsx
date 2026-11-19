import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import ProductCard from "../components/ProductCard";
import { EmptyState, ErrorBox, Loading } from "../components/States";
import { useFetch } from "../hooks";

const EMPTY = {
  q: "",
  category: "",
  min_price: "",
  max_price: "",
  location: "",
  material: "",
  in_stock: false,
  trust_tier: "",
  sort: "relevance",
};

export default function Catalog() {
  const [params, setParams] = useSearchParams();
  const [form, setForm] = useState({
    ...EMPTY,
    ...Object.fromEntries(params),
    in_stock: params.get("in_stock") === "true",
  });
  const [formError, setFormError] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  // Suggested searches
  const { data: suggestionsData } = useFetch(() => api.searchSuggestions(), []);
  const categories = useFetch(() => api.categories(), []);

  // Fetch search results using semantic search
  const { data, loading, error, reload } = useFetch(
    () =>
      api.searchSemantic({
        q: params.get("q") || undefined,
        category: params.get("category") || undefined,
        min_price: params.get("min_price") ? Number(params.get("min_price")) : undefined,
        max_price: params.get("max_price") ? Number(params.get("max_price")) : undefined,
        location: params.get("location") || undefined,
        material: params.get("material") || undefined,
        in_stock: params.get("in_stock") === "true" || undefined,
        trust_tier: params.get("trust_tier") || undefined,
        sort: params.get("sort") || "relevance",
      }),
    [params.toString()]
  );

  const applySearch = (override = {}) => {
    const updated = { ...form, ...override };
    const min = updated.min_price === "" ? null : Number(updated.min_price);
    const max = updated.max_price === "" ? null : Number(updated.max_price);
    if ((min !== null && (!Number.isFinite(min) || min < 0)) || (max !== null && (!Number.isFinite(max) || max < 0))) {
      return setFormError("Prices must be 0 or more.");
    }
    if (min !== null && max !== null && min > max) {
      return setFormError("Min price cannot exceed max price.");
    }
    setFormError("");

    const next = {};
    Object.entries(updated).forEach(([k, v]) => {
      if (k === "in_stock" && v) next[k] = "true";
      else if (v !== "" && v !== false && !(k === "sort" && v === "relevance")) next[k] = v;
    });
    setParams(next);
  };

  const submit = (e) => {
    e.preventDefault();
    applySearch();
  };

  const handleSuggestionClick = (queryText) => {
    setForm((prev) => ({ ...prev, q: queryText }));
    applySearch({ q: queryText });
  };

  const clear = () => {
    setForm(EMPTY);
    setFormError("");
    setParams({});
  };

  const items = data?.items || [];
  const detectedIntent = data?.detected_intent;

  return (
    <div className="container section">
      <div className="section-head" style={{ marginBottom: "0.5rem" }}>
        <div>
          <h1>Artisanal Marketplace</h1>
          <p className="muted small">
            Discover authentic handcrafted goods from master artisans across India. Search by natural descriptions, style, material, or occasion.
          </p>
        </div>
      </div>

      {/* Semantic Search Input Bar */}
      <form onSubmit={submit} className="search-bar-wrap">
        <span className="search-icon-inside">🔍</span>
        <input
          type="text"
          className="search-input-lg"
          placeholder="Search by meaning, style, use, or occasion... (e.g. 'brass diya for pooja', 'light blue pottery planter', 'chikankari cotton')"
          value={form.q}
          onChange={(e) => setForm({ ...form, q: e.target.value })}
          maxLength={150}
        />
        {form.q && (
          <button
            type="button"
            className="search-clear-btn"
            onClick={() => {
              setForm({ ...form, q: "" });
              applySearch({ q: "" });
            }}
          >
            ✕
          </button>
        )}
      </form>

      {/* Suggested Searches */}
      {suggestionsData?.suggestions && (
        <div className="pill-container">
          <span className="small muted" style={{ alignSelf: "center", marginRight: "0.25rem" }}>
            Try searching:
          </span>
          {suggestionsData.suggestions.slice(0, 5).map((s, idx) => (
            <button
              key={idx}
              type="button"
              className={`search-pill ${form.q === s.query ? "active" : ""}`}
              onClick={() => handleSuggestionClick(s.query)}
            >
              <span>✨</span> {s.query}
            </button>
          ))}
        </div>
      )}

      {/* Semantic Intent Breakdown */}
      {detectedIntent && (detectedIntent.occasions.length > 0 || detectedIntent.materials.length > 0 || detectedIntent.styles.length > 0) && (
        <div style={{ margin: "-0.5rem 0 1rem", fontSize: "0.82rem", color: "var(--muted)" }}>
          <span>Identified concepts: </span>
          {detectedIntent.occasions.map((o) => (
            <span key={o} className="semantic-tag">Occasion: {o}</span>
          ))}
          {detectedIntent.materials.map((m) => (
            <span key={m} className="semantic-tag">Material: {m}</span>
          ))}
          {detectedIntent.styles.map((s) => (
            <span key={s} className="semantic-tag">Craft style: {s}</span>
          ))}
        </div>
      )}

      {/* Filter toggle and controls */}
      <div className="filter-card">
        <div className="between" style={{ marginBottom: "0.5rem" }}>
          <strong style={{ fontSize: "0.95rem" }}>Filter & Sort</strong>
          <button
            type="button"
            className="linklike small"
            onClick={() => setShowFilters(!showFilters)}
          >
            {showFilters ? "Hide advanced filters ▲" : "Show advanced filters (materials, location, trust tiers) ▼"}
          </button>
        </div>

        <form onSubmit={submit} className="filters">
          <label>
            Category
            <select
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            >
              <option value="">All Categories</option>
              {(categories.data || []).map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </label>

          <label>
            Min Price (₹)
            <input
              type="number"
              min="0"
              placeholder="0"
              value={form.min_price}
              onChange={(e) => setForm({ ...form, min_price: e.target.value })}
            />
          </label>

          <label>
            Max Price (₹)
            <input
              type="number"
              min="0"
              placeholder="Any"
              value={form.max_price}
              onChange={(e) => setForm({ ...form, max_price: e.target.value })}
            />
          </label>

          <label>
            Sort By
            <select
              value={form.sort}
              onChange={(e) => setForm({ ...form, sort: e.target.value })}
            >
              <option value="relevance">Relevance & Craft Match</option>
              <option value="newest">Newest First</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
            </select>
          </label>

          {showFilters && (
            <>
              <label>
                Artisan Location / State
                <input
                  type="text"
                  placeholder="e.g. Rajasthan, Bihar, Lucknow"
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                />
              </label>

              <label>
                Craft Material
                <select
                  value={form.material}
                  onChange={(e) => setForm({ ...form, material: e.target.value })}
                >
                  <option value="">Any Material</option>
                  <option value="Terracotta">Terracotta / Clay</option>
                  <option value="Cotton">Cotton / Handloom</option>
                  <option value="Silk">Pure Silk</option>
                  <option value="Brass">Brass / Metal</option>
                  <option value="Wood">Sheesham / Wood</option>
                  <option value="Leather">Hand-stitched Leather</option>
                  <option value="Bamboo">Bamboo & Cane</option>
                </select>
              </label>

              <label>
                Seller Trust Tier
                <select
                  value={form.trust_tier}
                  onChange={(e) => setForm({ ...form, trust_tier: e.target.value })}
                >
                  <option value="">All Artisan Tiers</option>
                  <option value="master_artisan">👑 Master Artisan</option>
                  <option value="trusted_artisan">⭐ Trusted Artisan</option>
                  <option value="verified_maker">🛡️ Verified Maker</option>
                </select>
              </label>

              <label className="inline" style={{ alignSelf: "center", marginTop: "1rem" }}>
                <input
                  type="checkbox"
                  checked={form.in_stock}
                  onChange={(e) => setForm({ ...form, in_stock: e.target.checked })}
                />
                In Stock Only
              </label>
            </>
          )}

          <div className="row" style={{ marginTop: "0.5rem" }}>
            <button className="btn btn-small" type="submit">
              Apply
            </button>
            <button className="btn btn-outline btn-small" type="button" onClick={clear}>
              Reset
            </button>
          </div>
        </form>

        {formError && <div className="alert alert-error small" style={{ marginTop: "0.5rem" }}>{formError}</div>}
      </div>

      {/* Provider Info Banner */}
      {data && (
        <div className="between" style={{ margin: "0.5rem 0 1rem", fontSize: "0.82rem", color: "var(--muted)" }}>
          <div>
            Showing <strong>{items.length}</strong> {items.length === 1 ? "handmade piece" : "handmade pieces"}
            {params.get("q") ? ` for "${params.get("q")}"` : ""}
          </div>
          <div style={{ fontStyle: "italic" }}>
            Provider: {data.is_ai_powered ? "AI Vector Search" : "Local Conceptual Search"}
          </div>
        </div>
      )}

      {loading && <Loading text="Searching artisanal collections..." />}
      <ErrorBox message={error} onRetry={reload} />

      {/* Empty State */}
      {!loading && !error && items.length === 0 && (
        <div style={{ textAlign: "center", padding: "3rem 1rem" }}>
          <EmptyState
            title="No matching handmade items found"
            text="Try adjusting your keywords, broadening your price filter, or explore one of our suggested searches below:"
          />
          <div className="pill-container" style={{ justifyContent: "center", marginTop: "1rem" }}>
            {data?.suggested_searches?.map((s, idx) => (
              <button
                key={idx}
                type="button"
                className="search-pill"
                onClick={() => handleSuggestionClick(s)}
              >
                {s}
              </button>
            ))}
          </div>
          <button className="btn btn-outline btn-small" style={{ marginTop: "1rem" }} onClick={clear}>
            Clear All Filters
          </button>
        </div>
      )}

      {/* Products Grid */}
      <div className="grid">
        {items.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </div>
  );
}
