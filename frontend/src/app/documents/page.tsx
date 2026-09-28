"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { StateBadge } from "@/components/StateBadge";
import { api, ApiError, type DocumentPage } from "@/lib/api/client";
import { formatDate, formatSize } from "@/lib/labels";

function Upload() {
  const router = useRouter();
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const uploaded = await api.upload(file);
      router.push(`/documents/${uploaded.id}`);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Ngarkimi dështoi.");
      setBusy(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => input.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          send(e.dataTransfer.files[0]);
        }}
        disabled={busy}
        className={`flex w-full flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-12 text-center transition ${
          dragging ? "border-cyan-600 bg-cyan-50" : "border-slate-300 bg-white hover:border-cyan-500 hover:bg-slate-50"
        }`}
      >
        <svg aria-hidden viewBox="0 0 24 24" className="size-10 text-cyan-700" fill="none" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 16V4m0 0-4 4m4-4 4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
        </svg>
        <span className="mt-3 font-semibold text-slate-900">
          {busy ? "Duke ngarkuar…" : "Ngarkoni raportin e laboratorit"}
        </span>
        <span className="mt-1 text-sm text-slate-500">PDF, deri në 20 MB · tërhiqeni këtu ose klikoni</span>
      </button>
      <input
        ref={input}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => send(e.target.files?.[0])}
      />
      {error && (
        <p role="alert" className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {error}
        </p>
      )}
    </div>
  );
}

function History() {
  const [page, setPage] = useState<DocumentPage | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api
      .json<DocumentPage>("/documents?limit=50")
      .then(setPage)
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Lista nuk u ngarkua."));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Rifreskim i lehtë ndërsa ndonjë dokument po përpunohet.
  useEffect(() => {
    if (!page?.items.some((d) => !d.terminal)) return;
    const timer = setInterval(load, 2000);
    return () => clearInterval(timer);
  }, [page, load]);

  if (error) return <p className="text-sm text-rose-700">{error}</p>;
  if (!page) return <p className="text-sm text-slate-500">Duke u ngarkuar…</p>;
  if (page.items.length === 0) {
    return (
      <p className="rounded-2xl border border-slate-200 bg-white px-6 py-10 text-center text-sm text-slate-500">
        Ende nuk keni ngarkuar asnjë dokument.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-slate-100 overflow-hidden rounded-2xl border border-slate-200 bg-white">
      {page.items.map((doc) => (
        <li key={doc.id}>
          <Link href={`/documents/${doc.id}`} className="flex items-center gap-4 px-5 py-4 hover:bg-slate-50">
            <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-slate-100 text-xs font-semibold text-slate-500">
              PDF
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate font-medium text-slate-900">{doc.filename}</span>
              <span className="block text-sm text-slate-500">
                {formatDate(doc.uploaded_at)} · {formatSize(doc.size_bytes)}
                {doc.channel === "ocr" && " · lexuar me OCR"}
              </span>
            </span>
            <StateBadge state={doc.state} />
          </Link>
        </li>
      ))}
    </ul>
  );
}

export default function DocumentsPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Analizat tuaja</h1>
        <p className="mt-1 text-slate-500">
          Sistemi lexon vlerat, i krahason me intervalin referent dhe shkruan një shpjegim që kontrollohet
          para se t&apos;ju shfaqet.
        </p>
        <div className="mt-8">
          <Upload />
        </div>
        <h2 className="mt-12 mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Historia</h2>
        <History />
      </div>
    </AppShell>
  );
}
