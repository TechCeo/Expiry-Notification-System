export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1",
  authMode: import.meta.env.VITE_AUTH_MODE ?? "oidc",
  oidcApiToken: import.meta.env.VITE_OIDC_API_TOKEN ?? "id_token",
  oidc: {
    authority: import.meta.env.VITE_OIDC_AUTHORITY ?? "",
    clientId: import.meta.env.VITE_OIDC_CLIENT_ID ?? "expiry-notification-web",
    redirectUri:
      import.meta.env.VITE_OIDC_REDIRECT_URI ??
      `${window.location.origin}/auth/callback`,
    postLogoutRedirectUri:
      import.meta.env.VITE_OIDC_POST_LOGOUT_REDIRECT_URI ?? window.location.origin,
    scope: import.meta.env.VITE_OIDC_SCOPE ?? "openid profile email"
  }
} as const;
