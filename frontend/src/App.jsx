import { Link, Route, Routes } from "react-router-dom";
import LanguagePrompt from "./components/LanguagePrompt";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminPanel from "./pages/AdminPanel";
import ArtisanProfile from "./pages/ArtisanProfile";
import Artisans from "./pages/Artisans";
import Cart from "./pages/Cart";
import Catalog from "./pages/Catalog";
import Checkout from "./pages/Checkout";
import Features from "./pages/Features";
import Home from "./pages/Home";
import ListingForm from "./pages/ListingForm";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import Orders from "./pages/Orders";
import Policy from "./pages/Policy";
import ProductDetail from "./pages/ProductDetail";
import Register from "./pages/Register";
import SellerDashboard from "./pages/SellerDashboard";

export default function App() {
  return (
    <>
      <LanguagePrompt />
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/shop" element={<Catalog />} />
          <Route path="/product/:id" element={<ProductDetail />} />
          <Route path="/artisans" element={<Artisans />} />
          <Route path="/artisan/:id" element={<ArtisanProfile />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/features" element={<Features />} />
          <Route path="/policy/:slug" element={<Policy />} />

          <Route path="/checkout" element={<ProtectedRoute roles={["buyer"]}><Checkout /></ProtectedRoute>} />
          <Route path="/orders" element={<ProtectedRoute><Orders /></ProtectedRoute>} />
          <Route path="/seller" element={<ProtectedRoute roles={["artisan"]}><SellerDashboard /></ProtectedRoute>} />
          <Route path="/seller/new" element={<ProtectedRoute roles={["artisan"]}><ListingForm /></ProtectedRoute>} />
          <Route path="/seller/edit/:id" element={<ProtectedRoute roles={["artisan"]}><ListingForm /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute roles={["admin"]}><AdminPanel /></ProtectedRoute>} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="footer">
        <div className="container">
          <p>
            <Link to="/policy/terms">Terms</Link> · <Link to="/policy/privacy">Privacy</Link> ·{" "}
            <Link to="/policy/shipping">Shipping</Link> · <Link to="/policy/refunds">Refunds</Link> ·{" "}
            <Link to="/features">Feature status</Link>
          </p>
          <p className="muted small">&copy; Digi Karigari</p>
        </div>
      </footer>
    </>
  );
}
