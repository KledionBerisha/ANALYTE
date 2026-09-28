/**
 * Hapat e përpunimit, ndërsa ndodhin.
 *
 * Hapat vijnë nga kalimet e regjistruara në shërbim, jo nga një kohëmatës i
 * rremë: çdo shenjë e plotësuar është një kalim që ndodhi vërtet.
 */

import type { StatusOut } from "@/lib/api/client";
import { PIPELINE, STATE_LABEL } from "@/lib/labels";

export function Progress({ status }: { status: StatusOut }) {
  const reached = new Set(["uploaded", ...status.transitions.map((t) => t.target)]);
  const steps = reached.has("ocr_running")
    ? [...PIPELINE.slice(0, 2), "ocr_running", ...PIPELINE.slice(2)]
    : PIPELINE;

  return (
    <section className="mx-auto max-w-md rounded-2xl border border-slate-200 bg-white px-6 py-6">
      <h2 className="font-semibold text-slate-900">Duke e përpunuar dokumentin</h2>
      <p className="mt-1 text-sm text-slate-500">Zakonisht zgjat disa sekonda; dokumentet e skanuara pak më shumë.</p>
      <ol className="mt-5 space-y-3">
        {steps.map((step) => {
          const done = reached.has(step) && step !== status.state;
          const current = step === status.state;
          return (
            <li key={step} className="flex items-center gap-3 text-sm">
              <span
                className={`grid size-5 place-items-center rounded-full text-[10px] ${
                  done
                    ? "bg-cyan-700 text-white"
                    : current
                      ? "bg-cyan-100 ring-2 ring-cyan-600"
                      : "bg-slate-100"
                }`}
              >
                {done && "✓"}
                {current && <span className="size-1.5 animate-pulse rounded-full bg-cyan-700" />}
              </span>
              <span className={done || current ? "text-slate-900" : "text-slate-400"}>{STATE_LABEL[step]}</span>
            </li>
          );
        })}
      </ol>
      {status.job?.failed && (
        <p role="alert" className="mt-5 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
          Përpunimi u ndal nga një gabim i sistemit. Dokumenti nuk u humb; provoni ta ngarkoni sërish.
        </p>
      )}
    </section>
  );
}
