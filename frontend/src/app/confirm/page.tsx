"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { Logo } from "@/components/AppShell";
import { api, ApiError } from "@/lib/api/client";

type Result = "working" | "confirmed" | "failed";

/**
 * Lidhja nga email-i: `/confirm?token=…`.
 *
 * Tokeni lexohet një herë dhe hiqet menjëherë nga adresa (`replaceState`), që të mos mbetet te historiku
 * ose te koka `Referer` e faqeve të tjera. `started` e ndalon thirrjen e dytë që React e bën në zhvillim
 * (StrictMode): tokeni vlen një herë, dhe e dyta do ta shfaqte si të dështuar një lidhje të mirë.
 */
export default function ConfirmPage() {
  const [result, setResult] = useState<Result>("working");
  const [detail, setDetail] = useState<string | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const token = new URLSearchParams(window.location.search).get("token");
    window.history.replaceState(null, "", window.location.pathname);
    // Pa token, e njëjta rrugë dështimi si lidhja e shpenzuar: nuk ka çfarë t'i dërgohet shërbimit.
    (token ? api.confirmEmail(token) : Promise.reject(new ApiError(400, "Lidhja nuk ka token")))
      .then(() => setResult("confirmed"))
      .catch((caught) => {
        setDetail(caught instanceof ApiError ? caught.title : null);
        setResult("failed");
      });
  }, []);

  return (
    <div className="grid flex-1 place-items-center px-4 py-16">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Logo />
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          {result === "working" && <p className="text-sm text-slate-600">Duke konfirmuar email-in…</p>}
          {result === "confirmed" && (
            <>
              <h1 className="text-lg font-semibold text-slate-900">Email-i u konfirmua</h1>
              <p role="status" className="mt-2 text-sm text-slate-600">
                Llogaria është aktive. Tani mund të hyni.
              </p>
              <Link
                href="/login"
                className="mt-5 block rounded-lg bg-cyan-700 px-4 py-2.5 text-center text-sm font-semibold text-white hover:bg-cyan-800"
              >
                Hyr
              </Link>
            </>
          )}
          {result === "failed" && (
            <>
              <h1 className="text-lg font-semibold text-slate-900">Lidhja nuk vlen</h1>
              <p role="alert" className="mt-2 text-sm text-slate-600">
                {detail ?? "Lidhja është e pavlefshme ose ka skaduar."} Mund të kërkoni një të re nga faqja e hyrjes.
              </p>
              <Link href="/login" className="mt-5 block text-sm font-medium text-cyan-700 hover:underline">
                Te hyrja
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
