import { STATE_LABEL } from "@/lib/labels";

const TONE: Record<string, string> = {
  delivered: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  rejected: "bg-rose-50 text-rose-700 ring-rose-200",
  failed_ingestion: "bg-rose-50 text-rose-700 ring-rose-200",
  no_findings: "bg-slate-100 text-slate-600 ring-slate-200",
};

export function StateBadge({ state, failed = false }: { state: string; failed?: boolean }) {
  const tone = failed
    ? "bg-rose-50 text-rose-700 ring-rose-200"
    : (TONE[state] ?? "bg-cyan-50 text-cyan-800 ring-cyan-200");
  const busy = !failed && !TONE[state];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${tone}`}>
      {busy && <span className="size-1.5 animate-pulse rounded-full bg-cyan-600" />}
      {failed ? "Gabim gjatë përpunimit" : (STATE_LABEL[state] ?? state)}
    </span>
  );
}
