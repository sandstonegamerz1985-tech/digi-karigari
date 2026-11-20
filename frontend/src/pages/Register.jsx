import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ErrorBox, Notice } from "../components/States";
import { useAuth } from "../context/AuthContext";
import { useLang } from "../i18n";
import { supabaseClient } from "../lib/supabase";

export default function Register() {
  const { register } = useAuth();
  const { t } = useLang();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "buyer", craft: "", city: "", state: "", bio: "" });
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [verifiedEmail, setVerifiedEmail] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [otpBusy, setOtpBusy] = useState(false);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });
  const isArtisan = form.role === "artisan";
  const normalizedEmail = form.email.trim().toLowerCase();
  const isEmailVerified = Boolean(normalizedEmail) && verifiedEmail === normalizedEmail;

  const sendOtp = async () => {
    if (!/^\S+@\S+\.\S+$/.test(normalizedEmail)) {
      setError("Please enter a valid email address first.");
      return;
    }

    setOtpBusy(true);
    setError("");
    setNotice("");
    try {
      const { error: sendError } = await supabaseClient.auth.signInWithOtp({
        email: normalizedEmail,
        options: { shouldCreateUser: true },
      });
      if (sendError) throw sendError;
      setOtpSent(true);
      setNotice("If this email can sign up, a one-time code has been sent. Check your inbox and spam folder.");
    } catch (err) {
      setError(err.message || "Could not send the verification code. Please try again.");
    } finally {
      setOtpBusy(false);
    }
  };

  const verifyOtp = async () => {
    if (!/^\d{6}$/.test(otp.trim())) {
      setError("Enter the 6-digit code from your email.");
      return;
    }

    setOtpBusy(true);
    setError("");
    setNotice("");
    try {
      const { error: verifyError } = await supabaseClient.auth.verifyOtp({
        email: normalizedEmail,
        token: otp.trim(),
        type: "email",
      });
      if (verifyError) throw verifyError;

      setVerifiedEmail(normalizedEmail);
      setOtpSent(false);
      setOtp("");
      setNotice("Email verified. Complete the form to create your account and password.");
      // Supabase is used here for first-sign-up email verification only. The
      // marketplace keeps using its existing email/password authentication.
      await supabaseClient.auth.signOut();
    } catch (err) {
      setError(err.message || "That code could not be verified. Request a new one and try again.");
    } finally {
      setOtpBusy(false);
    }
  };

  const validate = () => {
    if (!isEmailVerified) return "Verify your email with the one-time code before creating your account.";
    if (form.name.trim().length < 2) return "Please enter your name (at least 2 letters).";
    if (!/^\S+@\S+\.\S+$/.test(normalizedEmail)) return "Please enter a valid email address.";
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
    setNotice("");
    try {
      const payload = { name: form.name.trim(), email: normalizedEmail, password: form.password, role: form.role };
      if (isArtisan) Object.assign(payload, { craft: form.craft, city: form.city, state: form.state, bio: form.bio });
      const user = await register(payload);
      navigate(user.role === "artisan" ? "/seller" : "/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const updateEmail = (event) => {
    const email = event.target.value;
    setForm((current) => ({ ...current, email }));
    setVerifiedEmail("");
    setOtpSent(false);
    setOtp("");
    setNotice("");
  };

  return (
    <div className="container narrow section">
      <h1>{t("nav.register")}</h1>
      <p className="muted">Verify your email once, then create a password for future logins.</p>
      <ErrorBox message={error} />
      {notice && <p className="alert alert-success" role="status">{notice}</p>}

      <section className="card card-body form" aria-label="Email verification">
        <label>
          {t("auth.email")}
          <input type="email" value={form.email} onChange={updateEmail} autoComplete="email" required />
        </label>
        {!isEmailVerified && (
          <>
            <button type="button" className="btn btn-outline" onClick={sendOtp} disabled={otpBusy}>
              {otpBusy && !otpSent ? "Sending code..." : "Send email code"}
            </button>
            {otpSent && (
              <>
                <label>
                  6-digit email code
                  <input
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    pattern="[0-9]{6}"
                    maxLength={6}
                    value={otp}
                    onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 6))}
                    required
                  />
                </label>
                <button type="button" className="btn" onClick={verifyOtp} disabled={otpBusy || otp.length !== 6}>
                  {otpBusy ? "Verifying..." : "Verify email"}
                </button>
              </>
            )}
          </>
        )}
        {isEmailVerified && <p className="alert alert-success">Email verified: {normalizedEmail}</p>}
      </section>

      <form className="card card-body form" onSubmit={submit}>
        <label>
          {t("auth.name")}
          <input value={form.name} onChange={set("name")} maxLength={80} required />
        </label>
        <label>
          {t("auth.password")} (8+)
          <input type="password" value={form.password} onChange={set("password")} autoComplete="new-password" minLength={8} required />
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
        <button className="btn" disabled={busy || !isEmailVerified}>
          {busy ? t("common.loading") : "Verify and create account"}
        </button>
      </form>
      <p>
        {t("auth.haveAccount")} <Link to="/login">{t("nav.login")}</Link>
      </p>
    </div>
  );
}
