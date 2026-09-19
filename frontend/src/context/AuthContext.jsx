import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, setUnauthorizedHandler } from "../lib/api.js";

const AuthContext = createContext(null);
export const LAST_ANSWER_PREFIX = "citecache:last-answer:";

function clearSessionData() {
  try {
    Object.keys(sessionStorage).filter((k) => k.startsWith(LAST_ANSWER_PREFIX)).forEach((k) => sessionStorage.removeItem(k));
  } catch {
    /* storage unavailable */
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | authed | guest

  useEffect(() => {
    setUnauthorizedHandler(() => {
      clearSessionData();
      setUser(null);
      setStatus("guest");
    });
    api
      .me()
      .then((u) => {
        setUser(u);
        setStatus("authed");
      })
      .catch(() => setStatus("guest"));
  }, []);

  const signIn = useCallback(async (mode, username, password) => {
    const u = mode === "signup" ? await api.signup(username, password) : await api.login(username, password);
    setUser(u);
    setStatus("authed");
  }, []);

  const signOut = useCallback(async () => {
    await api.logout().catch(() => {});
    clearSessionData();
    setUser(null);
    setStatus("guest");
  }, []);

  const value = useMemo(() => ({ user, status, signIn, signOut }), [user, status, signIn, signOut]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
