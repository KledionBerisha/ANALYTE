"use client";

import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import {
  api,
  ApiError,
  type TwoFactorEnrollment,
  type TwoFactorStatus,
} from "@/lib/api/client";

const INPUT =
  "mt-1.5 block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-600/20";
const PRIMARY =
  "rounded-lg bg-cyan-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-cyan-800 disabled:opacity-60";

function message(caught: unknown): string {
  return caught instanceof ApiError ? caught.message : "Shërbimi nuk u arrit. Provoni sërish.";
}

function RecoveryCodes({ codes, onDone }: { codes: string[]; onDone: () => void }) {
  const [saved, setSaved] = useState(false);
  return (
    <div className="rounded-2xl border border-amber-300 bg-amber-50 p-6">
      <h2 className="text-base font-semibold text-slate-900">Ruani kodet e rimëkëmbjes</h2>
      <p className="mt-1 text-sm text-slate-700">
        Këto kode shfaqen vetëm një herë; shërbimi nuk i ruan dhe nuk mund t&apos;i shfaqë sërish. Secili vlen një herë
        dhe ju hap llogarinë nëse humbni aplikacionin e vërtetimit. Ruajini në një vend të sigurt.
      </p>
      <ul className="mt-4 grid grid-cols-2 gap-2 font-mono text-sm text-slate-900">
        {codes.map((code) => (
          <li key={code} className="rounded-md bg-white px-3 py-1.5 text-center">
            {code}
          </li>
        ))}
      </ul>
      <label className="mt-4 flex items-center gap-2 text-sm text-slate-700">
        <input type="checkbox" checked={saved} onChange={(e) => setSaved(e.target.checked)} />
        I kam ruajtur
      </label>
      <button type="button" disabled={!saved} onClick={onDone} className={`mt-4 ${PRIMARY}`}>
        Mbaro
      </button>
    </div>
  );
}

function Enroll({ onActive }: { onActive: (codes: string[]) => void }) {
  const [enrollment, setEnrollment] = useState<TwoFactorEnrollment | null>(null);
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function begin() {
    setBusy(true);
    setError(null);
    try {
      setEnrollment(await api.twoFactorEnroll());
    } catch (caught) {
      setError(message(caught));
    } finally {
      setBusy(false);
    }
  }

  async function confirm(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      onActive((await api.twoFactorConfirm(code)).recovery_codes);
    } catch (caught) {
      setError(message(caught));
      setBusy(false);
    }
  }

  if (enrollment === null) {
    return (
      <div>
        <p className="text-sm text-slate-600">
          Verifikimi në dy hapa kërkon, përveç fjalëkalimit, një kod me gjashtë shifra nga një aplikacion vërtetimi në
          telefon (p.sh. Google Authenticator, Aegis, 1Password). Aktivizimi mbyll seancat e tjera të hapura.
        </p>
        <button type="button" onClick={begin} disabled={busy} className={`mt-4 ${PRIMARY}`}>
          {busy ? "Një moment…" : "Aktivizo"}
        </button>
        {error && (
          <p role="alert" className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </p>
        )}
      </div>
    );
  }

  return (
    <form onSubmit={confirm}>
      <p className="text-sm text-slate-600">
        Shtoni llogarinë në aplikacion me çelësin më poshtë (zgjidhni «shtoni me çelës» ose «shkruani çelësin me
        dorë»), pastaj shkruani kodin që shfaq aplikacioni. Ky çelës shfaqet vetëm tani. Nuk ofrohet kod QR; nëse
        aplikacioni pranon adresë <code>otpauth://</code>, kopjojeni te fusha e tij.
      </p>
      <dl className="mt-4 space-y-3 text-sm">
        <div>
          <dt className="font-medium text-slate-700">Çelësi</dt>
          <dd className="mt-1 break-all rounded-md bg-slate-100 px-3 py-2 font-mono text-slate-900">
            {enrollment.secret}
          </dd>
        </div>
        <div>
          <dt className="font-medium text-slate-700">Adresa otpauth</dt>
          <dd className="mt-1 break-all rounded-md bg-slate-100 px-3 py-2 font-mono text-xs text-slate-900">
            {enrollment.otpauth_uri}
          </dd>
        </div>
      </dl>
      <label className="mt-4 block text-sm font-medium text-slate-700">
        Kodi nga aplikacioni
        <input
          type="text"
          required
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={7}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          className={`${INPUT} font-mono tracking-widest`}
        />
      </label>
      {error && (
        <p role="alert" className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {error}
        </p>
      )}
      <button type="submit" disabled={busy} className={`mt-4 ${PRIMARY}`}>
        {busy ? "Një moment…" : "Konfirmo dhe aktivizo"}
      </button>
    </form>
  );
}

function Disable({ onDone }: { onDone: () => void }) {
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.twoFactorDisable(password, code);
      onDone();
    } catch (caught) {
      setError(message(caught));
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
      >
        Çaktivizo
      </button>
    );
  }
  return (
    <form onSubmit={submit} className="max-w-sm">
      <p className="text-sm text-slate-600">
        Për ta çaktivizuar kërkohet fjalëkalimi dhe një kod i vlefshëm (nga aplikacioni ose një kod rimëkëmbjeje).
      </p>
      <label className="mt-4 block text-sm font-medium text-slate-700">
        Fjalëkalimi
        <input
          type="password"
          required
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={INPUT}
        />
      </label>
      <label className="mt-4 block text-sm font-medium text-slate-700">
        Kodi
        <input
          type="text"
          required
          autoComplete="one-time-code"
          maxLength={24}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          className={`${INPUT} font-mono tracking-widest`}
        />
      </label>
      {error && (
        <p role="alert" className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {error}
        </p>
      )}
      <button type="submit" disabled={busy} className={`mt-4 ${PRIMARY}`}>
        {busy ? "Një moment…" : "Çaktivizo verifikimin në dy hapa"}
      </button>
    </form>
  );
}

export default function SecurityPage() {
  const [status, setStatus] = useState<TwoFactorStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fresh, setFresh] = useState<string[] | null>(null);

  const load = useCallback(() => {
    api
      .twoFactorStatus()
      .then(setStatus)
      .catch((caught) => setError(message(caught)));
  }, []);

  useEffect(load, [load]);

  return (
    <AppShell>
      <div className="max-w-xl">
        <h1 className="text-xl font-semibold text-slate-900">Siguria e llogarisë</h1>
        <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">Verifikimi në dy hapa</h2>
          {error && (
            <p role="alert" className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {error}
            </p>
          )}
          {!status && !error && <p className="mt-3 text-sm text-slate-500">Duke u ngarkuar…</p>}
          {status && fresh && (
            <div className="mt-4">
              <RecoveryCodes
                codes={fresh}
                onDone={() => {
                  setFresh(null);
                  load();
                }}
              />
            </div>
          )}
          {status && !fresh && !status.enabled && (
            <div className="mt-3">
              <Enroll
                onActive={(codes) => {
                  setFresh(codes);
                  setStatus({ enabled: true, recovery_codes_remaining: codes.length });
                }}
              />
            </div>
          )}
          {status && !fresh && status.enabled && (
            <div className="mt-3">
              <p role="status" className="text-sm text-slate-700">
                Aktiv. Kode rimëkëmbjeje të mbetura: <strong>{status.recovery_codes_remaining}</strong>.
              </p>
              {status.recovery_codes_remaining <= 2 && (
                <p className="mt-2 text-sm text-amber-800">
                  Kanë mbetur pak kode. Për të marrë të reja, çaktivizojeni dhe aktivizojeni sërish.
                </p>
              )}
              <div className="mt-4">
                <Disable onDone={load} />
              </div>
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
