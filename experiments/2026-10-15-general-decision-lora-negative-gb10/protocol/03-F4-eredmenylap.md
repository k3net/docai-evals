# K03F4 eredménylap (03-runbook v1, 7. pont)

A 03-as kör végső mérése: egy sok magyar (és 25% angol) feladatcsaládon tanított döntési LoRA (G3) a három kitartott
rétegen, a kalibrált bázishoz (L1★) és a feladatspecifikus LoRA-khoz (L3-spec) mérve.

- **A mérés módja:** a v1 rögzítése 2026-10-14 10:08-kor történt (`kor03/rogzites/v1/`, a manifest sha256-ja `86e5e9ac…`).
  A G3-karok F4-eredményeit és az összehasonlításokat a rögzítés előtt nem néztük meg. Az elemzés 2026-10-14
  21:33–21:37 között futott a v1 szerint: 10 000 ismétlés, hierarchikus bootstrap (seed × klaszter), a val-ok és a
  kalibrációs minták klaszteresen újramintázva, a τ replikánként újraválasztva.
- **Források:**
  - gépi táblák: [eredmenylap_gepi.md](eredmenylap_gepi.md);
  - teljes kimenet: `f4_elemzes03.json`;
  - technikai lezárás: `teljesseg.json`;
  - leíró bontások: `f4_leiro03.json` (`kor03/eszkozok/f4_leiro03.py`, utólagos).
- **Az értelmezés** (utolsó szakasz) kézzel írt, 2026-10-15.

**Definíciók:**
- **lef@95:** a pontozott itemek aránya, amelyet a kar a val-on választott τ@95 fölött nem-X opcióhoz rendel;
- **precizitás:** ezek közül a helyes, ⚠ = 0,93 alatt;
- **X-fedés:** az X-gold itemek közül hánynál X a top-1 (τ-független);
- **AURC:** a kar saját nem-X döntéseinek kockázat–lefedettség görbéje alatti terület (a 00 definíciója);
- **elfogadott hiba X-goldon:** a τ fölött opcióhoz rendelt item, amelynek a goldja X.

## Összefoglalás

- **H1 mindhárom kitartott rétegen: „nem teljesíti a követelményeket”.**
  - A G3 mindenhol szignifikánsan többet fogad el: +7,2 és +11,1 pont között.
  - A precizitása viszont a val-τ-val mindenhol 0,93 alatt marad: 0,866–0,912.
  - A HO-terméken és a HO-routingon az AURC is szignifikánsan rosszabb, a HO-újon jobb.
- **A precizitásesés a HO-terméken és a HO-routingon az X-itemekből jön.** A nem-X itemeken a G3 0,99-es precizitással
  dönt, az X-gold itemekből viszont kétszer annyit rendel magabiztosan opcióhoz, mint a bázis. Ez a 01 L3
  irrelevancia-hibája, és most olyan családon is megjelenik, amelyet a G3 nem látott.
- **A bázis-horgony ezt nem védte ki.** Az X-fedés megőrzése sem a G3-nál, sem a G3-keménynél nem igazolható, és
  a horgony hatása rétegenként ellentétes irányú (H6, feltáró).
- **A kalibráció nem visz át:**
  - a val-τ egyik rétegen sem tartja a 0,93-at;
  - a 200 itemes célréteg-mintán a HO-terméken és a HO-routingon nincs olyan τ, amely a szabályt teljesítené;
  - a HO-újon van, de ott a G3 annyit tud, mint a bázis.
- **A H2 formálisan „érdemi átvitel” mindkét rétegen.** A H2 azonban csak lefedettséget hasonlít: a HO-terméken a G3
  ugyanazt a lefedettséget 0,91-es precizitáson éri el, amelyet a 00 adaptere 0,97-esen.
- **A publikus általános döntési adapter feltétele ebben a körben nem teljesült.** A recept módosítása a 7.10 szerint
  külön kísérleti kör.

## Technikai lezárás (7.9)

- Mind a 25 szükséges kiolvasás (az F4 tizenkettő, az F2 L1★ val/eval, az F3 val-ok, az L3-spec saját val-jai) teljes,
  ismétlődés és érvénytelen sor nélkül. A modellnév minden soron a karé.
- **Pótlás:**
  - G3 s1: 5545 pár, 1387 item; G3 s3: 2206 pár, 553 item;
  - a pótolt párok pontosan a hibanapló párjai;
  - az eredeti sorok előtagja bitre a pecsétnek megfelelő (178 315, illetve 181 654 sor);
  - az élő PECSET a rögzítéskori pillanatképpel kezdődik.
- **Futásazonosítók:** `K03F4-potlas 2026-10-14 21:20:34` (G3 s1) és `21:31:45` (G3 s3).
- **Példányzaj (L0′ − L1★):** a top-1-billenés 1,2–3,5%, a |Δlef@95| ≤ 0,2 pont. Az L0′-szabály sehol nem lépett
  életbe.
- **Önellenőrzés:** egyik fő kontraszt pontbecslése sem esik a saját bootstrap-CI-jén kívül.

## Rétegek (pontbecslés, val-τ)

**HO-termék** — pontozott 4524, ebből X-gold 1103

| kar | lef@95 | precizitás | AURC | ECE | X-fedés | top-1 |
|---|---|---|---|---|---|---|
| L1★ (perm-átlag, T = 1,431) | 0,653 | 0,963 | 0,0296 | 0,058 | 0,415 | 0,824 |
| L0′ (új példány) | 0,654 | 0,964 | 0,0293 | 0,057 | 0,419 | 0,825 |
| G3, 3 seed átlaga [tartomány] | 0,761 [0,744–0,794] | 0,912 ⚠ [0,878–0,933] | 0,0434 | 0,062 | 0,340 | 0,809 |
| G3-kemény s1 | 0,740 | 0,921 ⚠ | 0,0365 | 0,054 | 0,395 | 0,817 |
| G3-hu s1 | 0,722 | 0,942 | 0,0378 | 0,062 | 0,327 | 0,810 |
| L3-spec (00), 3 seed átlaga [tartomány] | 0,756 [0,750–0,764] | 0,973 [0,967–0,976] | 0,0016 | 0,013 | 0,942 | 0,965 |

**HO-routing (a 01 megerősítő tesztje)** — pontozott 7416, ebből X-gold 2454

| kar | lef@95 | precizitás | AURC | ECE | X-fedés | top-1 |
|---|---|---|---|---|---|---|
| L1★ (perm-átlag, T = 1,431) | 0,644 | 0,918 ⚠ | 0,0343 | 0,023 | 0,765 | 0,889 |
| L0′ (új példány) | 0,644 | 0,918 ⚠ | 0,0359 | 0,023 | 0,762 | 0,888 |
| G3, 3 seed átlaga [tartomány] | 0,732 [0,730–0,733] | 0,866 ⚠ [0,861–0,870] | 0,0816 | 0,064 | 0,570 | 0,840 |
| G3-kemény s1 | 0,738 | 0,858 ⚠ | 0,0844 | 0,074 | 0,529 | 0,827 |
| G3-hu s1 | 0,681 | 0,898 ⚠ | 0,0589 | 0,049 | 0,712 | 0,880 |
| L3-spec (01), 3 seed átlaga [tartomány] | 0,768 [0,759–0,774] | 0,838 ⚠ [0,831–0,844] | 0,0641 | 0,090 | 0,670 | 0,865 |

**HO-új (KIE/validáció)** — pontozott 2200, ebből X-gold 306

| kar | lef@95 | precizitás | AURC | ECE | X-fedés | top-1 |
|---|---|---|---|---|---|---|
| L1★ (perm-átlag, T = 1,431) | 0,568 | 0,938 | 0,0717 | 0,043 | 0,353 | 0,721 |
| L0′ (új példány) | 0,567 | 0,939 | 0,0716 | 0,045 | 0,369 | 0,718 |
| G3, 3 seed átlaga [tartomány] | 0,636 [0,620–0,661] | 0,905 ⚠ [0,892–0,916] | 0,0444 | 0,074 | 0,653 | 0,745 |
| G3-kemény s1 | 0,635 | 0,906 ⚠ | 0,0410 | 0,088 | 0,611 | 0,744 |
| G3-hu s1 | 0,592 | 0,926 ⚠ | 0,0467 | 0,055 | 0,732 | 0,755 |

A val-τ@95: L1★ 0,716; G3 s1 0,786, s2 0,759 (nyers kar), s3 0,760; G3-kemény 0,759; G3-hu 0,850. Az L3-spec saját
val-ján: 00: 0,275–0,343, 01: 0,339–0,496.

## Hipotézisek

| hipotézis | ítélet | részletek |
|---|---|---|
| H1 — HO-termék | **nem teljesíti a követelményeket** | precizitás 0,912 < 0,93; Δlef@95 +11,1 pont [6,9; 16,1], p < 0,0001; ΔAURC +0,014 [0,002; 0,027], p = 0,016 (a G3 ellen, Holm után is szignifikáns) |
| H1 — HO-routing | **nem teljesíti a követelményeket** | precizitás 0,866; Δlef@95 +8,9 pont [6,7; 11,3]; ΔAURC +0,047 [0,039; 0,057] (a G3 ellen) |
| H1 — HO-új | **nem teljesíti a követelményeket** | precizitás 0,905; Δlef@95 +7,2 pont [3,7; 11,0]; ΔAURC −0,027 [−0,033; −0,022] (a G3 javára) |
| H2 — HO-termék | **érdemi átvitel** (csak lefedettség) | L3−L1★ +10,3 pont [6,3; 15,3]; D +5,7 pont [2,5; 9,7]; nyereségarány (leíró) 1,05 [0,73; 1,62] |
| H2 — HO-routing | **érdemi átvitel** (csak lefedettség) | L3−L1★ +12,4 pont [9,6; 15,1]; D +2,6 pont [0,7; 4,9]; nyereségarány 0,71 [0,55; 0,94] |
| H3(a) val-τ | **nem teljesítette** mindhárom rétegen | precizitás [CI]: HO-termék 0,912 [0,875; 0,941], HO-routing 0,866 [0,846; 0,882], HO-új 0,905 [0,880; 0,925] |
| H3(b) célréteg-τ | HO-termék, HO-routing: **nincs megfelelő τ, nem siker**; HO-új: **teljesítette** | a replikák 90%-ában (HO-termék), illetve 97%-ában (HO-routing) sincs τ; HO-új: precizitás 0,975 [0,938; 0,989], lefedettség 0,34–0,52 seedenként (L1★: 0,976 / 0,50) |
| H4 — HO-termék | **nem teljesíti a követelményeket** | G3 s1 precizitás 0,924; ΔAURC +0,005 [0,002; 0,009] (az angollal rosszabb); Δlef +2,5 pont [−0,3; 5,9] |
| H4 — HO-új | **nem teljesíti a követelményeket** | G3 s1 precizitás 0,916; Δlef +2,9 pont [1,4; 5,4]; ΔAURC −0,003 [−0,009; 0,002] |
| H4 — HO-routing magyar része | **segít** | ΔAURC −0,0026 [−0,0048; −0,0010]; Δlef +0,6 pont [−1,6; 3,0]; G3 s1 precizitás 0,964 |
| H5 (leíró) | — | a lef@95 mind a 23 teszt-ID-családon nő; a precizitás a jogi családokon esik (MultiEURLEX 0,78 → 0,68, NJT fejezet 0,93 → 0,77, NJT cím 0,95 → 0,87) |
| H6(a) X-fedés, −2 pont | **nem igazolható** sem a G3-nál, sem a G3-keménynél | G3 − L1★: HO-routing −19,3 pont [−24,3; −15,5], HO-termék −7,6 pont [−13,8; −0,4]; G3-kemény − L1★: −23,6 [−25,3; −21,9], illetve −2,0 [−4,5; 0,4] |
| H6(b) horgony (G3 s1 − G3-kemény s1) | feltáró | HO-routing: X-fedés −1,1 pont [−2,2; −0,1], AURC −0,006 [−0,010; −0,003]; HO-termék: X-fedés −6,7 pont [−8,8; −4,6], AURC +0,007 [0,004; 0,010] |
| H6(c) átcímkézett routing-itemek (51) | leíró | a régi címkét adja (ebből a τ fölött): L1★ 13 (6), G3 12–15 (8–10), G3-kemény 15 (10), G3-hu 17 (12), 01 L3 26–29 (mind) |

**Érzékenységi blokkok:**
- **A tervezet HO-routing-rétege** (a T-hu-maradékkal, 9638 pontozott): G3 precizitás 0,882, Δlef@95 +8,3 pont
  [6,0; 10,8], ΔAURC +0,041. Az ítélet ugyanaz.
- **A pótlással érintett HO-routing-itemek** (1363): G3 precizitás 0,952, Δlef +5,5 pont. A nem érintettek (6053):
  0,842, illetve +9,7 pont. A pótolt itemek a fájl első blokkjából valók (BFCL simple, multiple, irrelevance, live
  simple, a live multiple egy része), így a különbség a forrásösszetételből jön. A példányhatás ebből nem különíthető
  el.

## Leíró bontások (utólagos, F4 után; az ítéletet nem változtatják)

**1. Honnan jön a precizitásesés** (pontbecslés, val-τ; a G3 a 3 seed átlaga):

| réteg | kar | elfogadott hiba X-goldon / rossz opción | nem-X precizitás | az X-gold itemek elfogadási aránya | hibák ≥ 0,95 bizalommal | kockázat 0,5-ös lefedettségen |
|---|---|---|---|---|---|---|
| HO-termék | L1★ | 101 / 8 | 0,997 | 9,2% | 5 (5%) | 0,018 |
| | G3 | 277 / 30 | 0,991 | 25,1% | 69 (23%) | 0,025 |
| | G3-kemény | 236 / 28 | 0,991 | 21,4% | 75 (28%) | 0,023 |
| | L3-spec (00) | 63 / 30 | 0,991 | 5,7% | 19 (20%) | 0,001 |
| HO-routing | L1★ | 368 / 23 | 0,995 | 15,0% | 151 (39%) | 0,049 |
| | G3 | 694 / 35 | 0,993 | 28,3% | 375 (51%) | 0,085 |
| | G3-kemény | 735 / 44 | 0,991 | 30,0% | 404 (52%) | 0,090 |
| | L3-spec (01) | 802 / 123 | 0,975 | 32,7% | 521 (56%) | 0,078 |
| HO-új | L1★ | 13 / 65 | 0,947 | 4,2% | 3 (4%) | 0,025 |
| | G3 | 24 / 109 | 0,921 | 7,8% | 58 (43%) | 0,026 |

**2. HO-routing forrásonként** (X-fedés / precizitás; az irrelevancia-forrásokon minden elfogadás hiba):

| forrás | n (X) | L1★ | G3 | G3-kemény | G3-hu | L3-spec (01) |
|---|---|---|---|---|---|---|
| BFCL irrelevance | 236 (236) | 0,860 / – | 0,672 / – | 0,636 / – | 0,814 / – | 0,718 / – |
| BFCL-live irrelevance | 856 (856) | 0,655 / – | 0,449 / – | 0,428 / – | 0,588 / – | 0,535 / – |
| When2Call | 3324 (1016) | 0,781 / 0,933 | 0,544 / 0,881 | 0,470 / 0,869 | 0,748 / 0,916 | 0,704 / 0,855 |
| T-hu (átnézett) | 541 (191) | 0,911 / 0,983 | 0,892 / 0,959 | 0,895 / 0,966 | 0,874 / 0,954 | 0,857 / 0,910 |
| T-katalógus | 586 (155) | 0,942 / 0,988 | 0,860 / 0,964 | 0,858 / 0,961 | 0,806 / 0,969 | 0,888 / 0,931 |
| BFCL simple/multiple, live simple/multiple | 1873 (0) | – / 0,996–1,000 | – / 0,996–1,000 | – / 0,991–1,000 | – / 0,997–1,000 | – / 0,972–1,000 |

**3. HO-termék alrétegenként:** a G3 precizitása 0,881 (T-közeli) és 0,935 (T-távoli) között, a nem-X precizitás
mindenhol 0,988–0,995. Az X-fedés 0,27–0,44 (L1★: 0,35–0,49, a 00 L3: 0,91–0,98). Az új szállítókon (T-újszállító) a
G3 0,906, az L1★ 0,960.

**4. HO-új családonként** (lef / precizitás / X-fedés):

| család | L1★ | G3 | G3-hu |
|---|---|---|---|
| kie.dátum | 0,580 / 0,983 / 0,500 | 0,648 / 0,969 / 0,651 | 0,596 / 0,995 / 0,811 |
| kie.mező | 0,884 / 0,989 / 0,758 | 0,899 / 0,983 / 0,783 | 0,889 / 0,988 / 0,818 |
| kie.összeg | 0,235 / 0,628 / 0,037 | 0,358 / 0,594 / 0,590 | 0,287 / 0,590 / 0,627 |

**5. A G3 s2 kalibrációs karja:** a val-on nála a nyers kar nyert. A többi seed perm-átlag karjával (T = 0,878,
τ = 0,767) a precizitása a HO-terméken 0,878 helyett 0,908, a HO-újon 0,892 helyett 0,912, a HO-routingon 0,870
helyett 0,864. A kar választása a seed-szórás egy részét magyarázza, de az ítéletet egyik rétegen sem változtatná meg.

## Értelmezés (kézzel írt, 2026-10-15; a fenti leíró bontásokra épül)

### Hol nyer és hol veszít a G3

1. **A nem-X döntéseken jó, és többet dönt.** A HO-terméken és a HO-routingon a G3 nem-X precizitása 0,991–0,993, a
   bázisé 0,995–0,997. A BFCL tiszta hívásain 0,996–1,000. A lefedettség mindhárom rétegen 7–11 ponttal nő, és ennek
   zöme a nem-X itemekből jön. A teszt-ID-n (H5) minden családon nő a lefedettség. Ez a „döntésre tanítás” része
   átvisz.
2. **A precizitásesés a HO-terméken és a HO-routingon teljes egészében az X-itemekből jön.** A G3 az X-gold itemek
   25%-át (HO-termék), illetve 28%-át (HO-routing) rendeli a τ fölött opcióhoz, a bázis 9%-át és 15%-át. A hibái
   23%-a, illetve 51%-a ≥ 0,95 bizalmú, a bázisé 5% és 39%. Ugyanez volt a 01 L3 hibája. Most egy olyan modellnél is
   megjelenik, amely a routing-csoportot nem látta, tehát nem a feladatspecifikus train X-összetételének műterméke,
   hanem a döntésre tanításé.
3. **HO-routing: az irrelevancia-felismerés a tanult X-típusok ellenére romlik.**
   - Az X-fedés: When2Call 0,78 → 0,54, BFCL-live irrelevance 0,66 → 0,45, BFCL irrelevance 0,86 → 0,67.
   - Az MVP v2-ben az out-of-scope X a második leggyakoribb X-típus volt (394 item, az 1619 X 24%-a), más családok
     állapotaiból. Ez a kitartott
     routing-irrelevanciára nem vitt át; a G3 itt a 01 L3-nál is rosszabb (X-fedés 0,57 vs. 0,67).
   - A G3-hu (angol gerinc nélkül) sokkal kevésbé romlik: a When2Call-on 0,75, a BFCL-live irrelevance-en 0,59. Ez
     utólagos megfigyelés, mert a H4 a routingnak csak a magyar részét mérte. Arra utal, hogy az angol döntési
     adat (a tipizált döntések) a „hívd meg” irányba tolja a modellt az angol eszközválasztó itemeken.
4. **HO-termék: a gold-drop X nem visz át.** A 00 L3 a HO-termék X-ét 94%-ban ismeri fel (a saját gold-drop
   receptjével tanult), a bázis 42%-ban, a G3 34%-ban. A val gold-drop rése (F3, jogi családok) a kitartott rétegen
   nagyobb: a G3 a „van hasonló jelölt, válaszd azt” mintát a számla → cikk feladatra is átviszi. A H5 jogi családjai
   (MultiEURLEX, NJT) ugyanezt mutatják eloszláson belül is.
5. **HO-új: a hiba itt más.** Az X-et jobban ismeri fel, mint a bázis (természetes X 0,01 → 0,84; az összeg-családon
   0,04 → 0,59), az AURC jobb. A precizitás a kie.összeg család miatt bukik:
   - ott minden kar gyenge (0,59–0,63), mert a feladat aritmetika, és gondolkodás nélkül nem megy (a JPT-kártya ugyanezt
     írja);
   - a G3 ezen a családon is többet fogad el (0,24 → 0,36) ugyanolyan rossz precizitással;
   - a dátum- és a mezőcsaládon a precizitás 0,97–0,98.

   A HO-új tehát inkább azt mutatja, hogy a rétegítélet egy rossz családon múlik, mint azt, hogy a G3 rosszul
   általánosít.
6. **A kalibráció nem visz át, és a célréteg-minta sem menti meg.**
   - A G3 val-τ-ja (0,76–0,79) a kitartott rétegeken túl engedékeny. A saját tesztjén illesztett τ mellett a G3
     lefedettsége a HO-routingon 0,00–0,05 lenne (a bázisé 0,47): a magabiztos X-hibák a rangsor elején vannak, ezért a 95%-os
     precizitás ott gyakorlatilag elérhetetlen.
   - Ezért nem talál τ-t a 200 itemes célréteg-minta sem (H3(b)). A Clopper–Pearson-szabályhoz a rangsor elején ~60
     hibátlan elfogadás kell egymás után, és ezt a magabiztos X-hibák megakadályozzák. A bázis is csak a replikák
     27–53%-ában talál ilyet.
   - A 01-lelet tehát általános adapterre is áll: a val-on választott τ nem visz át más X-eloszlású rétegre.
7. **A horgony nem védte az X-viselkedést.**
   - A G3 és a G3-kemény X-fedése a HO-routingon gyakorlatilag azonos (0,57 vs. 0,53; a horgonyos s1 0,52).
   - A HO-terméken a horgonyos s1 6,7 ponttal rosszabb, mint a kemény.
   - A val-on is csak az ECE-ben látszott a horgony (F3).

   A horgony formája (β = 0,5, KL a bázis eloszlására csak az X-gold train-itemeken) a kitartott családok X-ére nem
   hat. Egy seed, feltáró eredmény.
8. **A címkekonvenció-beégés nem jelentkezik.** Az 51 átcímkézett routing-itemen a G3 annyiszor adja a régi
   MASSIVE-címkét, mint a bázis (12–15 vs. 13), a 01 L3 kétszer annyiszor, mind a τ fölött. A routing azonban kimaradt
   a G3 tanításából, ezért ez nem bizonyítja, hogy a recept a beégést kivédi (H6(c), leíró).
9. **A H2 definíciójának gyengesége, mint a 01-ben.** A H2 a lefedettséget méri precizitási feltétel nélkül.
   - A HO-terméken a G3 „érdemi átvitel”-e mögött 0,91-es precizitás áll a 00 adapter 0,97-ével szemben, és ~27-szer
     nagyobb AURC.
   - A HO-routingon a referencia maga is bukik (a 01 L3 precizitása 0,84).

   Előre rögzített szabály, ezért nem írjuk át, de állítás nem épül rá.
10. **Seedek:** a lefedettség szórása kicsi (HO-routing 0,730–0,733), a precizitásé a HO-terméken nagy (0,878–0,933). A
    G3 s3 a HO-terméken épp eléri a 0,93-at; a s2-t részben a val-on választott nyers kar rontja (5. bontás).

### Ami megáll

- A G3 a nem-X döntéseken a bázis szintjén pontos, és mindenhol többet dönt. Eloszláson belül (H5) minden családon
  nagyobb a lefedettsége.
- A HO-routing magyar részén (T-hu, T-katalógus) a precizitása 0,95–0,97, és az angol gerinc ott javít (H4 „segít”).
- A KIE-validáció természetes X-ét („egyik tételsor sem hibás”) a G3 megtanulta és átviszi (X-fedés 0,01 → 0,84). A
  hiányzó feltételt („a döntéshez szükséges adat nincs a dokumentumban”) kissé jobban ismeri fel, mint a bázis
  (0,50 → 0,58). *Javítva 2026-10-15: korábban a zárójel a hiányzó feltételt írta a természetes X-hez.*
- A forrás címkézési konvencióit nem égeti be.

### Következmények (javaslat; a 7.10 szerint külön kísérleti kör)

- **Az X-döntést külön kell kezelni.** Kitartott családon a LoRA „van hasonló opció → válaszd” mintát tanul, és ezt
  sem a négy X-típus, sem a jelen horgony nem ellensúlyozza. A 01 leíró bontásában a „hívjon-e” kérdést a bázis
  döntötte el, és az X-fedés megmaradt. Ennek általános változata egy kétlépcsős döntés: X vagy nem X a kalibrált
  bázisból (vagy külön X-τ-val), és az opcióválasztás a LoRA-ból.
- **A kalibrációt a célforgalom X-eloszlásán kell választani**, de a 200 itemes minta a jelen CP-szabállyal kevés.
  Vagy nagyobb célréteg-minta kell, vagy olyan szabály, amely magabiztos hibák mellett is ad τ-t (pl. a precizitás
  rögzített lefedettségen).
- **Az angol gerinc szerepét újra kell nézni.** A magyar routingon segít, az angol irrelevancián (utólagos
  megfigyelés) ront. Ha marad, angol irrelevancia-típusokkal együtt.
- **Az aritmetikai KIE-családot** (összeg) gondolkodás nélküli egytokenes döntésre ne használjuk kitartott rétegként
  egyedül, vagy jelentsük külön.
- **Publikálás (9. pont):** a G3 adapter általános döntési adapterként nem publikálható (H1). A magyar döntési
  adatkészlet publikálása a licenc-konfigurációk szerint a H1-től független; erről külön döntés kell.

## Feltáró kiegészítés: kétlépcsős döntés (2026-10-15, utólagos)

`kor03/eszkozok/f4_ketlepcso03.py` → `f4_ketlepcso03.json`, a meglévő F4-kiolvasásokon (új tanítás nélkül).

- **A kombináció:** az X-ről a kalibrált bázis dönt (kapu: ha az L1★ top-1-e X, a döntés X), az opciót a G3 választja.
  A bizalom (1 − p_L1★(X)) · p_G3(opció | nem X), a τ@95 a val-on.
- **Bootstrap:** 2000 ismétlés, seed × klaszter, a τ replikánként újra.
- **Érvényesség:** a tesztrétegek már elhasználtak, ezért ez csak irányt ad egy új körhöz, megerősítő állítás nem
  épülhet rá.

| réteg | L1★ lef / prec. / AURC | kétlépcsős (3 seed) lef / prec. / AURC | Δlef@95 [CI] | ΔAURC [CI] | lefedettség 95%-os precizitáson (saját tesztjén illesztett τ): L1★ / kétlépcsős / G3 |
|---|---|---|---|---|---|
| HO-termék | 0,653 / 0,963 / 0,030 | 0,723 / 0,936 / 0,029 | +7,5 [3,2; 12,3] pont | −0,0005 [−0,0025; 0,0017] | 0,682 / 0,675 / 0,650 |
| HO-routing | 0,644 / 0,918 / 0,034 | 0,655 / 0,916 / 0,038 | +1,4 [−1,3; 4,0] pont | +0,0033 [0,0011; 0,0061] | 0,471 / 0,490 / 0,016 |
| HO-új | 0,568 / 0,938 / 0,072 | 0,634 / 0,907 / 0,070 | +7,1 [3,4; 11,5] pont | −0,0019 [−0,0057; 0,0017] | 0,525 / 0,512 / 0,528 |
| HO-routing magyar része | 0,624 / 0,986 / 0,004 | 0,647 / 0,979 / 0,004 | +2,7 [0,7; 5,2] pont | −0,0001 [−0,0007; 0,0009] | 0,679 / 0,685 / 0,667 |

- **A kapu a G3 kárát eltünteti.** Az X-fedés a bázisé, a HO-routing a bázis szintjére áll vissza (a G3 0,866-os
  precizitása helyett 0,916), és az AURC a HO-terméken és a HO-újon a bázisé.
- **Valódi nyereséget viszont alig ad.**
  - A val-τ-val ugyan többet fogad el (HO-termék +7,5 pont 0,936-os precizitással, ami a H1 küszöbe fölött van), de azonos
    precizitáson a lefedettsége a bázisé (0,675 vs. 0,682).
  - A többlet a lazább τ-ból jön, nem jobb rangsorból: a bázis a nem-X itemeken eleve 0,995–0,997-es precizitással dönt,
    így az opcióválasztásban a G3-nak nincs mit hozzátennie.
  - A HO-újon a kapu a G3 egyetlen valódi előnyét (természetes X, AURC 0,044) is eldobja.
- **A szűk keresztmetszet a kitartott terület X-konvenciója.**
  - A HO-termék X-ét a bázis 42%-ban, a G3 34%-ban ismeri fel. A saját területén tanított 00 L3 94%-ban.
  - Hogy mikor „nem illik egyik sem”, az területfüggő, és sem az általános tanítás, sem a bázis nem hozza magával.
  - Egy új körben ezért nem a döntésre tanítást, hanem az X-döntés célterületi illesztését (kis címkés minta,
    külön X-küszöb vagy X-fej) érdemes vizsgálni.
