"use client";

/**
 * Seanca e përdoruesit.
 *
 * `user` është `undefined` gjatë kontrollit të parë dhe `null` kur nuk ka
 * seancë. Dallimi ka rëndësi: pa të, faqja do të kërcente te hyrja për një
 * çast edhe kur seanca është e vlefshme.
 */

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { api, session, type Tokens, type UserOut, whenSessionLost } from "./api/client";

type Auth = {
  user: UserOut | null | undefined;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<Auth | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  // Pa token, dihet menjëherë që nuk ka seancë; me token, pritet `/auth/me`.
  const [user, setUser] = useState<UserOut | null | undefined>(() =>
    session.access() ? undefined : null,
  );

  const logout = useCallback(() => {
    session.clear();
    setUser(null);
    router.replace("/login");
  }, [router]);

  useEffect(() => {
    whenSessionLost(logout);
    if (!session.access()) return;
    api
      .json<UserOut>("/auth/me")
      .then(setUser)
      .catch(() => setUser(null));
  }, [logout]);

  const login = useCallback(async (email: string, password: string) => {
    session.save(await api.post<Tokens>("/auth/login", { email, password }));
    setUser(await api.json<UserOut>("/auth/me"));
  }, []);

  const register = useCallback(
    async (email: string, password: string) => {
      await api.post<UserOut>("/auth/register", { email, password });
      await login(email, password);
    },
    [login],
  );

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): Auth {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth jashtë AuthProvider");
  return value;
}
