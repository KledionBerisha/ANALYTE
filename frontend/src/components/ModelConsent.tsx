"use client";

import type { PrivacyConfig } from "@/lib/api/client";

/**
 * Pëlqimi për dërgimin te ofruesi i modelit gjuhësor (ADR 0019).
 *
 * Shfaqet vetëm kur shërbimi e ka modelin të ndezur (`model_enabled`), dhe është gjithmonë i pashënuar në fillim:
 * pëlqimi vlen vetëm për ngarkimin që vjen pas tij, dhe kutia kthehet e pashënuar pas çdo ngarkimi.
 *
 * Teksti thotë çfarë del vërtet nga sistemi. Lista e fushave është e nxjerrë nga kërkesa që ndërton
 * `generation/prompt.py`: vlerat, njësitë, pozicioni dhe numrat e intervalit, emrat e analiteve, termat me shpjegimet
 * e fjalorit dhe fjalitë e mjekut fjalë për fjalë. Nuk thotë asgjë për kushtet e ofruesit, sepse sistemi nuk i di.
 */
export function ModelConsent({
  config,
  checked,
  onChange,
  disabled,
}: {
  config: PrivacyConfig | null;
  checked: boolean;
  onChange: (value: boolean) => void;
  disabled: boolean;
}) {
  if (!config?.model_enabled) return null;
  const provider = config.model_provider ? ` (${config.model_provider})` : "";

  return (
    <fieldset className="mb-4 rounded-2xl border border-slate-200 bg-white px-5 py-4">
      <legend className="px-1 text-sm font-semibold text-slate-900">Shpjegimi me model gjuhësor (opsional)</legend>
      <label className="flex cursor-pointer items-start gap-3 text-sm text-slate-800">
        <input
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={(e) => onChange(e.target.checked)}
          className="mt-0.5 size-4 shrink-0 accent-cyan-700"
        />
        <span>
          Pranoj që përmbajtja e strukturuar e <strong>këtij dokumenti</strong> t&apos;i dërgohet një ofruesi të jashtëm
          të modelit gjuhësor{provider} që të shkruajë shpjegimin. Pëlqimi vlen vetëm për këtë ngarkim.
        </span>
      </label>
      <p className="mt-2 pl-7 text-sm text-slate-500">
        Nëse nuk e shënoni, shpjegimi shkruhet nga shablloni i sistemit dhe asnjë përmbajtje e dokumentit nuk i dërgohet
        ofruesit. Zgjidhni para se të ngarkoni skedarin.
      </p>
      <details className="mt-3 pl-7 text-sm text-slate-600">
        <summary className="cursor-pointer font-medium text-slate-700">Çfarë dërgohet saktësisht</summary>
        <div className="mt-2 space-y-2">
          <p>
            <strong>Dërgohet:</strong> emrat e analiteve, vlerat e matura me njësitë, pozicioni i tyre ndaj intervalit
            referent dhe numrat e intervalit, termat mjekësorë që përmend raporti (me shpjegimet e tyre nga fjalori i
            sistemit), dhe fjalitë e mjekut të kopjuara fjalë për fjalë.
          </p>
          <p>
            <strong>Nuk dërgohet:</strong> emri juaj, mosha, gjinia, emri i skedarit, vetë PDF-ja, data e matjes dhe emri
            i laboratorit. Intervalet referente të disa analiteve ndryshojnë sipas gjinisë dhe dërgohen si numra, prandaj
            mund ta lënë të kuptohet.
          </p>
          <p>
            Para dërgimit, sistemi kontrollon fjalitë e mjekut për emra, data, numra telefoni, adresa dhe të ngjashme;
            nëse gjen diçka, dokumenti nuk dërgohet fare dhe shpjegimi del me shabllon, me njoftim. Ky kontroll është i
            përafërt: nuk i kap të gjitha.
          </p>
          <p>
            Ofruesi është një palë e tretë jashtë këtij sistemi. Sistemi nuk mund të garantojë si i ruan ose i përdor ato
            të dhëna.
          </p>
        </div>
      </details>
    </fieldset>
  );
}
