"use client";

/**
 * Shpjegimi i dorëzuar.
 *
 * Teksti është ai që kaloi verifikimin, i paprekur në përmbajtje. Ndërfaqja
 * vetëm e ndan: njoftimi kritik (SP4) dhe shënimi për profesionistin (SP7)
 * dalin si elemente më vete, dhe citimet e mjekut dallohen nga ajo që thotë
 * sistemi — i njëjti dallim që verifikimi bën (ADR 0010).
 */

import { useState } from "react";

import type { ExplanationOut } from "@/lib/api/client";

const QUOTE = "Mjeku ka shënuar:";
const PREVIEW = 8;
/** Shpjegimi i gjatë palohet. Teksti nuk shkurtohet: pjesa e fshehur
 *  mbetet një klikim larg, dhe butoni thotë sa fjali mbeten. */

function sentences(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+(?=[A-ZËÇ“])/u)
    .map((s) => s.trim())
    .filter(Boolean);
}

export function CriticalBanner({ text }: { text: string }) {
  return (
    <div role="alert" className="flex gap-3 rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-rose-900">
      <svg aria-hidden viewBox="0 0 24 24" className="mt-0.5 size-5 shrink-0 text-rose-600" fill="currentColor">
        <path d="M12 2.25a1 1 0 0 1 .87.5l9.5 16.5A1 1 0 0 1 21.5 20.75h-19a1 1 0 0 1-.87-1.5l9.5-16.5a1 1 0 0 1 .87-.5Zm0 6a.9.9 0 0 0-.9.9v4.7a.9.9 0 1 0 1.8 0V9.15a.9.9 0 0 0-.9-.9Zm0 9.3a1.1 1.1 0 1 0 0-2.2 1.1 1.1 0 0 0 0 2.2Z" />
      </svg>
      <p className="font-medium">{text}</p>
    </div>
  );
}

export function VerificationBadge({ explanation }: { explanation: ExplanationOut }) {
  const { verification } = explanation;
  if (verification.is_fallback) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-800 ring-1 ring-inset ring-amber-200">
        Shpjegim i thjeshtë i sistemit
      </span>
    );
  }
  return (
    <span
      title={`Kontrolluar me ${verification.mode === "rules" ? "rregulla" : "rregulla dhe klasifikues"}; ${verification.violation_count} shkelje`}
      className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-800 ring-1 ring-inset ring-emerald-200"
    >
      <svg aria-hidden viewBox="0 0 20 20" className="size-3.5" fill="currentColor">
        <path d="M10 1.5 3 4.25v5.1c0 4.3 2.95 8.1 7 9.15 4.05-1.05 7-4.85 7-9.15v-5.1L10 1.5Zm3.53 6.28-4.24 4.95a.75.75 0 0 1-1.1.04L6.4 10.98a.75.75 0 1 1 1.06-1.06l1.2 1.2 3.72-4.34a.75.75 0 1 1 1.14.98Z" />
      </svg>
      I kontrolluar · asnjë shkelje e gjetur
    </span>
  );
}

export function OcrNotice({ explanation }: { explanation: ExplanationOut }) {
  const notice = explanation.notices.find((n) => n.code === "ocr");
  if (!notice) return null;
  return (
    <div className="flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-amber-900">
      <svg aria-hidden viewBox="0 0 20 20" className="mt-0.5 size-5 shrink-0 text-amber-600" fill="currentColor">
        <path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16Zm0 4a.9.9 0 0 1 .9.9v3.6a.9.9 0 1 1-1.8 0V6.9A.9.9 0 0 1 10 6Zm0 8.4a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z" />
      </svg>
      <p>{notice.text}</p>
    </div>
  );
}

export function Explanation({ explanation }: { explanation: ExplanationOut }) {
  const [expanded, setExpanded] = useState(false);
  const body = sentences(
    explanation.text
      .replace(explanation.banner ?? "\u0000", "")
      .replace(explanation.disclaimer, ""),
  );
  const own = body.filter((s) => !s.startsWith(QUOTE));
  const quotes = body.filter((s) => s.startsWith(QUOTE)).map((s) => s.slice(QUOTE.length).trim());

  return (
    <section className="rounded-2xl border border-slate-200 bg-white">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-6 py-4">
        <h2 className="font-semibold text-slate-900">Shpjegimi</h2>
        <VerificationBadge explanation={explanation} />
      </header>

      <div className="space-y-3 px-6 py-5 leading-relaxed text-slate-800">
        {(expanded ? own : own.slice(0, PREVIEW)).map((sentence, i) => (
          <p key={i}>{sentence}</p>
        ))}
        {own.length > PREVIEW && (
          <button
            onClick={() => setExpanded((e) => !e)}
            className="text-sm font-medium text-cyan-700 hover:underline"
          >
            {expanded ? "Shfaq më pak" : `Lexo të gjithë shpjegimin (${own.length - PREVIEW} fjali të tjera)`}
          </button>
        )}
      </div>

      {quotes.length > 0 && (
        <div className="border-t border-slate-100 px-6 py-5">
          <h3 className="text-sm font-semibold text-slate-900">Çfarë ka shënuar mjeku</h3>
          <p className="mt-0.5 text-xs text-slate-500">Fjalë për fjalë nga raporti — sistemi nuk i riformulon.</p>
          <ul className="mt-3 space-y-2">
            {quotes.map((quote, i) => (
              <li key={i} className="border-l-2 border-cyan-600 bg-slate-50 py-1.5 pr-3 pl-3 text-slate-800">
                {quote}
              </li>
            ))}
          </ul>
        </div>
      )}

      {explanation.notices.some((n) => n.code !== "ocr") && (
        <div className="border-t border-slate-100 px-6 py-4">
          <ul className="space-y-1.5 text-sm text-slate-600">
            {explanation.notices
              .filter((n) => n.code !== "ocr")
              .map((notice) => (
                <li key={notice.code} className="flex gap-2">
                  <span aria-hidden className="mt-2 size-1 shrink-0 rounded-full bg-slate-400" />
                  {notice.text}
                </li>
              ))}
          </ul>
        </div>
      )}

      <footer className="rounded-b-2xl bg-slate-50 px-6 py-4 text-sm text-slate-600">{explanation.disclaimer}</footer>
    </section>
  );
}
