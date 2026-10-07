"""
Ndërtimi i shtojcave të punimit nga burimet e vërteta.

    python scripts/build_appendices.py

"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "thesis" / "appendices"
RESULTS = ROOT / "evaluation" / "results"
HEADER = (
    "<!-- E gjeneruar nga scripts/build_appendices.py. Mos e ndrysho me dorë: "
    "ndrysho burimin dhe rigjenero. -->\n\n"
)


def _relabel(table: str, old: int, new: str) -> str:
    """Tabelat e shtojcave marrin shkronjën e shtojcës: `Tabela 1.` → `Tabela B.1.`"""
    return table.replace(f"Tabela {old}.", f"Tabela {new}.", 1)


def _cell(text: str) -> str:
    return " ".join(str(text).replace("|", "/").split())


# A — terminologjia


def appendix_a() -> str:
    with (ROOT / "resources" / "terminology.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    unsourced = sum(1 for r in rows if "plotësohet" in r["source_ref"])
    lines = [
        "## Shtojca A — Tabela e plotë terminologjike shqip",
        "",
        (
            f"Tabela mban {len(rows)} terma. **{unsourced} prej tyre mbajnë ende vendmbajtës në "
            "kolonën e burimit**: shpjegimet janë përkufizime pune të autorit dhe nuk janë "
            "referuar te një burim i verifikueshëm. Pa referencë, tabela vetë është burim "
            "informacioni të paverifikuar; kjo është kufizim i shprehur te seksioni 7.6, jo "
            "detaj i fshehur këtu."
            if unsourced
            else f"Tabela mban {len(rows)} terma. Secili zë mban në kolonën e burimit faqen ose "
            "përshkruesin (MeSH, MedlinePlus, Cleveland Clinic, Testing.com) që u lexua më "
            "2026-10-06 dhe që e mbështet shpjegimin shqip; shpjegimi është formulim i autorit, "
            "jo përkthim i burimit. Citimi i evidencës për secilin zë ruhet te "
            "`docs/thesis/worksheets/burimet_e_gjetura.md`."
        ),
        "",
        "*Tabela A.1. Termat, shpjegimet, kategoritë dhe sinonimet*",
        "",
        "| Termi | Shpjegimi | Kategoria | Sinonimet | Burimi |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {_cell(r['term'])} | {_cell(r['explanation_sq'])} | {_cell(r['category'])} "
            f"| {_cell(r['synonyms'].replace('|', ', '))} | {_cell(r['source_ref'])} |"
        )
    lines += ["", *_advice_table()]
    return "\n".join(lines) + "\n"


def _advice_table() -> list[str]:
    """Tabela A.2 — këshillat me burim (ADR 0023), një rresht për analit dhe drejtim."""
    with (ROOT / "resources" / "advice.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    from analyte.catalog import load_analytes

    names = {a.loinc_code: a.name_canonical_sq for a in load_analytes()}
    direction = {"increased": "mbi intervalin", "decreased": "nën intervalin"}
    filled = [r for r in rows if r["advice_sq"].strip() and "plotësohet" not in r["source_ref"]]
    decided_empty = [
        r for r in rows if not r["advice_sq"].strip() and "plotësohet" not in r["source_ref"]
    ]
    pending = len(rows) - len(filled) - len(decided_empty)
    lines = [
        f"Tabela A.2 mban këshillat me burim (ADR 0023): një fjali e vetme për çdo analit dhe drejtim, e shtypur "
        f"fjalë për fjalë nën vlerën përkatëse dhe e mbrojtur nga R8. {len(filled)} nga {len(rows)} rreshta kanë fjali "
        f"dhe burim të lexuar; {len(decided_empty)} rresht(a) kanë burim por asnjë fjali, sepse burimi nuk jep asgjë "
        f"për atë drejtim, dhe pacientit nuk i shfaqet asgjë; {pending} mbeten pa burim. Fjalia nuk emërton gjendje, "
        "nuk jep trajtim dhe nuk parashikon: ajo tregon vetëm çfarë mund t'i thotë pacienti mjekut dhe cilët faktorë "
        "para-analitikë përmend burimi. Çdo rresht i plotësuar kalon vetë nëpër R1, R2, R3 dhe SP1–SP3 "
        "(`tests/unit/test_advice.py`).",
        "",
        "*Tabela A.2. Këshillat me burim sipas analitit dhe drejtimit*",
        "",
        "| Analiti | Drejtimi | Fjalia | Burimi |",
        "|---|---|---|---|",
    ]
    for r in rows:
        sentence = _cell(r["advice_sq"]) if r["advice_sq"].strip() else "—"
        lines.append(
            f"| {_cell(names[r['loinc_code']])} | {direction[r['direction']]} | {sentence} | {_cell(r['source_ref'])} |"
        )
    return lines


# B — analitet, njësitë, kombinimet


def appendix_b() -> str:
    from scripts import build_tables as tables

    lines = [
        "## Shtojca B — Paneli i plotë i analiteve",
        "",
        "Tabelat dalin nga `resources/` me `scripts/build_tables.py`, po ata skedarë që lexon "
        "sistemi. Intervalet janë ato të tabelës së brendshme, që përdoren vetëm kur dokumenti "
        "nuk e shtyp vetë intervalin.",
        "",
        _relabel(tables.table_1(), 1, "B.1"),
        "",
        _relabel(tables.table_2(), 2, "B.2"),
        "",
        _relabel(tables.table_5(), 5, "B.3"),
    ]
    return "\n".join(lines) + "\n"


# C — katalogu i rregullave me shembuj


def _examples() -> list[tuple[str, str, str, str]]:
    """(rregulli, lloji, fjalia me defekt, prova e rregullit) mbi korpusin e korruptuar."""
    from analyte.domain.enums import ViolationType as V
    from analyte.domain.policy import RULE_BY_VIOLATION
    from analyte.generation.templates import build as build_template
    from analyte.textnorm import sentences as split_sentences
    from analyte.verification.pipeline import verify
    from ml.data.build_corruption_set import build_samples
    from ml.evaluate_rule_detector import corpus

    documents = corpus(60, 42)
    contexts = dict(documents)
    samples = build_samples(documents, seed=42)
    wanted = (
        V.UNGROUNDED_NUMBER,
        V.UNGROUNDED_ANALYTE,
        V.DIRECTION_MISMATCH,
        V.POLARITY_FLIP,
        V.HEDGE_REMOVED,
        V.FABRICATED_FINDING,
        V.OMITTED_RECOMMENDATION,
    )
    out = []
    for defect in wanted:
        sample = next((s for s in samples if s.defect is defect), None)
        if sample is None:
            continue
        context = contexts[sample.document_id]
        clean = {t for t, _, _ in split_sentences(build_template(context))}
        changed = [t for t, _, _ in split_sentences(sample.text) if t not in clean]
        found = [v for v in verify(context, sample.text).violations if v.type is defect]
        sentence = changed[0] if changed else "(një fjali e fshirë)"
        evidence = found[0].evidence if found else "(rregulli nuk e kapi)"
        out.append((RULE_BY_VIOLATION[defect].id, defect.value, sentence, evidence))
    return out


def _prohibited_example() -> tuple[str, str, str, str] | None:
    """Një shembull i SP1-3 nga grupi B i autorit: korruptuesit nuk e prodhojnë."""
    from analyte.domain.enums import ViolationType
    from analyte.domain.policy import RULE_BY_VIOLATION
    from evaluation import kits

    contexts = dict(kits.kit_contexts())
    rows = kits.read_rows(kits.KIT_DIR / "B_fjalite.csv", kits.B_COLUMNS, kits.B_OPTIONAL)
    from analyte.domain.policy import DISCLAIMER_SQ
    from analyte.generation.templates import build as build_template
    from analyte.verification.pipeline import verify

    rule_id = RULE_BY_VIOLATION[ViolationType.PROHIBITED_CLAIM].id
    for row in rows:
        if row["etiketa"] != "prohibited_claim":
            continue
        context = contexts[row["konteksti"]]
        text = build_template(context).replace(DISCLAIMER_SQ, f"{row['fjalia']} {DISCLAIMER_SQ}")
        hits = [v for v in verify(context, text).violations if v.type.value == "prohibited_claim"]
        if hits:
            return rule_id, "prohibited_claim", row["fjalia"], hits[0].evidence
    return None


def appendix_c() -> str:
    from scripts import build_tables as tables

    lines = [
        "## Shtojca C — Katalogu i plotë i rregullave të verifikimit",
        "",
        _relabel(tables.table_4(), 4, "C.1"),
        "",
        "*Tabela C.2. Një shembull i vërtetë për çdo rregull që korruptuesit e prodhojnë, "
        "me provën që jep rregulli*",
        "",
        "Shembujt janë marrë nga korpusi i korruptuar (fara 42): fjalia që ndryshoi krahasuar me "
        "shabllonin e pastër, dhe prova e shkelësit të rregullit mbi të. R4 (vlera kritike që "
        "mungon) dhe R9 (shpjegimi i një termi të pashpjeguar) nuk kanë korruptues; R9 u mat "
        "vetëm mbi grupin B, ku kapi vetëm 1 nga 5 fjalitë (seksioni 6.7).",
        "",
        "| Rregulli | Lloji | Fjalia me defekt | Prova e rregullit |",
        "|---|---|---|---|",
    ]
    rows = _examples()
    extra = _prohibited_example()
    if extra:
        rows.append(extra)
    for rule, kind, sentence, evidence in rows:
        lines.append(f"| {rule} | `{kind}` | {_cell(sentence)} | {_cell(evidence)} |")
    return "\n".join(lines) + "\n"


# D, E, F — çfarë nuk ekziston, e thënë shprehimisht


def _llm_run() -> dict | None:
    """Parametrat e ekzekutimit të vërtetë me model, nga skedari i rezultatit (jo nga `.env`)."""
    for name in ("E8", "E7", "E9", "E6"):
        path = RESULTS / "llm" / name / "result.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")).get("metadata", {}).get("llm")
    return None


def _example_prompt() -> tuple[str, str]:
    """Kërkesa e vërtetë për një dokument të korpusit, dhe blloku i rishkrimit për një shkelje të vërtetë."""
    import random

    from analyte.domain.policy import DISCLAIMER_SQ
    from analyte.generation import templates
    from analyte.generation.prompt import build_prompt
    from analyte.verification.pipeline import verify
    from data_generator.ground_truth import build_document
    from data_generator.ids import IdFactory

    for index in range(200):
        rng = random.Random(f"appendix-d/{index}")
        context = build_document(rng, IdFactory(rng), scanned_share=0.0).context
        if context.critical_findings() and context.assertions and context.glossary:
            break
    else:  # pragma: no cover
        raise AssertionError("asnjë dokument me vlerë kritike, pohime dhe fjalor")

    first = build_prompt(context).user
    defective = templates.build(context).replace(
        DISCLAIMER_SQ, f"Vlera e matur është 987654. {DISCLAIMER_SQ}"
    )
    second = build_prompt(context, verify(context, defective).violations).user
    feedback = second[second.index("Shpjegimi i mëparshëm") :].split("\n\nShkruaje shpjegimin.")[0]
    return first, feedback


def appendix_d() -> str:
    from analyte.generation.prompt import PROMPT_VERSION, SYSTEM
    from evaluation import llm_judge, ungrounded

    run = _llm_run()
    user, feedback = _example_prompt()
    if run is not None:
        parameters = (
            "| Parametri | Vlera |\n|---|---|\n"
            f"| Ofruesi | `{run['provider']}` |\n"
            f"| Modeli | `{run['model']}` |\n"
            f"| Temperatura | {run['temperature']} |\n"
            f"| Arsyetimi (`thinking`) | `{run['thinking']}` (dërgohet vetëm te Gemini) |\n"
            f"| Kufiri i daljes | {run['max_output_tokens']} shenja |\n"
        )
    else:
        parameters = (
            "*Parametrat e ekzekutimit nuk janë ende të regjistruar: nuk ka rezultat të "
            "`evaluation/results/llm/`.*\n"
        )
    return (
        "## Shtojca D — Kërkesat për modelin gjuhësor\n\n"
        "Të gjitha kërkesat dalin nga kodi që i dërgon, jo nga një kopje e shkruar me dorë. Modeli "
        "merr vetëm `GroundingContext` (§5.2.1): asnjë kërkesë nuk ka parametër për dokumentin "
        "(një test e kontrollon). Përjashtim i vetëm është kushti A i ablacionit (E6), që sheh "
        "tekstin e dokumentit me qëllim, si bazë krahasuese.\n\n"
        "### Tabela D.1. Parametrat e ekzekutimit\n\n"
        + parameters
        + f"\nVersionet e kërkesave: gjeneruesi `{PROMPT_VERSION}`, kushti A "
        f"`{ungrounded.UNGROUNDED_PROMPT_VERSION}`, gjykatësi `{llm_judge.JUDGE_VERSION}`. Çdo "
        "përgjigje e modelit ruhet në `evaluation/cache/llm/` me kërkesën e plotë, prandaj çdo "
        "numër i Kapitullit 6 rikrijohet pa thirrje të reja.\n\n"
        "### D.2. Udhëzimet e gjeneruesit (kushtet B, C dhe D)\n\n"
        "Fjalë për fjalë, nga `generation/prompt.py`:\n\n"
        f"```text\n{SYSTEM}\n```\n\n"
        "**Vendim dizajni që duhet deklaruar.** Rregulli 3 e drejton modelin te shprehjet e "
        "pozicionit që verifikuesi i njeh («mbi intervalin referent», «nën intervalin referent»). "
        "Rregulli R3 e njeh drejtimin vetëm në ato forma, dhe një model që shkruan «i lartë» do ta "
        "kalonte R3 pa u parë. Pra kushtet B–D maten me një kërkesë që i përshtatet kontratës së "
        "verifikuesit; një kërkesë pa këtë kufizim do të prodhonte më shumë gabime drejtimi të "
        "padukshme për rregullat, jo më pak.\n\n"
        "### D.3. Një kërkesë e vërtetë për një dokument të korpusit\n\n"
        "Pjesa që ndryshon nga dokumenti në dokument (konteksti). Dokumenti është ndërtuar nga "
        "fara `appendix-d`; emrat e analiteve, vlerat dhe pohimet janë ato të kontekstit.\n\n"
        f"```text\n{user}\n```\n\n"
        "### D.4. Blloku i rigjenerimit\n\n"
        "Kur përpjekja e parë refuzohet, e dyta merr shkeljet e saj (fjalia e daljes dhe arsyeja "
        "e rregullit, asgjë nga dokumenti). Shembull i vërtetë: shablloni me një numër të shpikur.\n\n"
        f"```text\n{feedback}\n```\n\n"
        "### D.5. Kërkesa naive e kushtit A (E6)\n\n"
        "Pa udhëzime sigurie, pa strukturë dhe pa kontekst të bazuar; modeli merr tekstin e "
        "dokumentit.\n\n"
        f"```text\n{ungrounded.SYSTEM}\n\n"
        "Ky është dokumenti mjekësor i pacientit:\n\n[teksti i dokumentit]\n\n"
        "Shpjegoja pacientit çfarë thotë ky dokument, në gjuhë të thjeshtë.\n```\n\n"
        "### D.6. Gjykatësi i E12\n\n"
        "Gjykatësi merr po atë kontekst dhe po atë tekst si rregullat, dhe përkufizimet e "
        "rregullave nga katalogu (jo kodin e tyre):\n\n"
        f"```text\n{llm_judge.SYSTEM}\n```\n"
    )


def appendix_e() -> str:
    return (
        "## Shtojca E — Udhëzimet e anotimit për dokumentet reale\n\n"
        "**Nuk aplikohet.** Nuk u përdorën dokumente reale: miratimi etik nuk është marrë. Eksperimenti "
        "E13 (vlefshmëria e jashtme) mbetet i pamatur, dhe kjo deklarohet si kufizimi kryesor te "
        "seksioni 7.6. Grupet e shkruara C dhe B (`evaluation/handwritten/`) nuk janë dokumente "
        "reale dhe nuk e zëvendësojnë E13.\n"
    )


def appendix_f() -> str:
    return (
        "## Shtojca F — Instrumenti i studimit me përdorues\n\n"
        "**Nuk aplikohet.** Studimi me përdorues (PK7, E14) nuk u krye, kështu që nuk ka instrument "
        "për t'u paraqitur dhe nuk raportohen rezultate kuptueshmërie. Seksioni 6.9 e thotë këtë "
        "shprehimisht.\n"
    )


# G — skema SQL


def appendix_g() -> str:
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.schema import CreateIndex, CreateTable

    from analyte.persistence.tables import Base

    dialect = postgresql.dialect()
    statements = []
    for table in Base.metadata.sorted_tables:
        statements.append(str(CreateTable(table).compile(dialect=dialect)).strip() + ";")
        for index in sorted(table.indexes, key=lambda i: i.name or ""):
            statements.append(str(CreateIndex(index).compile(dialect=dialect)).strip() + ";")
    return (
        "## Shtojca G — Skema SQL e bazës së të dhënave\n\n"
        f"Skema PostgreSQL e ndërtuar nga modelet (`persistence/tables.py`): {len(Base.metadata.tables)} "
        "tabela. Migrimet Alembic (`backend/alembic/versions/`) e prodhojnë të njëjtën skemë; një test "
        "krahason rezultatin e tyre me modelet. Terminologjia dhe intervalet referente nuk janë në "
        "bazë (`resources/` është burimi i vetëm).\n\n```sql\n"
        + "\n\n".join(statements)
        + "\n```\n"
    )


# H — konfigurimet dhe farat


def appendix_h() -> str:
    from analyte.domain.policy import LEGACY_RULES_VERSION, POLICY_VERSION, RULES_VERSION
    from analyte.ingestion import ocr
    from evaluation.metrics import base

    manifest = json.loads((ROOT / "data" / "v1" / "manifest.json").read_text(encoding="utf-8"))
    summary = manifest["summary"]
    lines = [
        "## Shtojca H — Konfigurimet e eksperimenteve dhe farat fillestare",
        "",
        "*Tabela H.1. Korpusi sintetik*",
        "",
        "| Parametri | Vlera |",
        "|---|---|",
        f"| Versioni i gjeneruesit | `{manifest['generator_version']}` |",
        f"| Fara | {manifest['seed']} |",
        f"| Dokumente | {summary['documents']} ({summary['scanned_documents']} të skanuara, "
        f"pjesa e synuar {manifest['scanned_share']:.0%}) |",
        f"| Faqe | {summary['pages']} |",
        f"| Gjetje laboratorike | {summary['findings']} |",
        f"| Pohime të mjekut | {summary['assertions']} |",
        f"| Terma të pashpjeguar | {summary['unexplained_terms']} |",
        f"| Dokumente me vlerë kritike | {summary['documents_with_critical_value']} |",
        "",
        "*Tabela H.2. Versionet dhe parametrat fiks të sistemit*",
        "",
        "| Parametri | Vlera |",
        "|---|---|",
        f"| Katalogu i rregullave | `{LEGACY_RULES_VERSION}` te eksperimentet e ngrira (E4, E6–E11, grupet A, B, C); "
        f"`{RULES_VERSION}` te shërbimi (ADR 0021) |",
        "| Kontrolli i besueshmërisë i OCR-së | i fikur te eksperimentet e ngrira; i ndezur te shërbimi (ADR 0020) |",
        f"| Politika e sigurisë | `{POLICY_VERSION}` |",
        f"| OCR | Tesseract, gjuha `{ocr.DEFAULT_LANGUAGE}`, `--psm {ocr.DEFAULT_PSM}`, "
        f"{ocr.DEFAULT_DPI} dpi |",
        f"| Rimostrimi bootstrap | {base.BOOTSTRAP_RESAMPLES} rimostrime, fara {base.BOOTSTRAP_SEED}, "
        "njësia është dokumenti |",
        "",
        "*Tabela H.3. Rezultatet që ekzistojnë dhe prejardhja e tyre*",
        "",
        "| Eksperimenti | Pipeline | Kodi (git) | Pema e punës | Korpusi |",
        "|---|---|---|---|---|",
    ]
    for path in result_files():
        label = path.parent.relative_to(RESULTS).as_posix()
        meta = json.loads(path.read_text(encoding="utf-8")).get("metadata")
        if not meta:
            lines.append(f"| {label} | — | — | — | — (pa metadata) |")
            continue
        code = meta["code"]
        dirty = "e papastër" if code["working_tree_dirty"] else "e pastër"
        pipeline = (meta.get("pipeline") or {}).get("name")
        dataset = (meta.get("dataset") or {}).get("version")
        lines.append(
            f"| {label} | {f'`{pipeline}`' if pipeline else '—'} | `{code['git_sha'][:10]}` | {dirty} "
            f"| {f'`{dataset}`' if dataset else '—'} |"
        )

    runs = sorted(RESULTS.glob("E11/*/result.json"))
    if runs:
        lines += [
            "",
            "*Tabela H.4. Klasifikuesi XLM-RoBERTa (trajnuar në Colab) dhe pragjet e zgjedhura mbi validimin*",
            "",
            "| Hyrja | Modeli | Epoka | Shkalla e të nxënit | Batch | Gjatësia | Fara | Pajisja | Pragu 1 | Pragu 2 |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for path in runs:
            r = json.loads(path.read_text(encoding="utf-8"))
            run = r["run"]
            points = r["operating_points"]
            second = points.get("false_alarm_budget")
            lines.append(
                f"| {r['input']} | `{run['model']}` | {run['epochs']:g} | {run['learning_rate']} "
                f"| {run['batch']} | {run['max_length']} | {run['seed']} | {run['device']} "
                f"| {points['max_macro_f1']['threshold']} | {second['threshold'] if second else '—'} |"
            )
        lines += [
            "",
            "Pragu 1 është ai me macro F1 më të lartë mbi validimin; pragu 2 është ai me macro F1 më të "
            "lartë ndër ata që bllokojnë jo më shumë se 5% të teksteve të pastra të validimit "
            "(seksioni 6.7).",
        ]
    return "\n".join(lines) + "\n"


# I — shembuj dokumentesh


def appendix_i() -> str:
    import pymupdf

    data = ROOT / "data" / "v1"
    manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    images = OUT / "images"
    images.mkdir(parents=True, exist_ok=True)

    lines = [
        "## Shtojca I — Shembuj dokumentesh nga korpusi sintetik",
        "",
        "Dy dokumente të korpusit: njëri dixhital dhe njëri i skanuar, që kanë të njëjtën përmbajtje "
        "të prodhuar nga i njëjti gjenerues. Emrat e pacientëve në to janë të shpikur nga gjeneruesi.",
        "",
    ]
    for scanned, label, plural_label in (
        (False, "dixhital", "dixhital"),
        (True, "i skanuar", "të skanuar"),
    ):
        entry = next(d for d in manifest["documents"] if d["is_scanned"] is scanned)
        truth = json.loads((data / entry["file"]).read_text(encoding="utf-8"))
        pdf = pymupdf.open(data / entry["pdf"])
        name = f"dokument_{'skanuar' if scanned else 'dixhital'}.png"
        pdf[0].get_pixmap(matrix=pymupdf.Matrix(1.4, 1.4)).save(images / name)
        pdf.close()

        lines += [
            f"### Dokument {label} (`{Path(entry['pdf']).name}`)",
            "",
            f"![Faqja e parë e dokumentit {plural_label}](appendices/images/{name})",
            "",
            f"*Figura I.{2 if scanned else 1}. Faqja e parë e një dokumenti {plural_label} të korpusit sintetik*",
            "",
            "E vërteta bazë për gjashtë gjetjet e para:",
            "",
            "| Analiti | Vlera | Njësia | Intervali | Statusi |",
            "|---|---|---|---|---|",
        ]
        for f in truth["context"]["findings"][:6]:
            low, high = f.get("ref_low"), f.get("ref_high")
            interval = f"{low} – {high}" if low is not None and high is not None else "—"
            lines.append(
                f"| {f.get('analyte_name_canonical')} | {f.get('value_canonical')} "
                f"| {f.get('unit_canonical')} | {interval} | {f.get('status')} |"
            )
        lines += [
            "",
            "Narrativa e mjekut (fillimi):",
            "",
            f"> {truth['narrative_text'][:420].strip()}…",
            "",
        ]
    return "\n".join(lines) + "\n"


BUILDERS = {
    "A_terminologjia.md": appendix_a,
    "B_analitet.md": appendix_b,
    "C_rregullat.md": appendix_c,
    "D_kerkesat_e_modelit.md": appendix_d,
    "E_anotimi_i_dokumenteve_reale.md": appendix_e,
    "F_studimi_me_perdorues.md": appendix_f,
    "G_skema_sql.md": appendix_g,
    "H_konfigurimet.md": appendix_h,
    "I_shembuj_dokumentesh.md": appendix_i,
}


def result_files() -> list[Path]:
    """Skedarët e rezultateve që hyjnë te Tabela H.3: eksperimentet kryesore, E11 (një për hyrje) dhe
    ato me modelin gjuhësor te `llm/`. Radhitja: sipas numrit të eksperimentit, pastaj rezultatet e modelit."""
    found = (
        list(RESULTS.glob("E*/result.json"))
        + list(RESULTS.glob("E11/*/result.json"))
        + list(RESULTS.glob("llm/E*/result.json"))
    )

    def key(path: Path) -> tuple[bool, int, str]:
        relative = path.parent.relative_to(RESULTS)
        experiment = next(part for part in relative.parts if re.match(r"E\d+", part))
        return (
            relative.parts[0] == "llm",
            int(re.match(r"E(\d+)", experiment).group(1)),
            relative.as_posix(),
        )

    return sorted(set(found), key=key)


def sync_into_thesis(thesis: Path, directory: Path = OUT) -> list[str]:
    """Zëvendëson te teksti i plotë çdo seksion `## Shtojca X — …` me skedarin e shtojcës përkatëse.

    Shtojcat jetojnë në dy vende (skedarët e veçantë dhe teksti i plotë); pa këtë hap ato largohen.
    Kthen shkronjat e shtojcave që ndryshuan.
    """
    text = thesis.read_text(encoding="utf-8")
    heads = list(re.finditer(r"^## Shtojca ([A-I]) — .*$", text, re.MULTILINE))
    changed = []
    for index in reversed(range(len(heads))):  # nga fundi, që pozicionet e mëparshme të mos lëvizin
        head = heads[index]
        end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
        span = text[head.start() : end]
        core = re.sub(r"\n---\s*$", "", span.rstrip())
        suffix = span[len(core) :]
        source = next(directory.glob(f"{head.group(1)}_*.md")).read_text(encoding="utf-8")
        body = source[source.index("## Shtojca") :].rstrip()
        if body != core.rstrip():
            changed.append(head.group(1))
            text = text[: head.start()] + body + suffix + text[end:]
    thesis.write_text(text, encoding="utf-8", newline="\n")
    return sorted(changed)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="build_appendices")
    parser.add_argument(
        "--thesis",
        type=Path,
        default=None,
        help="pas ndërtimit, përditëso edhe seksionet e shtojcave te ky skedar (p.sh. docs/thesis/teza_v3.md)",
    )
    args = parser.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, build in BUILDERS.items():
        (OUT / name).write_text(HEADER + build(), encoding="utf-8", newline="\n")
        print(f"shkruar docs/thesis/appendices/{name}")
    if args.thesis:
        changed = sync_into_thesis(args.thesis)
        print(f"{args.thesis}: shtojcat e ndryshuara: {', '.join(changed) or 'asnjë'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
