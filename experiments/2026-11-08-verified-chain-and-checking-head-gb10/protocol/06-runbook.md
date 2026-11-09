# Runbook 06: célterületi megbízhatóság a B1 változatlan döntésein

**A B1 (a négy opciósorrendet átlagoló alapmódszer) változatlan döntésein javítja-e a helyes és a hibás javaslatok
rangsorolását egy 100, 200 vagy 500 célterületi alapeseten tanított megbízhatósági modell?**

- **Verzió:** v0.2, 2026-10-29: a v0.1 és az F1 pilot után Dani pontosításaival (14. pont D3, D7–D11; Napló).
  **Státusz:** a D1–D11 elfogadva; az F1 kész; az F2 (a friss családok építése) indul.
- **Előzmény:** a [05-runbook](05-runbook.md) 05a-ja negatív az előre rögzített szabály szerint (2026-10-29). Az
  általános, célterületi tanítás nélküli saját fej sikerét nem támasztja alá, a széles 05b-adatépítés nem indul.
  - Az utólagos diagnosztika (`kor05/eredmenyek/F3/v1a_diag/diag05.md`) szerint a HO-terméken a H hátrányának fele a
    tartalmi fej rosszabb javaslataiból jön.
  - A célterületi megbízhatósági tanítás (H-T-meta) a sorrendet mind a négy HO-rétegen javította, a HO-terméken a B1
    szintjéig.
  - Ezért a 06 a B1 döntéseit megtartja, és csak azt tanítja, melyikben érdemes megbízni.
- **Gép és infrastruktúra:** mint a 05-ben: spark-dev, a HF BF16 bázis, egyszerre egy nagy GPU-folyamat, a HF bázis
  mellett nem fut vLLM-példány.
- **Adatelv:** tanítás csak publikus és szintetikus adaton, mert az eredményt publikáljuk. Valós tenantadat csak
  értékelésre (Dani, 2026-10-28); ebben a körben nincs valós réteg, mert minden kar célterületi tanítást kér (14. pont,
  D1).
- **Végtermék:** döntés arról, hogy a „B1 + célterületi megbízhatóság” megér-e egy következő kört. Ez kutatási
  továbblépés, nem automatizálási garancia (8.3). Tanulmány, negatív eredmény esetén is.

> A hipotézist, a végpontokat, a szeleteket, a hiperparamétereket és a döntési szabályt a friss családok
> kalibrációs és tesztszeletének megnyitása előtt rögzítjük (`kor06/rogzites/v1/`, a 05 `befagyaszt05` és `pecset05`
> mintájára). A friss családok kalibrációs és tesztszeletének kiolvasása pecsételve fut.

---

## 1. Kutatási kérdés és hipotézis

- **K1 (fő):** a B1 javaslatain a célterületen tanított megbízhatósági modell (B1-R) rangsora jobb-e a B1 saját
  pontszámánál (B1-S), friss feladatcsaládokon?
- **K2 (másodlagos):** megéri-e egyáltalán lecserélni a B1 döntéseit? A H-T-meta (saját tartalmi fej, célterületi
  megbízhatósággal) a B1-S-hez mérve.
- **K1 három szintje** (különböző erősségű, önmagukban is értelmes eredmények; D11):
  1. a B1-R jobb a jelenlegi B1-nél (B1-S): az elsődleges végpont és a 8.3 szabály;
  2. a B1-R jobb az egyszerű NONE-kezelésnél (B1-N) és a kis tanult referenciánál (B1-LR);
  3. a B1-R a konkrét jelöltválasztások (SELECT) hibáit is jobban felismeri: a SELECT-AURC (8.1).
- **K3 (leíró):**
  - kell-e a nyereséghez a neurális fej, vagy elég egy kis, erősen regularizált modell (B1-LR);
  - hogyan változik a nyereség a tanítóminta méretével (100 → 200 → 500 alapeset);
  - mennyi munkát vesz át a munkapontnál.

## 2. Karok

| kar | javaslat | megbízhatósági pontszám | szerep |
|---|---|---|---|
| **B1-S** | B1 | a B1 saját pontszáma: a négy sorrendre átlagolt valószínűség a javasolt opción | elsődleges referencia |
| **B1-R** | B1, változatlanul | neurális megbízhatósági modell, célterületen tanítva (2.1) | a K1 fő vizsgálata |
| **B1-N** | B1, változatlanul | a B1 saját pontszáma, de minden NONE-javaslat a SELECT-ek mögött (2.4) | előre rögzített referencia: mennyi előny érhető el tanítás nélkül (D8) |
| **B1-LR** | B1, változatlanul | L2-regularizált logisztikus regresszió öt jellemzőn (2.2) | kis tanult referencia (K1 2. szint, K3) |
| **H-T-meta** | a H tartalmi feje | a H megbízhatósági feje, célterületen cross-fittelve (05 3.3, D3) | másodlagos összevetés (K2) |

- **A célcímke mindig az, hogy a B1 konkrét javaslata helyes-e.** A 05-ben a H döntéseire tanított megbízhatósági
  fej nem B1-fej; a B1-R-t a B1 helyességére tanítjuk újra.
- **A Platt-kalibráció nem külön kar.** Egyetlen pontszámra alkalmazva sorrendtartó: átírja a számokat (a túl
  magabiztos 0,99-ből lehet 0,91), de a rangsort nem. Ezért:
  - az AURC-t nem változtatja;
  - ha a τ-t ugyanazon a mintán minden lehetséges határon keressük, a választható elfogadott halmazok is ugyanazok;
  - a szerepe a valószínűségek pontossága, ezt a 8.4 diagnosztikája méri (Brier, ECE).

### 2.1. B1-R

- **Bemenet:**
  - a B1 kiolvasásából a kis jellemzők: a javasolt opció átlagos valószínűsége, a top-1 és a top-2 különbsége, az X
    („egyik sem”) valószínűsége, az entrópia, a négy sorrend egyetértése a javaslattal, az opciószám;
  - a kanonikus sorrend rejtett állapotai a 20., 28. és 40. rétegen (a 05 H-jellemzői): a kérdés, valamint a javasolt
    opció vége és átlaga; NONE-javaslatnál az X-sor.
- **Architektúra:** a 05 `RelHead` H-változata, a kis jellemzők a B1-éi.
- **Tanítás:** a 14. pont D2 döntése szerint. A javaslat: előtanítás a D_meta-n a B1 helyességére (ehhez a D_meta-n
  új B1-kiolvasás kell, 1., 2. és 3. sorrend), majd célterületi finomhangolás. A 05 T-meta beállításai rögzítve, a
  LR a D_meta-n választott.
- **A tanítóminta nulla pontja:** az előtanított, célterületen nem tanított fej. Leíró, a tanulási görbe kezdete.
- **Seedek:** 17, 42, 73. A tesztpontszám a három seed átlaga.

### 2.2. B1-LR

- **Jellemzők** (rögzítve, standardizálva a tanítómintán):
  - a top-1 és a top-2 pontszámkülönbsége;
  - az „egyik sem” pontszáma;
  - a négy opciósorrend egyetértése (a javaslatot adó sorrendek aránya);
  - a B1 saját pontszáma (14. pont, D3);
  - NONE-jelző: a B1 javaslata „egyik sem”-e (D3, a pilot után). A B1-R is megkapja ezt az információt; e nélkül a
    B1-R − B1-LR a NONE-konvenció megtanulását is mérné.
- **Regularizáció:** L2, a C a tanítómintán belüli 5-szörös, alapesetenkénti cross-validationnel, a C ∈
  {0,01; 0,03; 0,1; 0,3; 1} rácson.
- **Tanítás:** csak a célterületi mintán.

### 2.3. Amit a karok összevetése nem dönt el (D10)

- A B1-R − B1-LR különbség a bemenetből (rejtett állapotok), a hálózat felépítéséből és az előtanításból is
  származhat. Ebben a körben **a teljes módszerek különbségéről** beszélünk; „a belső állapotok többletet adnak”
  állítás nem következik belőle.
- Ehhez egy későbbi kör azonos felépítésű és tanítású fejet kérne, rejtett állapotokkal és nélkülük.

### 2.4. B1-N

- A B1 saját sorrendje, azzal a módosítással, hogy minden NONE-javaslat a SELECT-javaslatok mögé kerül; a NONE-ok
  egymás közti sorrendje is a B1 saját pontszáma.
- Determinisztikus, tanítás nélküli. Azt méri, mennyi a B1-S-hez mért előnyből egyetlen mechanikus szabály
  (az F1-ben a HO-terméken ront, a HO-újon a B1-R teljes előnyét adja).

### 2.5. H-T-meta

- A 05 H tartalmi és megbízhatósági feje, változatlan beállításokkal. A friss családokon kell hozzá HF-kivonás.
- A javaslatai eltérnek a B1-étől, ezért az összevetésben a ΔAURC mellett a felbontása is szerepel:
  ΔAURC\* (a javaslatok) + ΔE-AURC (a sorrend) (8.1).

## 3. Adat

### 3.1. Friss családok

- **Három új feladatcsalád.** Egyik sem szerepelt a 05 egyetlen szeletében sem, és a 03-ban sem tanítóként, sem
  tesztként.
  - A 05 pool 218 családjából 216 már szerepelt egy 05-szeletben, a maradék kettő a 03 külső eval-készlete
    (`level.sib200`: 1004 alapeset; `qa.belebele`: 488). Ezért **új adatépítés kell**: három család, nem a széles 05b.
- **Forrás:** a 05 4.2 szintetikus családjelöltjei közül három (14. pont, D1).
  - A címke a konstrukcióból jön.
  - A generátor Apache-2.0 licencű, nem Qwen-családú és nem Gemma (Mistral Small 4 vagy Muse-Glimmer-30B). A Llama
    csak szűrhet.
  - Utána emberi címkeaudit (05 4.3) és családtávolság-audit (05 4.2).
- **Méret:** családonként ≥ 2000 független alapeset.
- **Állapot- és nyelvi összetétel (D9):** a MATCH, NO_MATCH, MISSING_DATA és OUT_OF_SCOPE aránya, valamint a nyelvi
  arány családonként a generálás előtt rögzítve (3.4), a T500-ra, a CAL-ra és a TESZT-re ugyanazzal a rétegzett
  mintavétellel. A generálás után **a modellek eredményei alapján nem válogatunk** (3.4).

### 3.2. Szétválasztás (családonként, alapesetenként, a változatok generálása előtt)

| szelet | alapeset | szerep | pecsét |
|---|---|---|---|
| T500 | 500 | tanítóminta. T100 ⊂ T200 ⊂ T500, egymásba ágyazva | nincs |
| CAL | 500 | a τ kiválasztása (alapesetenként egy item, a 05 szabályával) | igen |
| TESZT | ≥ 1000 | értékelés, érintetlen | igen |

- A T100 és a T200 öt független, egymásba ágyazott húzás a T500-on belül (seed `k06-minta:<húzás>`); a T500 rögzített.
- **Az eredmény megfogalmazása:** „100 tanító alapeset, további 500 kalibrációs alapeset mellett”, nem pedig „100
  példa elég”. A τ-szabály (CP-alsó ≥ 0,95, ≥ 200 elfogadott) 100 összes példával eleve teljesíthetetlen.
- A kétértelmű itemek (`ketertelmu`) sem a tanításban, sem az értékelésben nem szerepelnek.
- Egy alapeset minden itemje (változata) ugyanabba a szeletbe kerül. A tanítás az alapeset minden itemjét használja,
  a bootstrap alapesetenként mintáz (8.2).

### 3.3. Fejlesztési adat: a 05 elhasznált HO-rétegei (14. pont, D5)

- A HO-rétegek a 05a-ban már nyitva voltak, ezért a 06-ban **csak fejlesztésre** szolgálnak: a csővezeték
  kipróbálására, a hatásméret becslésére, az erő-szimulációra (8.5) és a hibakeresésre. Tesztként nem.
- **Tanítóminta:** a célcsalád-minták (`cel:ho-*`; a HO-terméken 444 alapeset, ezért ott T100/T200/T400). **Értékelés:**
  a `teszt:ho-*` rétegek.
- A B1-kiolvasás és a rejtett állapotok ezeken már megvannak (pecsét alatt, a v1a óta nyitva), GPU nem kell.
- Ami a fejlesztésen dől el (jellemzők, hiperparaméterek, a D2–D3 változata), az a v1-ben rögzül, mielőtt a friss
  családok kalibrációs és tesztszelete megnyílik.

### 3.4. Az összetétel rögzítése és a válogatás tilalma (D9)

- **Mi rögzül a generálás előtt** (`kor06/spec/csaladok06.yaml`, a v1-manifestben is):
  - családonként a négy állapot célaránya és a nyelvi arány (magyar / angol);
  - a szétválasztás **sabloncsoportonként** (D12): az azonos sablonból származó esetek (ugyanaz a szintetikus cég
    nyitott számlái, ugyanaz a berendezésmodell az okkatalógusával, ugyanaz a szintetikus szabályzat) egy csoportot
    alkotnak, és a csoport egészében kerül a T500, a CAL vagy a TESZT részbe, a generálás előtt;
  - a szeleten belül az állapot × nyelv kvóták pontosan teljesülnek (D9);
  - a szűrési szabályok (3.5) és a pótlás módja.
- **Válogatás:** a generálás után egyetlen item vagy alapeset sem kerül ki vagy be az alany (Qwen, B1, B1-R, H)
  kimenete alapján. A megengedett szűrés (3.5) az alanytól független, előre rögzített érvényességi szabály.
- **Pontos kvóta, válogatás nélkül:** cellánként (szelet × nyelv × állapot) ~30% tartalékot tervezünk. A szűrés után a
  terv előre rögzített hash-sorrendjében az első N túlélő marad (N a cella kvótája). Ha kevesebb él túl, ugyanazzal a
  tervezési szabállyal új alapesetek jönnek, a sorrend folytatásaként. A túlélők közül más szempont szerint nem
  válogatunk.
- **Közlés:** a tényleges összetétel szeletenként, a célaránnyal együtt.

### 3.5. Generálás és szűrés (F2)

- **A 03 receptje** (`kor03/eszkozok/szint03.py`, `kor03/spec/szintetikus_csaladok.yaml`): a terv
  determinisztikusan adja az állapotot, a gold-ot és a szcenárió-dimenziókat, a generátor csak a szöveget írja. A
  generátor önálló válasza soha nem címke (D13).
- **Generátor:** Muse-Glimmer-30B, rögzített verzióval (D13).
- **Generálási próba (a teljes generálás előtt):** családonként kis minta (~24 item, állapot × nyelv cellánként 3).
  Ellenőrizzük kézzel:
  - természetes-e a magyar szöveg;
  - nincs-e benne helykitöltő vagy a címkét kimondó mondat;
  - a konstrukció valóban egyértelműen meghatározza-e az állapotot és a helyes opciót.

  Dani nézi át; a recepteket csak ezen a próbán módosítjuk, a teljes generálás után nem.
- **Modellszűrő nincs (D15).** A tervhez kötött programellenőrzés (a döntő tények jelenléte, illetve MISSING_DATA-nál
  hiánya; nyelv; címkét kimondó fordulat) dönt; ami elbukik, legfeljebb háromszor újragenerálódik. Az elvesztés és az
  újragenerálás oka állapotonként az összesítőbe kerül.
- **Audit:** emberi címkeaudit (05 4.3, Dani vakon, a Gemma második ítéletével) és családtávolság-audit (05 4.2,
  bge-m3). A kapu: a maradék címkehiba egyoldali 95%-os felső korlátja ≤ 2%.

## 4. Kiolvasás és jellemzők

- **B1:** a 05 `hf_jellemzo05` útja, a kanonikus sorrend jellemzőkkel, az 1–3. sorrend jellemzők nélkül. Ugyanaz a
  prompt és a címkeaudit, mint a 05-ben.
- **A D_meta 1–3. sorrendje:** új kiolvasás, csak a D2 (a) változatához (~6000 item × 3).
- **A friss családok:** T500 pecsét nélkül; a CAL és a TESZT pecsételve (`cache/k06/pecset/`, root, 700).

## 5. Tanítás

- **Hiperparaméterek:** a 05-ből átvéve, vagy a fejlesztési adaton (3.3) választva; a v1-ben rögzítve.
- **A szeletek szerepe (Dani, 2026-10-31):**
  - T500: tanítás és modellválasztás (belső korai megállás, a B1-LR C-je), sabloncsoportos foldokkal (D23);
  - CAL: előre rögzített szabályú küszöbválasztás és Platt-illesztés (8.4);
  - TESZT: végső értékelés, rajta semmi nem illesztődik.
- **Futások:** 3 család × 4 méret (0, 100, 200, 500) × 5 húzás (a 100-nál és a 200-nál) × 3 seed a neurális fejekre;
  a B1-LR determinisztikus. CPU-n elfér; a H-T-meta a 05 `tmeta` útján.

## 6. Kalibráció és munkapont

- A τ a CAL-szeleten, a 05 szabályával: alapesetenként egy item, CP-alsó ≥ 0,95, ≥ 200 elfogadott döntés.
- A τ csak a gyakorlati végponthoz kell (8.4). Az elsődleges végpont τ-független.

## 7. Helyesség

- **Szigorú** (elsődleges, a 05 D2-je szerint): a NONE csak a `NO_MATCH`-en helyes. **Enyhe** (leíró): a NONE
  minden nem-MATCH állapoton helyes.
- Ha egy friss családban nincs `MISSING_DATA` vagy `OUT_OF_SCOPE`, ott a kettő egybeesik.

## 8. Végpontok, statisztika, kapu

### 8.1. Végpontok

- **Elsődleges:** ΔAURC (S+N), B1-R − B1-S, a T500-on, családonként és a három család egyenlő súlyú átlagában. Az
  AURC a 05 v1a-definíciója (a DEFER a rangsor végén, hibaként; a B1 nem DEFER-el).
  - A két B1-kar javaslatai azonosak, ezért az AURC\* (a tökéletes sorrend AURC-je) is azonos, és
    ΔAURC = ΔE-AURC. Itt elég a ΔAURC.
- **Másodlagos, előre rögzítve:**
  - **K1 2. szint:** B1-R − B1-N és B1-R − B1-LR (ΔAURC, családonként és átlagban).
  - **K1 3. szint, SELECT-AURC:** az AURC minden karnál **ugyanazokon az itemeken: amelyekre a B1 SELECT-et
    javasolt** (D7). A B1-karoknál ez a B1 SELECT-javaslatainak sorrendje; a H-T-meta ugyanezeken az itemeken a saját
    döntéseivel (a DEFER a rangsor végén).
  - **K2:** H-T-meta − B1-S, ΔAURC = ΔAURC\* + ΔE-AURC felbontással (a 05 `diag05` módszere).
- **Leíró:**
  - **a NONE-javaslatokon belüli hibafelismerés:** AUROC a B1 NONE-javaslatain, minden B1-karra (D7);
  - a javaslatfajták (SELECT / NONE) aránya és helyessége, állapotonként;
  - a tanulási görbe (0, 100, 200, 500);
  - B1-LR − B1-S;
  - az enyhe helyesség;
  - az AUROC.
- **Közlés családonként, hangsúlyosan (D11):** az átlag mellett minden végpont családonként; és hogy az abszolút
  AURC-javulás mekkora része jön az egyes családokból. Az F1-ben az abszolút javulás ~89%-a a HO-routingból jött;
  ez az összesítést nem érvényteleníti, de korlátozza, mennyire nevezhető általánosnak az előny.
- **Magyar bontás kötelezően (D9):** minden végpont nyelvenként is, a magyar részre külön. Az F1-ben a HO-routing-hu
  SELECT-AURC-je a B1-R-rel romlott, a CI teljesen 0 felett (+0,0023 [0,0005; 0,0044]).

### 8.2. Statisztika

- **Bootstrap:**
  - klaszteres: a TESZT **sabloncsoportjai** (D23; a 06-ban az alapeset maga az item), családonként; az átlagnál a
    családok rögzítettek (egyenlő súly); egy ismétlésen belül minden kar ugyanazokat a csoportokat kapja;
  - 10 000 ismétlés, seed 20261029;
  - a pont és a replika is a futások (seed × húzás) mérőinek átlaga; a futások közti eltérés külön sor (D24; a v0.2
    replikánként egy seedet és egy húzást sorsolt).
- **A gyakorlati végpontnál:** a CAL is újramintázva, a τ replikánként újra (a 05 módszere).
- Kétoldali p; a három család Holm-korrigált p-je leíró.

### 8.3. Továbblépési szabály (kutatási, nem automatizálási)

- **A következő kör indokolt, ha a T500-on:**
  1. a három friss családból legalább kettőn javul az AURC (B1-R − B1-S < 0, pontbecslés);
  2. és a három család egyenlő súlyú átlagos AURC-jében a relatív csökkenés legalább 10%:
     átlag(AURC_B1-R) / átlag(AURC_B1-S) ≤ 0,90.
- **Minden intervallumot bemutatunk.** Hogy a 2. pont 95%-os intervallumának is 0 alatt kell-e lennie: 14. pont, D4.
- **Ez a szabály egy következő kör indoklása.** Precizitás- és munkaponti feltétel szándékosan nincs benne; azok egy
  automatizálási megerősítés feltételei lennének (a 05a tanulsága, Napló 2026-10-29).

### 8.4. Gyakorlati és kalibrációs leírás (nem része a szabálynak)

- **A munkapont:** a CAL-on választott τ-nál:
  - elfogadott itemek és alapesetek, hibák típusonként, precizitás;
  - a lefedettség;
  - alapesetenként: legalább egy, illetve minden itemje elfogadva; minden elfogadva és helyes (a `jev_merleg05`
    mérőszámai).

  Mindegyik alapesetszintű klaszteres intervallummal, és azzal, hogy a replikák hányadában nincs munkapont.
- **Kalibráció:** a B1-S és a B1-R valószínűségeinek Brier-pontszáma és ECE-je a TESZT-en, Platt nélkül és a CAL-on
  illesztett Platt-tal. Csak diagnosztika.

### 8.5. Erő (a v1 előtt)

- Szimuláció a fejlesztési adat (3.3) hatásméreteiből, az `mde03` módszerével. Kimenet: 1000 TESZT-alapesettel
  mekkora relatív AURC-csökkenés mutatható ki családonként és átlagban.
- Ha a 10% alulerős, a v1 előtt nagyobb TESZT-et kérünk, nem a szabályt lazítjuk.
- **Tervezési becslés (Dani, 2026-10-31):** az `mde06` itemszintű klaszterrel és replikánként egy seeddel számolt, a
  sablonos klasztert és a futásátlagot nem modellezi. A B1 helyességének ≈ 0 ICC-je nem azonos a rangsorkülönbség
  sablonon belüli függőségével.

## 9. Fázisok

| fázis | tartalom | GPU | előfeltétel |
|---|---|---|---|
| F0 | a 14. pont döntései; a terv v0.2 | — | Dani |
| F1 | fejlesztés a HO-rétegeken (3.3): B1-R, B1-LR, H-T-meta a `cel → teszt` irányban; a D_meta B1-kiolvasása (D2 a) | csak a D_meta kiolvasásához | F0 |
| F2 | a három friss család építése, címke- és családtávolság-audit | generátor (vLLM, külön) | F0; párhuzamos az F1-gyel |
| F3 | a friss családok kiolvasása: a T500 nyitva, a CAL és a TESZT pecsét alatt | HF BF16 | F2 |
| F4 | az erő-szimuláció (8.5); a v1 rögzítése | — | F1, F3 |
| F5 | a pecsét nyitása, az elemzés, az eredménylap | — | F4, Dani „mehet”-je |

## 10. JEV: külön alkalmazási eredmény (a 05-ből)

A 06-tól független; a 05 eredménylapjára kerül, a következő óvatossággal (`kor05/eredmenyek/F3/v1a_diag/jev_merleg05.json`).

- **HO-termék:** egy család (számlasor → cikk), 3854 item, 2085 alapeset.
  - **Itemszinten:** 1262 elfogadott item, 5 hiba, precizitás 99,6%.
    - Az intervallum Clopper–Pearsonnal [99,1; 99,9], alapesetszintű klaszteres bootstrappal [99,2; 99,9]. A
      függőség itt alig tágítja.
  - **Alapesetszinten:** legalább egy item elfogadva az alapesetek 43,9%-ában; minden item elfogadva és helyes
    (teljesen átvett, hibátlan munka) 19,9%-ban [18,2; 21,6].
- **A munkapont törékeny:** a τ-t az általános kalibrációs mintán választottuk. Ennek újramintázásakor a replikák
  33%-ában nincs munkapont, a teljesen átvett munka intervalluma [0; 44,7%].
- **Megfogalmazás:** „egy feladattípuson, rögzített küszöbbel, az alapesetek ötödét teljesen és hibátlanul vette át;
  a küszöb az általános kalibrációval nem stabil”. Nem: „44%-nyi munkát vesz át”.

## 11. Eszközök (terv)

- `kor06/eszkozok/b1rel06.py` — a B1-R és a B1-LR tanítása és kiértékelése. A 05 `megbizhatosag05` RelHead-jére épül.
- `kor06/eszkozok/szeletek06.py` — a friss családok szétválasztása alapesetenként, egymásba ágyazott húzásokkal.
- `kor06/eszkozok/elemzes06.py` — a 8. pont, a `diag05` felbontásával és a `jev_merleg05` munkaponti mérőszámaival.
- `kor06/eszkozok/bontas06.py` — a javulás bontása NONE- és SELECT-javaslatokra (az F1 utólagos elemzése; a v1-ben az
  `elemzes06.py` része lesz).
- `kor06/spec/csaladok06.yaml` — a friss családok terve: állapot- és nyelvi célarányok, szcenárió-dimenziók, generátor,
  szűrés (3.4–3.5).
- `kor06/eszkozok/szint06.py` — az F2 generátora: `sablon`, `terv`, `gen`, `final`, `lap`, `audit`; `nevelo` (D17, a
  „A(z)” gépies javítása a raw szövegeken, az eredeti megőrzésével); `ellenoriz` (a hibaelhárítás tervhez kötött
  szabálytábla-ellenőrzése, D15–D16).
- `kor06/eszkozok/kiolvas06.py` — az F3 B1-kiolvasása: a `hf_jellemzo05` változatlanul, csak a betöltője cserélve a
  06-os itemekre; pecsétkapuval (a CAL és a TESZT csak a `cache/k06/pecset/` alá, rajtuk `egyezes` nem fut).
- `kor06/eszkozok/pecset06.py` — a `pecset05` 06-os útvonalakkal; a manifest az itemfájlok sha256-át is rögzíti.
- `kor06/eszkozok/audit06.py` — a címkeaudit (D14) vak, offline felülete és összesítése a kapuval.
- `kor06/eszkozok/gemma06.py` — a Gemma második ítéletének összesítése (a kiolvasás a `kiolvaso03` ids-módja, négy
  sorrend, a 03 val-temperature-rel): egyezés a konstrukcióval családonként, állapotonként, nyelvenként és
  sabloncsoportonként, az auditkulcsokra a kör `gemma_itelet.json`-ja. Triage, itemet nem töröl (D15).
- `kor06/eszkozok/tavolsag06.py` — a családtávolság-audit (bge-m3, a 05 itemkészletéhez, centroid- és itemszinten, a
  referencia-családok egymás közti távolságával viszonyítva).
- `kor06/eszkozok/mde06.py` — az erőszimuláció (8.5) az F1b kimenetéből: 1000 alapeset, alapesetenként egy item;
  rétegenként és az átlagra, a „három ugyanilyen család” forgatókönyvekkel.
- `kor06/eszkozok/b1t500_06.py` — a B1 szintje a friss családok nyitott T500-án (13. pont, AURC < 0,01 → csere).
- `kor06/eszkozok/friss06.py` — az F5: a `b1rel06.f1` tanítása a friss családokon (a 06-os meta, szeletek és
  jellemzőgyökerek, a pecsét kapujával; a fold-egység a sabloncsoport, D23), az `elemzes06` értékelése (sablonos
  klaszter, 10 000 ismétlés, a 8.3 szabály a D4-gyel, Holm), a 8.4 munkapontja (`munkapont`), a D20 bontása (`bontas`)
  és a füstteszt a nyitott T500-on (`fusteszt`, mérőszám nélkül).
- `kor06/eszkozok/befagyaszt06.py` — a v1 rögzítése (`manifest`, `rogzit --jovahagyas`, `ellenoriz`), a
  `befagyaszt05` mintájára; a vázlat: `kor06/rogzites/v1/v1-vazlat.md`.
- Sorok: `k06f2_hiba.sh` (K06F2HB, a hibaelhárítás teljes építése a próba programos kapujával), `k06f3_kiolvas.sh`
  (K06F3, span-ellenőrzés, T500 nyitva, CAL/TESZT pecsét alatt), `k06f2_javitas.sh` (K06F2J, a D18–D19 javítás),
  `k06f2_gemma.sh` (K06F2G, a Gemma-ítélet és a családtávolság-audit), `k06f2_bank.sh` (K06F2K, a D21–D22 javítás,
  a bank újrakiolvasása K06F3C-ként és a Gemma a bankon).
- Újrahasznosítva: `hf_jellemzo05`, `pecset05` és `befagyaszt05` (06-os útvonalakkal), `kalib05.label_table`.

## 12. Szabályok

A 05 12. pontja változatlanul, különösen:
- a Qwen-család nem generál és nem ellenőriz, csak alany;
- a Llama szűrhet, címkét nem ad;
- a pecsét alatti kimenetekről a rögzítés előtt csak darabszám és idő kerül naplóba vagy összegzésbe.

## 13. Kockázatok

- **Alulerő:** 1000 TESZT-alapesettel a családonkénti 10% bizonytalan lehet. Ezt a 8.5 kezeli.
- **A szintetikus családok könnyűek lehetnek a B1-nek:** ha a B1 saját AURC-je közel 0, a relatív javulásnak nincs
  tere. A családtávolság-audit mellett a fejlesztési adatból becsült B1-AURC-tartományt is figyeljük. Ha egy család
  B1-AURC-je < 0,01, azt a v1 előtt cseréljük.
- **A HO-fejlesztés túlillesztése:** a jellemzőket és a hiperparamétereket a HO-rétegeken választjuk. A friss
  családokon ez a választás teszt; a rögzítés ezt védi.

## 14. Döntések (Dani)

| # | kérdés | javaslat |
|---|---|---|
| D1 | a három friss család forrása | a 05 4.2 szintetikus jelöltjeiből: pénzügyi párosítás, műszaki hibaelhárítás, szabálymegfelelés. Valós tenantadat nem lehet, mert a karok célterületen tanítanak (2026-10-28-i elv). |
| D2 | a B1-R tanítása | (a) előtanítás a D_meta-n a B1 helyességére + célterületi finomhangolás (a T-meta mintájára; kell hozzá a D_meta B1-kiolvasása), vagy (b) csak célterületi tanítás. Javaslat: (a). A 100 alapesetről indított neurális fej (b)-vel könnyen túlillesztődik, és az (a) adja a tanulási görbe 0 pontját. |
| D3 | a B1-LR jellemzői | Dani hármasa + a B1 saját pontszáma, hogy a B1-LR a referencia kiterjesztése legyen. Nélküle a B1-LR akár a saját pontszám hiánya miatt is veszíthet. **A pilot után (Dani, 2026-10-29): + NONE-jelző ötödikként.** |
| D4 | a 8.3 2. pontja | a pontbecslés ≥ 10% és a 95%-os intervallum alsó határa > 0, a „kimutathatóan” miatt. A családonkénti 1. pont pontbecslés marad. |
| D5 | a 05 HO-rétegei fejlesztési adatként (3.3) | igen. Gyors hatásméret-becslés GPU nélkül, mielőtt az F2-be munka megy. Az eredménye csak tervezést szolgál. |
| D6 | a helyesség | szigorú elsődleges, enyhe leíró (a 05 D2-je). |
| D7 | (a pilot után) SELECT-AURC | **Elfogadva (Dani, 2026-10-29).** Előre rögzített másodlagos végpont, minden karnál ugyanazokon, a B1 által SELECT-nek javasolt itemeken; a NONE-javaslatokon belüli hibafelismerés külön leíró sor (8.1). |
| D8 | B1-N referencia | **Elfogadva (Dani, 2026-10-29).** „B1, NONE-javaslatok utoljára”, előre rögzített, tanítás nélküli referencia (2.4). |
| D9 | összetétel | **Elfogadva (Dani, 2026-10-29).** A négy állapot és a nyelv aránya, valamint a rétegzett szétválasztás a generálás előtt rögzítve; a generálás után a modellek eredményei alapján nincs válogatás (3.4); a magyar bontás kötelező (8.1). |
| D10 | a rejtett állapotok szerepe | **Elfogadva (Dani, 2026-10-29).** Ebben a körben a teljes módszerek különbségéről beszélünk (2.3). |
| D11 | a K1 szintjei és a közlés | **Elfogadva (Dani, 2026-10-29).** A három szint (1.), családonkénti hangsúlyos közlés az abszolút javulás megoszlásával (8.1). |
| D9 számai | az állapot- és a nyelvi arány | **Elfogadva (Dani, 2026-10-29).** Mindhárom családban és a T500-on, a CAL-on és a TESZT-en is MATCH 60% / NO_MATCH 20% / MISSING_DATA 10% / OUT_OF_SCOPE 10%, állapotonként fele magyar, fele angol (`kor06/spec/csaladok06.yaml`). **Kutatási összetétel, nem a DocAI-forgalom becslése:** az összesített eredmény erre az összetételre vonatkozik. Ugyanannak az esetnek a magyar és az angol változata nem kerülhet külön szeletbe; ha ilyen pár készül, közös csoportazonosítót kap (a terv nem készít ilyet: minden alapeset egy nyelven, önálló tervből). |
| D12 | változatok | **Elfogadva (Dani, 2026-10-29).** Alapesetenként egy item. Megfogalmazás: **ebben a körben nem vizsgáljuk a parafrázisokkal és változatokkal szembeni stabilitást.** Az egy item nem jelent függetlenséget: az azonos forrásból vagy szorosan összetartozó sablonból származó esetek csoportosan kerülnek szeletbe (3.4, sabloncsoport). |
| D13 | generátor | **Elfogadva (Dani, 2026-10-29).** Muse-Glimmer-30B, rögzített verzióval (`meta-models/Muse-Glimmer-30B@a4e59da52a7bc87ae7251dd5545c0dd437c44b68`; a modellkártya Apache-2.0). Előbb családonként kis generálási próba (3.5). A helyes címkét a konstrukció adja; a generátor önálló válasza soha nem válik címkévé. A Gemma független második bíráló marad. **Tartalék, ha a Muse a próbán nem megfelelő (Dani, 2026-10-29):** (1) GPT-OSS-120B (Apache-2.0, natív MXFP4, ~80 GB, Sparkon validált; a szabályokat követő, összetettebb példák első jelöltje); (2) GLM-4.7-Flash (30B, ~3B aktív, BF16 ~60 GB + futtatás) csak az Apache-only szabály kifejezett módosításával, mert MIT licencű. Egyik sincs még a spark-deven. |
| D14 | címkeaudit | **Elfogadva (Dani, 2026-10-29).** 300 item, családonként 100, azon belül állapot × nyelv szerint rétegezve; Dani vakon, a Gemma második ítéletével; a kapu változatlan (a maradék hiba felső korlátja ≤ 2%, 300 példán legfeljebb 1 hiba). |
| D15 | modellszűrő (3.5) | **Elfogadva (Dani, 2026-10-29): nincs modellszűrő**, és nincs a megoldó modell válaszán alapuló szűrés. A rövidség vagy a B1 számára könnyű volt sem kizárási ok. A minőséget a tervhez kötött programellenőrzés és a független emberi audit adja. A Gemma vitás példát jelezhet felülvizsgálatra, de az eltérő véleménye önmagában nem töröl itemet. Az elutasítások és a pótlások oka állapotonként megmarad. |
| D16 | a hibaelhárítás feladat-meghatározása | **Elfogadva (Dani, 2026-10-29).** A v3 próbán a helyes válasz nem következett egyértelműen a látható adatokból (például az `en:MISSING_DATA:0000`-n az egyik opció leírása a tünetre további mérés nélkül is ésszerű; az `en:MATCH:0000`-n a 198 V-os érzékelőérték nem bizonyítja az érzékelő hibáját). Ezért: előre, programmal ellenőrzött diagnosztikai szabálytábla, amelyet a megoldó is megkap (minden opció a saját szabályával); a kérdés: „A diagnosztikai szabályok szerint melyik hibát igazolják a megadott adatok?”; a MISSING_DATA-ból pontosan a szabályhoz szükséges mérés hiányzik. A család csak beérkező felhasználói bejelentéseket tartalmaz. Új próba, a teljes építés Dani próbalap-döntése után. A GPT-OSS-120B-re emiatt nem váltunk. **A teljes építés jóváhagyva (Dani, 2026-10-30 reggel: „jóváhagyom, haladjunk tovább”)**, az 5. próba programos kapujával (legalább 22/24 item, és a `szint06.py ellenoriz` hibátlan). A jóváhagyás az 5. próba lapjának elkészülte előtt született; ha Dani a lap alapján elveti, a teljes építés eldobandó. |
| D17 | a bank- és a szabálycsalád „A(z)” hibája | **Elfogadva (Dani, 2026-10-30): gépies javítás.** „A(z) X” helyére „A X” vagy „Az X” a következő szó kezdőhangja szerint (`szint06.py nevelo`); a tények, az állapotok és a válogatás nem változnak; az eredeti szöveg a raw `szoveg_eredeti` mezőjében marad. Újragenerálás nincs. |
| D18 | a szabálycsalád angol költségnemei (az 1. audit, a077 és a124) | **Elfogadva (Dani, 2026-10-30): gépies javítás a szabályszövegben.** „Domestic business travel and accommodation” → „Business travel and accommodation”; „Client entertainment and gifts” → „Business entertainment and gifts”. A szövegek, a tények és a válogatás nem változnak; a prompt az angol itemek 85%-ában változik, ezért a család újrakiolvasása kell. Az a szabály- vagy opciószöveg, amely a konstrukcióban meg nem alapozott feltételt állít, címkehiba. |
| D19 | az 1. audit kétértelmű tételei (Dani, 2026-10-30: „lehet ezekkel is érdemes kezdeni valamit”) | **Bank (a055, a071, a098, a108, a120, a256):** a banki szövegben a cégnév szerepe nem volt jelölve (2000-ből 1506-ban szerepel a saját cég neve). Javítás: minden banki tétel elején rögzített sor, „Számlatulajdonos: <saját cég>” / „Account holder: …” (`to_item`); a szöveg és a válogatás nem változik. **Szabálycsalád (a093, a106, a135, a178):** a „beszerzési igény egy új szerverre” OUT_OF_SCOPE-jelleg átfedett a munkaeszköz-beszerzés pontjával (M is védhető). Javítás: a jelleg helyett „lakcímváltozás bejelentése a HR-nek” / „notification of a change of home address to HR”, a 65 érintett terv szövege újragenerálva. Dani javaslata (a feladatleírásban kizárni az előzetes beszerzést) helyett ez azért, mert a B1 generikus kerete feladatleírást nem kap, és a kérdés pontosítása az átfedést a munkaeszköz-ponttal nem szüntetné meg. **Új audit:** a bank- és a szabálycsaládra friss 100-100 item (az 1. kör itemei nélkül); a hibaelhárítás 1. körös 100 iteme (hibátlan) beszámít, a kapu így ismét 300 itemre szól. |

| D20 | a NONE-konvenció (az éjszakai T500-lelet: szigorú helyességnél az itemek ~20%-a a B1-nek biztos hiba) | **Elfogadva (Dani, 2026-10-31).** A B1-R − B1-N (a K1 2. szintje) és a nyereség NONE- és SELECT-javaslatokra bontása (`bontas06`) az eredménylapon kiemelt, kötelező sor, családonként. |
| D21 | a bank MISSING_DATA (a Gemma-ítélet: két azonos összegű számlából az esedékességhez közelebbit választja) | **Dani, 2026-10-31: az esedékesség szerinti választás elfogadható döntés, ezért a címke vitatható.** Javítás a sablonban: a közös összegű számlapár azonos esedékességet kap (`bank_sablon`); a kelte, a tények és a véletlensorozat változatlan. Az opciószöveg a banki tervek ~81%-ában változik (egy esedékesség), a szöveg nem. A szabálycsalád MISSING_DATA-ja nem érintett: ott az összeg hiányzik, a kategória mindkét küszöbváltozata az opciók közt van, a Gemma árat tippel. |
| D22 | a 2. audit címkehibája (b136: „Számla kiegyenlítés 2026/1845”, holott a terv szerint számlaszám nincs) | **Dani, 2026-10-31: a konstrukció hibás.** A tényellenőrzés nem nézte a kitalált hivatkozást. Javítás: a banki szövegben (az OUT_OF_SCOPE kivételével) a tranzakció dátumán és a terv számlaszámán kívül nem lehet más dátum, hónap- vagy számlahivatkozás (`bank_idegen`; a bankszámlaszám és a ≥ 8 jegyű tranzakcióazonosító megengedett); a prompt is kimondja. Az elbukó 20 raw rekord (ebből 16 item: 12 MATCH, 4 NO_MATCH) újragenerálódik. |
| D23 | (a v1 előtt) a klaszter- és a fold-egység | **Elfogadva (Dani, 2026-10-31): a sabloncsoport.** A 06-ban az alapeset maga az item (D12), ezért a 8.2 alapesetenkénti bootstrapja itemszintű lett volna. A tanítás és a validáció szétválasztása (a finomhangolás foldjai, a belső korai megállás, a B1-LR CV-je) és a bootstrap sabloncsoportonként (TESZT 60, T500 30, CAL 30 sablon családonként); egy ismétlésen belül minden kar ugyanazokat a csoportokat kapja. A T100 / T200 mérete itemszám, a sablonszám közölve; a ≥ 200 elfogadott τ-feltétel mennyiségi feltétel (nem 200 független megfigyelés), a CAL újramintázása sablonos. A B1 helyességének sablonon belüli ICC-je a T500-on ≈ 0 (−0,04…−0,02), de ez nem azonos a rangsorkülönbség függőségével: az erőszámítás tervezési becslés. |
| D24 | (a v1 előtt) a seedek összevonása | **Elfogadva (Dani, 2026-10-31).** Elsődleges a futások (seed × húzás) AURC-jének átlaga; a bootstrap replikánként ugyanazokon a csoportokon a futások átlagát számolja; a futások közti eltérés (futásonkénti ΔAURC, min–max, szórás) külön sor. A v1-ben a 8.4 munkapontja és a D20 bontása is így számol. |
---

## Napló

- **2026-10-29 — v0.1 vázlat.**
  - Dani: a B1 döntései maradnak, a megbízhatóságot tanítjuk; a fő kérdés a fenti; három kar + egy kis
    regularizált referencia.
  - A Platt diagnosztika, nem kar. A minta 100 ⊂ 200 ⊂ 500 tanító alapeset, külön CAL és TESZT.
  - A T500 elsődleges. A továbblépés: legalább 2/3 család és ≥ 10% relatív AURC-csökkenés.
  - A JEV külön alkalmazási eredmény, óvatos megfogalmazással.
  - **Adatfelmérés:** a 05 pool 218 családjából 216 szerepelt 05-szeletben, kettő a 03 külső eval-készlete, ezért
    új, kis adatépítés kell (3.1).
- **2026-10-29 délután — Dani: „mehet” a D1–D6-ra; az F1 indul.**
  - **D_meta B1-kiolvasás:** a 05 `hf_jellemzo05` változatlanul, D_meta:b1 (`kor06/eszkozok/k06f1_b1meta.sh`); 13:56-kor
    indult.
  - **Kód:**
    - `kor06/eszkozok/b1rel06.py`: a B1-R előtanítása és az F1-futás a HO-rétegeken;
    - `kor06/eszkozok/elemzes06.py`: az F1 elemzése, a 8.3 szabály próbájával.

    A 05 moduljait csak importálják, nem módosítják: a 05 v1a-manifestje változatlan marad.
  - **Memória:** a HF-bázis betöltése alatt a spark-deven 16 GB szabad. A jellemzőket betöltő CPU-futások a kiolvasás
    után indulnak.
- **2026-10-29 16:06 — a D_meta:b1 kész; az előtanítás és az F1.**
  - **Kiolvasás:** 18 000 sor (6000 item × 3 sorrend), 2,47 item/s, 16:06-kor kész; a memória utána 115 GB szabad.
  - **Próba (D_cal_prob, `cache/k06/proba`):** 2904 item, 30 s, hibátlan.
  - **Előtanítás (D_meta, `cache/k06/b1rel`):** 5796 item (a kétértelműek nélkül), fit 4618 / val 1178, 55 s.
    - A választott lr 1e-4 (az átlagos val BCE 0,408, illetve 0,415 a 3e-4-nél); 4–6 epoch.
    - A B1 helyessége a D_meta-n 71,5%.
    - Val AUROC: a B1 saját pontszáma 0,796; a B1-R seedenként 0,877 / 0,873 / 0,868. Ez a D_meta saját eloszlása,
      nem célterületi eredmény.
  - **F1:** `kor06/eszkozok/k06f1_futas.sh` (a három HO-réteg CPU-n, majd `elemzes06.py`, 2000 ismétlés), 16:09:58-kor
    indult.
- **2026-10-29 16:24 — az F1 eredménye (fejlesztési futás; a HO-rétegek a 05a-ban nyitva voltak, döntést nem alapoz).**
  - **Futás:** a három réteg 16:09:58 és 16:23 között, az elemzés 16:24-ig (`kor06/eredmenyek/F1/f1_elemzes.{md,json}`).
  - **Ellenőrzés a 05-tel:** a B1-S és a H AURC-ja mind a négy rétegen bájtra egyezik a v1a-val. A teljes mintás
    H-T-meta 0,5–1%-on belül van (0,0508 / 0,0515; 0,0797 / 0,0801; 0,0975 / 0,0975; 0,0322 / 0,0327): a cross-fit
    ugyanaz az eljárás, a különbség a 06 saját mintázásából jön.
  - **Szigorú helyesség, teljes tanítóminta** (444 / 491 / 500 alapeset), B1-R − B1-S:
    - HO-routing −0,1422 [−0,1520; −0,1330];
    - HO-termék −0,0042 [−0,0070; −0,0011];
    - HO-új −0,0140 [−0,0172; 0,0025].

    A 8.3 szabály próbája: 3/3 réteg javul (pontbecslés), átlag-arány 0,565 [0,449; 0,800] → teljesülne. Enyhe
    helyességgel (a szigorúra tanított pontszámokkal): 1/3, arány 1,080 → nem.
  - **Tanítóméret (HO-termék):**
    - 100: +0,0027 [−0,0022; 0,0101];
    - 200: −0,0023 [−0,0065; 0,0014];
    - teljes: −0,0042 (a 100 itt nem elég).

    HO-új: −0,0040 / −0,0095 / −0,0140, mindegyik CI-je átlépi a 0-t.
  - **Egyéb összevetések, teljes minta:**
    - **B1-R − B1-R0** (a célterületi finomhangolás): mindhárom szűrőrétegen negatív, a CI 0 alatt. A B1-R0 a
      HO-terméken és a HO-újon rosszabb a B1-S-nél.
    - **B1-R − B1-LR:** −0,0079 a HO-routingon, −0,0090 a HO-terméken (a CI 0 alatt), a HO-újon nem különbözik.
    - **H-T-meta − B1-R:** a HO-terméken +0,0152 [0,0098; 0,0221]; a H tartalmi javaslatai rontanak (ΔAURC* +0,0121), a
      05 diag-képével egyezően.
  - **Bontás** (`kor06/eszkozok/bontas06.py` → `F1/bontas06.{md,json}`; utólagos, leíró, a 05 kétszintű húzásával):
    - **A szigorú javulás nagy része egyetlen mintázat.** A B1 NONE-javaslatai a HO-routingon és a HO-újon szigorúan
      szinte mind hibásak, mert részleges állapotú alapeseteken születnek: szigorúan 12,9% és 2,5% helyes, enyhén 92,4%
      és 88,2%. A B1 saját pontszáma ezeket elöl tartja (NONE-on belüli AUROC 0,268 és 0,017).
    - **A B1-R0 már célterületi tanítás nélkül hátrateszi őket** (0,979 és 0,991).
    - **Utólagos viszonyítás, „B1-S·NONE-utolsó”** (a B1 sorrendje, a NONE-javaslatok a SELECT-ek mögött): AURC
      0,1028 / 0,0476 / 0,0930. B1-R − ehhez:
      - HO-routing −0,0221 [−0,0271; −0,0175];
      - HO-termék −0,0120 [−0,0153; −0,0086];
      - HO-új −0,0010 [−0,0057; 0,0048].
    - **Csak a SELECT-javaslatokon**, B1-R − B1-S:
      - HO-routing −0,0185 (−37%);
      - HO-termék −0,0015 [−0,0038; 0,0010] (−5%);
      - HO-új −0,0010 (−1%);
      - HO-routing-hu +0,0023 [0,0005; 0,0044].
    - **Olvasat:**
      - a HO-új javulása gyakorlatilag teljes egészében a NONE-konvenció;
      - a HO-routingon a NONE-konvención túl a SELECT-sorrend is valóban javul;
      - a HO-terméken a teljes javulás kicsi (−10,6%), és a SELECT-részen nem szignifikáns.
  - **Tervezési kérdés Daninak** (az F2 előtt): a szigorú elsődleges helyesség (D6) mellett a fő kontraszt nagyrészt
    azt méri, hogy a fej megtanulja-e a részleges állapotokon adott NONE szigorú hibáját. Javaslatok:
    - (a) a SELECT-javaslatokon számolt AURC előre rögzített másodlagos végpontként;
    - (b) a B1-LR kapjon NONE-jelzőt ötödik jellemzőként, hogy a kis referencia is megtanulhassa ezt a mintázatot, és
      a B1-R − B1-LR ezen túli jelet mérjen;
    - (c) a friss családok állapotösszetétele (a részleges állapotok aránya) a generálás előtt rögzítve és
      dokumentálva.
- **2026-10-29 este — Dani: az (a)–(c) elfogadva, pontosításokkal; v0.2.**
  - **Elfogadva:** D7 SELECT-AURC, D8 B1-N, D9 összetétel és magyar bontás, D10 a rejtett állapotok szerepe, D11 a K1
    szintjei; a D3 kiegészül a NONE-jelzővel.
  - **Dani olvasata:**
    - A pilot fő tanulsága: a megbízhatósági fej megtanulhatja a feladat elfogadási szabályait, de az általános
      hibafelismerési előnye még nem egyértelmű.
    - Üzletileg számít, hogy a nem végrehajtható „egyik sem” választ a rendszer felismeri; a friss mérésből derüljön
      ki, mennyivel tud többet egy tanult fej egy egyszerű szabálynál.
    - A HO-terméken a mechanikus NONE-hátrasorolás ront, a tanult fej javít, tehát nem csak egy „NONE = rossz”
      szabály.
    - A HO-routingon a NONE-on belüli AUROC 0,982, de ezt az előtanított fej is majdnem így tudja (0,979).
  - **Pontosítás az előző bejegyzéshez:** a szigorúan hibás NONE-javaslatok állapota nem „részleges”:
    - HO-routing: 1801 NONE-javaslatból 1432 OUT_OF_SCOPE, 232 NO_MATCH, 137 MATCH; a réteg 29%-a OUT_OF_SCOPE;
    - HO-új: 119-ből 102 MISSING_DATA, 3 NO_MATCH, 14 MATCH;
    - HO-routing-hu: 303-ból 55 OUT_OF_SCOPE, 232 NO_MATCH (a réteg 6%-a OUT_OF_SCOPE, ezért ott a B1-N kevésbé hat);
    - HO-termék: 429-ből 48 OUT_OF_SCOPE, 332 NO_MATCH.

    A B1-nek nincs DEFER-je, ezért ezeken a szigorú helyesség mellett egyik javaslata sem helyes: a fej itt az állapotot
    ismeri fel.
  - **A HO-routing részesedése:** az abszolút AURC-javulás (0,1422 + 0,0042 + 0,0140) 88,7%-a a HO-routingé.
- **2026-10-29 18:00 — Dani: D9 számai, D12, D13, D14 elfogadva** (14. pont).
  - Kiegészítések:
    - a 60/20/10/10 kutatási összetétel, nem a valós forgalom becslése;
    - a magyar és az angol változat nem kerülhet külön szeletbe;
    - a parafrázis-stabilitást ebben a körben nem vizsgáljuk;
    - a sablon szerinti csoportos szétválasztás marad;
    - a generátor rögzített verzióval fut;
    - előbb családonként kis próba;
    - a generátor válasza nem címke;
    - az audit családonként 100.
  - **Rögzített verziók:**
    - Muse-Glimmer-30B `a4e59da5…`;
    - szűrő: Llama-3.3-70B-Instruct-FP8 `fde04ee7…`;
    - második bíráló: Gemma-4-26B-A4B-it `4d7ae498…`.
- **2026-10-29 17:57 — F1b: a v0.2 kódja a HO-rétegeken** (`kor06/eredmenyek/F1b/f1_elemzes.{md,json}`; fejlesztési
  futás).
  - **Változatlan:** a B1-S, a B1-R, a B1-R0, a H és a H-T-meta pontosan az F1 értékeit adja (az F1 reprodukálódik).
  - **Új: a B1-N, a SELECT-AURC és a NONE-on belüli AUROC.**
  - **Változott: a B1-LR a NONE-jelzővel.** A B1-R − B1-LR (teljes minta):
    - HO-routing: −0,0076 [−0,0109; −0,0043]; SELECT-en −0,0068 [−0,0110; −0,0028];
    - HO-termék: −0,0010 [−0,0035; 0,0018] (az F1-ben a négy jellemzővel −0,0090);
    - HO-új: −0,0017 [−0,0071; 0,0036];
    - HO-routing-hu: +0,0008 [−0,0044; 0,0061]; SELECT-en +0,0023 [0,0005; 0,0046].
  - **Olvasat:** a NONE-jelzővel a kis logisztikus regresszió a HO-terméken és a HO-újon a B1-R szintjén van; a
    nagyobb módszer előnye (K1 2. szint) csak a HO-routingon mutatható ki. A „teljes módszerek különbsége”
    megfogalmazás (D10) érvényes.
- **2026-10-29 18:05 — F2: a generálási próba indul** (`kor06/eszkozok/szint06.py`, `kor06/eszkozok/k06f2_proba.sh`).
  - **Recept:**
    - a bank- és a szabálycsalád sablonja programból készül (cégenként 14 nyitott számla, illetve szabályzatonként 3
      költségnem × 2 értéksáv);
    - a hibaelhárítás okkatalógusa a Muse-tól jön: 4 tünetcsoport × 2 ok, okonként egy megkülönböztető mérés.
  - **A döntő tények programellenőrzése** (összeg, partner, számlaszám, mért értékek; MISSING_DATA-nál a hiányzó adat
    hiánya; címkét kimondó fordulat, okmegnevezés, szabálypont-hivatkozás). Ami elbukik, legfeljebb háromszor
    újragenerálódik, aztán elvész; az elvesztés oka tételesen a naplóba kerül.
  - **Sablonok:** nyelvenként 60 (15 T500, 15 CAL, 30 TESZT). A próba két-két saját sablonon fut, ezek a teljes
    építésben nem szerepelnek.
  - **Tartalék generátor (Dani, 2026-10-29), ha a Muse a próbán nem megfelelő:**
    - GPT-OSS-120B (Apache-2.0);
    - GLM-4.7-Flash, de csak a licencszabály módosításával (MIT).
  - **A Llama-szűrő a próbán még nem fut;** a teljes generálás előtt kötöm be (3.5).
- **2026-10-29 18:26 — az 1. generálási próba (v1): saját átnézés után nem ment Danihoz; javítva.**
  - **Futás:** a Muse 646 s alatt állt fel. 71/72 item; a hibaelhárításban egy MISSING_DATA esett ki, mert a szövegbe
    bekerült a hiányzónak szánt érték.
  - **Hibák:**
    - **Nyelv.** Az angol itemek közül magyar szöveget kapott:
      - a bankban 1/12;
      - a hibaelhárításban 8/12, és mind a 12 angol hibaelhárítási item opciói is magyarok voltak (az angol sablon
        katalógusa magyarul jött vissza);
      - a szabálycsaládban 3/12.

      A Muse a magyar utasítástörzset követte, nem az angol nyelvsort.
    - **Bank, dátum:** a tranzakció dátumát a generátor választotta, sokszor a számlák kelte elé (2025-12, 2026-02).
      Ez dátum alapján minden opciót kizárna, így az állapot nem egyértelmű.
    - **Bank, irány:** az OUT_OF_SCOPE-nál véletlen irány (például „bejövő munkabér”).
    - **Bank, forma:** önmagyarázó mondat a formáról („…referenced without separators as…”).
    - **Hibaelhárítás, viszonyítás:** a mért érték mellett nem volt viszonyítási érték, így nem dönthető el, hogy egy
      érték eltérő-e. A konstrukció nem határozta meg egyértelműen a helyes okot.
    - **Hibaelhárítás, OUT_OF_SCOPE:** a szöveg szó szerint átvette, hogy „a berendezés hibátlanul működik” (az
      utasításból).
    - **Szabálycsalád:** a kérelem szó szerint ismételte a költségnem leírását, így a döntés szóegyezés lett.
  - **Javítások:**
    - az utasítás teljesen a cél nyelvén, nyelvellenőrzéssel a szövegen és a katalóguson;
    - a bankban rögzített tranzakciódátum a legkésőbbi érintett számlakelte után, programmal ellenőrizve; az
      OUT_OF_SCOPE kimenő tétel;
    - a hibaelhárításban a mért érték mellett a gyári érték is, programmal ellenőrizve;
    - a szabálycsaládban a költségnem helyett konkrét helyzet (például „vonatjegy és egy éjszakai szállás egy
      debreceni ügyféllátogatáshoz”), a leírás szó szerinti átvétele tiltva;
    - a formát magyarázó és az állapotot kimondó utasításrészek kivéve.
  - **Tárolás:** a v1 kimenete a spark-deven `kor06/adat/f2_proba_v1`.
  - **A 2. próba 18:31-kor indult.**
- **2026-10-29 18:55 — a 2. próba (v2): a bank- és a szabálycsalád rendben, a hibaelhárítás az ellenőrzőn bukott.**
  - **Hozam:** a bank 23/24 (1 OUT_OF_SCOPE PII/URL miatt esett ki), a szabálycsalád 24/24, a hibaelhárítás 17/24.
    Angol itemben már nincs magyar opció.
  - **A hibaelhárítás kiesésének oka a saját ellenőrzőm volt:**
    - a nyelvszűrő az ékezetarányból dolgozott, és magyarnak vette az angol szöveget, ha az aláírásban magyar név állt
      (a +36-os telefonszabály miatt a Muse ilyeneket ír): 18 elbukott próbálkozás;
    - a MISSING_DATA tiltott mért értéke („22”) egy dátumban („2026.10.22.”) is találatot adott.
  - **Javítás:**
    - a szöveg nyelve a magyar (funkciószó vagy ékezetes szó) és az angol funkciószavak arányából, a katalógusé
      továbbra is az ékezetarányból. A két próba itemjein bemérve: a v1 ténylegesen magyar nyelvű angol itemjeit
      elutasítja, a v2 itemjei közül egyet sem; a „be” és a „has” kikerült az angol listáról, mert magyar szó is.
    - a MISSING_DATA-nál az érték és a mértékegység együtt tiltott; a jelenlétnél az érték önálló számként
      (tizedesvessző vagy -pont).
  - **Tárolás:** a v2 a spark-deven `kor06/adat/f2_proba_v2`. **A 3. próba 18:57-kor indult.**
- **2026-10-29 19:21 — a 3. próba (v3): 72/72.**
  - **Hozam:** bank 24/24 (újragenerálás: 2 JSON, 1 PII/URL, 1 eltérő dátum); hibaelhárítás 24/24 (2 rossz nyelv);
    szabálycsalád 24/24.
  - **Saját átnézés:** az angol szövegek és a katalógus angol; a mért és a gyári érték együtt szerepel; a
    konstrukció az átnézett itemeken egyértelmű. Kisebb észrevételek: egy OUT_OF_SCOPE üzenet fordított irányú (a
    technikus ír a felhasználónak); néhány okkatalógus technikailag kétes, de belsőleg következetes.
  - **Átadás:** a próbalap (`kor06/adat/f2_proba_v3/proba/proba_lap.md`) Danihoz került. A v3 a spark-deven
    `kor06/adat/f2_proba_v3`.
  - **Előkészítve az éjszakára** (`kor06/eszkozok/k06f2_ejszaka.sh`; szárazon tesztelve kamu szövegekkel):
    - teljes tervezés: családonként 120 sablon, 2604 terv;
    - a kvóta szerinti összeállítás; legfeljebb két pótlókör;
    - auditminta.

    Dani jóváhagyására vár (a Muse megfelelősége, D15).
- **2026-10-29 20:18 — Dani: a Muse marad (D13), modellszűrő nincs (D15), a hibaelhárítás szabálytáblás (D16);
  éjszakai sor.**
  - **Dani észrevételei a v3 próbalapon:**
    - a magyar szöveg többnyire elfogadható;
    - javítandó fordulat a `szabaly.koltsegelszamolas:proba:hu:OUT_OF_SCOPE:0001`-ben: „Somlyó Ipari Kft. vagyok”
      helyett „A Somlyó Ipari Kft.-től írok” (a promptba szabályként bekerült);
    - a hibaelhárításban a helyes válasz nem következett egyértelműen a látható adatokból (D16).

    Ez a próbalap áttekintésén alapuló döntés, nem a 300 itemes vak audit helyettesítése.
  - **A szabálytáblás recept:**
    - a katalógus okonként relációt és számszerű küszöböt ad; a program ellenőrzi, hogy a hibás érték teljesíti a
      relációt, a normál nem;
    - az opció szövege: „ok — igazolt, ha a tünet: …, és a(z) M kisebb/nagyobb, mint T”;
    - a mért értékek gyári érték nélkül szerepelnek;
    - MISSING_DATA-nál 1–2, a MATCH-nél és a NO_MATCH-nél 0–1 irreleváns mérés más tünetcsoportból, hogy a mérések
      száma ne árulja el az állapotot;
    - helyben, kézzel írt katalóguson kipróbálva.
  - **Éjszakai sor** (`kor06/eszkozok/k06f2_ejszaka.sh`, 20:18:46-kor indult, a laptoptól függetlenül):
    1. a hibaelhárítás szabálytáblás próbája (24 item; a lapja reggel Danihoz kerül; a hibája nem állítja le a sort);
    2. a bank- és a szabálycsalád teljes építése (családonként 2604 terv, kvóta szerinti összeállítás, legfeljebb két
       pótlókör);
    3. az auditminta a két családra.

    Várható vége 01:00 és 04:00 között, a Muse 64 párhuzamos kérésnél mért áteresztésétől függően.
- **2026-10-29 20:25 — hajnali sor** (`kor06/eszkozok/k06f2_hajnal.sh`; Dani: „04:00 és 08:00 közt … kezdd el építeni
  a legvalószínűbben jó családot, ne álljon üresen a GPU”).
  - **Mit csinál:**
    - megvárja a K06F2 végét;
    - utána a hibaelhárítás teljes építése a szabálytáblás recepttel (120 sablon, 2604 terv, kvóta szerinti
      összeállítás, legfeljebb két pótlókör, az auditminta frissítése).
  - **Fenntartással:** Dani próbalap-döntése előtt fut. Ha a próbát elveti, a teljes építést eldobjuk; addig a
    kimenetbe senki nem néz bele, a naplóba csak darabszámok kerülnek.
  - **Programos kapu:**
    - a K06F2 hiba nélkül végzett;
    - a szabálytáblás próba legalább 22/24 itemet adott.

    Ha a kapu nem teljesül, a sor nem indul, és az okot a FAILED-K06F2H-ba írja.
- **2026-10-30 reggel — az éjszakai és a hajnali sor eredménye; két hiba a magyar szövegben.**
  - **Futás:**
    - a K06F2 22:07-kor, a K06F2H 23:11-kor végzett (53 perc). A 01:00 és 04:00 közé tett becslésem túl pesszimista
      volt, a GPU 23:11 óta üresen állt.
    - Memóriariasztás nem volt.
  - **Összetétel:** mindhárom családban 2000 item; T500 500 / CAL 500 / TESZT 1000; fele magyar, fele angol;
    MATCH 1200 / NO_MATCH 400 / MISSING_DATA 200 / OUT_OF_SCOPE 200. Hiányzó cella nincs, pótlókör nem kellett;
    120 sablon, egy sablon csak egy szeletben.
  - **Elvesztés** (végleg elvesztett terv, állapotonként az összesítőben):
    - bank: 44 / 2604; főleg Muse JSON-hiba (MATCH 26, NO_MATCH 6, MISSING_DATA 6), plusz 3 MISSING_DATA, ahol a
      hiányzónak szánt partner bekerült a szövegbe;
    - szabálycsalád: 11 / 2604, mind a nyelvszűrő miatt.

      A nyelvszűrő hibái a tömör angol üzenetekre koncentrálódnak: 95 elbukott próbálkozás 440 tervre, végleg 10 terv
      veszett el. Egy rövid angol szövegben a magyar nevű aláírás már 8% fölé viszi a magyarszó-arányt. A kvóta pontos
      marad, de a túlélő tömör angol szövegek ritkábban tartalmaznak magyar nevet. Kis stílushatás; közlendő.
  - **Hibaelhárítás:**
    - a szabálytáblás próba 24/24 lett. A program a próba mind a 24 itemén alkalmazta a szabályokat a tényekre, és
      pontosan a konstrukciót kapta vissza: MATCH-nél egyedül a gold igazolódik, a többi állapotnál egy opció sem.
    - A fenntartásos teljes építés 2000 itemet adott.
  - **Hiba 1, a saját promptomból:** a „cég nem személy” szabály példája („A(z) X Kft.-től írok”) szó szerint a
    szövegekbe került. Érintett magyar item:
    - bank 193 / 1000;
    - szabálycsalád 295 / 1000;
    - hibaelhárítás (fenntartásos építés) 927 / 1000;
    - próba 12 / 24.
  - **Hiba 2:** a hibaelhárítási katalógusok közül 29 / 120 (a próbán 1 / 4) programazonosító-szerű, aláhúzásos nevet
    tartalmazott (például „dob_tengely_azonos_azonos_zaj”).
  - **Javítás:**
    - a névelő a név kezdőhangjából, programmal (`nevelo`);
    - „a(z)” a szövegben elutasító ok;
    - a katalógusban aláhúzásos vagy programazonosító-szerű név elutasító ok. A meglévő 120 sablonból 33-at
      utasítana el.
  - **Archiválva** (helyben és a spark-deven is):
    - a hibaelhárítás v4-es próbája: `kor06/adat/f2_proba_v4`;
    - a fenntartásos teljes építés és a háromcsaládos auditminta: `kor06/adat/f2_hiba_spekulativ_v1`.
  - **Az 5. hibaelhárítási próba 07:08-kor indult.**
  - **A bank- és a szabálycsaládnál nyitott** (Dani dönt):
    - (a) gépies névelő-javítás: „A(z) X” → „A X” / „Az X” a következő szó kezdőhangja szerint; szárazon 193 + 295
      item, utána 0 maradék;
    - (b) az érintett magyar itemek újragenerálása.

- **2026-10-30 délelőtt — D17, a hibaelhárítás teljes építése és az F3 sora.**
  - **Dani döntései:** a bank- és a szabálycsaládnál gépies névelő-javítás (D17), újragenerálás nincs; a hibaelhárítás
    teljes építése jóváhagyva (D16 kiegészítése), az 5. próba programos kapujával.
  - **D17 végrehajtva** (`szint06.py nevelo`, majd `final`, a spark-deven):
    - bank: 244 raw szöveg javítva, ebből 193 a válogatott itemek között; szabálycsalád: 386, ebből 295;
    - ellenőrizve: azonos item-sorrend, más mező nem változott, az összesítő tartalma azonos, „(z)” sehol nem maradt; a
      javított szövegek mind átmennek a mai tényellenőrzésen;
    - az eredeti szöveg a raw `szoveg_eredeti` mezőjében, a javítás előtti raw a `raw/<család>.elotte-nevelo.jsonl`-ben.
  - **Még egy „a(z)”, az opciószövegben:** a hibaelhárítás szabályszövege („… és a(z) <mérés> kisebb, mint …”) maga is
    „a(z)”-t írt. Javítva (`nevelo`); az 5. próba terve már a javított kóddal készült.
  - **Új ellenőrzés:** `szint06.py ellenoriz` — a terv mérései és a szabálytábla szerint MATCH-nél pontosan a gold
    igazolódik, a többi állapotnál egyik opció sem; plusz „a(z)” és programazonosító-szerű név. Visszamenőleg: a v4-es
    próbán 0 szabálylogikai hiba (12 „a(z)”, 8 név), az archivált fenntartásos építés 2000 itemén 0 szabálylogikai hiba
    (1000 „a(z)”, 239 név).
  - **Span-ellenőrzés** (`kiolvas06.py spanok`, CPU): a bank- és a szabálycsalád 4000 itemén, két sorrendben (8000
    prompt) 0 hiba; a prompt mediánja 364, p99-e 608 token.
  - **Sorok a spark-deven, láncolva:** K06F2P (5. próba) → K06F2HB (07:16-tól vár; kapu: ≥ 22/24 és `ellenoriz --proba`
    hibátlan; teljes építés, `ellenoriz`, 300-as auditminta) → K06F3 (07:21-től vár; span-ellenőrzés, T500 nyitva, CAL és
    TESZT pecsét alatt, manifest).
  - **Az 5. próba** 07:25-kor kész: 24/24 item, elvesztés és újragenerálás nincs; `ellenoriz --proba` hibátlan
    (szabálylogika, „a(z)”, nevek). A lap (`kor06/adat/f2/proba/proba_lap.md`) átnézve: „a(z)” nincs, az opciók névelője
    a mérés nevéhez igazodik, a cég mindenhol „A … Kft.-től írok”. Apróságok: a katalógusnevek a mondat közepén is
    nagybetűsek („és a Hálózati bemeneti feszültség …”), és az angol szövegben a tünet néha szó szerint, nyelvtanilag
    döcögősen kerül a mondatba („We are observing output voltage fluctuates under load”). A címkét egyik sem érinti.
  - **A K06F2HB kapuja átment**, a teljes építés 07:25-kor indult (várható vége 08:35).
  - **Az audit felülete:** `kor06/eszkozok/audit06.py` (`html`, `osszesit`), az `atnezes.py` mintájára, vakon: az
    item-id kimondja az állapotot, ezért a lap átlátszatlan kulcsot (a001…) mutat, család, nyelv és szelet nélkül;
    eltérésnél második ítélet a konstrukció címkéjével és a terv tényeivel. A kapu: a „konstrukció hibás” és a
    „kétértelmű” ítélet címkehiba, az egyoldali 95%-os Clopper–Pearson felső korlát ≤ 2%. Az archivált mintán kipróbálva
    (300 item, a lapon nincs azonosító-szivárgás; szimulált döntésekkel 1 hiba → 1,57%).
- **2026-10-30 délelőtt — két leállás, javítás, újraindítás 10:45-kor.**
  - **K06F2HB, 07:53:** a katalógusépítés (`sablon`) leállt, mert a `muszaki.hibaelharitas:hu:029` hat próbán át sem
    ment át az ellenőrzésen. A lépés csak a végén írt, így a 119 kész katalógus is elveszett.
    - Valószínű ok: a reggel bevezetett névszabály (`[a-z][A-Z]`) a jogos szakszavakat is elutasította. Az archivált
      2400 katalógusnévből ilyen a „PoE”, a „SoC” és a „WiFi”, vagyis egy hálózati eszköz katalógusa eleve nem
      mehetett át. Az elutasítás okát a kód nem naplózta, ezért ez következtetés, nem mért adat.
    - **Javítás:** `AZONOSITO_RX` = aláhúzás vagy CamelCase (`[a-z]{2}[A-Z][a-z]`). Az archivált katalógusokon
      ugyanazt a 239 programazonosító-szerű nevet fogja meg, a fenti öt szakszót átengedi. A próbálkozások száma
      12; a kész katalógus azonnal a `.reszleges` fájlba kerül, újraindításkor onnan folytatódik; az elutasítás oka
      próbálkozásonként a `.elutasitas` fájlba; a JSON-hiba sem állítja le a többit.
  - **K06F3 (bank és szabálycsalád):**
    - a K06F2HB leállása után (07:54) indult, és 09:57-re lefutott: span-ellenőrzés, T500 nyitva (2 × 2000 forward), CAL és TESZT a pecsét alatt
      (12000 forward), 2,2–2,6 forward/s.
    - A pecsét lezárása elbukott, mert a manifest kódlistája a hibaelhárítás még nem létező itemfájlját is kérte.
      Javítva (csak a létező itemfájl), a lezárás 10:44-kor sikerült: `kor06/rogzites/pecset/K06F3.json`, 26 fájl,
      0,45 GB, 8 feladat, mind kész, a várt darabszámmal.
  - **A GPU 09:58 és 10:45 között üresen állt.** A sorokra nem figyeltem, és a két hiba csak Dani kérdésére derült ki.
  - **Újraindítva:** K06F2HB 10:45 (várható vége 11:55), mögötte a K06F3H (`FAZIS=K06F3H`: a bank- és a szabálycsalád
    kész shardjai kimaradnak, csak a hibaelhárítás fut; a végén az összes pecsét alatti fájl manifestje).
  - **A katalógusépítés 11:12-re kész**, mind a 120 katalógus. 31 sablonnál volt elutasítás, összesen 54 próba:
    - programazonosító-szerű név 36, a szabály és az értékek ellentmondanak 12, hiányos ok 6;
    - a `hu:029` „vállalati Wi-Fi hozzáférési pont”, ez alátámasztja a fenti okot; most 3 elutasítás után átment;
    - a `hu:005` és a `hu:033` a 7. próbára ment át, a régi hatos korláttal ezek is leállították volna a lépést.
  - Terv: 2604 (MATCH 1560, NO_MATCH 520, MISSING_DATA 262, OUT_OF_SCOPE 262); a generálás 11:12-kor indult.
- **2026-10-30 dél — a hibaelhárítás kész; az F2 adatépítése lezárult (az audit előtt).**
  - **K06F2HB 11:55-re kész** (60 perc): 2000 item / 2604 terv, 2592 túlélő; T500 500 / CAL 500 / TESZT 1000; fele magyar,
    fele angol; MATCH 1200 / NO_MATCH 400 / MISSING_DATA 200 / OUT_OF_SCOPE 200; hiányzó cella nincs, 120 sablon.
  - **Elvesztés:** 12 terv (MATCH 9 és NO_MATCH 2: az ok neve a szövegben; MISSING_DATA 1: a hiányzónak szánt érték a
    szövegben). Újragenerálás (minden próbálkozás): az ok neve a szövegben 33, rossz nyelv 18, a hiányzó érték a
    szövegben 3.
  - **`ellenoriz` a 2000 itemen hibátlan:** szabálylogika, „a(z)”, nevek.
  - **Auditminta:** 300 item, családonként 100. A vak lap (`audit06.py html`): `kor06/adat/f2/audit/atnezo.html`, sig
    `300-f4f65705fa`; a lapon nincs azonosító-szivárgás és nincs „(z)”. A kulcsleképezés helyben, a
    `kor06/adat/f2/audit/atnezo_kulcsok.json`-ben.
  - **K06F3H:** a span-ellenőrzés a három családon átment; a hibaelhárítás T500-a 11:56-kor indult, utána jön a CAL, a
    TESZT és a teljes manifest (K06F3H).
- **2026-10-30 délután — auditlelet a szabálycsaládban (Dani, a077 és a124).**
  - **Lelet:** két angol MATCH item, megoldókulcs „Domestic business travel and accommodation …”, Dani válasza M. A szöveg
    nem mondja meg, hogy az út belföldi-e (EUR-ös összeg, Bristol vagy hely nélküli telephelyi bejárás). Dani pontosítása:
    a C válasz nem biztosan téves, de a szövegből nem következik egyértelműen.
  - **Ok, a konstrukcióban:** az angol `travel` költségnem leírása „domestic …”, de a négy angol helyzet egyike sem
    állapítja meg a belföldiséget (Leeds, Bristol, „site inspection”, „regional office”), és a prompt csak a helyzetet adja
    át. A magyar oldalon nincs ilyen gond: magyar városok, forint, Kft.
  - **Kör:** 173 angol `travel`-célú item, egyikben sincs „domestic” (MATCH 118, NO_MATCH 37, MISSING_DATA 18). A
    NO_MATCH-en az X mindkét olvasatban helyes; a MATCH-en a címke nem következik a szövegből; a MISSING_DATA-n az M és az X
    is védhető. Rokon, gyengébb eset: „client entertainment and gifts” a „lunch after a supplier negotiation” és a „wine
    tasting to welcome a new partner” helyzettel (106 item); a mintában az a081-et Dani nem jelezte.
  - **A kapu ezzel már nem mehet át** (2 hiba > 1): javítás és új audit kell a szabálycsaládra. Döntés Danié.
- **2026-10-30 délután — az 1. audit eredménye és a javítás sora.**
  - **1. kör** (`audit06.py osszesit`, Dani döntései: `kor06/adat/f2/audit/dontesek_kor1.json`; összesítő:
    `kor06/eredmenyek/F2/audit/osszesito.md`): 300 / 300 átnézve, 12 címkehiba (2 „konstrukció hibás”, 10 „kétértelmű”),
    a felső korlát 6,40%: **nem ment át**.
    - hibaelhárítás 100 / 100 egyezik;
    - bank 6 kétértelmű (a cégnév szerepe);
    - szabálycsalád 2 hibás (belföldiség) és 4 kétértelmű (szerverbeszerzés).
  - **Javítás:** D18 és D19 (14. pont). A szabálycsalád próbáján (másolaton): 2539 raw rekord marad, ebből 1076-nál új az
    opciószöveg; a 65 szerverbeszerzési terv újragenerálásra kerül; meglévő szöveg a mai tényellenőrzésen nem bukik. A
    bankon mind a 2000 item megkapja a számlatulajdonos-sort, más mező nem változik.
  - **Új eszközök:** `szint06.py ujraterv` (a raw rekordok az új tervvel; megengedett eltérés: az opciószöveg, a
    `tipus_leiras` és a `kerelem_jellege`; minden más eltérésnél leáll), `szint06.py audit --kor 2 --csalad …`,
    `audit06.py --kor 2` (`--elozo`: az 1. kör a nem újramintázott családokra).
  - **K06F2J** (12:45-től vár a K06F3H-ra): a javítás, a Muse csak a 65 szöveghez, a régi bank- és szabálykiolvasás
    archívumba (`cache/k06/archiv_v1`, illetve a pecsét alatt `cache/k06/pecset/archiv_v1`), a 2. audit mintája, utána
    K06F3B (a két család újrakiolvasása, új manifest).
  - **K06F3H 13:09-re kész:** a hibaelhárítás T500-a nyitva, a CAL és a TESZT pecsét alatt; manifest
    `kor06/rogzites/pecset/K06F3H.json` (39 fájl, 0,68 GB, teljes).
  - **K06F2J adatjavítása 13:23-ra kész:**
    - **szabálycsalád:** a 65 új szöveg mind átment, 2593 túlélő (az elvesztés változatlanul 11, mind nyelvi); 2000 item
      ugyanazokkal az id-kkel, 1949 szöveg azonos, 51 új (a volt szerverbeszerzés); „Domestic” és „Client entertainment”
      egyik opcióban sincs; a hatókörön kívüli itemekben a „szerver” már csak informatikai hibabejelentésben szerepel (3);
    - **bank:** 2000 / 2000 item kezdődik a számlatulajdonos-sorral;
    - a régi bank- és szabálykiolvasás 12 könyvtára archívumban (4 nyitott, 8 a pecsét alatt).
  - **2. audit:** 200 item (bank 100, szabálycsalád 100, az 1. kör itemei nélkül), a lap
    `kor06/adat/f2/audit/kor2/atnezo.html` (sig `200-b85784f958`, kulcsok b001…, azonosító-szivárgás és „(z)” nincs).
  - **K06F3B** 13:23-kor indult (T500 nyitva, utána CAL és TESZT a pecsét alatt).
  - **K06F3B 15:25-re kész** (a K06F2J is):
    - T500 nyitva: bank 13:45, szabálycsalád 13:58 (kanonikus 500, b1 1500 családonként);
    - CAL és TESZT a pecsét alatt;
    - manifest `kor06/rogzites/pecset/K06F3B.json`: 65 fájl, teljes, a három család mind a 12 feladata
      (CAL kanonikus 500, b1 1500; TESZT kanonikus 1000, b1 3000).
    - A manifest az új items-fájlok hash-ét rögzíti, ezek egyeznek a helyi fájlokkal.
    - A bank és a szabálycsalád új kiolvasásának hash-e eltér az archívbeliétől.
    - A hibaelhárítás 9 adatfájlja bájtra egyezik a K06F3H-val; csak a 4 `osszegzes.json` íródott újra (időbélyeg).
    - Az `archiv_v1` a pecsét alatt marad, és a manifest azt is rögzíti.
  - `eszkozok/sync.sh back06` ettől kezdve a `kor06/rogzites/`-t (a pecsét manifestjeit) is lehozza.
- **2026-10-30 éjjel — K06F2G** (23:55-től): a Gemma 4 26B-A4B-it második ítélete mindhárom család mind a 6000
  itemjén, négy sorrendben.
  - A prompt a 03 generikus kerete: gold és item-id nélkül. A címkék egytokenesek, a leghosszabb prompt 796 token.
  - Az összesítés után a családtávolság-audit következik (bge-m3, a 05 itemkészlete: 218 család, 66 587 item; a próba
    családonként 30 itemmel lefutott).
  - A Gemma kimenete nem az alany kiolvasása, ezért nem a pecsét alá tartozik.
  - Az auditkulcsokra bontott ítéletet helyben számolom: a kulcsfájl csak a laptopon van. Dani első, vak ítélete
    előtt nem nyitom meg.

  - **Memória:** a Gemma betöltése alatt (00:00–00:02) a szabad memória 17 GB-ig ment le, mert mellette az erőszimuláció
    is futott. Ez a 15 GB-os határ fölött maradt, de szűken. Modellbetöltés alatt mellette CPU-feladat sem fut.
  - **F4, erőszimuláció (8.5; `kor06/eszkozok/mde06.py`, `kor06/eredmenyek/F4/mde06.md`):**
    - A bemenet az F1b (a v0.2 kódja) a három szűrőrétegen, a friss családok helyettesítőjeként: 1000
      TESZT-alapeset, alapesetenként egy item, 4000 replika, véletlen seed.
    - Rétegenkénti MDE80 relatívan: HO-routing 13,3%, HO-termék 18,1%, HO-új 8,2%.
    - Az átlag MDE80-ja relatív csökkenésként:
      - a három dev rétegre 5,8%;
      - ha mindhárom friss család ugyanolyan szerkezetű, mint egy-egy réteg: 3,9% (3 × routing), 9,6% (3 × termék),
        4,4% (3 × új).
    - A D4 ereje pontosan 10%-os valódi csökkenésnél a legrosszabb szerkezetben (3 × termék) 0,83, 15%-nál 0,99.
    - A „pontbecslés ≥ 10%” feltétel 10%-os valódi csökkenésnél szerkezetéből adódóan 0,5 valószínűségű; ez nem
      erőhiány.
    - **Következtetés:** a 8.5 szerint az 1000-es TESZT az átlagra nem alulerős; nagyobb TESZT nem kell. A
      családonkénti 10% nem mutatható ki, de a szabály családonként csak a pontbecslést kéri.
  - **A 13. pont kockázata, a B1 a nyitott T500-on (`kor06/eszkozok/b1t500_06.py`, `kor06/eredmenyek/F3/b1_t500.md`):**
    - B1-AURC: bank 0,127, hibaelhárítás 0,226, szabálycsalád 0,281 (pontosság 0,72–0,74). Mindhárom ≫ 0,01, nincs
      csere. A relatív MDE ilyen AURC-szinten inkább a HO-routing- és a HO-új-szerű, kedvezőbb esetekhez esik közel.
    - **Megfigyelés a v1 előtt:**
      - Szigorú helyességnél az OUT_OF_SCOPE-on a B1 mind az 50 esetben NONE-t javasol, és ez mindig hiba.
      - A MISSING_DATA-n a bank és a szabálycsalád mindig SELECT-et ad, a hibaelhárítás 32/50 esetben NONE-t; mindkettő
        hiba.
      - Így az itemek ~20%-a a B1-nek szerkezetileg biztos hiba.
      - Az F1-ben a nyereség nagyobb része a NONE-konvencióból jött. Ezért a K1 2. szintje (B1-R − B1-N) itt is
        kulcsfontosságú, és a közlésben a nyereséget a NONE- és a SELECT-javaslatokra bontani kell (`bontas06`).
  - **K06F2G, a Gemma-ítélet (00:03–00:21):** 24 000 kiolvasás hibátlanul (~21/s).
    - A sor `gemma06 osszesit` lépése hibával állt meg, mert a 03 val-temperature fájlja nincs a spark-deven. Az
      összesítés helyben fut, és a sorból kivettem.
    - A bge-m3 lépés emiatt külön futott (00:24–00:28).
  - **A Gemma második ítélete (`kor06/eredmenyek/F2/gemma/osszesito.md`; temperature 4,974, négy sorrend):**
    - Egyezés a konstrukcióval: összesen 90,5%; MATCH 99,2–100%, OUT_OF_SCOPE 99,5–100%.
    - NO_MATCH: bank 77,8%, szabálycsalád 79,0%, hibaelhárítás 94,5%. A két megnézett T500-példa (bank: azonos
      összeg, más számlaszám a közleményben; szabálycsalád: 229 060 Ft a 200 000 Ft-os pont mellett) szándékos közeli
      zavaró opció, a címke helyes.
    - MISSING_DATA: bank 4,5% (191 / 200 eltér, 133-nál legalább 3/4 sorrend egyetért), szabálycsalád 37,0%,
      hibaelhárítás 79,5%.
      - A bank MISSING_DATA-n két azonos összegű számla van, a közlemény „utalás”, a partner hiányzik. A Gemma az
        esedékességhez legközelebbit választja; a B1 is minden esetben SELECT-et ad (T500: 0 / 50 NONE).
      - Az 1. körben Dani a bank MISSING_DATA-itemek egyikét sem jelölte. **Kérdés Daninak:** elfogadható-e
        egyértelmű válasznak az esedékesség szerinti döntés? Ha igen, a bank MISSING_DATA meghatározása vitatható.
    - Sabloncsoportonként a legkisebb egyezés 57–75% (~15 item). Rendszerszintű kiugrás nincs, a magyar sablonok
      vannak hátrébb.
    - Az auditkörök kulcsaira: 1. kör 56 / 300, 2. kör 46 / 200 eltérés. A 2. kör kulcsonkénti ítéletét
      (`audit/kor2/gemma_itelet.json`) Dani vak exportja előtt nem nyitom meg. Itemet nem töröltünk és nem javítottunk
      (D15).
  - **Családtávolság-audit (`kor06/eredmenyek/F2/tavolsag/tavolsag06.md`; bge-m3, 66 587 referencia-item, 218
    család):**
    - A friss családok legközelebbi referencia-családja (centroid-koszinusz): bank → kie.datum 0,822, hibaelhárítás →
      en.eval.fastino 0,774, szabálycsalád → level.dokumentumtipus 0,803.
    - Viszonyításként a referencia-családok legközelebbi másik családja:
      - más csoportban: medián 0,752, q90 0,856;
      - ugyanabban a csoportban: medián 0,864.
    - A friss családok tehát úgy esnek a meglévőkhöz, mint két külön csoport családjai egymáshoz.
    - Itemszinten a legnagyobb koszinusz bank 0,788, hibaelhárítás 0,685, szabálycsalád 0,755. Egyik sem éri el a 0,90-et,
      közeli duplikátum nincs. Viszonyításként a referencia-itemek más családhoz mért értéke: q95 0,849, q99 0,916.
    - **Kézi indoklás (vázlat, Dani megerősítésére):**
      - **bank ↔ kie:** a közelség a felszínből jön: összeg, dátum, cégnév. A kie mezőt olvas ki egy iratból, a bank
        egy banki tételt párosít nyitott számlák listájával (két forrás egyeztetése, közlemény és összeg).
      - **szabálycsalád ↔ level.dokumentumtipus / triage:** mindkettő kategóriába sorol, de a szabálycsaládban a
        döntés összeghatáron és jóváhagyási szabályon múlik (küszöb-következtetés), nem a szöveg témáján.
      - **hibaelhárítás:** a legtávolabbi; mérésekből és diagnosztikai szabálytáblából következtet, nincs megfelelője.
- **2026-10-31 reggel — a 2. címkeaudit és a döntések:**
  - **Dani exportja:** `kor06/adat/f2/audit/kor2/dontesek.json`, 200 / 200. Egy eltérés: b136, Dani X, a konstrukció A
    (`gold_hibas`). Az összesítő (`--elozo` az 1. körre, a hibaelhárítás 100 itemjével) 300 / 300 itemet tartalmaz,
    1 címkehibával. Az egyoldali 95%-os felső korlát 1,57% ≤ 2%: **a kapu átment**
    (`kor06/eredmenyek/F2/audit/kor2/osszesito.md`).
  - **A Gemma a 2. körben** (a kulcsonkénti ítéletet Dani exportja után nyitottam meg): 154 / 200 egyezik.
    - Eltér 37 MISSING_DATA-n (bank 24, szabálycsalád 13) és 9 NO_MATCH-en. MATCH-en nem tér el, a b136-on a hibás
      A-t választja.
    - A felülvizsgálati szabály (MATCH-eltérés, vagy NO_MATCH 4/4 sorrendben) három kulcsot ad: b017, b135, b169.
      Mindhárom szándékos közeli zavaró opció, a címke helyes; Dani is X-et adott rájuk.
  - **D20, D21, D22** (14. pont).
  - **A b136 hibája rendszerszintű, de kis kiterjedésű:** a banki itemekből 16-ba került kitalált számlaszám,
    hivatkozás vagy idegen dátum (2026/1845, 2026/0842, „Számla 00124”, „2026/08/15”). Ezek közül az
    ellentmondó számlaszám 3–5 MATCH-ben van. A szabálycsaládban a több összeget tartalmazó szövegek tételes bontások,
    amelyek kiadják a végösszeget; ott nincs teendő.
  - **Családtávolság:** Dani a kézi indoklást megerősítette.
  - **A javítás sora** (`k06f2_bank.sh`, K06F2K):
    1. sablon, terv, újratervezés (a másolaton lefutott: 2584 rekord marad, 20 újragenerálandó);
    2. a Muse a 20 szöveghez, `final`;
    3. a bank régi kiolvasása `archiv_v2`-be;
    4. K06F3C (a bank újrakiolvasása, új manifest);
    5. a Gemma a bankon.
  - **K06F2K** 07:16-kor indult (a másolaton próbált lépésekkel azonos számokkal).
  - **Az F5 kódja** (`friss06.py`, `befagyaszt06.py`, `kor06/rogzites/v1/v1-vazlat.md`) elkészült.
    - A füstteszt a nyitott T500-on fut, amint a K06F3C kiolvasása egyenletes, és legalább 35 GB a szabad memória.
    - **A klaszteregységről D23 javaslat.** A 06-os itemek group_id-je maga az item-azonosító. A TESZT 60
      sabloncsoportból áll, csoportonként kb. 17 itemmel.
    - A B1 helyességének sablonon belüli ICC-je a nyitott T500-on bank −0,038, hibaelhárítás −0,028, szabálycsalád
      −0,016.

  - **A K06F2K adatjavítása 07:30-ra kész:**
    - 2000 item ugyanazokkal az id-kkel; 16 új szöveg (a D22 szerint kieső itemek), 1619 itemnél új opciószöveg (D21:
      egy esedékesség).
    - A tényellenőrzés mind a 2000-en hibátlan.
    - A 16 új szövegben csak a partner, az összeg, a dátum és a „számla kiegyenlítése” áll. A b136 új szövege:
      „2026-10-02 Terhelés 328 820 Ft Vértesvölgy Irodatechnikai Zrt. Számla kiegyenlítése”.
    - A 200 MISSING_DATA-itemben a közös összegű pár esedékessége mind azonos.
  - **K06F3C** 07:30-kor indult.
  - **Füstteszt:** az első indítás (07:42) idő előtt jött. A bank T500-ának b1-sorrendjei még hiányoztak, ezért a
    tanítás „permutációi hiányosak” hibával állt meg. Az új indítás a pecsét alatti rész egyenletes futására vár.
- **2026-10-31 reggel — Dani a D23-ról és a v1-vázlatról:**
  - A D23-at sabloncsoporttal elfogadta.
  - Három pontosítást kért: az erőszámítás csak tervezési becslés; a szeletek szerepe; a seedek összevonása (ez lett a
    D24).
  - A szöveg a vázlatban és a runbookban (5., 8.2, 8.5) átírva.
  - **A kód:** a `friss06` a bootstrapban replikánként a futások átlagát számolja (`rep_atlag`), és külön sorban
    közli a futások közti eltérést (`futasok`) és a T100 / T200 sablonszámát (`minta_sablonok`). A munkapont is
    futásátlagot számol; a `bontas06.reteg` `seed_atlag` kapcsolót kapott (az F1 viselkedése alapból változatlan).
  - A füstteszt 08:03-kor indult újra.

  - **Füstteszt (`friss06 fusteszt`, a nyitott T500-on, a tanítóminta a teszt is; mérőszámot nem néztem meg):**
    - 08:03–08:17: a tanítás mindhárom családon lefutott. Karonként 83 pontszámsor, a B1-sorok hossza mind 500.
    - Az első értékelés hibával állt meg: enyhe helyességnél a bank NONE-javaslatai mind helyesek, ezért a NONE-on
      belüli AUROC egyik replikában sem értelmezhető. Javítás: az `elemzes06.summ` ilyenkor `ci95 = None`-t ad (az F1
      számait ez nem érinti).
    - Az újrafuttatás (`--tanitas-nelkul`) hibátlan: 3 család, 6 nyelvi részszelet, a kapu a D4-gyel, a futások
      (B1-R | T500: 3, T100 / T200: 15), a munkapont 4 karral, a bontás.
    - Az értékelés 50 ismétléssel 5 s, 10 000-rel kb. 17 perc.
    - **A T100 / T200 sablonszáma:**
      - bank: T100 30 / 29 / 29 / 29 / 29, T200 mind 30;
      - hibaelhárítás: T100 30 / 30 / 30 / 30 / 29, T200 mind 30;
      - szabálycsalád: T100 30 / 27 / 28 / 29 / 29, T200 mind 30.
    - A füstteszt kimenete (`cache/k06/f5_fust`) a T500 saját mintáján mért értékeket tartalmaz. Nem néztem meg, és
      nem része a v1-nek.
  - **K06F2K 08:56-ra kész.**
    - A K06F3C pecsétmanifest (`kor06/rogzites/pecset/K06F3C.json`) 78 fájl, teljes; a bank négy feladata
      (CAL 500 / 1500, TESZT 1000 / 3000) megvan.
    - Az itemfájlok hash-e azonos a helyiekével.
    - A hibaelhárítás és a szabálycsalád 7–7 pecsét alatti adatfájlja bájtra azonos a K06F3B-vel.
    - A bank 7 új adatfájlja mind eltér az `archiv_v2`-beli régitől.
    - Az elvesztett tervek száma változatlanul 44.
  - **A Gemma a javított bankon** (`gemma_f2_bank_v2.jsonl`, 8000 kiolvasás, hiba nélkül). Az összesítő a nem banki régi
    kiolvasással együtt `kor06/eredmenyek/F2/gemma/osszesito.md`; az előző változat `elotte_D21_D22/` alatt.
    - A bank MISSING_DATA egyezése 4,5% → 13,5%.
    - **A D21 hatása:** előtte a 191 eltérésből 133-nál legalább 3/4 sorrend ugyanazt választotta, az
      esedékességhez legközelebbit. Most a 173 eltérés mind a közös összegű pár egyike. A négy sorrendből a pár első
      tagját 0–4-szer választja (15 / 29 / 64 / 52 / 13), ami közel véletlen.
    - A maradék eltérés a Gemma ismert X-kerülése, nem újabb árulkodó jel.
  - **A v1 manifestje 08:58-kor kész** (`befagyaszt06.py manifest`): `kor06/rogzites/v1/MANIFEST.sha256`, 41 fájl, a
    hash-e `5ff6d8010f8f11e29ba95c3db8b5683e0b7ac257ba2d1954b3a96cbc66025ec8`.
    - **Tartalma:** a kód (06: 9, 05: 8, közös: 3), a 3 itemfájl, a családterv, a 05 kalibrációja, a H-fejek, az
      előtanított B1-R, a 2. audit összesítője, valamint a pillanatképek: `06-runbook-v1.md`, `v1-vazlat.md` (sha256
      `b370dec4…`) és `K06F3C.json`.
    - A pecsét zárva: ROGZITES.json nincs.
    - Az F5 sora (`k06f5.sh`, K06F5) kész, Dani jóváhagyására vár.
  - **A v1 rögzítve 09:15:32-kor** (`befagyaszt06.py rogzit`). A jóváhagyás Dani „mehet”-je a 41 fájlos manifestre.
    - `kor06/rogzites/v1/ROGZITES.json`: a manifest hash-e `5ff6d801…25ec8`, a K06F3C pecsétmanifesté `ef3e961b…a3fc0`.
    - Az `ellenoriz` rendben; ettől a ponttól nyitott a pecsét.
    - A K06F5 09:15:38-kor indult (`k06f5.sh`).
  - **A K06F5 09:48:30-kor kész**, hiba nélkül (tanítás 09:15–09:26, értékelés 09:47-ig, bontás és munkapont 09:48-ig).
    - Az eredménylap: `kor06/eredmenyek/F5/eredmenylap.md`.
    - **A 8.3 szabály a D4-gyel teljesül:**
      - mindhárom családon B1-R < B1-S;
      - az átlagos AURC aránya 0,205 [0,187; 0,224].
    - **A K1 mindhárom szintje teljesül mindhárom családon.** A banki SELECT-javulás határeset: a felső határ −0,0001.
    - **D20:** az átlagos nyereség 72%-a a NONE hátrasorolásából jön (B1-N), 28%-a a B1-R többlete.
    - **Enyhe helyességgel nem teljesülne:** az arány 0,965 [0,881; 1,063].
    - **Önellenőrzés:** minden pontbecslés a saját intervallumán belül; a szeletek sablonjai diszjunktak; a promptban
      nincs item-id és állapotmező.
    - A futás figyelője (ssh until-loop) 255-tel megszakadt; a futást nem érintette.
  - **A 06 lezárása (Dani, 2026-10-31):**
    - a 06 sikeres a vállalt kérdésben, a sikerkritériumot utólag nem módosítjuk;
    - a következő kör iránya: állapotjelző B1 erősebb referenciaként, utána valódi magyar adat egy családon;
    - a H tartalmi fej hátrébb sorolva.
    - A terv vázlata: `07-runbook.md` v0.1.
  - **Önellenőrzés (Dani kérésére, 11:30 körül):**
    - az eredménylap számai a JSON-okból újraszámolva egyeznek; a MATCH-en rossz opció (1 / 7 / 5) közvetlenül is
      megszámolva az `f1.json`-ból;
    - a kód: a bootstrap 60 sablonklasztert húz visszatevéssel; a bontás és az elemzés intervalluma ≤ 0,001-re egyezik;
      a munkapont hibasorai τ-szűrtek; a naplókban nincs figyelmeztetés;
    - **új korlát az eredménylapon:** a családterv nehéz negatívjai a B1-nek nem nehezek, a 3. szint itt szinte csak
      állapothibát mér; a címkezaj–E-AURC összevetés heurisztikusnak jelölve;
    - az `f5_bontas.md` gépi fejléce az F1-es szöveget viszi (a `bontas06.lap` a v1 manifestjében van, nem módosítjuk;
      az eredménylap jelzi);
    - a 07 v0.1 javításai: D3 (a D_meta már négyállapotú, a B1-R a 06 recept marad), K2 (80%-os felső korlát, helyes
      adatbekérés/továbbítás külön sor), 3.3 és D6 (erősebb diagnosztikai konstrukció, a méret az F1 hibaaránya
      után), D5 (a 10% felülvizsgálandó az erőbecslés után, a rögzítés előtt).
