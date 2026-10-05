"use client";

import Link from "next/link";
import { useState } from "react";

import { Logo } from "@/components/AppShell";
import { api, ApiError } from "@/lib/api/client";

/**
 * Kërkesa për lidhjen e rivendosjes së fjalëkalimit (ADR 0018).
 *
 * Përgjigja e shërbimit është e njëjtë për çdo email, dhe ndërfaqja shfaq vetëm atë: nuk thotë kurrë nëse email-i
 * ka llogari.
 */
export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setSent((await api.forgotPassword(email)).message);
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
        {sent !== null ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h1 className="text-lg font-semibold text-slate-900">Kontrolloni email-in</h1>
            <p role="status" className="mt-2 text-sm text-slate-600">
              {sent}
            </p>
          </div>
        ) : (
          <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h1 className="text-lg font-semibold text-slate-900">Harruat fjalëkalimin?</h1>
            <p className="mt-1 text-sm text-slate-500">
              Shkruani email-in e llogarisë. Do t&apos;ju dërgojmë një lidhje për të vendosur një fjalëkalim të ri.
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
              {busy ? "Një moment…" : "Dërgo lidhjen"}
            </button>
          </form>
        )}
        <p className="mt-4 text-center text-sm text-slate-500">
          <Link href="/login" className="font-medium text-cyan-700 hover:underline">
            Mbrapa te hyrja
          </Link>
        </p>
      </div>
    </div>
  );
}
