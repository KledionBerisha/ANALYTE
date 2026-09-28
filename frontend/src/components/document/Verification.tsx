/**
 * Si u kontrollua shpjegimi.
 *
 * Çdo përpjekje e gjeneruesit, e pranuar apo jo, me shkeljet e gjetura.
 * Tekstet e refuzuara nuk shfaqen — vetëm pse u refuzuan. Paraqitja e plotë
 * e rrugës është pjesë e premtimit: pacienti mund të shohë që kontrolli
 * ndodhi dhe çfarë ndali.
 */

import type { Assertion, CrossReference, Finding, VerificationOut } from "@/lib/api/client";
import { CROSSREF_LABEL, STATUS_LABEL, VIOLATION_LABEL } from "@/lib/labels";

export function Verification({ verification }: { verification: VerificationOut }) {
  return (
    <details className="group rounded-2xl border border-slate-200 bg-white">
      <summary className="flex cursor-pointer list-none items-center justify-between px-6 py-4">
        <span className="font-semibold text-slate-900">Si u kontrollua shpjegimi</span>
        <span className="text-sm text-slate-500 group-open:hidden">Shfaq</span>
        <span className="hidden text-sm text-slate-500 group-open:inline">Fshih</span>
      </summary>
      <ol className="space-y-3 border-t border-slate-100 px-6 py-5">
        {verification.attempts.map((attempt) => {
          const violations = attempt.verification?.violations ?? [];
          return (
            <li key={attempt.attempt} className="rounded-xl bg-slate-50 px-4 py-3">
              <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                <span className="font-medium text-slate-900">
                  {attempt.is_fallback ? "Shabllon rezervë" : `Përpjekja ${attempt.attempt}`}
                  <span className="ml-2 font-normal text-slate-500">{attempt.generator}</span>
                </span>
                <span
                  className={`text-xs font-medium ${
                    attempt.delivered ? "text-emerald-700" : attempt.failed ? "text-rose-700" : "text-amber-700"
                  }`}
                >
                  {attempt.delivered
                    ? "U shfaq"
                    : attempt.failed
                      ? "Gjeneruesi dështoi"
                      : `U refuzua · ${violations.length} shkelje`}
                </span>
              </div>
              {attempt.verification && (
                <p className="mt-1 text-xs text-slate-500">
                  Rregullat {attempt.verification.rules_version}
                  {attempt.verification.classifier_version && ` · klasifikuesi ${attempt.verification.classifier_version}`} ·{" "}
                  {attempt.verification.duration_ms} ms
                </p>
              )}
              {violations.length > 0 && (
                <ul className="mt-2 space-y-1 text-sm">
                  {violations.map((v, i) => (
                    <li key={i} className="text-slate-700">
                      <span className="font-medium text-amber-800">{VIOLATION_LABEL[v.type] ?? v.type}:</span> {v.evidence}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          );
        })}
      </ol>
    </details>
  );
}

/**
 * Mospërputhjet ndërmjet shënimit të mjekut dhe matjes — të paraqitura, jo të
 * fshehura. Sistemi nuk vendos kush ka të drejtë; ai tregon që të dyja nuk
 * përputhen dhe e lë bisedën te mjeku.
 */
export function Contradictions({
  refs,
  findings,
  assertions,
}: {
  refs: CrossReference[];
  findings: Finding[];
  assertions: Assertion[];
}) {
  const shown = refs.filter((r) => r.state === "contradiction" || r.state === "mentioned_not_measured");
  if (shown.length === 0) return null;
  const finding = new Map(findings.map((f) => [f.id, f]));
  const assertion = new Map(assertions.map((a) => [a.id, a]));

  return (
    <section className="rounded-2xl border border-amber-200 bg-amber-50/60 px-6 py-4">
      <h2 className="text-sm font-semibold text-amber-900">Për t&apos;u diskutuar me mjekun</h2>
      <ul className="mt-2 space-y-2 text-sm text-amber-950">
        {shown.map((r) => {
          const said = r.assertion_id ? assertion.get(r.assertion_id) : undefined;
          const measured = r.finding_id ? finding.get(r.finding_id) : undefined;
          return (
            <li key={r.id}>
              {said && <span className="italic">“{said.text_span}”</span>}
              <span className="block text-amber-800">
                {CROSSREF_LABEL[r.state]}
                {measured &&
                  ` — vlera e matur: ${String(measured.value_canonical)} ${measured.unit_canonical} (${STATUS_LABEL[measured.status]?.toLowerCase()})`}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
