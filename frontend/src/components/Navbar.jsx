import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { useLang } from "../i18n";

export default function Navbar() {
  const { user, logout } = useAuth();
  const { count } = useCart();
  const { t, lang, setLang } = useLang();
  const [open, setOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadNotifs, setUnreadNotifs] = useState(0);
  const [unreadMessages, setUnreadMessages] = useState(0);
  const notifRef = useRef(null);
  const navigate = useNavigate();

  const close = () => {
    setOpen(false);
    setNotifOpen(false);
  };

  const fetchNotifsAndMessages = async () => {
    if (!user) return;
    try {
      const res = await api.notifications();
      setNotifications(res.notifications || []);
      setUnreadNotifs(res.unread_count || 0);

      const convos = await api.conversations();
      const unreadTotal = (convos || []).reduce((acc, c) => acc + (c.unread_count || 0), 0);
      setUnreadMessages(unreadTotal);
    } catch {
      // Background poll failure is silent
    }
  };

  useEffect(() => {
    if (user) {
      fetchNotifsAndMessages();
      const timer = setInterval(fetchNotifsAndMessages, 15000);
      return () => clearInterval(timer);
    } else {
      setNotifications([]);
      setUnreadNotifs(0);
      setUnreadMessages(0);
    }
  }, [user]);

  // Click outside to close notification dropdown
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setNotifOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  const handleNotifClick = async (n) => {
    if (!n.is_read) {
      try {
        await api.markNotificationRead(n.id);
        setNotifications((prev) => prev.map((item) => (item.id === n.id ? { ...item, is_read: true } : item)));
        setUnreadNotifs((prev) => Math.max(0, prev - 1));
      } catch {}
    }
    setNotifOpen(false);
    if (n.link) {
      navigate(n.link);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setNotifications((prev) => prev.map((item) => ({ ...item, is_read: true })));
      setUnreadNotifs(0);
    } catch {}
  };

  const link = (to, label, badge = null) => (
    <NavLink to={to} onClick={close} className={({ isActive }) => (isActive ? "active" : "")} style={{ position: "relative" }}>
      {label}
      {badge ? (
        <span
          style={{
            marginLeft: "0.3rem",
            fontSize: "0.72rem",
            background: "var(--saffron)",
            color: "#fff",
            borderRadius: "999px",
            padding: "0.1rem 0.45rem",
            fontWeight: "700",
          }}
        >
          {badge}
        </span>
      ) : null}
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
          {user?.role === "buyer" && link("/cart", t("nav.cart"), count || null)}
          {user && link("/orders", t("nav.orders"))}
          {user && link("/messages", "Messages", unreadMessages || null)}
          {user?.role === "artisan" && link("/seller", t("nav.sell"))}
          {user?.role === "admin" && link("/admin", t("nav.admin"))}
          {!user && link("/cart", t("nav.cart"), count || null)}
          {!user && link("/login", t("nav.login"))}
          {!user && link("/register", t("nav.register"))}

          {/* Notification Bell */}
          {user && (
            <div className="notif-wrap" ref={notifRef}>
              <button
                className="notif-btn"
                title="Notifications"
                aria-label="Notifications"
                onClick={() => setNotifOpen(!notifOpen)}
              >
                🔔
                {unreadNotifs > 0 && <span className="notif-badge-pill">{unreadNotifs}</span>}
              </button>

              {notifOpen && (
                <div className="notif-dropdown">
                  <div className="between" style={{ padding: "0.75rem 1rem", borderBottom: "1px solid var(--border)", background: "#faf8f5" }}>
                    <strong style={{ fontSize: "0.9rem" }}>Marketplace Notifications</strong>
                    {unreadNotifs > 0 && (
                      <button className="linklike small" onClick={handleMarkAllRead}>
                        Mark all read
                      </button>
                    )}
                  </div>
                  {notifications.length === 0 ? (
                    <div className="small muted" style={{ padding: "1.5rem 1rem", textAlign: "center" }}>
                      No notifications yet
                    </div>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.id}
                        className={`notif-item ${!n.is_read ? "unread" : ""}`}
                        onClick={() => handleNotifClick(n)}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.2rem" }}>
                          <span style={{ fontWeight: 700, color: "var(--indigo)" }}>{n.title}</span>
                          <span className="small muted" style={{ fontSize: "0.72rem" }}>
                            {new Date(n.created_at).toLocaleDateString("en-IN", { month: "short", day: "numeric" })}
                          </span>
                        </div>
                        <div className="small" style={{ color: "var(--text)" }}>{n.message}</div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}

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
            title="Language"
          >
            {lang === "en" ? "हिन्दी" : "English"}
          </button>
        </nav>
      </div>
    </header>
  );
}
