import {
  createContext,
  PropsWithChildren,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";
import { User, UserManager, WebStorageStateStore } from "oidc-client-ts";

import { setTokenProvider } from "../../api/client";
import { config } from "../../config";

type AuthContextValue = {
  isAuthenticated: boolean;
  isLoading: boolean;
  apiToken: string | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  completeLogin: () => Promise<void>;
  setDevToken: (token: string) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const manager =
  config.authMode === "oidc"
    ? new UserManager({
        authority: config.oidc.authority,
        client_id: config.oidc.clientId,
        redirect_uri: config.oidc.redirectUri,
        post_logout_redirect_uri: config.oidc.postLogoutRedirectUri,
        response_type: "code",
        scope: config.oidc.scope,
        userStore: new WebStorageStateStore({ store: window.localStorage })
      })
    : null;

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null);
  const [devToken, setDevTokenState] = useState(
    () => window.localStorage.getItem("expiry.devToken") ?? ""
  );
  const [isLoading, setIsLoading] = useState(config.authMode === "oidc");

  useEffect(() => {
    if (!manager) {
      return;
    }
    setIsLoading(true);
    manager
      .getUser()
      .then((storedUser) => {
        setUser(storedUser && !storedUser.expired ? storedUser : null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const oidcToken =
    config.oidcApiToken === "access_token" ? user?.access_token : user?.id_token;
  const apiToken = config.authMode === "dev-token" ? devToken : oidcToken ?? null;
  setTokenProvider(async () => apiToken);

  const login = useCallback(async () => {
    if (config.authMode === "dev-token") {
      return;
    }
    setIsLoading(true);
    await manager?.signinRedirect();
  }, []);

  const logout = useCallback(async () => {
    if (config.authMode === "dev-token") {
      window.localStorage.removeItem("expiry.devToken");
      setDevTokenState("");
      return;
    }
    await manager?.signoutRedirect();
  }, []);

  const completeLogin = useCallback(async () => {
    if (!manager) {
      return;
    }
    setIsLoading(true);
    const signedIn = await manager.signinRedirectCallback();
    setUser(signedIn);
    setIsLoading(false);
  }, []);

  const setDevToken = useCallback((token: string) => {
    window.localStorage.setItem("expiry.devToken", token);
    setDevTokenState(token);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: Boolean(apiToken),
      isLoading,
      apiToken,
      login,
      logout,
      completeLogin,
      setDevToken
    }),
    [apiToken, completeLogin, isLoading, login, logout, setDevToken]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
