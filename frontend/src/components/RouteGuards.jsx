import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { Spinner } from "./icons.jsx";

function FullPageSpinner() {
  return (
    <div className="flex h-full items-center justify-center text-slate-400">
      <Spinner className="size-6" />
    </div>
  );
}

export function RequireAuth() {
  const { status } = useAuth();
  const location = useLocation();
  if (status === "loading") return <FullPageSpinner />;
  if (status === "guest") return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}

export function GuestOnly() {
  const { status } = useAuth();
  if (status === "loading") return <FullPageSpinner />;
  if (status === "authed") return <Navigate to="/documents" replace />;
  return <Outlet />;
}
