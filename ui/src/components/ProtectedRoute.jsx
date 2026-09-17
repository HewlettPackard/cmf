/***
 * Require a Keycloak session when the API has KEYCLOAK_AUTH_MODE=required.
 ***/

import React, { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import {
  authIsRequired,
  fetchAuthConfig,
  isAuthenticated,
} from "../auth";

function ProtectedRoute({ children }) {
  const location = useLocation();
  const [state, setState] = useState({ loading: true, required: true });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const cfg = await fetchAuthConfig();
        if (!cancelled) {
          setState({ loading: false, required: authIsRequired(cfg) });
        }
      } catch {
        // If config is unreachable, still gate on local session when API is locked down.
        if (!cancelled) setState({ loading: false, required: true });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-600">
        Checking authentication…
      </div>
    );
  }

  if (state.required && !isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return children;
}

export default ProtectedRoute;
