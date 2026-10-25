import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { useLang } from "../i18n";

export default function Navbar() {
  const { user, logout } = useAuth();
  const { count } = useCart();
  const { t, lang, setLang } = useLang();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const close = () => setOpen(false);
  const link = (to, label) => (
    <NavLink to={to} onClick={close} className={({ isActive }) => (isActive ? "active" : "")}>
      {label}
    </NavLink>
  );

  return (
    <header className="navbar">
      <div className="container nav-inner">
        <Link to="/" className="logo" onClick={close}>
          Digi <span>Karigari</span>
        </Link>
        <button className="nav-toggle" aria-label="Toggle menu" aria-expanded={open} onClick={() => setOpen(!open)}>
          &#9776;
        </button>
        <nav className={`nav-links ${open ? "open" : ""}`}>
          {link("/", t("nav.home"))}
          {link("/shop", t("nav.shop"))}
          {link("/artisans", t("nav.artisans"))}
          {link("/features", t("nav.features"))}
          {user?.role === "buyer" && link("/cart", `${t("nav.cart")}${count ? ` (${count})` : ""}`)}
          {user && link("/orders", t("nav.orders"))}
          {user?.role === "artisan" && link("/seller", t("nav.sell"))}
          {user?.role === "admin" && link("/admin", t("nav.admin"))}
          {!user && link("/cart", `${t("nav.cart")}${count ? ` (${count})` : ""}`)}
          {!user && link("/login", t("nav.login"))}
          {!user && link("/register", t("nav.register"))}
          {user && (
            <button
              className="linklike"
              onClick={() => {
                logout();
                close();
                navigate("/");
              }}
            >
              {t("nav.logout")} ({user.name.split(" ")[0]})
            </button>
          )}
          <button
            className="btn btn-small btn-outline"
            onClick={() => setLang(lang === "en" ? "hi" : "en")}
            title="Language (demo-only: only some labels are translated)"
          >
            {lang === "en" ? "हिन्दी" : "English"}
          </button>
        </nav>
      </div>
    </header>
  );
}
