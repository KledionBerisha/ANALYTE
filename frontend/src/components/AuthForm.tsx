"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Logo } from "@/components/AppShell";
import { ApiError } from "@/lib/api/client";
import { useAuth } from "@/lib/auth";

type Mode = "login" | "register";

const COPY: Record<Mode, { title: string; action: string; switchText: string; switchHref: string; switchLink: string }> = {
  login: {
    title: "Hyni në llogari",
    action: "Hyr",
    switchText: "Nuk keni llogari?",
    switchHref: "/register",
    switchLink: "Krijoni një",
  },
  register: {
    title: "Krijoni llogari",
    action: "Krijo llogarinë",
    switchText: "Keni llogari?",
    switchHref: "/login",
    switchLink: "Hyni",
  },
};

export function AuthForm({ mode }: { mode: Mode }) {
  const { user, login, register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const copy = COPY[mode];

  useEffect(() => {
    if (user) router.replace("/documents");
  }, [user, router]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await (mode === "login" ? login(email, password) : register(email, password));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Shërbimi nuk u arrit. Provoni sërish.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid flex-1 place-items-center px-4 py-16">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Logo />
        </div>
        <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h1 className="text-lg font-semibold text-slate-900">{copy.title}</h1>
          <p className="mt-1 text-sm text-slate-500">
            Shpjegim i qartë i analizave tuaja, i kontrolluar para se ta lexoni.
          </p>

          <label className="mt-6 block text-sm font-medium text-slate-700">
            Email
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-600/20"
            />
          </label>
          <label className="mt-4 block text-sm font-medium text-slate-700">
            Fjalëkalimi
            <input
              type="password"
              required
              minLength={mode === "register" ? 10 : undefined}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-600/20"
            />
            {mode === "register" && (
              <span className="mt-1 block text-xs font-normal text-slate-500">Të paktën 10 shenja.</span>
            )}
          </label>

          {error && (
            <p role="alert" className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="mt-6 w-full rounded-lg bg-cyan-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-cyan-800 disabled:opacity-60"
          >
            {busy ? "Një moment…" : copy.action}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          {copy.switchText}{" "}
          <Link href={copy.switchHref} className="font-medium text-cyan-700 hover:underline">
            {copy.switchLink}
          </Link>
        </p>
      </div>
    </div>
  );
}
