import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ErrorBox, Notice } from "../components/States";
import { useAuth } from "../context/AuthContext";
import { useLang } from "../i18n";

export default function Register() {
  const { register } = useAuth();
  const { t } = useLang();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "buyer", craft: "", city: "", state: "", bio: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });
  const isArtisan = form.role === "artisan";

  const validate = () => {
    if (form.name.trim().length < 2) return "Please enter your name (at least 2 letters).";
    if (!/^\S+@\S+\.\S+$/.test(form.email)) return "Please enter a valid email address.";
    if (form.password.length < 8) return "Password must be at least 8 characters.";
    if (isArtisan && (!form.craft.trim() || !form.city.trim())) return "Artisans must enter their craft and city.";
    return "";
  };

  const submit = async (e) => {
    e.preventDefault();
    const problem = validate();
    if (problem) return setError(problem);
    setBusy(true);
    setError("");
    try {
      const payload = { name: form.name.trim(), email: form.email.trim(), password: form.password, role: form.role };
      if (isArtisan) Object.assign(payload, { craft: form.craft, city: form.city, state: form.state, bio: form.bio });
      const user = await register(payload);
      navigate(user.role === "artisan" ? "/seller" : "/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container narrow section">
      <h1>{t("nav.register")}</h1>
      <ErrorBox message={error} />
      <form className="card card-body form" onSubmit={submit}>
        <label>
          {t("auth.name")}
          <input value={form.name} onChange={set("name")} maxLength={80} />
        </label>
        <label>
          {t("auth.email")}
          <input type="email" value={form.email} onChange={set("email")} autoComplete="email" />
        </label>
        <label>
          {t("auth.password")} (8+)
          <input type="password" value={form.password} onChange={set("password")} autoComplete="new-password" />
        </label>
        <label>
          {t("auth.iAm")}
          <select value={form.role} onChange={set("role")}>
            <option value="buyer">{t("auth.buyer")}</option>
            <option value="artisan">{t("auth.artisan")}</option>
          </select>
        </label>

        {isArtisan && (
          <>
            <Notice>An admin must approve your artisan account before you can add listings and get the Verified badge.</Notice>
            <label>
              {t("auth.craft")}
              <input value={form.craft} onChange={set("craft")} maxLength={80} placeholder="e.g. Blue pottery" />
            </label>
            <label>
              {t("auth.city")}
              <input value={form.city} onChange={set("city")} maxLength={80} />
            </label>
            <label>
              {t("auth.state")}
              <input value={form.state} onChange={set("state")} maxLength={80} />
            </label>
            <label>
              {t("auth.bio")}
              <textarea rows={4} value={form.bio} onChange={set("bio")} maxLength={600} />
            </label>
          </>
        )}
        <button className="btn" disabled={busy}>
          {busy ? t("common.loading") : t("auth.createAccount")}
        </button>
      </form>
      <p>
        {t("auth.haveAccount")} <Link to="/login">{t("nav.login")}</Link>
      </p>
    </div>
  );
}
