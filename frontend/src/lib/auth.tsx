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

import {
  api,
  type RegisterOut,
  session,
  type Tokens,
  type UserOut,
  whenSessionLost,
} from "./api/client";

type Auth = {
  user: UserOut | null | undefined;
  login: (email: string, password: string) => Promise<void>;
  /** Kthen mesazhin e shërbimit; llogaria nuk hyn derisa email-i të konfirmohet (ADR 0016). */
  register: (email: string, password: string) => Promise<string>;
  logout: () => void;
  /** Revokon çdo seancë te shërbimi, pastaj del këtu. Hedh gabim nëse shërbimi nuk u arrit. */
  logoutEverywhere: () => Promise<void>;
};

const AuthContext = createContext<Auth | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  // Pa token, dihet menjëherë që nuk ka seancë; me token, pritet `/auth/me`.
  const [user, setUser] = useState<UserOut | null | undefined>(() =>
    session.access() ? undefined : null,
  );

  // Seanca u humb: tokenët janë tashmë të pavlefshëm, s'ka çfarë t'i thuhet shërbimit.
  const leave = useCallback(() => {
    session.clear();
    setUser(null);
    router.replace("/login");
  }, [router]);

  // Dalje me dëshirë: seanca mbyllet edhe te shërbimi, para se tokenët të fshihen.
  const logout = useCallback(() => {
    void api.endSession();
    leave();
  }, [leave]);

  useEffect(() => {
    whenSessionLost(leave);
    if (!session.access()) return;
    api
      .json<UserOut>("/auth/me")
      .then(setUser)
      .catch(() => setUser(null));
  }, [leave]);

  const login = useCallback(async (email: string, password: string) => {
    session.save(await api.post<Tokens>("/auth/login", { email, password }));
    setUser(await api.json<UserOut>("/auth/me"));
  }, []);

  // Regjistrimi nuk hap seancë: llogaria aktivizohet vetëm pasi të hapet lidhja te email-i.
  const register = useCallback(async (email: string, password: string) => {
    return (await api.post<RegisterOut>("/auth/register", { email, password })).message;
  }, []);

  // Pret shërbimin: «dil kudo» që dështon në heshtje do të linte seancat e hapura.
  const logoutEverywhere = useCallback(async () => {
    await api.endAllSessions();
    leave();
  }, [leave]);

  return (
    <AuthContext.Provider value={{ user, login, register, logout, logoutEverywhere }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): Auth {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth jashtë AuthProvider");
  return value;
}
