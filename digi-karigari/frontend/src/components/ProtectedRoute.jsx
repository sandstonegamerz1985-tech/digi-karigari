import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Loading, Notice } from "./States";

// Wrap a page in <ProtectedRoute roles={["admin"]}> to restrict it.
// NOTE: this only hides pages. The REAL security checks happen on the backend.
export default function ProtectedRoute({ roles, children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (roles && !roles.includes(user.role)) {
    return (
      <div className="container">
        <Notice kind="error">This page is only for: {roles.join(", ")}. You are logged in as {user.role}.</Notice>
      </div>
    );
  }
  return children;
}
