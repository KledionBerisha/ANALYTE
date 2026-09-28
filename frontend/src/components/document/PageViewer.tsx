"use client";

/**
 * Faqja e dokumentit origjinal, me kutinë e vlerës së zgjedhur.
 *
 * Kutitë janë në pika PDF me origjinë lart-majtas (ADR 0007), prandaj
 * vendosen si përqindje të përmasave të faqes dhe ndjekin figurën në çdo
 * gjerësi ekrani. Për dokumentet e lexuara me OCR, kutia vjen nga faqja e
 * drejtuar dhe mund të zhvendoset pak nga figura e anuar — kjo shënohet.
 */

import { useEffect, useState } from "react";

import { api, type Finding, type PagesOut } from "@/lib/api/client";

type Box = NonNullable<Finding["bbox"]>;

export function PageViewer({
  documentId,
  selected,
  scanned,
}: {
  documentId: string;
  selected: Finding | null;
  scanned: boolean;
}) {
  const [pages, setPages] = useState<PagesOut | null>(null);
  const [page, setPage] = useState(1);
  const [image, setImage] = useState<{ page: number; url: string } | null>(null);
  const [failed, setFailed] = useState(false);

  // Zgjedhja e një vlere hap faqen e saj. Rregullohet gjatë vizatimit, jo në
  // efekt, që faqja e re të mos vizatohet një herë me kutinë e vjetër.
  const [shownFor, setShownFor] = useState(selected);
  if (selected !== shownFor) {
    setShownFor(selected);
    if (selected) setPage(selected.page);
  }

  useEffect(() => {
    api
      .json<PagesOut>(`/documents/${documentId}/pages`)
      .then(setPages)
      .catch(() => setFailed(true));
  }, [documentId]);

  useEffect(() => {
    let url: string | null = null;
    api
      .pageImage(documentId, page)
      .then((u) => {
        url = u;
        setImage({ page, url: u });
      })
      .catch(() => setFailed(true));
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [documentId, page]);

  if (failed) {
    return <p className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">Faqja nuk u ngarkua.</p>;
  }

  const box: Box | null = selected && selected.page === page ? (selected.bbox ?? null) : null;
  const src = image?.page === page ? image.url : null;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white">
      <header className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
        <h2 className="text-sm font-semibold text-slate-900">Dokumenti origjinal</h2>
        {pages && pages.count > 1 && (
          <div className="flex items-center gap-1 text-sm">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded px-2 py-0.5 text-slate-600 hover:bg-slate-100 disabled:opacity-30"
              aria-label="Faqja e mëparshme"
            >
              ‹
            </button>
            <span className="tabular-nums text-slate-500">
              {page} / {pages.count}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(pages.count, p + 1))}
              disabled={page === pages.count}
              className="rounded px-2 py-0.5 text-slate-600 hover:bg-slate-100 disabled:opacity-30"
              aria-label="Faqja tjetër"
            >
              ›
            </button>
          </div>
        )}
      </header>
      <div className="p-3">
        <div className="relative overflow-hidden rounded-lg bg-slate-100 ring-1 ring-slate-200">
          {src ? (
            // eslint-disable-next-line @next/next/no-img-element -- URL objekti, jo burim statik
            <img src={src} alt={`Faqja ${page} e dokumentit`} className="block w-full" />
          ) : (
            <div className="aspect-[1/1.414] animate-pulse" />
          )}
          {box && pages && src && (
            <div
              className="source-box pointer-events-none absolute rounded-sm"
              style={{
                left: `${(box.x0 / pages.width) * 100}%`,
                top: `${(box.y0 / pages.height) * 100}%`,
                width: `${((box.x1 - box.x0) / pages.width) * 100}%`,
                height: `${((box.y1 - box.y0) / pages.height) * 100}%`,
              }}
            />
          )}
        </div>
        <p className="mt-2 px-1 text-xs text-slate-500">
          {selected
            ? `${selected.analyte_name_raw} — rreshti nga i cili u lexua vlera.`
            : "Zgjidhni një vlerë për të parë nga u lexua."}
          {scanned && selected && " Te dokumentet e skanuara kutia mund të jetë pak e zhvendosur."}
        </p>
      </div>
    </section>
  );
}
