"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Logo } from "@/components/AppShell";
import { api, ApiError } from "@/lib/api/client";
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
  const { user, login, verify, register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState<string | null>(null);
  const [needsConfirmation, setNeedsConfirmation] = useState(false);
  const [resent, setResent] = useState(false);
  // Hapi i dytë (ADR 0018): sfida vjen vetëm pasi fjalëkalimi është i saktë.
  const [challenge, setChallenge] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [useRecovery, setUseRecovery] = useState(false);
  const copy = COPY[mode];

  useEffect(() => {
    if (user) router.replace("/documents");
  }, [user, router]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setNeedsConfirmation(false);
    try {
      if (mode === "login") setChallenge(await login(email, password));
      else setSent(await register(email, password));
    } catch (caught) {
      // 403 vjen vetëm kur fjalëkalimi është i saktë dhe email-i s'është konfirmuar.
      setNeedsConfirmation(caught instanceof ApiError && caught.status === 403);
      setError(caught instanceof ApiError ? caught.message : "Shërbimi nuk u arrit. Provoni sërish.");
    } finally {
      setBusy(false);
    }
  }

  async function submitCode(event: React.FormEvent) {
    event.preventDefault();
    if (challenge === null) return;
    setBusy(true);
    setError(null);
    try {
      await verify(challenge, code);
    } catch (caught) {
      // Sfida skadon pas pak minutash ose pas ndryshimit të fjalëkalimit: atëherë duhet fjalëkalimi sërish.
      setError(caught instanceof ApiError ? caught.message : "Shërbimi nuk u arrit. Provoni sërish.");
    } finally {
      setBusy(false);
    }
  }

  function backToPassword() {
    setChallenge(null);
    setCode("");
    setUseRecovery(false);
    setError(null);
  }

  async function resend() {
    setResent(false);
    try {
      await api.resendConfirmation(email);
      setResent(true);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Shërbimi nuk u arrit. Provoni sërish.");
    }
  }

  if (challenge !== null) {
    return (
      <div className="grid flex-1 place-items-center px-4 py-16">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex justify-center">
            <Logo />
          </div>
          <form onSubmit={submitCode} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h1 className="text-lg font-semibold text-slate-900">Verifikimi në dy hapa</h1>
            <p className="mt-1 text-sm text-slate-500">
              {useRecovery
                ? "Shkruani një nga kodet e rimëkëmbjes që ruajtët. Secili vlen vetëm një herë."
                : "Shkruani kodin me gjashtë shifra nga aplikacioni i vërtetimit."}
            </p>
            <label className="mt-6 block text-sm font-medium text-slate-700">
              {useRecovery ? "Kodi i rimëkëmbjes" : "Kodi"}
              <input
                type="text"
                required
                autoFocus
                inputMode={useRecovery ? "text" : "numeric"}
                autoComplete="one-time-code"
                maxLength={useRecovery ? 24 : 7}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-2 font-mono tracking-widest text-slate-900 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-600/20"
              />
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
              {busy ? "Një moment…" : "Vazhdo"}
            </button>
            <button
              type="button"
              onClick={() => {
                setUseRecovery(!useRecovery);
                setCode("");
                setError(null);
              }}
              className="mt-4 text-sm font-medium text-cyan-700 hover:underline"
            >
              {useRecovery ? "Përdor kodin e aplikacionit" : "Përdor një kod rimëkëmbjeje"}
            </button>
          </form>
          <p className="mt-4 text-center text-sm text-slate-500">
            <button type="button" onClick={backToPassword} className="font-medium text-cyan-700 hover:underline">
              Mbrapa te fjalëkalimi
            </button>
          </p>
        </div>
      </div>
    );
  }

  if (sent !== null) {
    return (
      <div className="grid flex-1 place-items-center px-4 py-16">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex justify-center">
            <Logo />
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h1 className="text-lg font-semibold text-slate-900">Kontrolloni email-in</h1>
            <p role="status" className="mt-2 text-sm text-slate-600">
              {sent}
            </p>
            <button
              type="button"
              onClick={resend}
              className="mt-5 text-sm font-medium text-cyan-700 hover:underline"
            >
              Nuk e morët? Dërgoje sërish
            </button>
            {resent && (
              <p role="status" className="mt-2 text-xs text-slate-500">
                Nëse llogaria pret konfirmim, mesazhi u nis sërish.
              </p>
            )}
            {error && (
              <p role="alert" className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
                {error}
              </p>
            )}
          </div>
          <p className="mt-4 text-center text-sm text-slate-500">
            Pasi ta hapni lidhjen,{" "}
            <Link href="/login" className="font-medium text-cyan-700 hover:underline">
              hyni
            </Link>
          </p>
        </div>
      </div>
    );
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
          {mode === "login" && (
            <p className="mt-2 text-right text-sm">
              <Link href="/forgot-password" className="font-medium text-cyan-700 hover:underline">
                Harrova fjalëkalimin
              </Link>
            </p>
          )}

          {error && (
            <p role="alert" className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {error}
            </p>
          )}
          {needsConfirmation && (
            <p className="mt-2 text-sm text-slate-600">
              <button type="button" onClick={resend} className="font-medium text-cyan-700 hover:underline">
                Dërgo një lidhje të re konfirmimi
              </button>
              {resent && <span className="ml-2 text-xs text-slate-500">U nis, nëse llogaria pret konfirmim.</span>}
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
