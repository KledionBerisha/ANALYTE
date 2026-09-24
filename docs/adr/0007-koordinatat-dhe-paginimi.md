# 0007 — Origjina e koordinatave dhe pronësia e paginimit

**Gjendja:** i zbatuar

## Konteksti

Çdo gjetje ruan kutinë kufizuese të rreshtit prej të cilit doli, që
ndërfaqja të mund të theksojë zonën burimore. PDF-ja i mat koordinatat me
origjinë poshtë-majtas; bibliotekat me të cilat lexohet faqja — PyMuPDF
dhe pdfplumber — i raportojnë me origjinë lart-majtas.

Njëkohësisht, numri i faqes ku bie një rresht është pjesë e së vërtetës
bazë, dhe ai varet nga mënyra si faqja mbushet.

## Vendimi

**Koordinatat ruhen me origjinë lart-majtas**, ashtu si i lexon sistemi.
Kthimi nga sistemi i PDF-së bëhet një herë, te vizatuesi i korpusit.

**Paginimi i përket së vërtetës bazë, jo vizatuesit.** Gjeneruesi
llogarit se në cilën faqe bie çdo rresht përpara se dokumenti të
vizatohet; vizatuesi numëron rreshtat njësoj dhe e kontrollon përputhjen
me pohim gjatë vizatimit.

## Alternativat e refuzuara

**Ruajtja në koordinatat native të PDF-së.** Do të kërkonte kthim në çdo
vend ku kutia përdoret. Një kthim i harruar nuk prish asgjë që duket: ai
thjesht e vendos theksimin diku tjetër në faqe, dhe kjo zbulohet muaj më
vonë kur dikush hap ndërfaqen.

**Paginimi i vendosur nga vizatuesi.** Do ta bënte të vërtetën bazë të
varur nga gjatësia e shkronjave, pra nga një ndryshim stili.

## Pasojat

Kutitë provohen dhe nuk besohen: një test nxjerr tekstin brenda çdo kutie
nga PDF-ja e prodhuar dhe kërkon aty emrin dhe vlerën e gjetjes. Ky test
është i vetmi që do ta kapte një gabim origjine.

Për faqet e skanuara, kutitë rrotullohen bashkë me faqen; përndryshe e
vërteta bazë do të tregonte vende ku nuk ka më asgjë.

Pohimi i përputhjes së paginimit e zuri një gabim të vërtetë të
vizatuesit: kur tabela mbaronte pikërisht në kufi faqeje, funksioni i
pozicionit e kthente rreshtin e radhës në krye të së njëjtës faqe dhe
narrativa vizatohej sipër tabelës. Për syrin duket si dy tekste të
mbivendosura; për nxjerrjen është rresht i përzier.
