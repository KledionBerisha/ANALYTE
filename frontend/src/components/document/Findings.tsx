/**
 * Vlerat e nxjerra, secila me statusin dhe burimin e vet.
 *
 * Vlera tregohet ashtu siç vjen nga shërbimi — varg dhjetor i saktë — pa u
 * kthyer në numër të JavaScript-it, që ekrani të tregojë saktësisht atë që u
 * verifikua.
 */

import type { Finding } from "@/lib/api/client";
import { STATUS_LABEL, STATUS_TONE } from "@/lib/labels";

function interval(f: Finding): string {
  if (f.ref_low != null && f.ref_high != null) return `${f.ref_low} – ${f.ref_high}`;
  if (f.ref_high != null) return `deri ${f.ref_high}`;
  if (f.ref_low != null) return `nga ${f.ref_low}`;
  return "—";
}

const ORDER: Record<string, number> = {
  critical_high: 0,
  critical_low: 0,
  high: 1,
  low: 1,
  uninterpretable: 2,
  normal: 3,
};

export function Findings({
  findings,
  selected,
  onSelect,
}: {
  findings: Finding[];
  selected: Finding | null;
  onSelect: (finding: Finding) => void;
}) {
  const sorted = [...findings].sort((a, b) => (ORDER[a.status] ?? 9) - (ORDER[b.status] ?? 9));
  const abnormal = findings.filter((f) => ["high", "low", "critical_high", "critical_low"].includes(f.status)).length;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white">
      <header className="flex items-baseline justify-between border-b border-slate-100 px-6 py-4">
        <h2 className="font-semibold text-slate-900">Vlerat</h2>
        <span className="text-sm text-slate-500">
          {findings.length} vlera · {abnormal} jashtë intervalit
        </span>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
              <th className="px-6 py-2.5 font-medium">Analiti</th>
              <th className="px-3 py-2.5 text-right font-medium">Vlera</th>
              <th className="px-3 py-2.5 font-medium">Intervali referent</th>
              <th className="px-6 py-2.5 font-medium">Statusi</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {sorted.map((f) => {
              const active = selected?.id === f.id;
              return (
                <tr
                  key={f.id}
                  onClick={() => onSelect(f)}
                  className={`cursor-pointer ${active ? "bg-cyan-50" : "hover:bg-slate-50"}`}
                  aria-selected={active}
                >
                  <td className="px-6 py-2.5">
                    <span className="font-medium text-slate-900">{f.analyte_name_canonical}</span>
                    {f.analyte_name_raw !== f.analyte_name_canonical && (
                      <span className="ml-2 text-xs text-slate-400">{f.analyte_name_raw}</span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-right tabular-nums text-slate-900">
                    {String(f.value_canonical)} <span className="text-slate-500">{f.unit_canonical}</span>
                  </td>
                  <td className="px-3 py-2.5 tabular-nums text-slate-600">{interval(f)}</td>
                  <td className="px-6 py-2.5">
                    <span className={`inline-block whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${STATUS_TONE[f.status]}`}>
                      {STATUS_LABEL[f.status] ?? f.status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
