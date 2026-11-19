import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, assetUrl } from "../api";
import { ErrorBox, Loading, Notice } from "../components/States";
import { FeatureTag } from "../components/Tag";
import { useFetch } from "../hooks";
import { useLang } from "../i18n";
import { checkImageFile } from "../utils";

const MAX_IMAGES = 5;

export default function ListingForm() {
  const { id } = useParams();
  const editing = Boolean(id);
  const navigate = useNavigate();
  const { t } = useLang();

  const categories = useFetch(() => api.categories(), []);
  const aiStatus = useFetch(() => api.aiStatus(), []);

  const [form, setForm] = useState({
    title: "",
    description: "",
    category: "",
    price: "",
    stock: "",
    shipping_fee: "0",
    materials: "",
    tags: "",
  });
  const [existing, setExisting] = useState([]);
  const [files, setFiles] = useState([]);
  const [loadingProduct, setLoadingProduct] = useState(editing);
  const [loadError, setLoadError] = useState("");

  const [notes, setNotes] = useState("");
  const [ai, setAi] = useState(null);
  const [aiBusy, setAiBusy] = useState(false);
  const [aiError, setAiError] = useState("");
  const [aiAssisted, setAiAssisted] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  // AI advisory photo quality and category checks
  const [advisoryReport, setAdvisoryReport] = useState(null);
  const [advisoryBusy, setAdvisoryBusy] = useState(false);
  const [advisoryError, setAdvisoryError] = useState("");

  const [errors, setErrors] = useState([]);
  const [saving, setSaving] = useState(false);

  const previews = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files]);
  useEffect(() => () => previews.forEach((u) => URL.revokeObjectURL(u)), [previews]);

  useEffect(() => {
    if (!editing) return;
    api
      .product(id)
      .then((p) => {
        setForm({
          title: p.title,
          description: p.description,
          category: p.category,
          price: String(p.price),
          stock: String(p.stock),
          shipping_fee: String(p.shipping_fee),
          materials: p.materials || "",
          tags: Array.isArray(p.tags) ? p.tags.join(", ") : (p.tags || ""),
        });
        setExisting(p.images);
        setAiAssisted(p.ai_assisted);
        if (p.ai_advisory) setAdvisoryReport(p.ai_advisory);
      })
      .catch((e) => setLoadError(e.message))
      .finally(() => setLoadingProduct(false));
  }, [editing, id]);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const onFiles = (e) => {
    const chosen = Array.from(e.target.files || []);
    e.target.value = "";
    const problems = [];
    const good = [];
    for (const f of chosen) {
      const problem = checkImageFile(f);
      if (problem) problems.push(problem);
      else good.push(f);
    }
    const room = MAX_IMAGES - existing.length - files.length;
    if (good.length > room) problems.push(`You can have at most ${MAX_IMAGES} photos in total.`);
    setFiles([...files, ...good.slice(0, Math.max(room, 0))]);
    setErrors(problems);
  };

  const removeExisting = async (img) => {
    if (existing.length + files.length <= 1) return setErrors(["A listing needs at least one photo."]);
    try {
      await api.deleteImage(id, img.id);
      setExisting(existing.filter((i) => i.id !== img.id));
    } catch (err) {
      setErrors([err.message]);
    }
  };

  // AI listing text suggestions
  const askAi = async () => {
    setAiError("");
    if (files.length === 0) return setAiError("Add a photo first. The assistant analyses the first photo you chose in this form.");
    setAiBusy(true);
    try {
      const fd = new FormData();
      fd.append("image", files[0]);
      fd.append("notes", notes);
      const res = await api.aiAssist(fd);
      setAi(res);
      setAiAssisted(true);
    } catch (err) {
      setAiError(err.message);
    } finally {
      setAiBusy(false);
    }
  };

  const applySuggestions = () => {
    if (!ai?.suggestions) return;
    const s = ai.suggestions;
    setForm((prev) => ({
      ...prev,
      title: s.title || prev.title,
      description: s.description || prev.description,
      category: s.category || prev.category,
      materials: s.materials?.join(", ") || prev.materials,
      tags: s.tags?.join(", ") || prev.tags,
    }));
  };

  // AI advisory image quality and category consistency check
  const runAdvisoryCheck = async () => {
    setAdvisoryError("");
    if (!form.category) {
      setAdvisoryError("Please select a category first so we can check category consistency.");
      return;
    }
    if (!form.title) {
      setAdvisoryError("Please enter a title for your craft piece.");
      return;
    }
    setAdvisoryBusy(true);
    try {
      const fd = new FormData();
      if (files.length > 0) {
        fd.append("image", files[0]);
      }
      fd.append("category", form.category);
      fd.append("title", form.title);
      fd.append("description", form.description);
      fd.append("notes", `${form.materials} ${form.tags} ${notes}`);
      const rep = await api.aiAdvisoryCheck(fd);
      setAdvisoryReport(rep);
    } catch (err) {
      setAdvisoryError(err.message || "Failed to run advisory check.");
    } finally {
      setAdvisoryBusy(false);
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    setErrors([]);
    const problems = [];
    if (!form.title.trim() || form.title.length < 3) problems.push("Title must be at least 3 characters.");
    if (!form.description.trim() || form.description.length < 10) problems.push("Description must be at least 10 characters.");
    if (!form.category) problems.push("Please pick a category.");
    const price = Number(form.price);
    if (!Number.isFinite(price) || price < 1) problems.push("Price must be at least 1 rupee.");
    const stock = Number(form.stock);
    if (!Number.isFinite(stock) || stock < 0) problems.push("Stock cannot be negative.");
    const ship = Number(form.shipping_fee || 0);
    if (!Number.isFinite(ship) || ship < 0) problems.push("Shipping fee cannot be negative.");
    if (existing.length + files.length === 0) problems.push("Add at least one photo of your craft.");
    if (aiAssisted && !confirmed) problems.push("Please review and confirm that you verified the AI-generated suggestions.");

    if (problems.length > 0) {
      setErrors(problems);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    setSaving(true);
    try {
      const fd = new FormData();
      fd.append("title", form.title.trim());
      fd.append("description", form.description.trim());
      fd.append("category", form.category);
      fd.append("price", String(price));
      fd.append("stock", String(stock));
      fd.append("shipping_fee", String(ship));
      fd.append("ai_assisted", String(aiAssisted));
      fd.append("materials", form.materials.trim());
      fd.append("tags", form.tags.trim());
      for (const f of files) fd.append("images", f);

      if (editing) {
        await api.updateProduct(id, fd);
      } else {
        await api.createProduct(fd);
      }
      navigate("/seller");
    } catch (err) {
      setErrors([err.message]);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } finally {
      setSaving(false);
    }
  };

  if (loadingProduct) return <Loading />;
  if (loadError) return <ErrorBox message={loadError} />;

  const s = ai?.suggestions;

  return (
    <div className="container narrow-lg section">
      <Link to="/seller">&larr; Back to Artisan Dashboard</Link>
      <h1>{editing ? "Edit Listing" : "Create New Handmade Listing"}</h1>

      {errors.length > 0 && (
        <div className="alert alert-error">
          <ul>
            {errors.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        </div>
      )}

      <form onSubmit={submit} className="form" style={{ marginTop: "1rem" }}>
        {/* Step 1: Photos */}
        <div className="card card-body form">
          <h3>1. Product Photographs ({existing.length + files.length} / {MAX_IMAGES})</h3>
          <p className="small muted">
            Upload clear photos taken in good natural light. Show different angles and close-ups of craftsmanship.
          </p>
          {existing.length + files.length < MAX_IMAGES && (
            <label>
              Add photos (JPG, PNG, WebP · up to 5 MB each)
              <input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={onFiles} />
            </label>
          )}

          <div className="thumbs">
            {existing.map((img) => (
              <div key={img.id} className="thumb-wrap">
                <img src={assetUrl(img.url)} alt="" />
                <button type="button" className="thumb-x" onClick={() => removeExisting(img)} aria-label="Remove photo">
                  ×
                </button>
              </div>
            ))}
            {previews.map((src, i) => (
              <div key={src} className="thumb-wrap">
                <img src={src} alt={`new ${i + 1}`} />
                <button type="button" className="thumb-x" onClick={() => setFiles(files.filter((_, n) => n !== i))} aria-label="Remove photo">
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Step 2: AI Advisory Photo & Category Check */}
        <div className="card card-body form advisory-report">
          <div className="between">
            <h3 style={{ margin: 0, color: "#9a3412" }}>
              2. AI Quality & Category Advisory Check <FeatureTag status="implemented" />
            </h3>
            <button
              type="button"
              className="btn btn-outline btn-small"
              onClick={runAdvisoryCheck}
              disabled={advisoryBusy}
            >
              {advisoryBusy ? "Inspecting..." : "🔍 Run Quality Check"}
            </button>
          </div>
          <p className="small muted" style={{ margin: "0.2rem 0 0.5rem" }}>
            Automated check for photo blur, underexposure/lighting, resolution, and whether your chosen category matches your product details.
          </p>

          <Notice kind="info">
            <strong>Advisory suggestions only:</strong> An admin makes the final decision on listing approval. A listing is NEVER automatically rejected or published based on AI advice.
          </Notice>

          {advisoryError && <ErrorBox message={advisoryError} />}

          {advisoryReport && (
            <div style={{ marginTop: "0.75rem", background: "#fff", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border)" }}>
              <div className="between" style={{ marginBottom: "0.5rem" }}>
                <strong>Inspection Checklist:</strong>
                <span className="small muted">Provider: {advisoryReport.provider}</span>
              </div>

              {advisoryReport.checks?.map((chk, i) => (
                <div key={i} className="check-row">
                  <span className={chk.status === "pass" ? "check-icon-pass" : "check-icon-advisory"}>
                    {chk.status === "pass" ? "✓" : "⚠️"}
                  </span>
                  <div>
                    <strong>{chk.name}:</strong> {chk.message}
                    {chk.suggestion && <div className="small muted" style={{ marginTop: "0.15rem" }}>💡 {chk.suggestion}</div>}
                  </div>
                </div>
              ))}

              {advisoryReport.category_summary && !advisoryReport.category_summary.is_match && (
                <div className="alert alert-warn small" style={{ marginTop: "0.75rem" }}>
                  💡 <strong>Category Suggestion:</strong> The assistant thinks this might be "{advisoryReport.category_summary.suggested}". You can keep your chosen category or switch if you prefer.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Step 3: AI Listing Assistant (Optional Title/Description Helper) */}
        <div className="card card-body form ai-box">
          <h3>
            3. AI Copywriting Assistant (Optional) <FeatureTag status={aiStatus.data?.mode === "live" ? "implemented" : "demo-only"} />
          </h3>
          <p className="small muted">
            Need help drafting your title and description? Enter rough artisan notes below and let the assistant write a warm, honest draft.
          </p>
          <label>
            Artisan Notes (e.g. "made on potters wheel with terracotta clay, hand-painted cobalt flowers, glazed inside")
            <textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={1000} />
          </label>
          <ErrorBox message={aiError} />
          <button type="button" className="btn btn-outline btn-small" onClick={askAi} disabled={aiBusy} style={{ alignSelf: "flex-start" }}>
            {aiBusy ? "Generating draft..." : "✨ Generate Description Draft"}
          </button>

          {s && (
            <div className="suggestions" style={{ marginTop: "0.75rem" }}>
              <p>
                <strong>Suggested Title:</strong> {s.title}
              </p>
              <p className="pre small"><strong>Draft:</strong> {s.description}</p>
              <button type="button" className="btn btn-small" onClick={applySuggestions}>
                Use This Draft in Form Below
              </button>
            </div>
          )}
        </div>

        {/* Step 4: Listing Details */}
        <div className="card card-body form">
          <h3>4. Product Listing Details</h3>

          <label>
            Listing Title *
            <input value={form.title} onChange={set("title")} placeholder="e.g. Hand-painted Blue Pottery Planter" maxLength={120} required />
          </label>

          <label>
            Craft Category *
            <select value={form.category} onChange={set("category")} required>
              <option value="">Select a category...</option>
              {(categories.data || []).map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </label>

          <label>
            Handcrafted Materials & Technique
            <input
              value={form.materials}
              onChange={set("materials")}
              placeholder="e.g. Terracotta clay, natural mineral slip, woodblock print, mulberry silk"
              maxLength={300}
            />
          </label>

          <label>
            Search Tags (comma-separated)
            <input
              value={form.tags}
              onChange={set("tags")}
              placeholder="e.g. diwali, pooja, handmade, planter, balcony, gift"
              maxLength={300}
            />
          </label>

          <label>
            Full Description *
            <textarea
              rows={6}
              value={form.description}
              onChange={set("description")}
              placeholder="Describe the craft tradition, dimensions, colors, and care instructions..."
              maxLength={2000}
              required
            />
          </label>

          <div className="grid grid-3">
            <label>
              Price (₹) *
              <input type="number" min="1" step="1" value={form.price} onChange={set("price")} required />
            </label>
            <label>
              Available Stock *
              <input type="number" min="0" step="1" value={form.stock} onChange={set("stock")} required />
            </label>
            <label>
              Estimated Shipping Fee (₹)
              <input type="number" min="0" step="1" value={form.shipping_fee} onChange={set("shipping_fee")} />
            </label>
          </div>

          {aiAssisted && (
            <label className="radio">
              <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
              I have verified the AI suggestions and confirm that the dimensions, materials, and claims are accurate.
            </label>
          )}

          <div className="alert alert-info small">
            🛡️ <strong>Admin Quality Review:</strong> When submitted, your listing enters the Admin Review Queue. An admin will review the photo quality and description before publishing it live to buyers.
          </div>

          <button className="btn" disabled={saving}>
            {saving ? "Saving..." : editing ? "Update Listing" : "Submit Listing for Review"}
          </button>
        </div>
      </form>
    </div>
  );
}
