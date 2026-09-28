/**
 * Emërtimet shqip për vlerat e enum-eve të shërbimit.
 *
 * Shërbimi flet me vlera angleze sepse ato ruhen në bazë; përdoruesi i sheh
 * vetëm këtu, të përkthyera në një vend të vetëm.
 */

export const STATE_LABEL: Record<string, string> = {
  uploaded: "Ngarkuar",
  rejected: "Refuzuar",
  ingesting: "Po lexohet",
  ocr_running: "Po njihet teksti (OCR)",
  text_extracted: "Teksti u lexua",
  failed_ingestion: "Nuk u lexua",
  parsing: "Po nxirren vlerat",
  no_findings: "Pa gjetje",
  grounded: "Vlerat u interpretuan",
  generating: "Po shkruhet shpjegimi",
  verifying: "Po verifikohet",
  template_fallback: "Shabllon rezervë",
  delivered: "Gati",
};

/** Rendi i hapave që tregohen gjatë përpunimit. */
export const PIPELINE: string[] = [
  "uploaded",
  "ingesting",
  "text_extracted",
  "parsing",
  "grounded",
  "generating",
  "verifying",
  "delivered",
];

export const TERMINAL_EXPLANATION: Record<string, { title: string; body: string }> = {
  rejected: {
    title: "Skedari nuk u pranua",
    body: "Skedari nuk mund të lexohej si PDF. Kontrolloni që të keni ngarkuar raportin e laboratorit dhe provoni sërish.",
  },
  failed_ingestion: {
    title: "Dokumenti nuk u lexua",
    body: "Faqet e dokumentit nuk mund të lexoheshin. Kjo nuk do të thotë se dokumenti është bosh — vetëm se sistemi nuk arriti ta lexojë.",
  },
  no_findings: {
    title: "Nuk u gjetën vlera",
    body: "Dokumenti u lexua, por nuk përmban vlera laboratorike ose shënime të mjekut që sistemi i njeh.",
  },
};

export const STATUS_LABEL: Record<string, string> = {
  critical_low: "Dukshëm e ulët",
  low: "E ulët",
  normal: "Normale",
  high: "E lartë",
  critical_high: "Dukshëm e lartë",
  uninterpretable: "Pa interval",
};

export const STATUS_TONE: Record<string, string> = {
  critical_low: "bg-rose-100 text-rose-800 ring-rose-300",
  low: "bg-amber-50 text-amber-800 ring-amber-200",
  normal: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  high: "bg-amber-50 text-amber-800 ring-amber-200",
  critical_high: "bg-rose-100 text-rose-800 ring-rose-300",
  uninterpretable: "bg-slate-100 text-slate-600 ring-slate-200",
};

export const VIOLATION_LABEL: Record<string, string> = {
  ungrounded_number: "Numër i pambështetur",
  ungrounded_analyte: "Analit i pamatur",
  direction_mismatch: "Drejtim i gabuar",
  missing_critical: "Vlerë kritike e munguar",
  polarity_flip: "Mohim i përmbysur",
  hedge_removed: "Rezervë e hequr",
  fabricated_finding: "Gjetje e shpikur",
  omitted_recommendation: "Rekomandim i munguar",
  ungrounded_term_explanation: "Term i shpjeguar pa bazë",
  prohibited_claim: "Pohim i ndaluar",
};

export const CROSSREF_LABEL: Record<string, string> = {
  agreement: "Përputhet me vlerën",
  contradiction: "Nuk përputhet me vlerën",
  mentioned_not_measured: "Përmendet, por nuk është matur",
  measured_not_mentioned: "Matur, por pa koment",
};

const MONTHS = ["jan", "shk", "mar", "pri", "maj", "qer", "korr", "gush", "sht", "tet", "nën", "dhj"];

/** Data shqip, e formatuar me dorë: shumë shfletues nuk kanë të dhënat e
 *  lokalitetit `sq`, dhe `Intl` do të kthente pa zhurmë formatin anglez. */
export function formatDate(iso: string): string {
  const d = new Date(iso);
  const time = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}, ${time}`;
}

export function formatSize(bytes: number): string {
  return bytes < 1024 * 1024 ? `${Math.round(bytes / 1024)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
