import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api } from "../api";
import { ErrorBox, Notice } from "../components/States";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { useLang } from "../i18n";
import { formatINR } from "../utils";

export default function Checkout() {
  const { t } = useLang();
  const { user } = useAuth();
  const cart = useCart();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    shipping_name: user?.name || "",
    shipping_address: "",
    city: "",
    pincode: "",
    phone: "",
    simulate_payment: "success",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (cart.items.length === 0) return <Navigate to="/cart" replace />;

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const validate = () => {
    if (form.shipping_name.trim().length < 2) return "Please enter the receiver's name.";
    if (form.shipping_address.trim().length < 5) return "Please enter a full address (at least 5 characters).";
    if (form.city.trim().length < 2) return "Please enter the city.";
    if (!/^\d{6}$/.test(form.pincode)) return "PIN code must be exactly 6 digits.";
    if (!/^\d{10}$/.test(form.phone)) return "Phone number must be exactly 10 digits.";
    return "";
  };

  const submit = async (e) => {
    e.preventDefault();
    const problem = validate();
    if (problem) return setError(problem);
    setBusy(true);
    setError("");
    try {
      const order = await api.createOrder({
        items: cart.items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
        ...form,
        shipping_name: form.shipping_name.trim(),
        shipping_address: form.shipping_address.trim(),
        city: form.city.trim(),
      });
      cart.clear();
      navigate("/orders", { state: { placed: order.id } });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container section">
      <h1>{t("checkout.title")}</h1>
      <div className="cart-layout">
        <form className="card card-body form" onSubmit={submit}>
          <ErrorBox message={error} />
          <label>
            {t("checkout.name")}
            <input value={form.shipping_name} onChange={set("shipping_name")} maxLength={80} />
          </label>
          <label>
            {t("checkout.address")}
            <textarea rows={3} value={form.shipping_address} onChange={set("shipping_address")} maxLength={300} />
          </label>
          <label>
            {t("checkout.city")}
            <input value={form.city} onChange={set("city")} maxLength={80} />
          </label>
          <label>
            {t("checkout.pincode")}
            <input inputMode="numeric" value={form.pincode} onChange={set("pincode")} maxLength={6} />
          </label>
          <label>
            {t("checkout.phone")}
            <input inputMode="numeric" value={form.phone} onChange={set("phone")} maxLength={10} />
          </label>

          <fieldset>
            <legend>{t("checkout.payment")}</legend>
            <Notice kind="warn">TEST MODE: no card details are collected and no real money is charged.</Notice>
            <label className="radio">
              <input type="radio" name="pay" checked={form.simulate_payment === "success"} onChange={() => setForm({ ...form, simulate_payment: "success" })} />
              {t("checkout.paySuccess")}
            </label>
            <label className="radio">
              <input type="radio" name="pay" checked={form.simulate_payment === "fail"} onChange={() => setForm({ ...form, simulate_payment: "fail" })} />
              {t("checkout.payFail")}
            </label>
          </fieldset>

          <button className="btn" disabled={busy}>
            {busy ? t("common.loading") : `${t("checkout.place")} - ${formatINR(cart.total)}`}
          </button>
        </form>

        <aside className="card card-body summary">
          {cart.items.map((i) => (
            <p key={i.product_id} className="between small">
              <span>
                {i.title} × {i.quantity}
              </span>
              <span>{formatINR(i.price * i.quantity)}</span>
            </p>
          ))}
          <hr />
          <p className="between">
            <span>{t("cart.shipping")}</span> <span>{formatINR(cart.shipping)}</span>
          </p>
          <p className="between total">
            <span>{t("cart.total")}</span> <span>{formatINR(cart.total)}</span>
          </p>
        </aside>
      </div>
    </div>
  );
}
