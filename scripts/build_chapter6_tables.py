"""
Tabelat numerike të Kapitullit 6, nga skedarët e rezultateve.

    python scripts/build_chapter6_tables.py              # i printon
    python scripts/build_chapter6_tables.py --json F     # i ruan edhe si JSON

Asnjë vlerë nuk shkruhet me dorë: çdo qelizë lexohet nga `evaluation/results/`
(E1, E2, E3, E5, E7, E8, E9, E10, E11 dhe grupi B). Grupi B rillogaritet nga
`python -m evaluation.kits check`, sepse rezultati i rregullave mbi B nuk
ruhet si skedar. Eksperimentet që nuk u kryen (E4, E6, E12) shfaqen në tabela
si «nuk matet», jo si zero.

Kapitulli 6 i `docs/thesis/teza_v3.md` e përmban këtë dalje të ngjitur; kur
rezultatet ekzekutohen përsëri, tabelat duhet krahasuar me të.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "evaluation" / "results"


def load(p):
    return json.loads((R / p).read_text(encoding="utf-8"))


def f(x, nd=3):
    return "—" if x is None else f"{x:.{nd}f}"


out = {}

# ---- Tabela 7 (E1 + E2)
e1 = load("E1/result.json")["metrics"]
e2 = load("E2/result.json")["metrics"]
names = [("analyte", "Emri i analitit"), ("value", "Vlera numerike"), ("unit", "Njësia"), ("interval", "Intervali referent")]
rows = ["| Fusha | Precision (dig.) | Recall (dig.) | F1 (dig.) | Precision (skan.) | Recall (skan.) | F1 (skan.) |", "|---|---|---|---|---|---|---|"]
for k, label in names:
    a, b = e1["per_field"][k], e2["per_field"][k]
    rows.append(f"| {label} | {f(a['precision'])} | {f(a['recall'])} | {f(a['f1'])} | {f(b['precision'])} | {f(b['recall'])} | {f(b['f1'])} |")
a, b = e1["micro"], e2["micro"]
rows.append(f"| **Mikro-mesatarja** | {f(a['precision'])} | {f(a['recall'])} | {f(a['f1'])} | {f(b['precision'])} | {f(b['recall'])} | {f(b['f1'])} |")
out["T7"] = "\n".join(rows)

# ---- Tabela 8 (E3)
e3 = load("E3/result.json")["metrics"]
order = ["normal", "high", "low", "critical_high", "critical_low", "uninterpretable"]
labels = {"normal": "normal", "high": "high", "low": "low", "critical_high": "critical_high", "critical_low": "critical_low", "uninterpretable": "uninterpretable"}
rows = ["| Statusi i vërtetë | Mbështetja | Precision | Recall | F1 |", "|---|---|---|---|---|"]
for c in order:
    p = e3["overall"]["per_class"][c]
    rows.append(f"| `{labels[c]}` | {p['support']} | {f(p['precision'])} | {f(p['recall'])} | {f(p['f1'])} |")
rows.append(f"| **Të gjitha** | {e3['overall']['total']} | | | saktësia {f(e3['overall']['accuracy'])} |")
out["T8"] = "\n".join(rows)

mat = e3["overall"]["matrix"]
hdr = "| e vërteta ↓ / e parashikuar → | " + " | ".join(f"`{c}`" for c in order) + " |"
rows = [hdr, "|---|" + "---|" * len(order)]
for t in order:
    cells = [str(mat.get(f"{t}->{p}", 0)) for p in order]
    rows.append(f"| `{t}` | " + " | ".join(cells) + " |")
out["T8_matrix"] = "\n".join(rows)

rows = ["| Burimi i intervalit | Vlera | Pjesa | Saktësia e statusit |", "|---|---|---|---|"]
labels_src = {"document": "dokumenti", "internal_table": "tabela e brendshme", "none": "asnjë (pa interval)"}
for k in ("document", "internal_table", "none"):
    rows.append(f"| {labels_src[k]} | {e3['by_reference_source'][k]['total']} | {f(e3['reference_source_share'][k])} | {f(e3['by_reference_source'][k]['accuracy'])} |")
out["T8_src"] = "\n".join(rows)

# ---- Tabela 10 (E5)
e5 = load("E5/result.json")["metrics"]
sup = load("supplementary/ch5_digital_and_no_ocr.json")
e5_dig = sup["E5_digital_no_ocr"]["metrics"]
e5_noocr = sup["E5_all_no_ocr"]["metrics"]
states = [("agreement", "përputhje"), ("contradiction", "kundërshtim"), ("mentioned_not_measured", "përmendur, jo matur"), ("measured_not_mentioned", "matur, jo përmendur")]
rows = ["| Gjendja | Mbështetja | Precision (me OCR) | Recall: dixhital | Recall: gjithë korpusi, pa OCR | Recall: gjithë korpusi, me OCR |", "|---|---|---|---|---|---|"]
for k, label in states:
    p = e5["overall"]["per_class"][k]
    rows.append(f"| `{k}` ({label}) | {p['support']} | {f(p['precision'])} | {f(e5_dig['recall_by_state'][k])} | {f(e5_noocr['recall_by_state'][k])} | {f(e5['recall_by_state'][k])} |")
rows.append(f"| **Saktësia e përgjithshme** | {e5['overall']['total']} | | {f(e5_dig['overall']['accuracy'])} | {f(e5_noocr['overall']['accuracy'])} | {f(e5['overall']['accuracy'])} |")
out["T10"] = "\n".join(rows)

# ---- Tabela 11 (E7-E9)
e7, e8, e9 = (load(f"E{i}/result.json")["metrics"] for i in (7, 8, 9))
A = {"ungrounded_number", "ungrounded_analyte", "direction_mismatch", "missing_critical"}


def split(m):
    d = m["by_type_reaching_user"]
    return sum(v for k, v in d.items() if k in A), sum(v for k, v in d.items() if k not in A)


rows = ["| Kushti | Eksperimenti | Fjali | Shkelje që arrijnë te përdoruesi | Për 100 fjali (95% CI) | Dega A | Dega B |", "|---|---|---|---|---|---|---|",
        "| A — pa bazim | E6 | — | **nuk matet** | — | — | — |"]
for label, eid, m in (("B — vetëm bazim", "E7", e7), ("C — bazim dhe rregulla", "E8", e8), ("D — bazim, rregulla dhe klasifikues", "E9", e9)):
    ci = m["ci95_reaching_user"]
    if ci["estimate"] == 0:
        txt = f"0.000 (95%: ≤ {f(ci['rule_of_three_high'])}, rregulla e tre)"
    else:
        txt = f"{f(m['rate_reaching_user_per_100_sentences'])} [{f(ci['low'])}–{f(ci['high'])}]"
    a, b = split(m)
    rows.append(f"| {label} | {eid} | {m['sentences']} | {m['violations_reaching_user']} | {txt} | {a} | {b} |")
out["T11"] = "\n".join(rows)

# ---- Tabela 12 / 13
e10 = load("E10/result.json")["metrics"]
kitB_rules = json.loads(subprocess.run([sys.executable, "-m", "evaluation.kits", "check"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT).stdout)["B"]
E11 = {(inp, rule): load(f"E11/{inp}/result.json")["operating_points"][rule] for inp in ("sentence", "context") for rule in ("max_macro_f1", "false_alarm_budget")}
KB = {(inp, rule): load(f"E11/{inp}/kit_B.json")["operating_points"][rule] for inp in ("sentence", "context") for rule in ("max_macro_f1", "false_alarm_budget")}


def clean_blocked(m, n):
    return f"{m['false_alarms_on_clean']} / {n}"


detectors = [("Rregullat deterministe (`r1.3`)", e10, kitB_rules)]
for inp, inl in (("sentence", "fjalia"), ("context", "fjalia + konteksti")):
    for rule, rl, th in (("max_macro_f1", "rregulli 1", None), ("false_alarm_budget", "rregulli 2", None)):
        t1 = E11[(inp, rule)]["threshold"]
        detectors.append((f"Klasifikuesi XLM-R, {inl}, {rl} (prag {t1})", E11[(inp, rule)]["metrics"], KB[(inp, rule)]["metrics"]))

rows = ["| Qasja | Korpusi i korruptuar: P | R | F1 | Macro F1 | Të pastra të bllokuara | Grupi B: P | R | F1 | Macro F1 | Të pastra të bllokuara |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for label, syn, nat in detectors:
    s, n = syn["micro"], nat["micro"]
    rows.append(f"| {label} | {f(s['precision'])} | {f(s['recall'])} | {f(s['f1'])} | {f(syn['macro_f1'])} | {clean_blocked(syn, 30)} | {f(n['precision'])} | {f(n['recall'])} | {f(n['f1'])} | {f(nat['macro_f1'])} | {clean_blocked(nat, 30)} |")
rows.append("| Modeli gjuhësor si gjykatës (E12) | **nuk matet** | | | | | **nuk matet** | | | | |")
out["T12"] = "\n".join(rows)

types = ["ungrounded_number", "ungrounded_analyte", "direction_mismatch", "polarity_flip", "hedge_removed", "fabricated_finding", "ungrounded_term_explanation", "prohibited_claim", "omitted_recommendation"]


def table13(sel):
    rows = ["| Lloji i defektit | Mbështetja | Rregullat | Fjalia, R1 | Fjalia, R2 | Fj.+konteksti, R1 | Fj.+konteksti, R2 |", "|---|---|---|---|---|---|---|"]
    for t in types:
        vals = []
        sup = None
        for i, (label, syn, nat) in enumerate(detectors):
            m = (syn if sel == "syn" else nat)["per_defect_type"].get(t)
            if m is not None and sup is None:
                sup = m["support"]
            vals.append(None if (m is None or m["support"] == 0) else m["f1"])
        if sup is None or sup == 0:
            continue
        rows.append(f"| `{t}` | {sup} | " + " | ".join(f(v, 2) for v in vals) + " |")
    return "\n".join(rows)


out["T13a"] = table13("syn")
out["T13b"] = table13("nat")

# ---- degët (H2)
def branch(pdt):
    res = {}
    for name, pred in (("A", lambda k: k in A), ("B", lambda k: k not in A)):
        tp = sum(v["tp"] for k, v in pdt.items() if pred(k))
        fp = sum(v["fp"] for k, v in pdt.items() if pred(k))
        fn = sum(v["fn"] for k, v in pdt.items() if pred(k))
        res[name] = (tp, fp, fn, tp / (tp + fp) if tp + fp else None, tp / (tp + fn) if tp + fn else None)
    return res


rows = ["| Detektori | Dega | Korpusi i korruptuar: P | R | Grupi B: P | R |", "|---|---|---|---|---|---|"]
for label, syn, nat in detectors:
    bs, bn = branch(syn["per_defect_type"]), branch(nat["per_defect_type"])
    for br in ("A", "B"):
        rows.append(f"| {label} | {br} | {f(bs[br][3])} | {f(bs[br][4])} | {f(bn[br][3])} | {f(bn[br][4])} |")
out["T_branch"] = "\n".join(rows)

if len(sys.argv) > 2 and sys.argv[1] == "--json":
    Path(sys.argv[2]).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for k, v in out.items():
    print("=====", k)
    print(v)
