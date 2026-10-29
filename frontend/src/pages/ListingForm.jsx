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

  const [form, setForm] = useState({ title: "", description: "", category: "", price: "", stock: "", shipping_fee: "0" });
  const [existing, setExisting] = useState([]); // photos already saved on the server
  const [files, setFiles] = useState([]); // new photos chosen in this form
  const [loadingProduct, setLoadingProduct] = useState(editing);
  const [loadError, setLoadError] = useState("");

  const [notes, setNotes] = useState("");
  const [ai, setAi] = useState(null); // the AI result (suggestions only)
  const [aiBusy, setAiBusy] = useState(false);
  const [aiError, setAiError] = useState("");
  const [aiAssisted, setAiAssisted] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  const [errors, setErrors] = useState([]);
  const [saving, setSaving] = useState(false);

  // Local previews of newly chosen photos
  const previews = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files]);
  useEffect(() => () => previews.forEach((u) => URL.revokeObjectURL(u)), [previews]);

  // When editing, load the existing listing
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
        });
        setExisting(p.images);
        setAiAssisted(p.ai_assisted);
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

  // ---- AI assistant ---------------------------------------------------------
  const askAi = async () => {
    setAiError("");
    if (files.length === 0) return setAiError("Add a photo first. The assistant analyses the first photo you chose in this form.");
    setAiBusy(true);
    try {
      const fd = new FormData();
      fd.append("image", files[0]);
      fd.append("notes", notes);
      setAi(await api.aiAssist(fd));
    } catch (err) {
      setAiError(err.message);
    } finally {
      setAiBusy(false);
    }
  };

  const applySuggestions = () => {
    const s = ai.suggestions;
    setForm({ ...form, title: s.title || form.title, description: s.description || form.description, category: s.category || form.category });
    setAiAssisted(true);
    setConfirmed(false);
  };

  // ---- Validation + submit --------------------------------------------------
  const validate = () => {
    const list = [];
    if (form.title.trim().length < 3 || form.title.length > 120) list.push("Title must be 3 to 120 characters.");
    if (form.description.trim().length < 10 || form.description.length > 2000) list.push("Description must be 10 to 2000 characters.");
    if (!form.category) list.push("Please choose a category.");
    const price = Number(form.price);
    const stock = Number(form.stock);
    const ship = Number(form.shipping_fee);
    if (!Number.isInteger(price) || price < 1 || price > 1000000) list.push("Price must be a whole number of rupees, at least 1.");
    if (!Number.isInteger(stock) || stock < 0 || stock > 10000) list.push("Stock must be a whole number, 0 or more.");
    if (!Number.isInteger(ship) || ship < 0 || ship > 5000) list.push("Shipping fee must be a whole number between 0 and 5000.");
    if (existing.length + files.length === 0) list.push("Please add at least one photo.");
    if (aiAssisted && !confirmed) list.push("Please tick the box to confirm you reviewed the AI-assisted text.");
    return list;
  };

  const submit = async (e) => {
    e.preventDefault();
    const list = validate();
    setErrors(list);
    if (list.length) return;
    setSaving(true);
    try {
      const fd = new FormData();
      fd.append("title", form.title.trim());
      fd.append("description", form.description.trim());
      fd.append("category", form.category);
      fd.append("price", form.price);
      fd.append("stock", form.stock);
      fd.append("shipping_fee", form.shipping_fee || "0");
      fd.append("ai_assisted", String(aiAssisted));
      files.forEach((f) => fd.append("images", f));
      if (editing) await api.updateProduct(id, fd);
      else await api.createProduct(fd);
      navigate("/seller");
    } catch (err) {
      setErrors([err.message]);
    } finally {
      setSaving(false);
    }
  };

  if (loadingProduct) return <Loading />;
  if (loadError)
    return (
      <div className="container section">
        <ErrorBox message={loadError} />
        <Link to="/seller">&larr; {t("seller.title")}</Link>
      </div>
    );

  const s = ai?.suggestions;

  return (
    <div className="container narrow-lg section">
      <Link to="/seller">&larr; {t("seller.title")}</Link>
      <h1>{editing ? t("listing.editTitle") : t("listing.newTitle")}</h1>

      {errors.length > 0 && (
        <div className="alert alert-error" role="alert">
          <ul>
            {errors.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
        </div>
      )}

      <form className="form" onSubmit={submit}>
        {/* Step 1: photos */}
        <div className="card card-body form">
          <label>
            {t("listing.photos")}
            <input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={onFiles} />
          </label>
          <div className="thumbs">
            {existing.map((img) => (
              <div key={img.id} className="thumb-wrap">
                <img src={assetUrl(img.url)} alt="saved" />
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

        {/* Step 2: AI assistant */}
        <div className="card card-body form ai-box">
          <h3>
            {t("listing.aiHeading")} <FeatureTag status={aiStatus.data?.mode === "live" ? "implemented" : "demo-only"} />
          </h3>
          {aiStatus.data && <Notice kind={aiStatus.data.mode === "live" ? "info" : "warn"}>{aiStatus.data.label}</Notice>}
          <label>
            {t("listing.aiNotes")}
            <textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={1000} />
          </label>
          <ErrorBox message={aiError} />
          <button type="button" className="btn btn-outline" onClick={askAi} disabled={aiBusy}>
            {aiBusy ? t("common.loading") : t("listing.aiButton")}
          </button>

          {s && (
            <div className="suggestions">
              <Notice kind={ai.mode === "live" ? "info" : "warn"}>
                {ai.mode === "live" ? "AI-generated suggestions. Nothing is published until you save the listing." : "DEMO suggestions (the photo was not analysed). Nothing is published until you save the listing."}
              </Notice>
              <p>
                <strong>Looks like:</strong> {s.product_type || "-"} · <strong>Category:</strong> {s.category}
              </p>
              {s.photo_advice && (
                <p className="small">
                  <strong>{t("listing.aiPhotoAdvice")}:</strong> {s.photo_advice}
                </p>
              )}
              <p>
                <strong>{t("listing.title")}:</strong> {s.title}
              </p>
              <p className="pre">{s.description}</p>
              {s.materials.length > 0 && <p className="small">Materials: {s.materials.join(", ")}</p>}
              {s.uncertain_points.length > 0 && (
                <>
                  <p className="small">
                    <strong>Please check:</strong>
                  </p>
                  <ul className="small">
                    {s.uncertain_points.map((u) => (
                      <li key={u}>{u}</li>
                    ))}
                  </ul>
                </>
              )}
              <button type="button" className="btn btn-small" onClick={applySuggestions}>
                {t("listing.aiApply")}
              </button>
            </div>
          )}
        </div>

        {/* Step 3: the editable review form */}
        <div className="card card-body form">
          <label>
            {t("listing.title")}
            <input value={form.title} onChange={set("title")} maxLength={120} />
          </label>
          <label>
            {t("listing.description")}
            <textarea rows={6} value={form.description} onChange={set("description")} maxLength={2000} />
          </label>
          <label>
            {t("listing.category")}
            <select value={form.category} onChange={set("category")}>
              <option value="">-</option>
              {(categories.data || []).map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
          <div className="grid grid-3">
            <label>
              {t("listing.price")}
              <input type="number" min="1" step="1" value={form.price} onChange={set("price")} />
            </label>
            <label>
              {t("listing.stock")}
              <input type="number" min="0" step="1" value={form.stock} onChange={set("stock")} />
            </label>
            <label>
              {t("listing.shippingFee")}
              <input type="number" min="0" step="1" value={form.shipping_fee} onChange={set("shipping_fee")} />
            </label>
          </div>

          {aiAssisted && (
            <label className="radio">
              <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
              {t("listing.confirm")}
            </label>
          )}

          <button className="btn" disabled={saving}>
            {saving ? t("common.loading") : editing ? t("listing.saveChanges") : t("listing.publish")}
          </button>
        </div>
      </form>
    </div>
  );
}
