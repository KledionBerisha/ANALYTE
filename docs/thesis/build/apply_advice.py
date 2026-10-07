"""Third pass over teza_v4.md: the sourced-advice table (ADR 0023, 2026-10-07)."""
import csv, pathlib, re

BUILD = pathlib.Path(__file__).parent
MD = BUILD / "teza_v4.md"
doc = MD.read_text(encoding="utf-8")

def rep(old, new):
    global doc
    if old not in doc:
        raise SystemExit("NOT FOUND: " + old[:90])
    doc = doc.replace(old, new, 1)

# analyte names for the appendix table
names = {r["loinc_code"]: r["name_canonical_sq"] for r in csv.DictReader(open("/mnt/user-data/uploads/ANALYTE/resources/analytes.csv", encoding="utf-8"))}
rows = list(csv.DictReader(open(BUILD.parent / "advice" / "advice.csv", encoding="utf-8")))
filled = [r for r in rows if r["advice_sq"]]
unfilled = [r for r in rows if not r["advice_sq"]]
assert len(rows) == 76

def short_src(s):
    m = re.match(r"(MedlinePlus|Cleveland Clinic|Testing\.com)[^,]*,\s*\"([^\"]+)\"", s)
    return f"{m.group(1)}, «{m.group(2)}»" if m else s.split(",")[0]

# ---------- 4.3.9 ----------
sec = """### 4.3.9 Këshillat me burim për vlerat jashtë intervalit

Pacienti që lexon se një vlerë është jashtë intervalit referent kërkon
edhe një hap tjetër: çfarë mund të bëjë me këtë. Kërkesa fillestare ishte
që modeli gjuhësor të shtonte një këshillë të shkurtër për çdo vlerë të
tillë. Kjo bie ndesh me parimin e punimit: një këshillë e shkruar nga
modeli është pohim mjekësor pa burim, SP1–SP3 e ndalojnë trajtimin dhe
këshillën klinike, dhe auditi i seksionit 5.6.1 tregon se rregullat kapin
vetëm një pjesë të gabimeve të modelit. Prandaj këshilla është e dhënë,
jo e gjeneruar (ADR 0023).

Një tabelë burimore, `resources/advice.csv`, mban një rresht për çdo
analit të panelit dhe çdo drejtim (38 analite, dy drejtime, 76 rreshta):
kodi LOINC, drejtimi, fjalia shqipe dhe burimi. Fjalia është një e vetme,
pa numra, pa emër gjendjeje, pa trajtim dhe pa parashikim, e formuluar si
temë ose pyetje për mjekun («Pyesni mjekun tuaj nëse kjo vlerë duhet
përsëritur esëll.»), dhe nuk thotë më shumë se faqja e pacientit nga e
cila rrjedh. Ngarkuesi e refuzon rreshtin me shifra, me më shumë se një
fjali, pa pikë në fund, me kod ose drejtim të panjohur, dhe një rresht
numërohet i plotësuar vetëm kur ka edhe fjalinë edhe burimin pa
vendmbajtës; rreshti i paplotësuar nuk i shfaqet kurrë pacientit.

Këshilla lidhet vetëm me gjetjet që kanë drejtim: vlerat normale, vlerat
pa interval referent dhe analitet e dyfishta nuk marrin asgjë. Ajo hyn në
`GroundingContext` bashkë me burimin, si zërat e fjalorit. Shablloni
determinist e shtyp menjëherë pas fjalisë së vlerës përkatëse; kërkesa
drejtuar modelit e jep si tekst për t'u kopjuar fjalë për fjalë, me
ndalesën «mos shto asnjë këshillë tjetër», dhe blloku shfaqet vetëm kur
konteksti ka këshilla. Kontekstet e eksperimenteve të Kapitullit 5 nuk
kanë, prandaj udhëzimet e sistemit, versioni i kërkesës `p1` dhe cache-i
i përgjigjeve mbeten bajt për bajt të njëjta dhe asnjë rezultat nuk
ndryshon. Verifikimi e mbron këshillën si rekomandim: në katalogun
`r1.4`, rregulli R8 kërkon që çdo këshillë e kontekstit të jetë në dalje
fjalë për fjalë, dhe një këshillë e hequr ose e riformuluar e çon
shpjegimin te shablloni (seksioni 4.5). Këshillat e dorëzuara ruhen të
plota në bazë (`document_advice`), që fjalia që pa pacienti të mbetet e
lexueshme edhe kur tabela ndryshon.

Tabela u dorëzua bosh dhe u plotësua më 7 tetor 2026: %d nga 76 rreshta
mbajnë një fjali dhe burimin e saj, faqe pacientësh të MedlinePlus (në
shumicën e rasteve seksioni «What do the results mean?»), të Cleveland
Clinic dhe të Testing.com, të hapura të gjitha atë ditë; për %s nuk ka
rresht, sepse asnjë faqe nuk jep përmbajtje të përdorshme për atë drejtim
(vlera e ulët është gjetja e shëndetshme). Një test e kalon çdo rresht të
plotësuar nëpër R1, R2, R3 dhe SP1–SP3 me kontekstin e vet, që një fjali
me numër, me analit tjetër, me trajtim ose me diagnozë të mos hyjë në
depo. Tabela e plotë është te Shtojca B (Tabela B.4); fjalitë nuk janë
rishikuar nga një klinicist (seksioni 6.6).

""" % (len(filled), " dhe ".join(f"{names[r['loinc_code']]} ({'e lartë' if r['direction']=='increased' else 'e ulët'})" for r in unfilled))
rep("nga mjeku familjar, jo te një matje e këtij punimi.\n\n## 4.4 Dega e raportit mjekësor",
    "nga mjeku familjar, jo te një matje e këtij punimi.\n\n" + sec + "## 4.4 Dega e raportit mjekësor")

# ---------- 4.5 verification ----------
rep("Katalogu i zbatuar (versioni `r1.3`) përmban edhe një rregull politike, SP1–SP3, që refuzon pohimet diagnostike, të trajtimit dhe prognostike; versioni i katalogut regjistrohet te çdo rezultat verifikimi. Katalogu i plotë me një shembull për çdo rregull është te Shtojca C.",
    "Katalogu i zbatuar (versioni `r1.3`) përmban edhe një rregull politike, SP1–SP3, që refuzon pohimet diagnostike, të trajtimit dhe prognostike; versioni i katalogut regjistrohet te çdo rezultat verifikimi. Në versionin `r1.4`, që përdor shërbimi, R8 mbulon edhe këshillat me burim të seksionit 4.3.9: secila duhet të shfaqet në dalje fjalë për fjalë, pa rregull të ri dhe pa lloj të ri shkeljeje. Katalogu i plotë me një shembull për çdo rregull është te Shtojca C.")

# ---------- 4.10 database ----------
rep("Tabela e shpjegimeve ruan veçmas daljen e papërpunuar të modelit dhe daljen përfundimtare të shfaqur, bashkë me versionin e kërkesës, modelin e përdorur dhe parametrat e tij.",
    "Tabela e këshillave (`document_advice`) ruan për çdo dokument fjalitë me burim që iu bashkëngjitën gjetjeve, të plota, për të njëjtën arsye si fjalori. Tabela e shpjegimeve ruan veçmas daljen e papërpunuar të modelit dhe daljen përfundimtare të shfaqur, bashkë me versionin e kërkesës, modelin e përdorur dhe parametrat e tij.")

# ---------- 4.12 safety policy ----------
rep("**Çfarë përdor shërbimi dhe çfarë u mat** (ADR 0020, 0021).",
    "**Këshillat me burim** (ADR 0023). Sistemi nuk gjeneron këshilla: e vetmja këshillë që i shfaqet pacientit është fjalia e tabelës `advice.csv` për analitin dhe drejtimin përkatës, me burim të lexuar, e kopjuar fjalë për fjalë dhe e verifikuar nga R8 (seksioni 4.3.9). Fjalia nuk emërton gjendje, nuk jep trajtim dhe nuk parashikon; ajo i drejton pacientin te mjeku me një temë ose pyetje konkrete.\n\n**Çfarë përdor shërbimi dhe çfarë u mat** (ADR 0020, 0021).")
rep("Klasifikuesi i fjalive nuk është pjesë e shërbimit (ADR 0022).",
    "Klasifikuesi i fjalive nuk është pjesë e shërbimit (ADR 0022). Tabela e këshillave u shtua pas matjeve dhe nuk ndikon asnjë kontekst eksperimenti.")

# ---------- 5.1 table ----------
rep("| Vendimet arkitekturore | 22 ADR (`docs/adr/`) |",
    "| Këshillat me burim | %d nga 76 rreshta të plotësuar (38 analite × dy drejtime) nga faqe pacientësh të lexuara më 7 tetor 2026; verifikim R8 nën `r1.4` (Tabela B.4) |\n| Vendimet arkitekturore | 23 ADR (`docs/adr/`) |" % len(filled))
rep("| Testet | 987 kalojnë, 0 anashkalohen", "| Testet | 987 kalojnë, 0 anashkalohen (gjendja e matur më 2026-10-05; tabela e këshillave shtoi 20 teste më pas)")

# ---------- 6.6 limitation ----------
rep("Rregullat u rishikuan nga një mjek familjar i vetëm, pa protokoll të shkruar; për P10 (leukocite dhe CRP) literatura jep mbështetje të pjesshme.",
    "Rregullat u rishikuan nga një mjek familjar i vetëm, pa protokoll të shkruar; për P10 (leukocite dhe CRP) literatura jep mbështetje të pjesshme. Këshillat me burim (seksioni 4.3.9, 75 fjali) rrjedhin nga faqe pacientësh, jo nga udhëzues klinikë, janë formulime të autorit, nuk janë rishikuar nga një klinicist, dhe u shtuan pas eksperimenteve: efekti i tyre mbi daljen e modelit (sa shpesh modeli e kopjon fjalinë fjalë për fjalë dhe sa dokumente shkojnë te shablloni për këtë arsye) nuk është matur.")

# ---------- 6.7 future work ----------
rep("Zgjerimi i tabelës terminologjike dhe i panelit të analiteve do ta rriste mbulimin praktik të sistemit pa ndryshuar arkitekturën.",
    "Zgjerimi i tabelës terminologjike dhe i panelit të analiteve do ta rriste mbulimin praktik të sistemit pa ndryshuar arkitekturën; rishikimi klinik i tabelës së këshillave dhe matja e R8 mbi këshillat me modelin e vërtetë (një kusht i ri ablacioni me kontekste që kanë këshilla) janë hapi i natyrshëm i radhës për atë tabelë.")

# ---------- Appendix B.4 ----------
lines = ["*Tabela B.4. Këshillat me burim për vlerat jashtë intervalit (`resources/advice.csv`)*", "",
         "| Kodi LOINC | Analiti | Drejtimi | Fjalia | Burimi |", "|---|---|---|---|---|"]
for r in rows:
    d = "↑" if r["direction"] == "increased" else "↓"
    if r["advice_sq"]:
        lines.append(f"| {r['loinc_code']} | {names[r['loinc_code']]} | {d} | {r['advice_sq']} | {short_src(r['source_ref'])} |")
    else:
        lines.append(f"| {r['loinc_code']} | {names[r['loinc_code']]} | {d} | — (pa rresht: asnjë faqe nuk jep përmbajtje të përdorshme për këtë drejtim) | — |")
b4 = "\n".join(lines) + "\n\nÇdo faqe u hap më 7 tetor 2026; adresa e plotë e secilës dhe fjalia angleze që e mbështet fjalinë shqipe ruhen te `docs/thesis/worksheets/keshillat_e_gjetura.csv`. Fjalitë janë formulime të autorit brenda asaj që thotë faqja dhe nuk janë rishikuar nga një klinicist.\n"
rep("u rishikuan dhe u konfirmuan nga një mjek i mjekësisë familjare në tetor 2026.\n",
    "u rishikuan dhe u konfirmuan nga një mjek i mjekësisë familjare në tetor 2026.\n\n" + b4)
rep("**Shtojca B** — Paneli i plotë i analiteve me kodet LOINC dhe intervalet referente rezervë",
    "**Shtojca B** — Paneli i plotë i analiteve me kodet LOINC, intervalet referente rezervë, rregullat e kombinimit dhe këshillat me burim")

MD.write_text(doc, encoding="utf-8")
print("advice pass ok:", len(filled), "filled")
