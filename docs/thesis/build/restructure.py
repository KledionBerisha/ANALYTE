"""Build teza_v4.md from teza_v3.md: UBT order/numbering, new Chapter 2, references."""
import re, pathlib

BUILD = pathlib.Path(__file__).parent
SRC = BUILD.parent / "teza_v3.md"
OUT = BUILD.parent / "teza_v4.md"

text = SRC.read_text(encoding="utf-8")
lines = text.split("\n")

def find(prefix, start=0):
    for i in range(start, len(lines)):
        if lines[i].startswith(prefix):
            return i
    raise KeyError(prefix)

i_hyrje = find("# 2 HYRJE")
i_lit = find("# 3 SHQYRTIMI")
i_prob = find("# 4 DEKLARIMI")
i_ref = find("# 8 REFERENCAT")
i_app = find("# 9 APPENDIXES")

front = lines[:i_hyrje]
hyrje = lines[i_hyrje:i_lit]
body = lines[i_prob:i_ref]          # chapters 4..7 (old numbering)
appendix = lines[i_app:]

# ---------- chapter renumbering (old N -> N-1) ----------
def ch(n):
    return str(int(n) - 1)

def renumber(s):
    # headings
    s = re.sub(r"^(#{1,4}) (\d)((?:\.\d+)*) ", lambda m: f"{m.group(1)} {ch(m.group(2))}{m.group(3)} ", s, flags=re.M)
    # §N, §N.x, §N.x.y
    s = re.sub(r"§(\d)(?=[.,;: )]|$)", lambda m: "§" + ch(m.group(1)), s)
    # Kapitulli/Kapitullit/Kapitullin N
    s = re.sub(r"(Kapitull\w*) (\d)", lambda m: m.group(1) + " " + ch(m.group(2)), s)
    s = re.sub(r"Kapitujt 6 dhe 7", "Kapitujt 5 dhe 6", s)
    # seksioni N.x / nënkapitullin N.x
    s = re.sub(r"(seksion\w*|nënkapitull\w*|Seksion\w*) (\d)(\.\d)", lambda m: m.group(1) + " " + ch(m.group(2)) + m.group(3), s)
    return s

front = [renumber(l) for l in front]
hyrje = [renumber(l) for l in hyrje]
body = [renumber(l) for l in body]
appendix = [renumber(l) for l in appendix]

# ---------- figure renumbering: 18..21 -> 17..20 ----------
def fig(s):
    return re.sub(r"(Figur\w*) (18|19|20|21)\b", lambda m: m.group(1) + " " + str(int(m.group(2)) - 1), s)
body = [fig(l) for l in body]

# ---------- table renumbering: tokenize old numbers ----------
def tab(s):
    return re.sub(r"(Tabel\w*) (\d+[ab]?)\b", lambda m: m.group(1) + " {{T" + m.group(2) + "}}", s)
body = [tab(l) for l in body]
body_text = "\n".join(body)
hyrje_text = "\n".join(hyrje)
app_text = "\n".join(appendix)

# ---------- targeted edits in body ----------
edits = [
    # remove stale placeholders
    ("analit dhe mbetet vendim i hapur. [REFERENCË — plotësohet]", "analit dhe mbetet vendim i hapur."),
    ("stimulues i tiroides i lartë me tiroksinë të lirë të ulët.\n[REFERENCË — plotësohet]", "stimulues i tiroides i lartë me tiroksinë të lirë të ulët."),
    ("*[Figura — plotësohet: shembull i një kombinimi nga gjetjet te fjalia e\ndaljes]*\n\n", ""),
    ("miratimi etik nuk vendosen nga sistemi dhe mbeten vendim i autorit [REFERENCË — plotësohet].",
     "miratimi etik nuk vendosen nga sistemi dhe mbeten vendim i autorit; kuadri ligjor përshkruhet te seksioni 2.7.3 [58], [59]."),
    # (2026-10-07) kolona e burimit mbetet: burimet u plotësuan te resources/terminology.csv
    # figure 17 / table 14 notes
    ("*Figura 17 nuk prodhohet: chat-i nuk është ndërtuar.*\n\n", ""),
    (" Tabela {{T14}} nuk prodhohet dhe nuk fabrikohen përgjigje pjesëmarrësish.", " Nuk fabrikohen përgjigje pjesëmarrësish."),
    # Tesseract / OCR citations
    ("e para u bë me Tesseract 5\n(ADR 0012)", "e para u bë me Tesseract 5 [52]\n(ADR 0012)"),
    # statistics citations
    ("rimostrim bootstrap (2 000 rimostrime, farë e fiksuar).", "rimostrim bootstrap [61] (2 000 rimostrime, farë e fiksuar)."),
    ("intervali përqindor del me gjerësi zero. Në atë rast raportohet kufiri i\nrregullit të treshit (3/n)",
     "intervali përqindor del me gjerësi zero. Në atë rast raportohet kufiri i\nrregullit të treshit (3/n) [60]"),
    ("auditi i E8 ka intervale Wilson 95%.", "auditi i E8 ka intervale Wilson 95% [62]."),
    ("raportohet përmes koeficientit Cohen's kappa.", "raportohet përmes koeficientit kappa të Cohen-it [64]."),
    ("duke e fryrë artificialisht performancën e matur të klasifikuesit dhe duke e bërë rezultatin e PK6 të pabesueshëm.",
     "duke e fryrë artificialisht performancën e matur të klasifikuesit dhe duke e bërë rezultatin e PK6 të pabesueshëm; rrjedhja e të dhënave është shkaku më i zakonshëm i rezultateve të paripërsëritshme në shkencën e bazuar në mësimin makinerik [63]."),
    # judge independence citation
    ("1. **Gjykatësi nuk është i pavarur nga sistemi:** është asistenti që ndihmoi ta ndërtojë.",
     "1. **Gjykatësi nuk është i pavarur nga sistemi:** është asistenti që ndihmoi ta ndërtojë; modelet e mëdha gjuhësore njohin dhe favorizojnë daljet e veta kur veprojnë si vlerësues [49], [47]."),
    # Tabela 7b -> 11 caption cleanup (already renumbered by TMAP)
]
for old, new in edits:
    if old not in body_text:
        raise SystemExit("edit not found: " + old[:60])
    body_text = body_text.replace(old, new)

# (2026-10-07) rreshtat e Tabelës 2 dhe paragrafi i saj mbajnë burimet e plotësuara; nuk hiqet asgjë

# untitled tables -> captions (tokens), and caption text tweaks
caps = [
    ("| Fusha | Saktësia | Mbulimi | F1 |\n|---|---|---|---|\n| Analiti | 0.996",
     "*Tabela {{TX1}}. Saktësia e nxjerrjes mbi kanalin e skanuar, sipas fushës (E2)*\n\n| Fusha | Saktësia | Mbulimi | F1 |\n|---|---|---|---|\n| Analiti | 0.996"),
    ("| Përbërësi | Gjendja e matur |\n|---|---|", "*Tabela {{TX2}}. Përbërësit e sistemit dhe gjendja e tyre e matur*\n\n| Përbërësi | Gjendja e matur |\n|---|---|"),
    ("*Tabela {{T7}}. Saktësia e nxjerrjes së të dhënave laboratorike*", "*Tabela {{T7}}. Saktësia e nxjerrjes së të dhënave laboratorike (E1 dhe E2)*"),
    ("*Matrica e konfuzionit të E3. Rreshti është statusi i vërtetë, kolona statusi i dhënë nga sistemi.*",
     "*Tabela {{TX3}}. Matrica e konfuzionit të E3. Rreshti është statusi i vërtetë, kolona statusi i dhënë nga sistemi.*"),
    ("*Tabela {{T8}}, vazhdim. Saktësia sipas burimit të intervalit*", "*Tabela {{TX4}}. Saktësia e statusit sipas burimit të intervalit (E3)*"),
    ("| | pa kontroll | me kontroll |\n|---|---|---|\n| Statuse të interpretuara",
     "*Tabela {{TX5}}. Efekti i kontrollit të besueshmërisë së OCR-së mbi 168 dokumentet e skanuara*\n\n| | pa kontroll | me kontroll |\n|---|---|---|\n| Statuse të interpretuara"),
    ("*Tabela {{T9}}. Besnikëria e thjeshtimit*", "*Tabela {{T9}}. Besnikëria e thjeshtimit (E4)*"),
    ("*Tabela {{T10}}. Saktësia e krahasimit të kryqëzuar*", "*Tabela {{T10}}. Saktësia e krahasimit të kryqëzuar (E5)*"),
    ("*Tabela {{T11}}, vazhdim. Shkeljet e prodhuara nga modeli, sipas llojit",
     "*Tabela {{TX6}}. Shkeljet e prodhuara nga modeli, sipas llojit"),
    ("Problemet e gjetura te 90 tekstet, sipas llojit:\n\n| Lloji i problemit | Numri i problemeve |",
     "Problemet e gjetura te 90 tekstet, sipas llojit, jepen te Tabela {{TX7}}.\n\n*Tabela {{TX7}}. Problemet e gjetura nga auditi, sipas llojit*\n\n| Lloji i problemit | Numri i problemeve |"),
    ("| Kushti | `r1.3`: fjali | shkelje te përdoruesi për 100 fjali | shabllon rezervë | `r1.4` + kontroll: fjali |",
     "*Tabela {{TX8}}. Kushtet e ablacionit me `r1.3` dhe me `r1.4` bashkë me kontrollin e OCR-së*\n\n| Kushti | `r1.3`: fjali | shkelje te përdoruesi për 100 fjali | shabllon rezervë | `r1.4` + kontroll: fjali |"),
    ("*Detektimi sipas degës.*", "*Tabela {{TX9}}. Detektimi sipas degës (A: laboratorike; B: narrative)*"),
    ("| Matje | `r1.3` | `r1.4` |\n|---|---|---|", "*Tabela {{TX10}}. Katalogu `r1.3` kundrejt `r1.4` mbi të njëjtat mostra*\n\n| Matje | `r1.3` | `r1.4` |\n|---|---|---|"),
]
for old, new in caps:
    if old not in body_text:
        raise SystemExit("caption not found: " + old[:70])
    body_text = body_text.replace(old, new, 1)

# assign sequential numbers by caption order
order = []
for m in re.finditer(r"^\*Tabela \{\{(T[^}]+)\}\}\.", body_text, re.M):
    if m.group(1) not in order:
        order.append(m.group(1))
final = {k: str(i + 1) for i, k in enumerate(order)}
# 13 -> 13a's number (first of the pair) for bare cross-refs "Tabelës 13"
final["T13"] = final["T13a"]
missing = set(re.findall(r"\{\{(T[^}]+)\}\}", body_text)) - set(final)
if missing:
    raise SystemExit("unresolved table tokens: %s" % missing)
body_text = re.sub(r"\{\{(T[^}]+)\}\}", lambda m: final[m.group(1)], body_text)
body_text = body_text.replace("tabelat 7–13 dhe 16 gjenerohen", "tabelat %s, %s, %s, %s, %s, %s dhe %s–%s gjenerohen" % (final["T7"], final["T8"], final["T9"], final["T10"], final["T11"], final["T16"], final["T12"], final["T13b"]))

# (2026-10-07) shtojcat A dhe B mbajnë kolonën e burimit: burimet u plotësuan te resources/*.csv
app_text = app_text.replace("(Tabela 3)", "(Tabela 3)")

# ---------- front matter ----------
figures = re.findall(r"^!\[Figura (\d+)\]", body_text, re.M)
fig_caps = {}
for m in re.finditer(r"^\*Figura (\d+)\. ([^*]+?)\*", body_text, re.M):
    fig_caps.setdefault(m.group(1), m.group(2).split(". ")[0].rstrip("."))
# keep original short titles from the v3 list for 1..16, 17..20 from new captions
list_src = "\n".join(front)
old_list = dict(re.findall(r"^Figura (\d+)\. (.+)$", list_src, re.M))
fig_titles = {}
for n in range(1, 17):
    fig_titles[n] = old_list[str(n)]
fig_titles[17] = "Rezultatet e ablacionit të shtresës së verifikimit"
fig_titles[18] = "Matrica e konfuzionit për klasifikimin e statusit"
fig_titles[19] = "Matricat e konfuzionit për tre qasjet e detektimit"
fig_titles[20] = "Llojet e shkeljeve: çfarë prodhon modeli dhe sa mirë zbulohen"
fig_list = "\n\n".join(f"Figura {n}. {t}" for n, t in fig_titles.items())

tab_titles = []
for m in re.finditer(r"^\*Tabela (\d+)\. ([^*]+?)\*", body_text, re.M):
    title = m.group(2)
    title = re.sub(r"\s*\(.*?\)\s*$", "", title) if len(title) > 90 else title
    title = title.split(". ")[0].rstrip(".")
    tab_titles.append((int(m.group(1)), title))
tab_list = "\n\n".join(f"Tabela {n}. {t}" for n, t in tab_titles)

glossary = "\n".join(front[find("# FJALORI I TERMAVE") + 1:]).strip()
abstract = (BUILD / "abstract.md").read_text(encoding="utf-8").strip()

TITLE = "Bazimi determinist dhe verifikimi i automatizuar i shpjegimeve mjekësore të gjeneruara nga modelet e mëdha gjuhësore"
cover = f"""::: {{custom-style="CoverLogo"}}
![](ubt_logo.jpeg){{width=15cm}}
:::

::: {{custom-style="CoverProgram"}}
Programi për Shkenca Kompjuterike dhe Inxhinierisë
:::

::: {{custom-style="CoverTitle"}}
{TITLE}
:::

::: {{custom-style="CoverLine"}}
Shkalla Bachelor
:::

::: {{custom-style="CoverLine"}}
Kledion Berisha
:::

::: {{custom-style="CoverLine"}}
Tetor / 2026

Prishtinë
:::

::: {{custom-style="PageBreak"}}
\\
:::

::: {{custom-style="CoverLogo"}}
![](ubt_logo.jpeg){{width=15cm}}
:::

::: {{custom-style="CoverProgram"}}
Programi për Shkenca Kompjuterike dhe Inxhinierisë
:::

::: {{custom-style="CoverLine"}}
Punim Diplome

Viti akademik [XXXX] – [YYYY]

Kledion Berisha
:::

::: {{custom-style="CoverTitle"}}
{TITLE}
:::

::: {{custom-style="CoverLine"}}
Mentori: [Titulli. Emri dhe Mbiemri]

Tetor / 2026
:::

::: {{custom-style="CoverFoot"}}
Ky punim është përpiluar dhe dorëzuar në përmbushjen e kërkesave të pjesshme për Shkallën Bachelor
:::
"""

ack = """Falënderoj mentorin tim për udhëzimet, vërejtjet dhe durimin gjatë gjithë punës në këtë punim, si dhe stafin akademik të Programit për Shkenca Kompjuterike dhe Inxhinierisë të UBT-së për njohuritë e marra gjatë studimeve.

Falënderoj familjen time për mbështetjen e pakushtëzuar.

Falënderoj gjithashtu komunitetin e programeve me burim të hapur, mbi të cilat është ndërtuar ky sistem."""

front_md = f"""{cover}

::: {{custom-style="FrontHeadingNoToc"}}
ABSTRAKT
:::

{abstract}

::: {{custom-style="FrontHeadingNoToc"}}
MIRËNJOHJE/FALENDERIME
:::

{ack}

::: {{custom-style="FrontHeading"}}
PËRMBAJTJA
:::

::: {{custom-style="TocPlaceholder"}}
[[TOC]]
:::

::: {{custom-style="FrontHeading"}}
LISTA E FIGURAVE
:::

::: {{custom-style="TocPlaceholder"}}
[[LOF]]
:::

::: {{custom-style="FrontHeading"}}
LISTA E TABELAVE
:::

::: {{custom-style="TocPlaceholder"}}
[[LOT]]
:::

::: {{custom-style="FrontHeading"}}
FJALORI I TERMAVE
:::

{glossary}
"""

lit = (BUILD / "ch2_literature.md").read_text(encoding="utf-8").strip()
refs = (BUILD / "references.md").read_text(encoding="utf-8").strip()

# Hyrje: fix chapter roadmap sentence (already renumbered) and status; add citations
hyrje_text = hyrje_text.replace("Kjo dukuri, e njohur në literaturë si halucinacion, është përshkruar në mënyrë sistematike nga Ji et al. [3]",
                                "Kjo dukuri, e njohur në literaturë si halucinacion, është përshkruar në mënyrë sistematike nga Ji et al. [3]")
hyrje_text = hyrje_text.replace("Kjo qasje e drejtpërdrejtë konsiderohet përgjithësisht si përparim, sepse e vendos pacientin në qendër të procesit dhe e pajis atë me informacionin që i përket.",
                                "Kjo qasje e drejtpërdrejtë konsiderohet përgjithësisht si përparim, sepse e vendos pacientin në qendër të procesit dhe e pajis atë me informacionin që i përket [11], [12].")
hyrje_text = hyrje_text.replace("Për pacientin, rezultati praktik është një dokument që e zotëron por nuk e kupton.",
                                "Për pacientin, rezultati praktik është një dokument që e zotëron por nuk e kupton [8], [10].")

body_text = body_text.rstrip("-\n ")
app_text = app_text.rstrip()

doc = "\n\n".join([front_md.strip(), hyrje_text.strip().rstrip("-").strip(), lit, body_text, refs, app_text]) + "\n"
# remove horizontal rules used as separators
doc = re.sub(r"\n---\n", "\n", doc)
# fig/table lists
doc = doc.replace("[[LOF_STATIC]]", fig_list).replace("[[LOT_STATIC]]", tab_list)
# figure captions below images; split long caption paragraphs
def swap(m):
    n, title, rest, path = m.group(1), m.group(2), m.group(3).strip(), m.group(4)
    out = f"![Figura {n}](" + path + ")\n\n*Figura " + n + ". " + title.rstrip(".") + ".*"
    if rest:
        out += "\n\n" + rest
    return out
doc = re.sub(r"^\*Figura (\d+)\. ([^\n*]*?)\*([^\n]*)\n\n!\[Figura \1\]\(([^)]+)\)", swap, doc, flags=re.M)
doc = re.sub(r"^### (Tabela [A-Z]\.\d+\. .+)$", r"*\1*", doc, flags=re.M)
doc = doc.replace("### Intervalet e besimit", "#### Intervalet e besimit")
# figures: renumber sequentially by order of appearance (captions, refs, alt text)
seq = []
for m in re.finditer(r"^\*Figura (\d+)\. ", doc, re.M):
    if m.group(1) not in seq: seq.append(m.group(1))
fmap = {old: str(i + 1) for i, old in enumerate(seq)}
doc = re.sub(r"(Figur\w*) (\d+)\b", lambda m: m.group(1) + " " + fmap.get(m.group(2), m.group(2)), doc)
doc = re.sub(r"Figurat 12–16", "Figurat 12–16", doc)
# split long captions: short title stays in the caption, the rest becomes a note paragraph
def split_cap(m):
    kind, num, title = m.group(1), m.group(2), m.group(3)
    if len(title) <= 80:
        return m.group(0)
    cut = None
    for sep in (". ", ": ", "; "):
        i = title.find(sep)
        if i > 15 and (cut is None or i < cut[0]):
            cut = (i, sep)
    if cut is None:
        return m.group(0)
    i, sep = cut
    short, rest = title[:i].rstrip(".:;"), title[i + len(sep):].strip()
    rest = rest[0].upper() + rest[1:] if rest else rest
    return f"*{kind} {num}. {short}.*\n\n*{rest}*" if rest else f"*{kind} {num}. {short}.*"
doc = re.sub(r"^\*(Figura|Tabela) (\d+|[A-Z]\.\d+)\. ([^\n]*?)\*$", split_cap, doc, flags=re.M)
# PËRMBAJTJA heading must not list itself
doc = doc.replace('::: {custom-style="FrontHeading"}\nPËRMBAJTJA\n:::', '::: {custom-style="FrontHeadingNoToc"}\nPËRMBAJTJA\n:::')
OUT.write_text(doc, encoding="utf-8")
print("figure map:", fmap)
(BUILD / "fig_list.md").write_text(fig_list, encoding="utf-8")
(BUILD / "tab_list.md").write_text(tab_list, encoding="utf-8")
print("tables:", final)
print("figures in body:", sorted(set(int(f) for f in figures)))
print("written", OUT, len(doc))
