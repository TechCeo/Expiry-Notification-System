import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../../shared/auth/AuthProvider";
import { ErrorState, LoadingState } from "../../shared/ui/State";

export function AuthCallbackPage() {
  const auth = useAuth();
  const { completeLogin } = auth;
  const [error, setError] = useState<unknown>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    completeLogin()
      .then(() => setDone(true))
      .catch(setError);
  }, [completeLogin]);

  if (error) {
    return <ErrorState error={error} />;
  }
  if (done) {
    return <Navigate to="/dashboard" replace />;
  }
  return <LoadingState />;
}
