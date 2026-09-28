"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { CriticalBanner, Explanation, OcrNotice } from "@/components/document/Explanation";
import { Findings } from "@/components/document/Findings";
import { PageViewer } from "@/components/document/PageViewer";
import { Progress } from "@/components/document/Progress";
import { Contradictions, Verification } from "@/components/document/Verification";
import { StateBadge } from "@/components/StateBadge";
import {
  api,
  ApiError,
  type Assertion,
  type CrossReference,
  type DocumentOut,
  type ExplanationOut,
  type Finding,
  type StatusOut,
  type VerificationOut,
} from "@/lib/api/client";
import { formatDate, TERMINAL_EXPLANATION } from "@/lib/labels";

type Result = {
  findings: Finding[];
  assertions: Assertion[];
  refs: CrossReference[];
  explanation: ExplanationOut | null;
  verification: VerificationOut | null;
};

const POLL_MS = 800;

export default function DocumentPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [document, setDocument] = useState<DocumentOut | null>(null);
  const [status, setStatus] = useState<StatusOut | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [selected, setSelected] = useState<Finding | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Gjendja: pyetet derisa dokumenti të arrijë një gjendje përfundimtare.
  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const next = await api.json<StatusOut>(`/documents/${id}/status`);
        if (!alive) return;
        setStatus(next);
        if (!next.terminal && !next.job?.failed) timer = setTimeout(poll, POLL_MS);
      } catch (caught) {
        if (alive) setError(caught instanceof ApiError ? caught.message : "Dokumenti nuk u ngarkua.");
      }
    }
    api.json<DocumentOut>(`/documents/${id}`).then(setDocument).catch(() => {});
    poll();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [id]);

  // Rezultatet: vetëm pasi gjendja është përfundimtare.
  useEffect(() => {
    if (!status?.terminal) return;
    const delivered = status.state === "delivered";
    Promise.all([
      api.json<Finding[]>(`/documents/${id}/findings`),
      api.json<Assertion[]>(`/documents/${id}/assertions`),
      api.json<CrossReference[]>(`/documents/${id}/cross-refs`),
      delivered ? api.json<ExplanationOut>(`/documents/${id}/explanation`) : Promise.resolve(null),
      delivered ? api.json<VerificationOut>(`/documents/${id}/verification`) : Promise.resolve(null),
    ])
      .then(([findings, assertions, refs, explanation, verification]) =>
        setResult({ findings, assertions, refs, explanation, verification }),
      )
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Rezultatet nuk u ngarkuan."));
    api.json<DocumentOut>(`/documents/${id}`).then(setDocument).catch(() => {});
  }, [id, status?.terminal, status?.state]);

  async function remove() {
    if (!window.confirm("Ta fshij dokumentin dhe gjithë rezultatet e tij? Kjo nuk kthehet mbrapsht.")) return;
    await api.remove(id);
    router.push("/documents");
  }

  return (
    <AppShell>
      <nav className="mb-4 text-sm">
        <Link href="/documents" className="text-slate-500 hover:text-slate-900">
          ← Analizat tuaja
        </Link>
      </nav>

      {error && <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}

      {document && (
        <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="truncate text-2xl font-semibold tracking-tight text-slate-900">{document.filename}</h1>
            <p className="mt-1 text-sm text-slate-500">
              Ngarkuar {formatDate(document.uploaded_at)}
              {document.channel === "ocr" && " · lexuar me OCR"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {status && <StateBadge state={status.state} failed={Boolean(status.job?.failed)} />}
            <button onClick={remove} className="rounded-md px-3 py-1.5 text-sm text-slate-500 hover:bg-rose-50 hover:text-rose-700">
              Fshi
            </button>
          </div>
        </header>
      )}

      {status && !status.terminal && <Progress status={status} />}

      {status?.terminal && status.state !== "delivered" && (
        <section className="mx-auto max-w-lg rounded-2xl border border-slate-200 bg-white px-6 py-6">
          <h2 className="font-semibold text-slate-900">{TERMINAL_EXPLANATION[status.state]?.title}</h2>
          <p className="mt-2 text-slate-600">{TERMINAL_EXPLANATION[status.state]?.body}</p>
          <p className="mt-4 text-xs text-slate-400">Arsyeja teknike: {status.reason}</p>
        </section>
      )}

      {status?.state === "delivered" && !result && !error && (
        <p className="py-16 text-center text-sm text-slate-500">Duke ngarkuar rezultatet…</p>
      )}

      {result?.explanation && document && (
        <div className="space-y-6">
          {result.explanation.banner && <CriticalBanner text={result.explanation.banner} />}
          <OcrNotice explanation={result.explanation} />
          <div className="grid gap-6 lg:grid-cols-12">
            <div className="min-w-0 space-y-6 lg:col-span-7">
              <Explanation explanation={result.explanation} />
              <Contradictions refs={result.refs} findings={result.findings} assertions={result.assertions} />
              <Findings findings={result.findings} selected={selected} onSelect={setSelected} />
              {result.verification && <Verification verification={result.verification} />}
            </div>
            <div className="min-w-0 lg:col-span-5">
              <div className="lg:sticky lg:top-6">
                <PageViewer documentId={id} selected={selected} scanned={document.channel === "ocr"} />
              </div>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
