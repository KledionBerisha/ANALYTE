# 0023 — Këshillat me burim: një tabelë, jo modeli gjuhësor

**Gjendja:** i zbatuar; tabela dërgohet bosh dhe plotësohet vetëm nga burime që autori i ka lexuar.
**Data:** 2026-10-07

## Konteksti

Pacienti që lexon shpjegimin kërkon edhe një hap tjetër: jo vetëm «vlera është mbi intervalin referent», por
«çfarë mund të bëj». Kërkesa e autorit ishte që modeli gjuhësor të japë një këshillë të shkurtër për çdo vlerë
jashtë intervalit (p.sh. për ushqimin), duke theksuar gjithnjë konsultën me mjekun.

Kjo bie ndesh me parimin e punimit: modeli nuk ka autoritet mbi faktet. Një këshillë e shkruar nga modeli është
pohim mjekësor pa burim, dhe SP1–SP3 (`domain/policy.py`) e ndalojnë shprehimisht trajtimin dhe këshillën
klinike. Auditi i E8 tregoi se rregullat kapin vetëm një pjesë të gabimeve të modelit (ADR 0015); një këshillë e
shpikur do të arrinte te pacienti pa u parë. Shembulli i vetë kërkesës («hani më pak yndyrë» për një vlerë të
hemoglobinës) tregon rrezikun: fjalia tingëllon e arsyeshme dhe nuk i përgjigjet vlerës.

## Vendimi

**Këshilla është e dhënë, jo gjenerim.** Një tabelë e re burimore, `resources/advice.csv`, me një rresht për çdo
analit të panelit dhe çdo drejtim (`increased`, `decreased`): `loinc_code, direction, advice_sq, source_ref`.
Ajo ndjek saktësisht modelin e tabelës terminologjike dhe të kombinimeve:

1. **Fjalia shtypet fjalë për fjalë.** Shablloni e vendos menjëherë pas fjalisë së vlerës përkatëse
   (`generation/templates.py`); kërkesa e modelit e jep si tekst për t'u kopjuar, me ndalesën «mos shto asnjë
   këshillë tjetër» (`generation/prompt.py`). Udhëzimet e sistemit (`SYSTEM`) nuk ndryshojnë dhe blloku shfaqet
   vetëm kur konteksti ka këshilla; kontekstet e eksperimenteve nuk kanë, prandaj kërkesat e tyre dhe cache-i
   i përgjigjeve mbeten bajt për bajt të njëjta dhe `PROMPT_VERSION` mbetet `p1`.
2. **Rreshti pa burim nuk i shfaqet kurrë pacientit.** `Advice.is_filled` kërkon fjali dhe burim pa vendmbajtës;
   `grounding/branch_a/advice.py` lidh vetëm rreshtat e plotësuar me gjetjet që kanë drejtim (jo normale, jo
   pa interval, jo analit të dyfishtë), dhe `GroundingContext.advice` mban fjalinë bashkë me burimin, si fjalori.
3. **Verifikimi e mbron si rekomandim.** R8 (`verification/rules_prose.py`), në katalogun `r1.4`, kërkon që çdo
   këshillë e kontekstit të jetë në dalje fjalë për fjalë; një këshillë e hequr ose e riformuluar është
   `omitted_recommendation` dhe shpjegimi bie te shablloni. Nuk shtohet rregull i ri dhe asnjë lloj i ri shkeljeje:
   katalogu, Shtojca C, etiketat e klasifikuesit dhe të gjykatësve mbeten të njëjta. `r1.3` i ngrirë nuk e
   kontrollon (kontekstet e tij nuk kanë këshilla, prandaj rezultatet e matura nuk ndryshojnë).
4. **Rreshti i plotësuar duhet të kalojë vetë rregullat.** Ngarkuesi (`catalog.load_advice`) refuzon shifrat
   (R1 do t'i refuzonte), fjalinë pa pikë ose me më shumë se një pikë (R8 krahason një fjali), drejtimin e
   panjohur dhe kodin e panjohur. Testi `test_every_filled_row_of_the_shipped_table_survives_its_own_verification`
   e kalon çdo rresht të plotësuar nëpër R1, R2, R3 dhe SP1–SP3 me kontekstin e vet: një fjali që përmend një
   analit tjetër, një numër, një trajtim («merrni», «ilaç») ose një diagnozë nuk hyn në depo.
5. **Gjurmueshmëria.** Këshillat ruhen të plota te `document_advice` (migrimi 0006), si fjalori: fjalia që pa
   pacienti mbetet e lexueshme edhe nëse tabela ndryshon. `GET /advice` e kthen tabelën të plotë, me
   `is_filled`, që askush të mos e paraqesë më të plotë seç është.

**Çfarë lejohet të thotë një rresht.** Një fjali e vetme, pa numra, pa emër gjendjeje, pa trajtim, pa parashikim,
e formuluar si pyetje ose temë për mjekun («Pyesni mjekun tuaj nëse …», «Flisni me mjekun tuaj për …»). Burimi
duhet të jetë një faqe pacienti e lexuar (MedlinePlus «What does a high/low result mean», faqe pacientësh të
shërbimeve shëndetësore kombëtare), dhe fjalia shqipe nuk guxon të thotë më shumë se burimi.

## Pasojat

- Korpusi `data/v1` nuk preket: `advice.csv` nuk hyn në `RESOURCE_FILES` të gjeneruesit, sepse nuk ndryshon
  asnjë dokument dhe asnjë të vërtetë bazë; `GroundingContext.advice` ka vlerë të parazgjedhur bosh.
- Fleta e punës `docs/thesis/worksheets/burimet.md` radhit edhe rreshtat e paplotësuar të këshillave.
- Deri sa autori të plotësojë rreshta, sjellja e sistemit është e pandryshuar: tabela bosh nuk lidh asgjë.
- Puna e burimeve mbetet e autorit, si te termat: 76 rreshta, dhe asnjë nuk shkruhet pa u lexuar burimi.
- **Rreshti me burim por pa fjali është vendim**: burimi nuk jep asgjë për atë drejtim (p.sh. CRP nën intervalin),
  pacientit nuk i shfaqet asgjë, dhe fleta e punës nuk e radhit më si të mbetur.
- 2026-10-07: autori plotësoi 75 nga 76 rreshta (71 MedlinePlus, 2 Cleveland Clinic, 2 Testing.com); CRP ↓ mbeti bosh me
  qëllim. Të gjithë rreshtat e plotësuar kalojnë `tests/unit/test_advice.py`. Shtojca A.2 e punimit e radhit tabelën.
