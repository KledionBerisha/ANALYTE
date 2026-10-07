"""Second pass over teza_v4.md: sources for the 82 terms and 11 rules were written into
resources/*.csv on 2026-10-07, the corpus was regenerated (version 3fede455) and the
combination rules were reviewed by a family physician. Update every passage that said
'no sources / not clinically reviewed', inject the regenerated Appendices A and B, and add
the rule sources to the reference list."""
import re, csv, pathlib

BUILD = pathlib.Path(__file__).parent
UP = pathlib.Path("/mnt/user-data/uploads/ANALYTE/docs/thesis")
MD = BUILD / "teza_v4.md"
doc = MD.read_text(encoding="utf-8")

def rep(old, new, count=1):
    global doc
    if old not in doc:
        raise SystemExit("NOT FOUND: " + old[:90])
    doc = doc.replace(old, new, count)

# ---------- new references [65]–[77] ----------
NEW_REFS = [
 ("P01", 'J. Snook, N. Bhala, I. L. P. Beales, et al., "British Society of Gastroenterology guidelines for the management of iron deficiency anaemia in adults," *Gut*, vol. 70, no. 11, pp. 2030–2051, 2021, doi: 10.1136/gutjnl-2021-324757.'),
 ("P02", 'H. S. Chaudhry and M. R. Kasarla, "Microcytic hypochromic anemia," in *StatPearls* [Internet]. Treasure Island, FL, USA: StatPearls Publishing, 2026. [Online]. Available: https://www.ncbi.nlm.nih.gov/books/NBK470252/, date accessed: 06.10.2026.'),
 ("P02b", 'M. W. Short and J. E. Domagalski, "Iron deficiency anemia: evaluation and management," *American Family Physician*, vol. 87, no. 2, pp. 98–104, 2013.'),
 ("P03", 'R. C. Langan and A. J. Goodbred, "Vitamin B12 deficiency: recognition and management," *American Family Physician*, vol. 96, no. 6, pp. 384–389, 2017.'),
 ("P04", 'American Diabetes Association Professional Practice Committee, "2. Diagnosis and classification of diabetes: Standards of Care in Diabetes—2025," *Diabetes Care*, vol. 48, suppl. 1, pp. S27–S49, 2025, doi: 10.2337/dc25-S002.'),
 ("P05", 'A. O. Hosten, "BUN and creatinine," in *Clinical Methods: The History, Physical, and Laboratory Examinations*, 3rd ed., H. K. Walker, W. D. Hall, and J. W. Hurst, Eds. Boston, MA, USA: Butterworths, 1990, ch. 193. [Online]. Available: https://www.ncbi.nlm.nih.gov/books/NBK305/, date accessed: 06.10.2026.'),
 ("P06", 'P. N. Newsome, R. Cramb, S. M. Davison, et al., "Guidelines on the management of abnormal liver blood tests," *Gut*, vol. 67, no. 1, pp. 6–19, 2018, doi: 10.1136/gutjnl-2017-315541.'),
 ("P08", 'S. A. Wilson, L. A. Stem, and R. D. Bruehlman, "Hypothyroidism: diagnosis and treatment," *American Family Physician*, vol. 103, no. 10, pp. 605–613, 2021.'),
 ("P09", 'D. S. Ross, H. B. Burch, D. S. Cooper, et al., "2016 American Thyroid Association guidelines for diagnosis and management of hyperthyroidism and other causes of thyrotoxicosis," *Thyroid*, vol. 26, no. 10, pp. 1343–1421, 2016, doi: 10.1089/thy.2016.0229.'),
 ("P09b", 'I. Kravets, "Hyperthyroidism: diagnosis and treatment," *American Family Physician*, vol. 93, no. 5, pp. 363–370, 2016.'),
 ("P10", 'L. K. Riley and J. Rupert, "Evaluation of patients with leukocytosis," *American Family Physician*, vol. 92, no. 11, pp. 1004–1011, 2015.'),
 ("P10b", 'A. Markanday, "Acute phase reactants in infections: evidence-based review and a guide for clinicians," *Open Forum Infectious Diseases*, vol. 2, no. 3, Art. no. ofv098, 2015, doi: 10.1093/ofid/ofv098.'),
 ("P11", 'F. Mach, C. Baigent, A. L. Catapano, et al., "2019 ESC/EAS Guidelines for the management of dyslipidaemias: lipid modification to reduce cardiovascular risk," *European Heart Journal*, vol. 41, no. 1, pp. 111–188, 2020, doi: 10.1093/eurheartj/ehz455.'),
]
num = {}
start = 65
ref_lines = []
for i, (key, text) in enumerate(NEW_REFS):
    n = start + i
    num[key] = n
    ref_lines.append(f"[{n}] {text}")
num["P07"] = num["P06"]
cite = {
    "P01": f"[{num['P01']}]", "P02": f"[{num['P02']}], [{num['P02b']}]", "P03": f"[{num['P03']}]",
    "P04": f"[{num['P04']}]", "P05": f"[{num['P05']}]", "P06": f"[{num['P06']}]", "P07": f"[{num['P06']}]",
    "P08": f"[{num['P08']}]", "P09": f"[{num['P09']}], [{num['P09b']}]",
    "P10": f"[{num['P10']}], [{num['P10b']}]", "P11": f"[{num['P11']}]",
}
rep("[64] J. Cohen, \"A coefficient of agreement for nominal scales,\" *Educational and Psychological Measurement*, vol. 20, no. 1, pp. 37–46, 1960, doi: 10.1177/001316446002000104.",
    "[64] J. Cohen, \"A coefficient of agreement for nominal scales,\" *Educational and Psychological Measurement*, vol. 20, no. 1, pp. 37–46, 1960, doi: 10.1177/001316446002000104.\n\n" + "\n\n".join(ref_lines))

# ---------- Appendices A and B: regenerated from the CSVs ----------
def appendix(name):
    t = (UP / "appendices" / name).read_text(encoding="utf-8")
    t = re.sub(r"<!--.*?-->\s*", "", t, flags=re.S).strip()
    t = re.sub(r"^### (Tabela [A-Z]\.\d+\. .+)$", r"*\1*", t, flags=re.M)
    return t
a_new = appendix("A_terminologjia.md")
b_new = appendix("B_analitet.md")
# B.3: replace the long source strings by reference numbers
def b3(m):
    pid = m.group(1)
    return f"| {pid} | {m.group(2)} | {cite[pid]} |"
b_new = re.sub(r"^\| (P\d\d) \| ([^|]+) \| [^\n]+ \|$", b3, b_new, flags=re.M)
b_new = b_new.replace("""> Burimi i secilit kombinim u lexua më 2026-10-06; citimi i evidencës dhe
> shkalla e mbështetjes (e plotë ose e pjesshme) për secilin jepen te
> `docs/thesis/worksheets/burimet_e_gjetura.md`. Kombinimet duhen konfirmuar
> nga mentori ose nga një mjek përpara dorëzimit.""",
"""Burimi i secilit kombinim u lexua më 2026-10-06; fjalia mbështetëse e secilit dhe shkalla e mbështetjes jepen te `docs/thesis/worksheets/burimet_e_gjetura.md`. Për P10 literatura e lidh leukocitozën me infeksionin dhe inflamacionin dhe e emërton CRP-në si tregues plotësues, por asnjë udhëzues nuk e përcakton çiftin si të tillë; mbështetja është e pjesshme. Të 11 kombinimet, me drejtimet e tyre, u rishikuan dhe u konfirmuan nga një mjek i mjekësisë familjare në tetor 2026.""")
assert "| P01 | " in b_new and "[65]" in b_new, b_new[:500]
ia = doc.index("## Shtojca A — Tabela e plotë terminologjike shqip")
ib = doc.index("## Shtojca B — Paneli i plotë i analiteve")
ic = doc.index("## Shtojca C — Katalogu i plotë i rregullave të verifikimit")
doc = doc[:ia] + a_new + "\n\n" + b_new + "\n\n" + doc[ic:]

# ---------- Table 5 extract: add the source column ----------
short = {}
with open(BUILD / "burimet_e_gjetura.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["kind"] == "term":
            s = row["source_ref"]
            m = re.match(r"(MeSH|MedlinePlus|Cleveland Clinic|Testing\.com)[^,]*,\s*\"([^\"]+)\"(?:\s*\(([^)]+)\))?", s)
            if m:
                pub, title, uid = m.group(1), m.group(2), m.group(3)
                short[row["key"]] = f"{pub}, «{title}»" + (f" ({uid})" if uid and pub == "MeSH" else "")
            else:
                short[row["key"]] = s.split(",")[0]
if "| Termi | Shpjegimi | Kategoria |\n|---|---|---|\n| anemi |" in doc:
    pass
if True:
    rep("| Termi | Shpjegimi | Kategoria |\n|---|---|---|\n| anemi |", "| Termi | Shpjegimi | Kategoria | Burimi |\n|---|---|---|---|\n| anemi |")
def t5(m):
    term = m.group(1)
    return f"| {term} | {m.group(2)} | {m.group(3)} | {short.get(term, '—')} |"
i5 = doc.index("*Tabela 5. Ekstrakt nga tabela terminologjike shqip*")
j5 = doc.index("*Ekstrakt i 10 zërave të parë", i5)
seg = re.sub(r"^\| ([^|]+) \| ([^|]+) \| (gjendje|proces) \|(?: [^|\n]* \|)?$", t5, doc[i5:j5], flags=re.M)
doc = doc[:i5] + seg + doc[j5:]
i82 = doc.index("Tabela përmban 82 zëra.")
j82 = doc.index("\n\n", i82)
doc = doc[:i82] + "@@P82@@" + doc[j82:]
rep("@@P82@@",
"""Tabela përmban 82 zëra. Çdo zë mban në kolonën e burimit faqen ose
përshkruesin (MeSH, MedlinePlus, Cleveland Clinic, Testing.com) që u lexua
më 6 tetor 2026 dhe që e mbështet shpjegimin shqip; shpjegimi është
formulim i autorit në gjuhë të thjeshtë, jo përkthim i burimit, dhe fjalia
mbështetëse e secilit zë ruhet bashkë me tabelën. Pa këtë referencë, tabela
do të ishte vetë burim informacioni të paverifikuar — pikërisht ajo që SP6
synon të pengojë. Shpjegimet nuk janë rishikuar nga një klinicist
(seksioni 6.6).""")

# ---------- 4.3.8 combinations ----------
rep("""burimi i rregullit. Njëmbëdhjetë rregulla mbulojnë kombinime të njohura
gjerësisht, si hemoglobina e ulët me ferritinë të ulët apo hormoni
stimulues i tiroides i lartë me tiroksinë të lirë të ulët.""",
f"""burimi i rregullit. Njëmbëdhjetë rregulla mbulojnë kombinime të njohura
gjerësisht, si hemoglobina e ulët me ferritinë të ulët {cite['P01']} apo hormoni
stimulues i tiroides i lartë me tiroksinë të lirë të ulët {cite['P08']}. Burimi i
secilit rregull është një udhëzues i një shoqate profesionale (BSG, ADA,
ATA, ESC/EAS) ose një shqyrtim i recensuar {cite['P02']}, {cite['P03']}, {cite['P04']}, {cite['P05']}, {cite['P06']}, {cite['P09']}, {cite['P10']}, {cite['P11']};
të gjitha u lexuan më 6 tetor 2026 dhe të 11 kombinimet, bashkë me
drejtimet e tyre, u rishikuan dhe u konfirmuan nga një mjek i mjekësisë
familjare në tetor 2026 (Tabela B.3).""")
rep("""të ndërtuara me dorë, jo mbi korpusin, dhe asnjë PK nuk mat saktësinë e
tyre klinike; ajo varet nga burimi i secilit rregull dhe nga shqyrtimi i
mentorit.""",
"""të ndërtuara me dorë, jo mbi korpusin, dhe asnjë PK nuk mat saktësinë e
tyre klinike; ajo mbështetet te burimi i secilit rregull dhe te rishikimi
nga mjeku familjar, jo te një matje e këtij punimi.""")

# ---------- 5.1 table ----------
rep("| Tabela terminologjike | 82 terma shqip, secili me burim të lexuar (Shtojca A); shpjegimet mbeten formulime të autorit |",
    "| Tabela terminologjike | 82 terma shqip, secili me burim të lexuar (Shtojca A) |")
rep("| Kombinimet ndërmjet analiteve | 11 rregulla, secila me burim të lexuar (Tabela B.3); P10 (leukocite ↑ + CRP ↑) mbështetet vetëm pjesërisht; asnjë rregull nuk është rishikuar nga mentor ose mjek |",
    "| Kombinimet ndërmjet analiteve | 11 rregulla, secila me burim të lexuar dhe të rishikuara nga një mjek familjar (Tabela B.3); P10 (leukocite ↑ + CRP ↑) mbështetet vetëm pjesërisht nga literatura |")

# ---------- 6.4 ----------
rep("Tabela terminologjike e ndërtuar në kuadër të këtij punimi (82 terma) mund të shërbejë si pikënisje për punime të ardhshme, por sot nuk është artefakt i ripërdorshëm: asnjë nga 82 shpjegimet nuk ka burim të shënuar dhe asnjë nuk është rishikuar nga një klinicist.",
    "Tabela terminologjike e ndërtuar në kuadër të këtij punimi (82 terma) mund të shërbejë si pikënisje për punime të ardhshme: çdo shpjegim mbështetet në një burim të lexuar (MeSH, MedlinePlus ose faqe pacientësh të institucioneve shëndetësore), por shpjegimet janë formulime të autorit dhe nuk janë rishikuar nga një klinicist; rregullat e kombinimit, përkundrazi, u rishikuan nga një mjek familjar (seksioni 4.3.8).")

# ---------- 6.6 item 10 ----------
rep("**10. Burimet.** Tabela terminologjike ka 82 terma dhe nuk mbulon çdo term të mundshëm mjekësor; asnjë nga 82 termat dhe asnjë nga 11 rregullat e kombinimit nuk ka burim të shënuar, dhe asnjë nuk është vlerësuar klinikisht. Paneli ka 38 analite, dhe rezultatet laboratorike jonumerike nuk mbulohen fare. Chat-i i lidhur me dokumentin nuk është ndërtuar.",
    "**10. Burimet dhe rishikimi klinik.** Tabela terminologjike ka 82 terma dhe nuk mbulon çdo term të mundshëm mjekësor. Të 82 shpjegimet dhe të 11 rregullat e kombinimit kanë burim të lexuar (Shtojca A, Tabela B.3), por burimet e termave janë faqe terminologjike dhe faqe pacientësh, jo literaturë klinike, dhe shpjegimet shqip nuk janë rishikuar nga një klinicist. Rregullat u rishikuan nga një mjek familjar i vetëm, pa protokoll të shkruar; për P10 (leukocite dhe CRP) literatura jep mbështetje të pjesshme. Paneli ka 38 analite, dhe rezultatet laboratorike jonumerike nuk mbulohen fare. Chat-i i lidhur me dokumentin nuk është ndërtuar.")

# ---------- Appendix H ----------
rep("| Versioni i gjeneruesit | `gen-1.0` |\n| Fara | 42 |",
    "| Versioni i gjeneruesit | `gen-1.0` |\n| Versioni i korpusit | `gen-1.0/s42/n500/37d8b080` gjatë matjeve; `gen-1.0/s42/n500/3fede455` pas shtimit të burimeve në tabelat burimore (7 tetor 2026), me përmbajtje të njëjtë (§5, hyrja) |\n| Fara | 42 |")

# ---------- acknowledgements ----------
rep("Falënderoj gjithashtu komunitetin e programeve me burim të hapur, mbi të cilat është ndërtuar ky sistem.",
    "Falënderoj mjekun e mjekësisë familjare që i rishikoi rregullat e kombinimit të analiteve.\n\nFalënderoj gjithashtu komunitetin e programeve me burim të hapur, mbi të cilat është ndërtuar ky sistem.")

MD.write_text(doc, encoding="utf-8")
print("ok; refs", num)
