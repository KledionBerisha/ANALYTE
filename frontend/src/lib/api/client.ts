/**
 * Klienti i API-së.
 *
 * Tipat vijnë nga `schema.d.ts`, i gjeneruar nga skema OpenAPI e shërbimit
 * (`npm run api:types`), jo të shkruar me dorë.
 *
 * Tokenët ruhen në `sessionStorage`: mbyllja e skedës e mbyll seancën. Për të
 * dhëna shëndetësore kjo është zgjedhja më e matur se `localStorage`, ku një
 * seancë mbetet e hapur në një kompjuter të përbashkët pa afat.
 *
 * Një 401 provon një rifreskim të vetëm dhe e përsërit kërkesën; nëse edhe
 * rifreskimi dështon, seanca pastrohet dhe përdoruesi kthehet te hyrja.
 */

import type { components } from "./schema";

export type Schemas = components["schemas"];
export type DocumentOut = Schemas["DocumentOut"];
export type DocumentPage = Schemas["DocumentPage"];
export type StatusOut = Schemas["StatusOut"];
export type ExplanationOut = Schemas["ExplanationOut"];
export type VerificationOut = Schemas["VerificationOut"];
export type Finding = Schemas["AnalyteFinding"];
export type Assertion = Schemas["ReportAssertion"];
export type CrossReference = Schemas["CrossReference"];
export type PagesOut = Schemas["PagesOut"];
export type Tokens = Schemas["Tokens"];
export type UserOut = Schemas["UserOut"];

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const ACCESS = "analyte.access";
const REFRESH = "analyte.refresh";

/** Gabimi i API-së në formën RFC 7807. */
export class ApiError extends Error {
  constructor(
    public status: number,
    public title: string,
    public detail?: string,
  ) {
    super(detail ? `${title}: ${detail}` : title);
  }
}

function storage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.sessionStorage;
  } catch {
    return null;
  }
}

export const session = {
  access: () => storage()?.getItem(ACCESS) ?? null,
  refresh: () => storage()?.getItem(REFRESH) ?? null,
  save(tokens: Tokens) {
    storage()?.setItem(ACCESS, tokens.access_token);
    storage()?.setItem(REFRESH, tokens.refresh_token);
  },
  clear() {
    storage()?.removeItem(ACCESS);
    storage()?.removeItem(REFRESH);
  },
};

let onSessionLost: () => void = () => {};
export function whenSessionLost(callback: () => void) {
  onSessionLost = callback;
}

async function toError(response: Response): Promise<ApiError> {
  try {
    const body = await response.json();
    return new ApiError(response.status, body.title ?? response.statusText, body.detail);
  } catch {
    return new ApiError(response.status, response.statusText || "Gabim i panjohur");
  }
}

async function tryRefresh(): Promise<boolean> {
  const token = session.refresh();
  if (!token) return false;
  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: token }),
  });
  if (!response.ok) return false;
  session.save(await response.json());
  return true;
}

async function send(path: string, init: RequestInit = {}, retry = true): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = session.access();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });

  if (response.status === 401 && retry && session.refresh()) {
    if (await tryRefresh()) return send(path, init, false);
    session.clear();
    onSessionLost();
  }
  if (!response.ok) throw await toError(response);
  return response;
}

export const api = {
  async json<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await send(path, init);
    return response.status === 204 ? (undefined as T) : response.json();
  },

  post<T>(path: string, body: unknown): Promise<T> {
    return api.json<T>(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  },

  upload(file: File) {
    const form = new FormData();
    form.append("file", file);
    return api.json<Schemas["UploadOut"]>("/documents", { method: "POST", body: form });
  },

  remove(id: string) {
    return api.json<void>(`/documents/${id}`, { method: "DELETE" });
  },

  /** Figura e faqes, si URL objekti — `<img>` nuk dërgon token. */
  async pageImage(id: string, page: number): Promise<string> {
    const response = await send(`/documents/${id}/pages/${page}`);
    return URL.createObjectURL(await response.blob());
  },
};
