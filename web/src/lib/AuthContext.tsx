import React, { createContext, useContext, useEffect, useState } from "react";
import { apiFetch, apiForm } from "./api";
import { clearTokens, getAccessToken, setTokens } from "./auth";

export type User = {
  id: number;
  name: string;
  email: string;
  role: "seller" | "supervisor" | "manager" | "admin";
  active: boolean;
  team?: string | null;
};

type AuthContextType = {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(getAccessToken());
  const [loading, setLoading] = useState(true);

  async function loadMe(accessToken: string) {
    const me = await apiFetch<User>("/api/auth/me", { token: accessToken });
    setUser(me);
  }

  useEffect(() => {
    const bootstrap = async () => {
      const existing = getAccessToken();
      if (!existing) {
        setLoading(false);
        return;
      }
      try {
        await loadMe(existing);
      } catch {
        clearTokens();
        setToken(null);
      } finally {
        setLoading(false);
      }
    };
    bootstrap();
  }, []);

  async function login(email: string, password: string) {
    const body = new URLSearchParams();
    body.append("username", email);
    body.append("password", password);
    const data = await apiForm<{ access_token: string; refresh_token: string }>(
      "/api/auth/login",
      body
    );
    setTokens(data.access_token, data.refresh_token);
    setToken(data.access_token);
    await loadMe(data.access_token);
  }

  function logout() {
    clearTokens();
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
