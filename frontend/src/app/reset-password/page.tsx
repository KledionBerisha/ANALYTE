"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { Logo } from "@/components/AppShell";
import { api, ApiError } from "@/lib/api/client";

type Phase = "form" | "done" | "failed";

/**
 * Lidhja nga email-i: `/reset-password?token=…` (ADR 0018).
 *
 * Si te `/confirm`, tokeni lexohet një herë dhe hiqet menjëherë nga adresa (`replaceState`), që të mos mbetet te
 * historiku ose te koka `Referer`; faqja shërbehet edhe me `Referrer-Policy: no-referrer`. Ndryshe nga konfirmimi,
 * tokeni nuk shpenzohet kur faqja hapet, por kur dërgohet formulari: ruhet në kujtesë (`useRef`), jo te adresa.
 */
export default function ResetPasswordPage() {
  const token = useRef<string | null>(null);
  const [password, setPassword] = useState("");
  const [again, setAgain] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [phase, setPhase] = useState<Phase>("form");

  useEffect(() => {
    // React në zhvillim e ekzekuton efektin dy herë: e dyta nuk duhet ta humbasë tokenin që adresa nuk e ka më.
    if (token.current === null) {
      token.current = new URLSearchParams(window.location.search).get("token");
      window.history.replaceState(null, "", window.location.pathname);
    }
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (password !== again) {
      setError("Dy fjalëkalimet nuk përputhen.");
      return;
    }
    if (!token.current) {
      setPhase("failed");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.resetPassword(token.current, password);
      token.current = null;
      setPhase("done");
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 400) {
        // Lidhja është e pavlefshme, e përdorur ose e skaduar: s'ka kuptim të provohet sërish me të njëjtën.
        setPhase("failed");
      } else {
        // Fjalëkalim shumë i shkurtër (422), shumë kërkesa (429) ose shërbimi i paarritshëm: lidhja mbetet e vlefshme.
        setError(caught instanceof ApiError ? caught.message : "Shërbimi nuk u arrit. Provoni sërish.");
      }
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
        {phase === "done" && (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h1 className="text-lg font-semibold text-slate-900">Fjalëkalimi u ndryshua</h1>
            <p role="status" className="mt-2 text-sm text-slate-600">
              Të gjitha seancat e hapura u mbyllën. Hyni me fjalëkalimin e ri.
            </p>
            <Link
              href="/login"
              className="mt-5 block rounded-lg bg-cyan-700 px-4 py-2.5 text-center text-sm font-semibold text-white hover:bg-cyan-800"
            >
              Hyr
            </Link>
          </div>
        )}
        {phase === "failed" && (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h1 className="text-lg font-semibold text-slate-900">Lidhja nuk vlen</h1>
            <p role="alert" className="mt-2 text-sm text-slate-600">
              Lidhja është e pavlefshme, e përdorur ose ka skaduar. Kërkoni një të re.
            </p>
            <Link href="/forgot-password" className="mt-5 block text-sm font-medium text-cyan-700 hover:underline">
              Kërko një lidhje të re
            </Link>
          </div>
        )}
        {phase === "form" && (
          <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h1 className="text-lg font-semibold text-slate-900">Fjalëkalim i ri</h1>
            <p className="mt-1 text-sm text-slate-500">
              Pasi ta ruani, çdo seancë e hapur e llogarisë mbyllet. Nëse keni verifikim në dy hapa, mbetet aktiv.
            </p>
            <label className="mt-6 block text-sm font-medium text-slate-700">
              Fjalëkalimi i ri
              <input
                type="password"
                required
                minLength={10}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-600/20"
              />
              <span className="mt-1 block text-xs font-normal text-slate-500">Të paktën 10 shenja.</span>
            </label>
            <label className="mt-4 block text-sm font-medium text-slate-700">
              Përsëriteni
              <input
                type="password"
                required
                autoComplete="new-password"
                value={again}
                onChange={(e) => setAgain(e.target.value)}
                className="mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-600/20"
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
              {busy ? "Një moment…" : "Ruaj fjalëkalimin"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
