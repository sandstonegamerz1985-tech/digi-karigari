import { createContext, useContext, useEffect, useState } from "react";
import { api, getToken, setToken } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!getToken());

  // On page load, if we have a saved token, ask the backend who we are.
  useEffect(() => {
    if (!getToken()) return;
    api
      .me()
      .then(setUser)
      .catch(() => setToken(null)) // token expired or invalid
      .finally(() => setLoading(false));
  }, []);

  const finishLogin = (res) => {
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  };

  const value = {
    user,
    loading,
    login: async (email, password) => finishLogin(await api.login(email, password)),
    register: async (payload) => finishLogin(await api.register(payload)),
    logout: () => {
      setToken(null);
      setUser(null);
    },
    refresh: async () => setUser(await api.me()),
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
