import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ErrorBox } from "../components/States";
import { useAuth } from "../context/AuthContext";
import { useLang } from "../i18n";

const DEMO = [
  ["Buyer", "buyer@digikarigari-demo.com"],
  ["Artisan (approved)", "meera@digikarigari-demo.com"],
  ["Artisan (pending)", "sanjay@digikarigari-demo.com"],
  ["Admin", "admin@digikarigari-demo.com"],
];

export default function Login() {
  const { login } = useAuth();
  const { t } = useLang();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) return setError("Please enter your email and password.");
    setBusy(true);
    setError("");
    try {
      const user = await login(email.trim(), password);
      const fallback = user.role === "admin" ? "/admin" : user.role === "artisan" ? "/seller" : "/";
      navigate(location.state?.from || fallback, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container narrow section">
      <h1>{t("nav.login")}</h1>
      <ErrorBox message={error} />
      <form className="card card-body form" onSubmit={submit}>
        <label>
          {t("auth.email")}
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
        </label>
        <label>
          {t("auth.password")}
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
        </label>
        <button className="btn" disabled={busy}>
          {busy ? t("common.loading") : t("nav.login")}
        </button>
      </form>
      <p>
        {t("auth.noAccount")} <Link to="/register">{t("nav.register")}</Link>
      </p>

      <div className="card card-body">
        <h3>{t("auth.demoAccounts")}</h3>
        <div className="row wrap">
          {DEMO.map(([label, mail]) => (
            <button
              key={mail}
              type="button"
              className="btn btn-small btn-outline"
              onClick={() => {
                setEmail(mail);
                setPassword("demo1234");
              }}
            >
              {label}
            </button>
          ))}
        </div>
        <p className="small muted">Click one to fill the form, then press Log in. (Run the seed script first.)</p>
      </div>
    </div>
  );
}
