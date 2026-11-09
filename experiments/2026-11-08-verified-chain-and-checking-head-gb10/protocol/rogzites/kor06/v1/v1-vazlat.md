# 06 v1 — a rögzített elemzés (vázlat Dani jóváhagyására)

Ez a lap rögzíti, mit és hogyan értékelünk a friss családok CAL- és TESZT-szeletén, a pecsét nyitása előtt. A runbook
(`06-runbook.md`, a rögzítéskor `06-runbook-v1.md`) a részletes leírás; ahol a kettő eltér, ez a lap dönt. A
rögzítés után a lista csak új verzióval (v1.1) módosítható, a pecsét alatti eredmények megtekintése előtt.

**Állapot:** 2026-10-31. A D23 és a D24 elfogadva (Dani, 2026-10-31). A pecsétmanifest a K06F3C (78 fájl, teljes;
a bank a D21–D22 után újrakiolvasva, a másik két család változatlan).

## 1. Kérdés és döntési szabály

- **K1 (elsődleges):** a B1 változatlan javaslatain a célterületen tanított megbízhatósági modell (B1-R, a teljes
  T500-zal) rangsora jobb-e a B1 saját pontszámánál (B1-S): ΔAURC (S+N) = AURC(B1-R) − AURC(B1-S) a TESZT-en, szigorú
  helyességgel, családonként és a három család egyenlő súlyú átlagában.
- **A 8.3 szabály (a D4-gyel), előre rögzítve — a következő kör indokolt, ha:**
  1. legalább két családon B1-R − B1-S < 0 (pontbecslés);
  2. átlag(AURC_B1-R) / átlag(AURC_B1-S) ≤ 0,90 (pontbecslés), **és** az arány 95%-os bootstrap-intervallumának felső
     határa < 1.
- **Ez kutatási továbblépés**, nem automatizálási garancia; precizitás- és munkaponti feltétel nincs benne (8.3).
- **A 10% gyakorlati választás**, nem statisztikai szabály. Az intervallum-feltétel azt támasztja alá, hogy van
  javulás; azt nem bizonyítja, hogy a valódi javulás legalább 10%.
- **A siker három szintje** (K1, D11), külön értelmezve:

  | eredmény | mire ad bizonyítékot |
  |---|---|
  | B1-R jobb a B1-S-nél | a tanított megbízhatósági módszer javít a B1 eredeti sorrendjén |
  | B1-R jobb a B1-N-nél és a B1-LR-nél is | többet ad az egyszerű NONE-hátrasorolásnál és az ötjellemzős referenciánál; ez **teljes módszerek** összevetése, önmagában nem bizonyítja, hogy a többletet a rejtett állapotok adják (D10) |
  | a SELECT-javaslatokon is javít | a konkrét opcióválasztások megbízhatóságát is jobban rendezi |

- **Érvényességi kör:** a három vizsgált család, az előírt összetétel (D9) és az 500 példás célterületi adaptáció.

## 2. Adat

- **Családok:** `penzugy.bankparositas`, `muszaki.hibaelharitas`, `szabaly.koltsegelszamolas`; családonként 2000
  item (T500 500 / CAL 500 / TESZT 1000), alapesetenként egy item (D12); MATCH 60% / NO_MATCH 20% / MISSING_DATA 10% /
  OUT_OF_SCOPE 10%, fele magyar, fele angol (D9); a szétválasztás sabloncsoportonként (T500 30, CAL 30, TESZT 60 sablon).
  Az itemfájlok sha256-a a manifestben.
- **A minőség, ami a rögzítéskor ismert:**
  - címkeaudit (D14): 300 / 300, 1 címkehiba (b136, a D22 javítja), a felső korlát 1,57% ≤ 2% — átment;
  - javítások: D17 („A(z)”), D18 (angol költségnemek), D19 (számlatulajdonos-sor; lakcímváltozás), D21 (azonos
    esedékesség a közös összegű számlapárnál), D22 (kitalált hivatkozás a banki szövegben);
  - a Gemma második ítélete triage (D15): itemet nem töröltünk és nem javítottunk; a D21 után a bank MISSING_DATA-n
    a közös összegű pár közti választása közel véletlen (az esedékesség szerinti jel eltűnt);
  - családtávolság (bge-m3): a friss családok más csoportbeli távolságra a meglévőktől, közeli duplikátum nincs;
  - a B1 a T500-on: AURC 0,13–0,28 (a 13. pont csereküszöbe 0,01).
- **Kétértelmű item nincs** (a `ketertelmu` mindenütt hamis); a generálás után modellkimenet alapján nem válogattunk.

## 3. Karok és tanítás (a `b1rel06.f1` útja, a `friss06.py` betöltőivel)

| kar | tanítás |
|---|---|
| B1-S | a B1 saját pontszáma: a négy sorrend átlagolt valószínűsége a javasolt opción; temperature a 05 D_cal_prob-illesztése (`kor05/eredmenyek/F3/kalib/kalib.json`) |
| B1-N | a B1-S, a NONE-javaslatok a SELECT-ek mögött (D8) |
| B1-R0 | a D_meta-n előtanított fej (`cache/k06/b1rel`, a LR az `elotanit.json`-ból), célterületi tanítás nélkül |
| B1-R \| n | a B1-R0 a 05 T-meta eljárásával finomhangolva a T100 / T200 / T500 mintán: öt fold, foldonként belső 20%-os korai megállás, a teszten az öt fold-modell logitjának átlaga; seed 17, 42, 73 |
| B1-LR \| n | L2-logisztikus regresszió öt jellemzőn (top-1 − top-2, X-valószínűség, sorrend-egyetértés, B1-pontszám, NONE-jelző); C a {0,01; 0,03; 0,1; 0,3; 1} rácson, ötszörös CV |
| H, H-T-meta \| n | a 05 H tartalmi és megbízhatósági feje; a H-T-meta ugyanazzal a finomhangolással, ugyanazokon a mintákon |

- **T100 ⊂ T200 ⊂ T500:** öt egymásba ágyazott húzás alapesetenként (`k06-minta:<húzás>`), a T500 rögzített.
- **Fold-egység (D23):** a finomhangolás öt foldja, a belső korai megállás és a B1-LR C-jének CV-je
  sabloncsoportonként (hash-alapú csoportos foldok, a `GroupKFold` értelmében; nem rétegzett), hogy egy sablon rokon
  változatai ne kerüljenek a választóvonal két oldalára.
- **A T100 / T200 mintamérete itemszám** (alapesetenként); a közlésben húzásonként a sablonok száma is szerepel. A
  B1-R, a B1-LR és a H-T-meta ugyanazon a mintán tanul.
- **A szeletek szerepe:**
  - T500: tanítás és modellválasztás (a finomhangolás belső korai megállása, a B1-LR C-je), sablonos foldokkal;
  - CAL: előre rögzített szabályú küszöbválasztás (τ) és Platt-illesztés, csak a 8.4 leíró sorához;
  - TESZT: végső értékelés, rajta semmi nem illesztődik.

## 4. Végpontok

- **Elsődleges:** ΔAURC (B1-R | T500 − B1-S), szigorú helyesség, családonként és átlagban (1.).
- **Másodlagos, előre rögzítve:**
  - K1 2. szint: B1-R − B1-N és B1-R − B1-LR;
  - K1 3. szint: SELECT-AURC minden karnál a B1 SELECT-javaslatainak itemjein (D7);
  - K2: H-T-meta − B1-S, ΔAURC = ΔAURC\* + ΔE-AURC.
- **Kötelező, kiemelt sor (D20):** a nyereség bontása NONE- és SELECT-javaslatokra, családonként (`friss06 bontas`), és a
  B1-R − B1-N a fő eredmény mellett.
- **Leíró:** NONE-on belüli AUROC; javaslatfajták aránya és helyessége állapotonként; tanulási görbe (0, 100, 200,
  500); B1-LR − B1-S; enyhe helyesség; az abszolút javulás családonkénti megoszlása; **magyar bontás kötelezően**
  (minden végpont nyelvenként, D9).
- **Gyakorlati és kalibrációs leírás (8.4, nem része a szabálynak):** τ a CAL-on (CP-alsó ≥ 0,95, ≥ 200 elfogadott),
  a munkapont a TESZT-en (lefedettség, precizitás, hibák típusonként); a bootstrapban a CAL is újramintázva és a τ
  replikánként újraválasztva, a munkapont nélküli replikák aránya; Brier és ECE Platt nélkül és a CAL-on illesztett
  Platt-tal.

## 5. Statisztika

- **Bootstrap:** klaszteres, egész sabloncsoportokat mintáz újra (D23), családonként; az átlagnál a családok
  rögzítettek; 10 000 ismétlés, seed 20261029. Egy ismétlésen belül minden kar ugyanazokat a csoportokat kapja. A munkapont
  bizonytalanságánál a CAL is sabloncsoportonként újramintázva, a τ replikánként újra.
- **A futások összevonása (D24):** a pontbecslés a futások (három seed; a T100 / T200-nál öt húzás × három seed)
  AURC-jének átlaga, és a bootstrap replikánként ugyanígy a futások átlagát számolja ugyanazokon a csoportokon. Az
  intervallum így a tesztminta bizonytalanságát írja le a betanított futások mellett; a tanítás véletlenségét a futások
  közti eltérés mutatja (futásonkénti ΔAURC, min–max, szórás), külön sorban.
- Kétoldali p; a három család Holm-korrigált p-je leíró.
- **Erő (8.5, `kor06/eredmenyek/F4/mde06.md`) — tervezési becslés:** 1000 TESZT-alapesettel az átlagos relatív
  csökkenés MDE80-ja 3,9–9,6%. A szimuláció itemszintű klaszterrel és replikánként egy seeddel számolt, a sablonos
  klasztert és a futásátlagot nem modellezi. A B1 helyességének sablonon belüli korrelációja a T500-on ≈ 0 (ICC
  −0,04…−0,02), de ez nem azonos a két kar rangsorkülönbségének sablonon belüli függőségével. A tényleges
  bizonytalanságot a TESZT sablonos intervalluma adja. A nagyobb TESZT kérése (8.5) erre a becslésre épül.

## 6. Futtatás (F5, Dani „mehet”-je után)

```bash
python3 kor06/eszkozok/befagyaszt06.py ellenoriz
for f in penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas; do
  python3 kor06/eszkozok/friss06.py tanit --csalad "$f" --out cache/k06/f5
done
python3 kor06/eszkozok/friss06.py elemez    --be cache/k06/f5 --out kor06/eredmenyek/F5
python3 kor06/eszkozok/friss06.py bontas    --be cache/k06/f5 --out kor06/eredmenyek/F5
python3 kor06/eszkozok/friss06.py munkapont --be cache/k06/f5 --out kor06/eredmenyek/F5
```

A kód a rögzítés előtt a nyitott T500-on futott füsttesztként (`friss06 fusteszt`, 2026-10-31 08:03–08:18: a
tanítóminta a teszt is; mérőszámot nem írt ki, csak a szerkezetet ellenőrizte). A T100-húzások családonként 27–30, a
T200-húzások mind a 30 T500-sablont lefedik. Várható futásidő: a tanítás kb. 15 perc, az értékelés kb. 20 perc.

## 7. Döntések a rögzítés előtt

| # | kérdés | javaslat |
|---|---|---|
| D23 | a klaszter- és a fold-egység | **Elfogadva (Dani, 2026-10-31): a sabloncsoport.** A tanítás és a validáció szétválasztása (a finomhangolás foldjai, a belső korai megállás, a B1-LR CV-je) és a bootstrap sabloncsoportonként; a T100 / T200 mérete itemszám, a sablonszám közölve; a ≥ 200 elfogadott τ-feltétel mennyiségi feltétel marad (nem 200 független megfigyelés), a CAL újramintázása sablonos. |
| D24 | a seedek összevonása | **Elfogadva (Dani, 2026-10-31).** Elsődleges a futások AURC-jének átlaga; a bootstrap replikánként ugyanezt számolja; a futások közti eltérés külön sor. |
