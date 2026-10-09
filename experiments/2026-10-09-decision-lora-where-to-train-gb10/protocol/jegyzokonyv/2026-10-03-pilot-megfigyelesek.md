# Pilot (F0.1, seed 101) — megfigyelések az F1-es generátorhoz

A pilot eldobható (runbook 9. pont, F0.1). Ez a lista azt gyűjti, amit az F1 teljes
generálása előtt javítani vagy dönteni kell. A végleges számok a pilot riportjaiból
(`generator_riport.json`, `osszeallit_riport.json`) kerülnek ide az F0B után.

## Futás

- **Generátor:** boot ~4 perc; S1–S4 914 s (494 cikk, 645 pár/megnevezés, 1002 sor). Négy
  párhuzamos kérés, ~84–96 token/s összesen, MTP-elfogadás ~90%.
- **S5–S6 első futása elhasalt (08:16):** a <user> HF-cache-ében a `BAAI/bge-m3`-nak csak
  az `onnx/` és `1_Pooling/` része volt meg, `config.json` és tokenizer nélkül. Javítás: a
  teljes `5617a9f6` snapshot (a prod `refs/main` revíziója) a `clf-study` cache-éből a
  kísérlet saját `cache/bge-m3`-jába került. A `common.BGE_M3` erre mutat, a vezénylő
  idempotensen másol. Konténer-próba: transformers 5.6, torch 2.11; a hasonlóság
  értelmes (ugyanaz a tétel két írásmódban 0,86, idegen tétel 0,37). Újraindítás
  08:18-kor, a generálás nem futott újra (`.ok`).

## S1 — katalógus (494 cikk: 298 termék, 162 szolgáltatás, 34 gyűjtő; 306 család)

- **Családméret:** 155 egytagú, 114 kéttagú, 37 háromtagú család. A „kb. fele egytagú”
  promptcél teljesült.
- **CJK:** 0 cikk.
- **Abszolút ár nem valószerű.** A `price_for` az alkategória egységár-kvartiliseiből
  (q1–q3) húz log-egyenletesen, de nem veszi figyelembe a mennyiségi egységet és a
  kiszerelést. Példa: „Krémes sütemény vaníliás 1 kg” 103 Ft/kg. A testvérek közti arány
  (méret^0,85) rendben van, így a döntési jel megmarad, csak a szint torz.
  - **Javaslat F1-re:** a generátor-LLM adjon referenciaárat a családhoz (Ft / egység). A
    profil-kvartilisek ezt csak csonkolják, nem helyettesítik.
- **Név–egység ellentmondás:** „Péksütemény vajas 100 g” egysége „kilogramm”. A valós
  számlákon is előfordul, de itt az LLM egységválasztásából jön.
  - **Javaslat:** ha a névben van tömeg vagy térfogat, az egység legyen darab, csomag
    vagy karton.
- **Gyűjtőnév:** „Egyéb egyéb szolgáltatás” (alkategória neve „Egyéb szolgáltatás”).
  Csak kozmetikai hiba, mert a gyűjtő sosem opció.

## S5–S8 — jelöltek és összeállítás (588 kiértékelő item: minden nem-train + 300 train)

- **X-arány** minden rétegben 0,24–0,26. Az opciószám X és nem-X itemeknél
  kiegyensúlyozott (pl. train 7,29 vs 7,19), tehát a listahossz nem árulja el az X-et. A
  shortcut-audit ezt még külön méri.
- **Nehézség a 4.5 célsávjaihoz képest** (BM25 top-1 gold 0,50–0,75; testvér a listán
  ≥ 0,40; BM25-margó medián ≤ 0,15):

  | réteg | n | BM25 top-1 | testvér | margó | kétértelmű |
  |---|---|---|---|---|---|
  | train | 714 | 0,55 ✓ | 0,62 ✓ | 0,27 ✗ | 0,13 |
  | val-belső | 16 | 0,67 ✓ | 0,67 ✓ | 0,45 ✗ | 0,31 |
  | val-szállító | 47 | 0,57 ✓ | 0,66 ✓ | 0,20 ✗ | 0,13 |
  | T-belső | 21 | 0,81 ✗ (könnyű) | 0,56 ✓ | 0,26 ✗ | 0,19 |
  | T-szállító | 65 | 0,82 ✗ (könnyű) | 0,57 ✓ | 0,37 ✗ | 0,12 |
  | T-közeli | 85 | 0,44 ✗ (nehéz) | 0,66 ✓ | 0,13 ✓ | 0,20 |
  | T-távoli | 54 | 0,65 ✓ | 0,40 ✓ | 0,31 ✗ | 0,00 |

  - **A T-belső és a T-szállító lexikailag könnyebb a trainnél.** Valószínű ok: a teszt-sor a
    `full` indexben keres, ahol a cikknek minden train-párból van aliasa. A train-sor viszont
    a 2-foldos indexben keres, ahol csak a másik fold aliasai vannak meg. Ez a szándékos
    szivárgásgátlás mellékhatása: a train nehezebb a tesztnél.
    - **Döntendő:** elfogadjuk (a prod is a teljes alias-készlettel keres), vagy a
      teszt-sorokhoz is alias-ritkítás kell.
    - Az alany L0-pontossága rétegenként (K0b-2) megmutatja, hogy ez a döntésben is
      számít-e.
  - **A margó szinte mindenhol a célsáv fölött van.** Valószínűleg maga a célsáv volt
    túl szigorú; a pilot erre való (4.5: a célsávok beállítása a pilotból).
  - **A T-távoli rétegben 0 kétértelmű item.** A „Konyhaüzemi anyag” cikkeinél az S8
    attribútum-alapú kétértelműsége nem talál fogást. Megnézendő, milyen attribútumokat
    kapnak ezek a cikkek.
- **X(b) a T-közeliben: 0.** Véletlen, nem kódhiba: a 35 X(b)-cikket a generátor
  egyenletesen húzza a 460 cikkből, és egy sem esett a „hús, hal” gyökérbe (P ≈ 1%).
  - **F1:** az X(b)-húzás legyen gyökérenként rétegzett.
- **Opciószám:** 3 itemnél csak 3 opció (+X) van. A 4.4 szerinti 6–11-es listahossz alá
  esik, ezek a pótlásból kifogyó itemek.

## K0b-2 — az alany (L0) a pilot-itemeken (588 item, egy példány, soros, bemelegítéssel)

- **Ismételhetőség:** a két soros alap-futás mind az 588 soron bájtra azonos (a K0a
  probe-ján 92–99% volt).
- **Címketömeg:** minimum 0,982, medián 0,9994. A „(” prefill a tömeget ~0-ra viszi
  (medián 0,0000), tehát prefill nincs — a K0b döntése áll.
- **„Egyik sem” vs „Nincs illő”:** az X-recall a „Nincs illő” szöveggel még rosszabb
  (train 0,19 → 0,10). Marad az „Egyik sem”.
- **Rétegenként** (alap):

  | réteg | n | pontosság | nem-X pontosság | X-recall | hamis X | conf medián |
  |---|---|---|---|---|---|---|
  | train | 300 | 0,72 | 0,91 | 0,19 | 0,03 | 0,96 |
  | val-belső | 16 | 0,75 | 1,00 | 0,00 | 0,00 | 0,99 |
  | val-szállító | 47 | 0,70 | 0,83 | 0,33 | 0,00 | 0,96 |
  | T-belső | 21 | 0,76 | 0,94 | 0,20 | 0,00 | 0,98 |
  | T-szállító | 65 | 0,74 | 0,94 | 0,13 | 0,02 | 0,98 |
  | T-közeli | 85 | 0,75 | 0,94 | 0,19 | 0,00 | 0,95 |
  | T-távoli | 54 | 0,80 | 0,98 | 0,29 | 0,03 | 0,98 |

- **X-fajta szerint** (alap; `P(X)` = az X szűkített valószínűsége):

  | itemfajta | n | pontosság | conf medián | `P(X)` medián |
  |---|---|---|---|---|
  | nem-X, egyértelmű | 390 | 0,94 | 0,99 | 0,0013 |
  | nem-X, kétértelmű | 48 | 0,79 | 0,94 | 0,0057 |
  | X(a) kényszerített | 107 | 0,21 | 0,65–0,75 | 0,05–0,14 |
  | X(a) természetes | 8 | 0,38 | 0,93 | 0,07 |
  | X(b) új termék | 35 | 0,11 | 0,71–0,90 | 0,03–0,07 |

- **Következtetések:**
  - **A lexikai könnyűség a döntésben alig látszik.** A nem-X pontosság a tesztrétegekben
    0,94–0,98, a trainben 0,91; a T-közeli 0,94, holott ott a BM25 top-1 csak 0,44. A
    nehézség szinte teljes egészében az X-en van.
  - **Az alany szinte sosem tartózkodik** (X-recall ~0,19), de a `P(X)` X-itemeken
    ~20× (X(b)) – 100× (X(a)) nagyobb, mint az egyértelmű nem-X itemeken. Egy X-re ható L1 kalibráció (batch- vagy
    contextual bias, temperature) ebből sokat kihozhat. **Erős L1★ várható**, a H2-ben
    ezt kell az L3-nak megvernie.
  - **Az X(b) a legnehezebb:** új terméknél az alany magabiztosan egy rokon cikket
    választ (conf ~0,9). Ezt a kalibráció kevésbé javítja; itt várható az L3 legnagyobb
    hozzáadott értéke.
  - **Túlmagabiztosság:** conf medián 0,95–0,98, miközben ~26% hibás.

## K0d — HF (FP8-hű BF16) ↔ vLLM (FP8) L0-egyezés a pilot-itemeken

- **Top-címke egyezés: 553/588 = 94,0%** (Wilson 95% CI 91,8–95,7%). Az X-itemeken 86%.
  A probe-on 98% volt (50 item), de ott kevés az alacsony margójú item.
  - **Kapu (9. pont):** a 90–95%-os sávban van → **az F3-ban fake-quant kar** kell.
- **Az eltérés helye — csak alacsony margón:**

  | vLLM margó (top1 − top2) | n | egyezés |
  |---|---|---|
  | < 0,1 | 32 | 47% |
  | 0,1–0,3 | 63 | 76% |
  | 0,3–0,6 | 58 | 95% |
  | 0,6–0,9 | 97 | 100% |
  | ≥ 0,9 | 338 | 100% |

- **Szisztematikus X-eltolódás:** a log P(X) HF − vLLM különbség mediánja −0,37, átlaga
  −0,43. A HF ~31%-kal kisebb P(X)-et ad; az X-et választó arány vLLM 6,5%, HF 5,8%. A
  pontosság vLLM 0,736, HF 0,726. A 35 eltérésből 17-ben csak a vLLM, 11-ben csak a HF jó.
- **Értelmezés:** a valószínű ok az aktiváció-kvantálás. A vLLM a blokkos FP8-lineárisok
  előtt tokenenként, 128-as csoportokban FP8-ra kvantálja az aktivációt; a HF-bázis
  BF16-aktivációval számol. Kisebb források:
  - a BF16-ba kerekített dekvantált súly (~2⁻⁹ relatív hiba);
  - eltérő GDN-kernelek.
- **Következmény:**
  - A τ és a kalibráció motoronként külön rögzül a val-on (8. pont), így a szisztematikus
    X-eltolódást a küszöb elnyeli. A H3(c) motorok közti összevetésében viszont benne
    marad.
  - A fake-quant kar (HF-ben aktiváció-kvantálás az FP8-modulok előtt) várhatóan
    mindkét tünetet csökkenti. Mérendő az F3 előtt: K0d-2, a pilot-itemeken.

## Párok és splitek (645 pár)

| réteg | pilot pár | teljes léptékre vetítve (~7×) | cél (4.4) |
|---|---|---|---|
| train (2 sor/pár) | 357 | ~5 000 sor | ~16 000 |
| val-belső | 16 | ~110 | ~1 500 |
| val-szállító | 47 | ~330 | ~1 000 |
| T-belső | 21 | ~150 | ~1 500 |
| T-szállító | 65 | ~460 | ~1 500 |
| T-közeli | 85 | ~600 | ~800 |
| T-távoli | 54 | ~385 | ~800 |

- A nem-train pár **egy** sort kap, ezért a réteg itemszáma ≈ a párszám (+ X(a) pótlás).
- **A T-belső és a val-belső szűk keresztmetszet.** Csak akkor jön létre, ha a cikknek
  legalább 2 train-szállítója van, és még akkor is csak 50% eséllyel. A szállítószám-súlyok
  1/2/3 = 0,55/0,30/0,15.
- **Döntendő az F1 előtt** (a pilot riportjai és az MDE alapján):
  - több cikk;
  - a T-belső kitartás valószínűségének emelése (≥ 2 train-szállítónál mindig);
  - több sor nem-train páronként. Ez csak részben segít: a klaszter a cikk, a hatásos
    mintaméret a cikkszám.
