import { Navigate, Outlet, useLocation } from "react-router-dom";

import { LoadingState } from "../ui/State";
import { useAuth } from "./AuthProvider";

export function RequireAuth() {
  const auth = useAuth();
  const location = useLocation();

  if (auth.isLoading) {
    return <LoadingState />;
  }

  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
