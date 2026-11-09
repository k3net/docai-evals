# Runbook 05: döntési fej a befagyasztott modell belső jelein, megbízhatósági fejjel és tartalmi állapotokkal

**A befagyasztott Qwen3.6 logitjain, rejtett állapotain és attentionjén tanított kis tartalmi és megbízhatósági fej
azonos precizitáson több helyes automatikus döntést ad-e, mint a kalibrált bázis? Kitartott feladatcsaládokon is,
és ha kell, kis célcsalád-mintával illesztve?**

- **Verzió:** v0.1 vázlat, 2026-10-28. A [forrásterv](dontesi-adapter-kutatasi-runbook.md) (v1.0, 2026-10-27) és Dani
  aznapi döntései alapján (14. pont). **Státusz:** az F0 folyamatban (2026-10-28); a 14. pont javaslatai jóváhagyva
  (Dani, 2026-10-28: „Mehet”). A [04-runbook](04-runbook.md) helyett fut (Dani, 2026-10-28); a 04 JEV-ága ide került
  (3.4).
- **Két lépcső:**
  - **05a — szűrő, új adat nélkül:** a 03 befagyasztott adatain és elhasznált rétegein.
  - **05b — megerősítő:** új, érintetlen feladatcsaládokon, csak ha a 05a kapuja átengedi (8.2).
  - A LoRA (a forrásterv L kara, P5) külön körben (05c), a 05b után.
- **Gép, alany, infrastruktúra:**
  - spark-dev, `Qwen/Qwen3.6-35B-A3B-FP8` (snapshot `95a723d0…`), MTP nélkül;
  - a jellemzők a HF-úton, az „FP8-hű BF16” bázison ([hf_kiolvaso.py](eszkozok/hf_kiolvaso.py), K0f-kapu);
  - vLLM v0.30.0 a 03-as kiolvasásokkal való kapcsolathoz, a JEV-hez és a kiszolgáláshoz;
  - leválasztott futások, egyszerre egy nagy GPU-folyamat. A HF BF16 bázis mellett nem fut vLLM-példány.
- **Bemenetek:**
  - a forrásterv; ebből a runbookból „forrásterv N.” néven hivatkozunk a pontjaira;
  - a 03 [eredménylapja](kor03/eredmenyek/F4/eredmenylap.md), a leíró bontásokkal (`f4_leiro03.json`) és a kétlépcsős
    feltáró elemzéssel (`f4_ketlepcso03.json`);
  - a 04 3.1 (JEV-35B) és 3.3 (X-leképezés) pontja;
  - a 00 L2a-eredménye (H4) és F5-terve (L4), a 01 [eredménylapja](kor01/eredmenyek/F4/eredmenylap.md).
- **Végtermékek (terv):**
  1. döntés arról, hogy a következő saját döntési modell fagyasztott fejre, LoRA-ra vagy a kalibrált bázisra épül;
  2. publikus fejek és kalibrátorok, ha az eredmény engedi (13. pont);
  3. a 05b-ben: új magyar döntési családok publikus adatkészlete, licencenként;
  4. tanulmány; negatív eredmény esetén is (a 03 mintájára).
- **Adatelv (Dani, 2026-10-28):** tanítás csak publikus és szintetikus adaton, mert az eredményt publikáljuk. Valós
  tenantadat csak értékelésre, aggregátumként.

> A hipotéziseket, a végpontokat, a szeleteket és a döntési szabályokat a teszt érintése előtt rögzítjük, a 03 7.10
> mintájára (`kor05/rogzites/`). Két rögzítés van: a **v1a** a 05a kitartott rétegeinek (HO-rétegek, célcsalád-minták)
> megnyitása előtt, a **v1b** az új 05b-családok megnyitása előtt. A kitartott rétegek HF-kivonása a v1a előtt is
> futhat, de csak pecsételve (`cache/k05/pecset/`, `pecset05.py`; 8.2, 10. pont F2). A nem kitartott szeletek (D_fit,
> D_dev, D_meta, D_cal) pecsét nélkül is kivonhatók (Napló, 2026-10-28).

---

## 0. Kiindulás

### 0.1. Amit a 00–04-ből tudunk

| lelet | következmény a 05-re | forrás |
|---|---|---|
| Az L2a (lineáris fej a 40. réteg rejtett állapotán, változatlan gerinccel) a 00 tesztjén +6,4 pont lef@95 (HF). Az X-fedés 0,43 → 0,86; a 27. réteg ugyanennyit ad | a C → H kérdés eloszláson belül eldőlt; az érdemi kérdés az átvitel | 00 F4, H4 |
| Kitartott családon a LoRA (01 L3, 03 G3) többet fogad el, de a precizitása 0,93 alá esik. A hiba teljes egészében az X-gold itemekből jön, a nem-X precizitás 0,99 | a fő kockázat az „egyik sem” döntés, nem az opcióválasztás | 01, 03 F4 |
| A val-on választott τ nem visz át más X-eloszlású rétegre; a 200 itemes célréteg-minta a CP-szabállyal kevés | célcsalád-illesztés kar, nagyobb mintával (3.3) | 03 H3 |
| Kétlépcsős döntés (az X a bázisból): kár nincs, nyereség sincs. A „mikor nem illik egyik sem” területfüggő | a megbízhatósági fejnek célterületi jel kell | 03 feltáró |
| A lef@95 szórásának 85–89%-a a τ-választásból jön; az MDE 6,5–6,8 pont rétegenként | a +3 pontos sikerfeltétel alulerős lehet; AURC társ-végpont (8.4) | 03 7.11 |
| HF ↔ vLLM top-címke-egyezés 94%, az X-itemeken 86% | a HF-en tanult fej a vLLM-FP8 kiszolgálásban újrakalibrálást kér (9. pont) | 00 K0d |
| `--enable-lora` mellett MoE-kernelváltás, a LoRA-t nem kérő forgalom ~6%-a billen | LoRA csak külön példányon | 00 H3 |
| A címkék egytokenesek (A–J = 32–41, X = 55); a névelő „A” ütközik, az „Egyik” → `E` | a P0 tokenauditja kész; az új 05b-promptokra megismételjük | 00 K0b |
| 40 réteg; minden 4. full attention (10 db), a többi 30 GatedDeltaNet. A config szerint (F0, 2026-10-28): rejtett dimenzió 2048, 16 query- és 2 KV-fej, fejdimenzió 256, részleges RoPE (0,25), kimeneti kapu az attention után | az A kar csak 10 rétegen mérhető; a 20., a 28. és a 40. réteg mindkét karhoz jó | 00 0. pont, F0 |
| A bírálók erős pozíciós torzítást mutatnak, és X-et alig választanak (1–2% a 25%-kal szemben). A Gemma bizonyos X-típusokon vak (NLI természetes X), a Mistral X-en szinte soha nem választ X-et | a Gemma ítélete triage, nem szűrő (4.3) | 00 4.8, 03 Napló |
| A tanárkapun mind a négy jelölt elbukott | a címke a konstrukcióból jön, utána emberi audit | 03 10. pont 14. |
| JEV-35B: 264 slotos fej, csupasz prompt, nincs „egyik sem” opció | külső referencia a 04 3.1 szerint | 04 0. pont |

### 0.2. A forrásterv és ez a runbook

**Változatlanul átvéve:**
- a cél és a kérdések (forrásterv 1.);
- az öt tartalmi állapot és a DEFER (3.);
- a C/H/A/L karok (4.);
- a D_* szeletek szerepe (5.2);
- a feature-kivonás elvei (7.);
- a fejek és a tanítás (8.);
- a kalibráció és a policy (9.);
- a mérőszámok (10.1–10.2);
- a kötelező ellenőrzések (13.).

**Eltérések, okkal:**
1. **Két lépcső:** a drága adatépítés csak igazolt jel után indul (Dani, 2026-10-28).
2. **Új kar: célcsalád-illesztés (T),** a 0.1 harmadik és negyedik sora miatt (Dani, 2026-10-28).
3. **JEV-35B külső referencia,** a 04 H1-e (Dani, 2026-10-28).
4. **A P0 nagy része kész** (0.1); ebből csak újraellenőrzés marad.
5. **A forrásterv 12. pontjának programjai a meglévő eszközökre képezve** (11. pont). A mappaszerkezet és a nevek a 03
   konvenciója szerint (`kor05/`).
6. **Rétegek: 20/28/40** (javaslat). A 75%-hoz a 28., mert full attention, és a 00 L2a 27-es mérésével szomszédos.
7. **Címkeaudit:** 600 példa a 300 helyett, mert a 2%-os felső korlát 300 példán legfeljebb 1 hibát enged (4.3). A
   második független ítélet a Gemma 4 (Dani, 2026-10-28).
8. **A +3 pontos sikerfeltétel mellé AURC társ-végpont** (javaslat, 8.4).
9. **Valós tenantadat csak értékelésre** (Dani, 2026-10-28).
10. **B2 kijelölve:** a G3 s1–s3 (03); a HO-terméken leíróként a 00 L3 is.
11. **Az AMBIGUOUS a 05b-ben lép be,** explicit egyválaszos szabállyal (2.3).
12. **A kiszolgálási keret** a vLLM v0.30 tényleges lehetőségei szerint (9. pont).

### 0.3. Amit nem tudunk, és ezért van ez a kör

1. Hordoz-e a befagyasztott modell belső állapota olyan jelet a kitartott családok X-döntéséről, amelyet a LoRA
   elrontott, a kalibrált bázis pedig nem használ ki?
2. Javítja-e a megbízhatósági fej a rangsort ott, ahol a τ-választás nem segít? A 03-ban a magabiztos X-hibák a rangsor
   elején álltak.
3. Mekkora célcsalád-minta kell ahhoz, hogy a 95%-os precizitás új családon is tartható legyen?
4. Ad-e az attention önálló többletet a rejtett állapotokon túl?
5. Kiszolgálható-e a nyertes fej a vLLM-en, vállalható költséggel?

---

## 1. Kutatási kérdések

| kérdés | hipotézis | 05a | 05b |
|---|---|---|---|
| K1 — van-e hasznos belső jel a logitokon túl? | H1: H javít C-hez képest | szűrő | megerősítő |
| K2 — ad-e önálló többletet az attention? | H2: A javít H-hoz képest | szűrő, ha kivitelezhető | megerősítő |
| K3 — átvisz-e a kiválasztott fej? | H3: a kiválasztott kar javít B1-hez képest érintetlen családokon | szűrő (elhasznált rétegeken) | megerősítő |
| K4 — segít-e az állapotok külön tanítása? | H4: kevesebb hamis SELECT a valódi negatív eseteken, mint összevont X-szel | szűrő | megerősítő |
| K5 — mennyit hoz a célcsalád-illesztés? | H5: a kiválasztott kar + T javít B1 + T-kal-hoz képest | szűrő | megerősítő |
| K6 — hol áll a JEV-35B? | H6: a 04 H1-e változatlanul | megerősítő (a 03-rétegeken) | leíró |

A kiszolgálás (forrásterv P4) külön kapu, nem hipotézis (9. pont).

---

## 2. Kimenet

### 2.1. Tartalmi állapot és végrehajtási döntés

- **Állapotok, az elsőbbség sorrendjében:**
  - `OUT_OF_SCOPE`
  - `MISSING_DATA`
  - `AMBIGUOUS`
  - `NO_MATCH` / `MATCH`

  Definíció és végrehajtható eredmény a forrásterv 3.1 táblázata szerint.
- **Mellékokok:** külön listában megőrizzük őket.
- **Egyenértékű válaszok:** ahol a feladat megengedi, elfogadható jelölthalmaz (`gold_set`) tárolódik, és nem
  címkézzük hibának.
- **DEFER:** külön mező; a döntési szabály eredménye (7. pont), nem azonos a `NO_MATCH`-csel.
- **Kimeneti API:** a forrásterv 3.1 JSON-ja. A `estimated_correctness` csak kalibráció és ellenőrzés után
  nevezhető helyességi valószínűségnek.

### 2.2. Leképezés a 03 adatára (05a)

A 04 3.3 szabálya: konstrukció és forrás szerint, itemenkénti átsorolás nélkül; vitás esetben a forrás jelölése dönt.

| 05 állapot | a 03 `x_type`, család | train (MVP v2) | HO-termék | HO-routing | HO-új |
|---|---|---|---|---|---|
| `MATCH` | `x_type` üres | 15 881 | a pontozott maradék | a pontozott maradék | a pontozott maradék |
| `NO_MATCH` | gold-drop; natural: `rag.relevancia`, `en.proc.state_perturbation`, `kie.osszeg` | 1037 | 975 | 271 | 91 |
| `MISSING_DATA` | missing-precondition; natural: `qa.milqa`, `nli.hucb` | 188 | 0 | 0 | 215 |
| `OUT_OF_SCOPE` | out-of-scope | 394 | 128 | 2183 | 0 |
| `AMBIGUOUS` | — (2.3) | 0 | 0 | 0 | 0 |

- A HO-oszlopok a pontozott X-gold itemek száma (a 04 táblája). Az `allapot05.py ellenoriz` mind a 12 számot
  pontosan visszaadja (F0, 2026-10-28).
- **A `nli.hucb` természetes X-e** („neutral”: a szövegből sem a következés, sem az ellentmondás nem dönthető el) a
  04-ben nem szerepelt, mert nincs az MVP v2-ben. A `qa.milqa` analógiájára `MISSING_DATA`; csak a D_dev-et és a
  test-id-ből képzett szeleteket érinti (7 + 26 item).
- **Kétértelmű itemek** (`ketertelmu`, 311 a trainben): `MATCH` a `soft` tagjaiból álló elfogadható halmazzal. A
  tanításban a halmaz összvalószínűségére számolt NLL a cél (forrásterv 8.1). A HO-rétegeken a 03 szabálya szerint nem
  pontozzuk őket.
- **Vékony szeletek:** a `MISSING_DATA` 188 tanító itemmel vékony, és csak a HO-újon mérhető. Az állapotszintű ítélet
  rá leíró.

### 2.3. AMBIGUOUS

- **A 05a-ban nincs `AMBIGUOUS` kimenet.** A 03 promptjai nem mondják ki, hogy pontosan egy válasz adható. Két
  egyenértékű jelölt mellett így a helyes címke `MATCH` elfogadható halmazzal. Egy konstruált `AMBIGUOUS` címke
  ellentmondana a promptnak.
- **A 05b-ben lép be,** két formában:
  - a családok `task_policy`-ja explicit egyválaszos szabályt tartalmaz, ahol ez a feladat része;
  - a forrásterv 5.3 ötödik változata (ellentmondó vagy többértelmű változat) az alapesettel egy szeletben.
- Dani döntése (2026-10-28): az `AMBIGUOUS` marad. Ez a 04 8. pont 3. döntését (a negyedik X-típus kihagyását)
  felülírja.

---

## 3. Karok

| kar | modell és kiolvasás | lépcső | szerep |
|---|---|---|---|
| **B0** | HF, perm-0, címkékre szűkített softmax + temperature | 05a, 05b | olcsó alap |
| **B1** | HF, L1★: négy permutáció átlaga + temperature | 05a, 05b | elsődleges referencia |
| **B1-T** | B1, a τ a célcsalád-mintán (a 03 H3(b) megfelelője) | 05a, 05b | a T-karok tisztességes referenciája |
| **B2** | G3 s1–s3: a 03 vLLM-kiolvasásai; a HO-terméken a 00 L3 is | 05a | történeti referencia, leíró (más motor) |
| **C** | befagyasztott modell + logitjellemzőkre tanított tartalmi és megbízhatósági fej | 05a, 05b | H1 alapja |
| **H** | C + rejtett állapotok (20., 28., 40. réteg) | 05a, 05b | H1 |
| **A** | H + attention-jellemzők ugyanezen a három rétegen | 05a, ha kivitelezhető; 05b | H2 |
| **K\*-X** | a kiválasztott kar (K\*), minden nem-`MATCH` állapot egy X-be összevonva | 05a, 05b | H4-abláció |
| **K\*-T-kal** | K\*, a Platt-kalibráció és a τ a célcsalád-mintán | 05a, 05b | H5 |
| **K\*-T-meta** | K\*, a megbízhatósági fej is a célcsalád-mintán (csoportos cross-fittinggel) | 05a, 05b | H5 |
| **JEV-a / JEV-b** | JEV-35B, vLLM, a 04 3.1 szerint | 05a, 05b | H6 |
| **L** | K\* + új LoRA | 05c | külön runbook |

- **A K\* kiválasztása:** C, H és (ha van) A közül a D_dev makro tartalmi NLL-je alapján (forrásterv 8.1). A
  HO-rétegek kiolvasásai addig pecsételve vannak (12. pont).
- **Az összevetés motorja:**
  - a B0, a B1, a C, a H és az A ugyanazon a HF-úton fut, a B0, a C, a H és az A ugyanabból a forwardból. Így a C–H és
    az A–H kontraszt motorfüggetlen;
  - a 03 vLLM-es L1★-kiolvasásai csak kapcsolódási pontként szerepelnek, az F1 HF ↔ vLLM-egyezésével együtt.

### 3.1. A jellemzők

- **C:** a forrásterv 7.2 listája egyetlen forwardból:
  - jelöltenként a címke teljes szókészletből számolt log-valószínűsége;
  - a jelöltekre és X-re normalizált eloszlás;
  - a top1–top2 rés, az entrópia, a jelöltszám;
  - az X pontszáma és a címketömeg.

  A B1 több sorrendjéből számolt stabilitás csak külön változatban, többletfuttatással.
- **H:** a forrásterv 7.3 szerint:
  - a prompt utolsó pozíciójának rejtett állapota a 20., a 28. és a 40. rétegen (a `hidden_states` indexei; 0 = az
    embedding);
  - jelöltenként a leírás utolsó tokenjének állapota és a span átlaga, ugyanezeken a rétegeken.

  Az indexeket a config `layer_types`-ából az F0-ban ellenőrizzük, és a manifestbe írjuk.
- **A:** a forrásterv 7.4 rögzített összesítései, ugyanazon a három (full attention) rétegen, fejenként, majd
  összesítve:
  - az utolsó promptpozíció → jelöltspan: összeg és tokenenkénti átlag;
  - a fejek közti szórás és a jelöltek közti koncentráció;
  - az adatspanra és az utasításspanra jutó tömeg;
  - kontrollváltozóként a span hossza és relatív pozíciója.

  A nyers maximum csak diagnosztika. Tetszőleges fejhalmazon nem keresünk.
- **Paraméterkeret:** a tényleges paraméterszámot közöljük. Ha a C és a H mérete érdemben eltér, egy paraméterben
  illesztett C-változat is fut (forrásterv 8.1).

### 3.2. A megbízhatósági fej

- A forrásterv 8.2 szerint, a rögzített tartalmi fejen, a D_meta-n.
- A cél a ténylegesen javasolt `MATCH`/`NO_MATCH` döntés helyessége.
- Minden kar saját, azonos felépítésű megbízhatósági fejet kap.
- A cross-fitting csak a K\*-T-meta karban szerepel.

### 3.3. Célcsalád-illesztés (T)

**Miért:** a 03-ban a τ nem vitt át (H3). A célréteg-minta pedig nem azért volt kevés, mert a τ-t rosszul
választottuk, hanem mert a magabiztos X-hibák a rangsor elején álltak. A τ újraválasztása a rangsoron nem változtat,
a megbízhatósági fej célcsalád-mintán való újratanítása igen.

**Két változat:**
- **T-kal:** csak a Platt-kalibrátor és a τ illeszkedik a célcsalád-mintán.
- **T-meta:** a megbízhatósági fej is újratanul a mintán, 5-szörös csoportos cross-fittinggel. A τ a cross-fittelt
  pontszámokon választódik.

**A minta:**
- rétegenként vagy családonként **500 alapeset** (`group_id`);
- hash-rang szerint, a predikciók megnézése nélkül húzva (az `f4_kalib03.py` módszere). A 03 meglévő 200-as mintái
  ennek részhalmazai;
- a mintába került alapesetek minden hipotézis tesztjéből kimaradnak;
- 500 alapesetnél ~0,6-os lefedettség mellett ~300 elfogadott döntés jön ki, ez fölötte van a policy 200-as
  alsó határának (7. pont).

**Tisztességes referencia:** a T-karokat a B1-T-hez mérjük, amely ugyanezen a mintán kapja a saját τ-ját.

**Valós tenantrétegen** a T illesztése belső műtermék. Nem publikáljuk, csak az eredménye kerül aggregátumként a
riportba (13. pont).

### 3.4. JEV-35B

A 04 3.1 változatlanul:
- bf16 checkpoint rögzített revízióval;
- a saját csupasz prompt bájtra;
- JEV-a: „Egyik sem” az utolsó betűzött opcióként. JEV-b: az „Egyik sem” opció nélkül;
- a fej bias-a a logprobokon;
- a mi kalibrációnk, a JEV `calibration.json`-ja leíróként.

A kimenet csak eval: nem lehet címke, soft target vagy szűrő. A HO-routingon szennyezett lehet, ezért a magyar rész
(HO-routing-hu) érzékenységi ítéletet kap.

---

## 4. Adat és szeletek

### 4.1. 05a: meglévő adat

A szeletek a `kor05/eszkozok/szeletek05.py` kimenetei (`kor05/adat/szeletek05.json`, 2026-10-28; seed
`k05:20261028`). A „pontozott” a nem kétértelmű itemek száma.

| szelet | forrás | item (pontozott) | `group_id` | pontozott állapotok: MATCH / NO_MATCH / MISSING / OOS |
|---|---|---|---|---|
| D_fit | a 03 MVP v2 train-je | 17 500 (17 189) | 16 313 | 15 570 / 1037 / 188 / 394 |
| D_dev | a `val03` | 3122 (3067) | 2720 | 2801 / 132 / 76 / 58 |
| D_meta | test-id + eval-kulso angol gerinc | 6000 (5796) | 4149 | 5088 / 480 / 141 / 87 |
| D_cal_prob | ugyanonnan | 3005 (2904) | 2101 | 2588 / 232 / 48 / 36 |
| D_cal_policy | ugyanonnan | 2997 (2907) | 2146 | 2574 / 261 / 24 / 48 |
| cel:ho-termek | HO-termék, 500 alapeset (cikk) | 1002 (839) | 500 | 619 / 206 / 0 / 14 |
| cel:ho-routing | HO-routing, megerősítő rész, 500 alapeset | 911 (902) | 500 | 592 / 35 / 0 / 275 |
| cel:ho-uj | HO-új, 500 alapeset | 500 (500) | 500 | 435 / 21 / 44 / 0 |
| teszt:ho-termek | a HO-termék maradéka | 4639 (3854) | 2364 | 2927 / 810 / 0 / 117 |
| teszt:ho-routing | a HO-routing maradéka (a T-hu-maradék nélkül) | 6728 (6659) | 3751 | 4467 / 242 / 0 / 1950 |
| teszt:ho-routing-hu | ennek magyar része (érzékenység) | 1080 (1011) | 1080 | 704 / 242 / 0 / 65 |
| teszt:ho-uj | a HO-új maradéka | 1900 (1900) | 1900 | 1629 / 80 / 191 / 0 |
| leiro:t-hu-maradek | a 03-ban is leíró | 2374 (2273) | 2374 | — |

- **A D_meta és a kalibrációs szeletek forrása:**
  - **Magyar rész:** a 03 test-id rétege (22 741 item a train-családokból; MATCH 19 423, NO_MATCH 2485,
    MISSING_DATA 447, OUT_OF_SCOPE 386). Csoportrétegenként arányos kvótával vettük.
  - **Angol rész:** az eval-kulso angol gerince (3100 item, a `LocalLLaMA/typed-decisions` teszt és a
    `fastino/fast-decisions`). Szeletenként ~25%, a D_fit és a `val03` angol arányához igazítva. X nincs benne.
  - Mindkettőt a 03-ban csak leíróan használtuk: modellt nem választottunk rajta.
  - A szeletek így a train-családok forgalmát tükrözik, nem a kitartott rétegekét. Ez a 03 val-τ helyzete; épp ezért
    van mellette T kar.
  - A `MISSING_DATA` nagyrészt a `qa.milqa`-ból jön (a kalibrációs szeletekben 24–48 item), állapotszinten csak
    leíró.
- **Átfedés:** a kapu szerint a létrehozott szeletek item- és csoportszinten diszjunktak egymástól és a
  D_fit/D_dev-től; a D_fit és a D_dev (a 03 splitje) között sincs átfedés. A szivárgás-auditot (8-gram és bge-m3) a
  03 a train ↔ minden eval-réteg párokra már lefuttatta; a 05a új forrást nem hoz be.
- **A célcsalád-minták** a 03 célréteg-kalibrációs mintáinak minden csoportját tartalmazzák. X-arányuk a teszt-maradékéval
  egyezik (a HO-routingon 34% / 33%, a HO-terméken 26% / 24%).
- **A HO-rétegek** a 03 v1-rétegei (`kor03/adat/f4/`, a 03 `items_eval` `ho-uj` része). A 03 kalibrációs mintái
  helyett a 3.3 500-as mintái maradnak ki.
- **Regressziós teszt:** a 00 és a 01 befagyasztott tesztjei a HO-termék és a HO-routing részei. Külön nem futnak.
- **Gépidő:**
  - perm-0 forward ~48 ezer itemen (D_fit a `fit` permutációval);
  - a B1-hez további három permutáció ~22 ezer itemen (a kalibrációs szeleteken, a célcsalád-mintákon és a teszten);
  - összesen ~113 ezer HF forward;
  - a mért ~0,37 s-os medián forwarddal (F0-smoke) ~12–15 óra, plus szeletenként 8 perc modellbetöltés.

### 4.2. 05b: új adat

**Követelmények** (forrásterv 5.1–5.4):
- 3–5 új feladatcsalád, családonként ≥ 1000–1500 független alapesettel: 500 a célcsalád-minta, 500–1000 a teszt;
- a split a változatok generálása előtt történik;
- a forrásterv 5.3 hat változata egy szeletben;
- természetes, irreleváns kérések valódi, közeli zavaró jelöltekkel;
- `task_policy` mező; `AMBIGUOUS` csak explicit egyválaszos szabály mellett;
- a forrásterv 5.4 sémája a 03 kulcsaival egyesítve: `content_state`, `gold_set`, `reason_tags`, `pair_id`,
  `label_origin`, `template_group_id`;
- a `gold_*` mezők és a bírálói adatok soha nem kerülnek promptba.

**Családtávolság-audit (a v1b előtt):**
- minden új család jelentés szerint különbözik a 03 csoportjaitól (03 5. pont). Egy új címkenév vagy új szállító nem
  új család;
- bge-m3 centroid-távolság a 03 csoportjaitól, kézi indoklással.

**Családjelöltek (javaslat, nem döntés):**

| család | feladat | természetes `NO_MATCH` / `MISSING_DATA` / `AMBIGUOUS` | forrás | kockázat |
|---|---|---|---|---|
| pénzügyi párosítás | bankkivonat-tétel → nyitott számla | nincs nyitott tétel / hiányzik a közlemény / két azonos összegű számla | szintetikus, nyilvános formátum | közel esik az entitásegyezéshez; aritmetika |
| szabálymegfelelés | költségtétel vagy kérelem → melyik szabálypont alá esik | egyik sem / hiányzó bizonylatadat / két szabálypont egyaránt illik | szintetikus szabályzat | közel esik a jogi csoporthoz |
| műszaki hibaelhárítás | tünet + mérések → ok vagy eljárás | egyik ismert ok sem / hiányzó mérés / két ok azonos tünettel | szintetikus | — |
| táblázatos sorválasztás | kérdés + táblázat → sor | nincs ilyen sor / hiányzó oszlop / holtverseny | szintetikus vagy nyílt tábla (licenc) | közel esik a QA-csoporthoz |
| ütemezés kényszerekkel | kérés + idősávok → sáv | egyik sem / hiányzó időtartam / két egyenértékű sáv | szintetikus | dátum-aritmetika; közel esik a HO-új `date.reasoning` családjához |

**Valós rétegek (csak értékelés; Dani, 2026-10-28):**

| réteg | feladat | megjegyzés |
|---|---|---|
| V-bank | bankkivonat-tétel ↔ számla, a felhasználói párosításból | a hiányzó párosítás nem automatikusan `NO_MATCH`: a gold zaját az F4-ben felmérjük |
| V-szállítólevél | bejövő szállítólevél ↔ bejövő számla (DOCAI-0171) | csak ha a párosítás addig elkészül |
| V-termék | számlasor → cikk (BA) | a HO-termék valós párja, nem új család; a riportban külön |

- A runbook és a riport tenantnevet nem tartalmaz, csak csoportkódot; a feloldás a `kor05/_belso/` alatt.
- Iratszöveg nem kerül Claude-kontextusba.
- A korpusz csak a spark-devre megy, és a kör végén onnan törlődik (a 02 mintájára).
- A jellemzők és a predikciók a spark-deven maradnak; a laptopra csak aggregátum jön vissza.

**A D_fit bővítése:**
- a 03 train-családjaira a forrásterv 5.3 ellentényes változatai: a döntő adat törlése (`MISSING_DATA`),
  ellentmondó változat (`AMBIGUOUS`, egyválaszos szabállyal), a kritikus részlet visszaállítása;
- a `MISSING_DATA` így nem marad 188 itemes.

**D_test_id (05b):** új, eddig nem húzott forrás-itemek a train-családokból, mert a 03 test-id a 05a-ban
kalibrációra megy.

**Generátor:**
- Apache-2.0 licencű, nem Qwen-családú, és nem a Gemma, mert a Gemma bíráló (4.3): Mistral Small 4 vagy
  Muse-Glimmer-30B;
- a Llama csak szűrhet;
- a címke a konstrukcióból jön.

### 4.3. Címkeaudit (05b)

- **Minta:**
  - 600 rétegzett példa (család × állapot), mind az öt állapottal;
  - a valós rétegeken külön ~200 rétegenként (javaslat);
  - a rétegzés nem függ a Gemma egyetértésétől.
- **Első ítélet: Dani, vakon.** Az `atnezes.py` felületén, gold, szavazat és mintaeredet nélkül (00 4.8 5.).
- **Második ítélet: a Gemma 4 26B-A4B-it** (Dani, 2026-10-28):
  - a spark-deven fut, gold nélkül, választást és bizalmat ad;
  - a `kiolvaso03` ids-módjával, a val-on illesztett temperature-rel;
  - az A–J és az X egytokenes a Gemma tokenizerében (03 Napló, 2026-10-09).
- **A Gemma ítélete triage, nem szűrő és nem címke** (00 4.8 3.). Az X-vakságát ismerjük; az egyetértéséből nem
  következtetünk a címke helyességére.
- **Adjudikáció:** eltéréskor Dani második köre a golddal és a generálási nyommal. A kimenet egyike: *gold hibás* /
  *én tévedtem* / *kétértelmű*. Csendes törlés nincs.
- **Kapu** (előre rögzítve): a javítás utáni maradék címkehiba egyoldali 95%-os felső korlátja ≤ 2%. A becslés az
  `atnezes.py osszesit` Jeffreys-poszteriorja Monte Carlóval.
  - Tájékoztatásul (Clopper–Pearson): 300 példán legfeljebb 1, 450-en legfeljebb 3, 600-on legfeljebb 6 hiba fér bele.
  - Bukáskor javítás és új audit következik, nem a modellfuttatás utáni átírás.
- **A végső teszt címkéinek javítása predikciók nélkül.**
- **Dani ideje:** 600 item × ~1 perc ≈ 10 óra, plus az adjudikáció.

---

## 5. Feature-kivonás

### 5.1. Út és prompt

- **Egy forward, minden jellemző:** egyetlen HF-forward adja a B0 címke-logprobjait, a C, a H és az A jellemzőit. A
  `hf_jellemzo05.py` a `hf_kiolvaso.py` bővítése, a K0f betöltési kapuval. A B1-hez a perm 1–3 külön fut, csak a
  kalibrációs szeleteken és a teszteken.
- **Prompt:**
  - `kozos03.render`, a 03 generikus kerete;
  - a HO-termék és a HO-routing a saját, natív promptjával, a 03 2. pontjának elsődleges módja szerint;
  - kikapcsolt gondolkodás;
  - az értékelésen a perm-0 az előre rögzített promptváltozat (forrásterv 9.);
  - a D_fit-en és a D_meta-n itemenként egy rögzített véletlen permutáció.
- **Spanok:**
  - a renderelt prompt karakter-offsetjeiből, a tokenizer `offset_mapping`-jével;
  - egységteszt: minden span visszafejtett szövege bájtra egyezik az opció szövegével;
  - kézi ellenőrzés 30 példán, publikus adaton (forrásterv P1).
- **Döntési pozíció:** a prompt utolsó tokenje a kikapcsolt gondolkodás előtagja után, ugyanaz, amelyet az L2a
  olvasott.

### 5.2. Attention-kivonás

- **Saját attention-függvény a transformers `AttentionInterface`-ében:**
  - a kimenetet változatlanul az SDPA adja;
  - mellette a három full-attention rétegen kiszámolja az utolsó query-sor softmaxát a K-mátrixra, fejenként;
  - az összesítéseket (3.1) azonnal képzi.

  N × N mátrixot nem tárolunk. A GB10-en nincs flash_attn, és a teljes eager attention drága.
- **Ellenőrizve (F0, 2026-10-28; transformers 5.6.0, `modeling_qwen3_5_moe.py`):**
  - az attention az `ALL_ATTENTION_FUNCTIONS.get_interface`-en át fut, a RoPE utáni q/k-val;
  - a kimeneti kapu (`attn_output * sigmoid(gate)`) az attention-függvény után jön, így a súlyokat nem érinti;
  - a GQA-t (16 / 2 fej) a burkoló a transformers `repeat_kv`-jének megfelelő `repeat_interleave`-vel kezeli.
  - **Smoke:** 20 D_dev-item. A logprobok az instrumentált és a nem instrumentált úton 20/20-ban bájtra azonosak. A két
    ismétlés között nincs billenés, a jellemzők eltérése 0. A medián forward ~0,37 s, a memóriacsúcs ~65 GiB; az
    instrumentáció +0,1 GiB.
- **Kapu (forrásterv P1):** az instrumentált és a nem instrumentált forward kimenete bájtra azonos. Ha a kivonás nem
  oldható meg, az A kar eredménye: „nem vizsgálható ebben a stackben”.

### 5.3. Tárolás

- **Becsült méret:** ~5–15 GB fp16 a 05a-ban.
- **A publikus adat jellemzői** a laptopra is szinkronizálhatók.
- **A valós rétegek jellemzői** a spark-deven maradnak, és a kör végén törlődnek.

---

## 6. Fejek és tanítás

**Változatlanul a forrásterv 8. pontja:**
- **Felépítés:** 128 dimenziós közös vetítés, egy 128 egységes GELU-réteg, 0,1 dropout. Minden jelöltet ugyanaz a
  pontozóháló értékel, maszkolással. A globális állapotok a promptvégi reprezentációból és a jelöltösszesítésekből
  jönnek.
- **Veszteség:** keresztentrópia. Elfogadható halmaznál a halmaz összvalószínűségére számolt NLL. Extra
  confidence-veszteség nincs.
- **Optimalizálás:** AdamW, LR {1e-4, 3e-4}, weight decay 0,01, batch 64, legfeljebb 20 epoch, patience 3, gradient
  clip 1,0.
- **Seedek:** 17, 42, 73.
- **Kiválasztás:** a D_dev makro tartalmi NLL-je alapján; az állapotonkénti hibákat közöljük.
- **Standardizálás** csak a D_fit alapján.
- **A megbízhatósági fej** a rögzített tartalmi fejen, a D_meta-n, BCE-vel.
- **Futtatás:** a fejek kicsik. A HF-modell kirakása után a spark-dev GPU-ján tanulnak, nem a kivonással párhuzamosan.

---

## 7. Kalibráció és döntési szabály

- **Kalibráció és döntési szabály:** a forrásterv 9. pontja.
  - A tartalmi softmax temperature-t kap a D_cal_prob-on, a megbízhatósági fej Platt-kalibrációt ugyanott.
  - A pontszámokat nem szorozzuk össze.
  - Egy közös τ szolgál a SELECT-re és a NONE-ra; mindkét akció pontosságát külön is jelentjük.
- **A τ szabálya** (D_cal_policy, illetve a T-karoknál a célcsalád-minta): a legnagyobb lefedettségű küszöb, amelynél
  a vállalt döntések pontosságának egyoldali 95%-os Clopper–Pearson alsó korlátja ≥ 0,95, legalább 200 elfogadott
  független alapeseten.
  - Tájékoztatásul: 200 elfogadott döntésnél legfeljebb 4 (pontosság ≥ 0,98), 300-nál legfeljebb 8 (≥ 0,973),
    500-nál legfeljebb 16 hiba (≥ 0,968) fér bele.
  - Ha nincs ilyen τ, a kar eredménye: „nincs igazolt munkapont”, 0% lefedettséggel. A pontossága nem értelmezett.
- **A B1 és a B1-T** ugyanezzel a szabállyal kapja a τ-t, a saját kalibrált pontszámán.

---

## 8. Mérőszámok, hipotézisek, kapuk

### 8.1. Mérőszámok

- **Elsődlegesek:** a forrásterv 10.1:
  - SELECT-lefedettség és -precizitás;
  - SELECT+NONE lefedettség és precizitás;
  - hamis SELECT a gold `NO_MATCH`-en, és külön a többi nem-`MATCH` állapoton;
  - hamis NONE a gold `MATCH`-en.

  A régi L1★ X-kimenete `NO_MATCH`-javaslat, a küszöb alatti kimenete DEFER. Az eredeti metrikát is közöljük.
- **Szűrési mérőszámok** a 04 2. pontjából:
  - **lef@p95:** a lefedettség, ha a τ-t a rétegen magán illesztjük. Felső korlát, csak a 05a-ban;
  - **MTX:** a magabiztos téves elfogadás az X-gold itemeken.
- **Diagnosztika:** a forrásterv 10.2:
  - risk–coverage görbe és AURC, SELECT-re és SELECT+NONE-ra külön;
  - confusion matrix és makro F1;
  - Brier, NLL és reliability diagram;
  - sorrend-, parafrázis- és jelöltszám-stabilitás; a páros példák helyes váltása;
  - családonkénti bontás; a HO-új `kie.osszeg` családja külön sorban (a 03 tanulsága);
  - paraméterszám, kivonási idő, p50/p95, memória.
- **Statisztika:** az `f4_elemzes03.py` módszere:
  - hierarchikus bootstrap, seed × klaszter, ahol a klaszter család → alapeset;
  - 10 000 ismétlés;
  - a τ replikánként újra; a kalibrációs szeletek is újramintázva;
  - páros különbségek, kétoldali p, Holm.

### 8.2. 05a: szűrő és kapu

- **Sorrend:**
  1. a K\* és minden hiperparaméter kiválasztása a D_dev-en;
  2. a v1a rögzítése;
  3. a HO-kiolvasások pecsétjének feloldása.
- **Fő szűrő-kontrasztok** a HO-rétegek maradékán, párosítva:
  - **S3:** K\* − B1;
  - **S5:** K\*-T-meta − B1-T és K\*-T-kal − B1-T.
- **Továbblép, ha** a három HO-rétegből legalább kettőn (v1a D1 (b), Dani, 2026-10-29):
  - a ΔAURC (SELECT+NONE) negatív, és a páros CI nem tartalmazza a 0-t;
  - a K\* precizitásának pontbecslése a saját τ-jánál ≥ 0,93, ha van munkapontja;
  - az MTX nem szignifikánsan nagyobb.

  Az S3 és az S5 külön ítéletet kap („T nélkül továbblép” / „csak T-vel továbblép”). A Δ SELECT-lef@95 és a lef@p95
  leíró. Az AURC a réteg minden pontozott itemjén számol, a DEFER a rangsor végén hibaként (v1a-vázlat, D1).
  - **Ok:** a D_dev-próbán a τ-szabály (CP-alsó ≥ 0,95, ≥ 200 elfogadott) mellett a Δlef@95 bimodális, mert a karok a
    határon billegnek. Az AURC τ-független (v1a-vázlat, D1 és 5. pont).
- **Leíró a 05a-ban:**
  - S1: H − C;
  - S2: A − H;
  - S4: K\* − K\*-X;
  - B2; lef@p95; családonkénti és X-típusonkénti bontás; a HO-routing-hu.
- **Kapu a 05b-be:** legalább egy „továbblép”. Ha nincs, a 05 a 05a-val lezárul. A lelet negatív folytatásként
  publikálható: a befagyasztott modell belső jele sem viszi át az X-döntést kitartott családra.

### 8.3. H6: JEV-35B (megerősítő, a 03-rétegeken)

- A 04 5.1 szabálya, egy cserével: JEV-a − L1★ és JEV-a − G3, Holm a 2 × 3 összevetésre, ugyanazokkal a
  feltételekkel és ítéletkategóriákkal, de az elsődleges végpont a ΔAURC (S+N), a Δlef@95 leíró (v1a D5, a D1-gyel
  összhangban).
- **Referenciák:** a 03 vLLM-kiolvasásai (L1★: `kor03/eredmenyek/F2/qwen_eval.jsonl`; G3 s1–s3: `F4/k03v2_g3_s*`), így
  a JEV-vel azonos motoron. A kalibrációjuk a 05 eljárása: temperature a D_cal_prob-on, τ a D_cal_policy-n.
- **Egy eltérés:** a mérés a HO-rétegek maradékán fut, hogy minden kar ugyanazokon az itemeken mérjen. A 04 v0.1-e
  nem volt rögzítve, így ez nem utólagos változtatás.
- **A rétegek a JEV számára érintetlenek:** a JEV-ről semmit nem hangoltunk rajtuk.

### 8.4. 05b: megerősítő (a v1b-ben véglegesítendő)

- **Sikerfeltételek:** a forrásterv 10.3 szerint:
  - az OOD SELECT- és SELECT+NONE precizitás pontbecslése ≥ 95%, az alsó korlát ≥ 93%;
  - legalább +3 pont SELECT-lefedettség B1-hez képest, pozitív páros intervallummal;
  - a hamis SELECT a `NO_MATCH`-en legfeljebb +1 ponttal romolhat;
  - legalább 200 elfogadott független teszteset.
- **Javaslat:**
  - **AURC társ-elsődleges végpont** a H3-ban és a H5-ben. A lef@95 szórását a 03-ban a τ-választás uralta (MDE 6,5–6,8
    pont), így egy +3 pontos valódi hatás „elégtelen bizonyíték” maradhat;
  - **a v1b előtt MDE-szimuláció** a 05a számaiból, az `mde03.py` módszerével. Ha a +3 pont alulerős, a v1b vagy
    nagyobb D_cal_policy-t és célcsalád-mintát kér, vagy az AURC-t teszi elsődlegessé.
- **Holm-család:** H1 (H − C), H2 (A − H), H3 (K\* − B1), H5 (K\*-T − B1-T). A H4 a forrásterv szerint abláció, külön.
- **Hipotézisenkénti verdikt:** támogatott / nem támogatott / elégtelen bizonyíték. A valós rétegek külön ítéletet
  kapnak, és nem részei az OOD-családállításnak.

---

## 9. Kiszolgálás (F7)

- **C: ma kiszolgálható.** A `kiolvaso03` ids-módja a vLLM-ből a jelen lévő címkék teljes szókészletes logprobjait adja
  (`logprob_token_ids`). Ebből minden C-jellemző kiszámolható.
- **H, csak a 40. réteg utolsó pozíciója: elvi út, kipróbálandó.**
  - A fej első rétege lineáris vetítés. Ez 128 többletsorként egy checkpoint-másolat `lm_head`-jébe írható (a 04 3.2
    elve), és a logprobjaik különbségeiből a vetítés visszaállítható.
  - Korlát: a többletsorok a teljes szókészletes normalizálást is módosítják. A C kar teljes szókészletes jellemzőjét
    ezért korrekcióval vagy külön kiolvasásból kell venni. A `--max-logprobs` korlátját is ellenőrizni kell.
- **H a középső rétegeken, a jelöltspanok és az A:** a vLLM v0.30 standard API-ja ezeket nem adja. A 00 F5 két útja
  egyike sem próbált:
  - a #59543 backportja;
  - a v0.30 `extract_hidden_states` spekulatív módszere.

  Ha egyik sem működik, az „ugyanazon a példányon” állítás csak a C-re és a 40. rétegre tartható. A HF-sidecar csak
  kutatási referencia.
- **Motorváltás:** a HF-BF16-on tanult fejet a vLLM-FP8 jellemzőin újra kell kalibrálni, külön serving-kalibrációs
  szeleten. Új serving holdout kell (forrásterv P4); a K0d 94%-os egyezése ezt indokolja.
- **LoRA (05c):** csak külön példányon. A spark-alphára és a spark-betára nem telepítünk; minden F7-mérés a spark-deven
  fut.
- **Kapu:** a forrásterv P4-e változatlanul. Egyforwardos H-nál legfeljebb +25% p95 idő B0-hoz képest, és legfeljebb
  +10% csúcsmemória ugyanazon a beállításon. A négyforwardos B1-hez viszonyított összköltséget külön közöljük.

---

## 10. Fázisok és kapacitás

| fázis | lépcső | forrásterv | tartalom | idő |
|---|---|---|---|---|
| F0 | 05a | P0 | Manifest: modell, tokenizer, image, snapshot, `layer_types`. A 2.2 leképezése (`allapot05.py`) egységtesztekkel. A szeletek (`szeletek05.py`), a célcsalád-minták, a szivárgás- és duplikátumaudit. A `hf_jellemzo05.py` (spanok, attention-függvény, C). A fej, a megbízhatósági fej, a kalibrátor, az elemző. A JEV promptépítője és a smoke a kártya példáin. A v1a vázlata | ~4–5 nap, GPU csak a smoke-okra |
| F1 | 05a | P1 | Instrumentációs pilot ~1000 D_dev/D_fit iteme, HO nélkül: span-ellenőrzés 30 példán; instrumentált és nem instrumentált forward bájtra; 100 item × 5 ismétlés; memória és p95 instrumentációval és nélküle; HF ↔ vLLM perm-0 egyezés (a K0d megismétlése) | ~1 gépnap |
| F2 | 05a | — | Kivonás a teljes 05a-adaton (~123 ezer forward, 4.1); a HO-kiolvasások pecsételve. A JEV-35B letöltése és kiolvasása (04 F1) | ~2–3 gépéjszaka |
| F3 | 05a | P2–P3 (szűrő) | A C/H/A fejek, a megbízhatósági fejek, a kalibráció, a K\* választása; a v1a rögzítése; a pecsét feloldása; az elemzés, a szűrő-ítélet, a H6, a 05a eredménylapja | ~2–3 nap |
| F4 | 05b | P2 | Az új családok építése, a családtávolság-audit, a valós rétegek kijelölése, a 600-as audit, a befagyasztás | ~2–3 hét; Dani ~10–12 óra |
| F5 | 05b | P2 | A fejek újratanítása a bővített D_fit-en, a kalibráció, az MDE-szimuláció, a v1b rögzítése | ~1 hét |
| F6 | 05b | P3 | Egy lezárt értékelési kör, ítéletek, eredménylap | ~2–3 nap |
| F7 | 05b | P4 | Kiszolgálás (9. pont) | ~1 hét; a backport-kísérlettől függ |
| — | 05c | P5 | LoRA, külön runbook: azonos adaton címkekiolvasás vs. fej, befagyasztott vs. LoRA-s gerinc (a 04 G3-fej karja itt kap helyet) | később |

A 05a naptári ideje ~2 hét.

---

## 11. Eszközök

| a forrásterv tervezett fájlja | meglévő eszköz | 05-ös feladat |
|---|---|---|
| `freeze_protocol.py` | `kor03/eszkozok/befagyaszt03.py`, `eszkozok/lib.sh: record_env` | `befagyaszt05.py`: a v1a/v1b manifestje; a HO-pecsét: `pecset05.py` (kész) |
| `build_splits.py` | `eszkozok/split_audit.py`, `kor03/eszkozok/szivargas03.py`, `eszkozok/duplikatum_audit.py`, `kor03/eszkozok/f4_kalib03.py` | `szeletek05.py`: D_* szeletek és célcsalád-minták, csoportosan |
| `audit_labels.py` | `eszkozok/atnezes.py`, `kor03/eszkozok/kiolvaso03.py` (Gemma, ids-mód) | a 4.3 protokollja, a Gemma második ítéletével |
| `extract_features.py` | `eszkozok/hf_kiolvaso.py` (`--hidden-layers`, K0f) | `hf_jellemzo05.py`: spanok, attention-sor, C-jellemzők |
| `train_content_head.py` | `eszkozok/l2a_szonda.py` | `fej05.py` |
| `make_correctness_labels.py`, `train_reliability_head.py` | — | `megbizhatosag05.py` (a T-meta cross-fittinggel) |
| `calibrate.py` | `eszkozok/elemzes.py` (L1-karok), `kor03/eszkozok/f4_kalib03.py` | `kalib05.py`: temperature, Platt, CP-τ |
| `evaluate.py`, `paired_statistics.py` | `kor03/eszkozok/f4_elemzes03.py`, `f4_leiro03.py`, `mde03.py` | `elemzes05.py`, `mde05.py` |
| `benchmark_serving.py` | a 00 F4 `perf_*` mérései, `kiolvaso03.py` | `kiszolgalas05.py` (F7) |
| `render_report.py` | a 03 `eredmenylap_gepi.md` generálása | `riport05.py` |
| — (JEV) | — | `jev05.py`: promptépítő, bias, kiolvasás (a 04 F0 JEV-része) |
| futtatás | `eszkozok/lanc.sh`, `folytat.sh`, `sync.sh`, `lib.sh`; a Gemma indítása a `kor03/eszkozok/f2g_smoke.sh` mintájára | `kor05/eszkozok/` |

- **Mappa:** `kor05/` alatt `eszkozok/`, `adat/`, `eredmenyek/F0…F7/`, `rogzites/v1a/`, `rogzites/v1b/` és `_belso/`.
- **Elemenként tárolandó:** a forrásterv 12. pontjának listája.
- **Teljes ügyféldokumentum** nem kerül publikus logba.

---

## 12. Szabályok és korlátok

- **Tanítóadat:** csak publikus és szintetikus. Valós tenantadat csak értékelésre, a 4.2 szabályaival (Dani,
  2026-10-28).
- **Modellek szerepe:**
  - a Qwen-család (a JEV-35B is) nem generál és nem ellenőriz; csak alany;
  - a Llama szűrhet, de a kimenete nem lehet címke vagy soft target;
  - a JEV kimenete csak eval;
  - a Gemma bíráló, ezért a 05b auditált családjait nem generálja.
- **Vakság:**
  - a 05a HO-kiolvasásai a v1a rögzítéséig pecsételve (`pecset05.py`): a könyvtár a konténer root-jáé, 700-as
    joggal; a `fej05.py` és az elemzők betöltője a v1a rögzítése (`kor05/rogzites/v1a/ROGZITES.json`) nélkül megáll;
    a sha256-manifest a feloldáskor igazolja, hogy a kiolvasás nem változott;
  - a 05b új családjainak tesztje a v1b-ig érintetlen;
  - teszt-címke semmilyen választásban nem szerepel (forrásterv 13.).
- **Futtatás:**
  - leválasztva (`nohup setsid`), egyszerre egy nagy GPU-folyamat;
  - a HF BF16 bázis mellett nincs vLLM-példány;
  - terhelés alatt is ≥ 15 GB szabad memória kell;
  - a spark-deven nincs mode-switch, `worker-mode.sh up` és `docker compose up` az `/opt/docai` alól.
- **Adatvédelem a valós rétegeken:**
  - csoportkód; a szöveg nem kerül Claude-kontextusba;
  - csak aggregátum hagyja el a spark-devet;
  - a kör végén minden tenantadat és jellemző törlődik a spark-devről.

---

## 13. Publikálás

- **Publikálható, ha az eredmény engedi:**
  - a publikus és szintetikus adaton tanított fejek és kalibrátorok;
  - a 05b új családjainak adatkészlete, a licenc-konfigurációk szerint (03 9. pont);
  - az eredmények, a valós rétegek aggregátumával együtt;
  - a JEV aggregált eredményei.
- **Nem publikálható:**
  - valós tenantitem és -jellemző;
  - a valós rétegen illesztett T-kalibrátor vagy megbízhatósági fej;
  - tenant- és ügyfélnév.
- **Szabály (javaslat):**
  - a fej publikus kiadása feltételezi, hogy a 05b H3-ja vagy H5-je „támogatott”;
  - negatív eredmény a 03 mintájára publikálható;
  - mindkettőről Dani dönt.

---

## 14. Döntések

**Dani, 2026-10-28:**
1. **A 05 a 04 helyett fut,** a 05a/05b lépcsővel.
2. **Az `AMBIGUOUS` marad.** Ez a 04 8. pont 3. döntését felülírja; a belépésének módja a 2.3-ban.
3. **A célcsalád-illesztés kar bekerül** (3.3).
4. **A JEV-35B-ág fut** (3.4, 8.3).
5. **Valós tenantadat értékelésre igen, tanításra nem,** mert az eredményt publikálni akarja.
6. **A címkeaudit második független ítélete a Gemma 4** (4.3).

**Örökölt:**
- a Llama szűrése nem tanítás (2026-10-07);
- a Qwen-család nem generál (2026-10-10);
- a JEV kimenete csak eval (04 7.);
- a spark-alphára és a spark-betára nem telepítünk.

**Jóváhagyva (Dani, 2026-10-28: „Mehet”):**
- a rétegek: 20/28/40 (3.1);
- a 05a szeletei (4.1): D_fit = MVP v2, D_dev = `val03`, D_meta és a kalibráció a test-id-ből;
- a célcsalád-minta: 500 alapeset, a T-kal és a T-meta (3.3);
- az `AMBIGUOUS` csak a 05b-ben (2.3);
- a 05a szűrő-szabálya és a 05b-kapu (8.2);
- az audit: 600 példa; Dani vak első ítélete, a Gemma második, Dani adjudikációja (4.3);
- az AURC társ-elsődleges végpontként és az MDE-szimuláció a v1b előtt (8.4);
- a 05b családjelöltjei és a valós rétegek (4.2);
- a publikálási szabály (13.).

---

## 15. Kockázatok

- **Elhasznált szűrőrétegek:** a 05a ítélete feltáró; megerősítő állítás csak a 05b-ből jöhet.
- **Motorhatás:** a HF-BF16 és a vLLM-FP8 közti eltérés (K0d: 94%) a kiszolgálásban a fej előnyét elviheti; erre van
  az F7 újrakalibrálása.
- **A célcsalád-minta szivárgása:** a T-karok a mintán illeszkednek. A tesztből a minta alapesetei kimaradnak, de a
  családon belüli sablonok közösek. A riportban jelezzük, és a valós rétegeken külön ítélet van.
- **Vékony állapotok:** a `MISSING_DATA` (188 tanító, 215 teszt item) és az `AMBIGUOUS` (a 05a-ban nincs) ítélete
  alulerős.
- **Az A kivitelezhetősége:** ha az attention-függvény nem illeszthető be bájtazonosan, az A nem vizsgálható; ez nem
  negatív eredmény (forrásterv 13.).
- **Kiszolgálhatóság:** a középső rétegekhez a vLLM-módosítás nem biztos, hogy elkészül. Akkor a H csak a 40. rétegen
  élesíthető.
- **A Gemma bírálói torzítása:** az X-vakság és a pozíciós torzítás miatt az audit nem támaszkodhat az egyetértésre
  (4.3).
- **Dani ideje:** a 600-as audit ~10 óra; a 05b üteme ezen múlik.
- **Valós gold zaja:** a felhasználói párosítás hiánya nem `NO_MATCH`. A V-bank gold-szabályát az F4-ben rögzítjük, és
  a valós rétegeket külön auditáljuk.
- **Az aritmetikai családok** (`kie.osszeg`, pénzügyi párosítás, ütemezés): gondolkodás nélküli egytokenes döntésben
  minden kar gyenge. Külön jelentjük, és egyetlen kitartott rétegként nem dönthetnek.

---

## 16. Források

- **Forrásterv:** [dontesi-adapter-kutatasi-runbook.md](dontesi-adapter-kutatasi-runbook.md) (v1.0, 2026-10-27); a
  külső forrásai [S1]–[S7] a 16. pontjában.
- **Saját:**
  - 00: [00-runbook.md](00-runbook.md), [eredménylap](eredmenyek/F4/eredmenylap.md);
  - 01: [01-runbook.md](01-runbook.md), [eredménylap](kor01/eredmenyek/F4/eredmenylap.md);
  - 03: [03-runbook.md](03-runbook.md), [eredménylap](kor03/eredmenyek/F4/eredmenylap.md);
  - 04: [04-runbook.md](04-runbook.md);
  - a publikált tanulmány: https://docai.hu/kutatas/hol-erdemes-tanitani;
  - a negatív eredmény: https://docai.hu/blog/altalanos-dontesi-adapter-negativ-eredmeny.
- **Külső:**
  - JEV-35B: https://huggingface.co/autotrust/JEV-35B;
  - Gemma 4 26B-A4B-it: https://huggingface.co/google/gemma-4-26B-A4B-it.

---

## Napló

- **2026-10-28 — v0.1 vázlat.**
  - **Alap:** a forrásterv (v1.0, 2026-10-27), a 00–04 körök áttekintése és Dani aznapi döntései (14. pont 1–6.).
  - **A forrástervhez képest:** a 0.2 eltérései. Főbb pontok:
    - két lépcső;
    - célcsalád-illesztés kar;
    - JEV-ág;
    - a P0 meglévő részei;
    - eszköz-hozzárendelés;
    - 600-as audit a Gemmával;
    - az `AMBIGUOUS` csak a 05b-ben;
    - kiszolgálási keret.
  - **Ellenőrizve (aggregátumon):**
    - az MVP v2 (17 500 item, 16 313 `group_id`; X-típusok: gold-drop 962, out-of-scope 394, natural 172,
      missing-precondition 91; 311 kétértelmű);
    - a `val03` (3122 item, 2720 `group_id`);
    - a test-id (22 741 item, 9 csoport) összetétele;
    - a HO-rétegek mérete (`kor03/adat`).
  - **Számolva:** a 4.3 és a 7. pont Clopper–Pearson-határai.
- **2026-10-28 — jóváhagyás és F0 (Dani: „Mehet”; a 14. pont javaslatai elfogadva).**
  - **Környezet** (`kor05/eredmenyek/F0/kornyezet.json`):
    - snapshot `95a723d0…`; a config, a tokenizer és a chat-sablon sha256-ja rögzítve;
    - `lora-train:2` (`sha256:9d0da0ae…`, transformers 5.6.0, torch 2.11.0+cu130);
    - vLLM v0.30.0 (`sha256:8a69ffad…`);
    - a BF16 bázis megvan (`cache/qwen36-fp8hu-bf16`, 65 GB);
    - a rétegtérkép a 0.1 szerint.
  - **Spark-dev:** a reggel indított `vllm-qwen38-flash-next-uncensored` konténert Dani engedélyével leállítottuk
    (`docker stop`; a konténer megvan, újraindítható). Utána 118 GB szabad.
  - **Állapot-leképezés** (`kor05/eszkozok/allapot05.py`, 14 egységteszt): a 04 3.3 mind a 12 darabszáma egyezik. Új
    szabály: a `nli.hucb` természetes X-e `MISSING_DATA` (2.2).
  - **Szeletek** (`szeletek05.py`): a 4.1 táblázata; a diszjunktsági kapu átment. A spark-deven a 03-as itemfájlok
    sha256-ja egyezik a manifestben rögzítettel.
  - **Spanok** (`hf_jellemzo05.py spanok`, CPU, a tréning-image-ben):
    - 96 608 prompt (minden 05a-szelet, perm 0 és 1), hiba 0;
    - tokenszám: medián 321, p99 1297, max 7908;
    - a 30 példás kézi minta (`kor05/eredmenyek/F0/spanok/minta30.md`) rendben: minden opció-span a teljes leírást
      fedi, az utolsó prompttoken mindenütt a `'\n\n'` döntési pozíció.
    - Forrás-sajátosság, nem javítjuk: néhány BFCL-live irrelevancia-item kérése egyetlen vezérlőkarakter (`\x16`); a
      01 és a 03 is így mérte.
  - **GPU-smoke** (`hf_jellemzo05.py egyezes`, 20 item): 5.2. A modellbetöltés 8 perc.
  - **Javítás:** a 4.1 korábbi mondata, hogy a `MISSING_DATA` a test-id-ben „szinte hiányzik”, téves volt: a
    missing-precondition 12 item, de a `qa.milqa` és a `nli.hucb` természetes X-ével a `MISSING_DATA` 447.
  - **Protokoll-pontosítás:**
    - **Mi változott:** a v1a a kitartott rétegek (HO, célcsalád-minták) HF-kivonása előtt kötelező, nem minden
      kivonás előtt. A nem kitartott szeletek kivonása (K05F2A, `k05f2a_vezenylo.sh`) előre futhat.
    - **Ok:** a vakság a HO-rétegek kimenetén múlik. A D_fit, D_dev, D_meta és D_cal jellemzői a v1a döntéseit nem
      árulják el, a gépidőt viszont párhuzamosítják a fejek kódjának írásával.
    - **Változatlan:** a K\* és a hiperparaméterek kiválasztása (8.2) a v1a után, a D_dev-en történik.
  - **Fej** (`fej05.py`): a C/H/A tartalmi fej a 6. pont szerint. Szintetikus egységtesztek (`test_fej05.py`, CPU, a
    tréning-image-ben) átmentek: a maszkolt opciók valószínűsége 0, a beültetett jelet megtanulja, a C kar rejtett
    vektor nélkül fut.
- **2026-10-28 17:40 — F1, az egyezés-mérés** (`hf_jellemzo05.py egyezes`, 100 D_dev-item × 5 ismétlés,
  `kor05/eredmenyek/F1/egyezes/egyezes.json`): **átment.**
  - Az instrumentált és a nem instrumentált út logprobjai 100/100-ban bájtra azonosak.
  - Az öt ismétlés között nincs top-címke-billenés, a rejtett állapotok és az attention-összesítések eltérése 0.
  - Költség: p50 0,353 s / 0,347 s, p95 0,577 s / 0,568 s (nem instrumentált / instrumentált); memóriacsúcs
    64,92 / 65,21 GiB (+0,3 GiB, +0,4%).
  - Az F1-ből még hátravan a HF ↔ vLLM perm-0 egyezés (a K0d megismétlése, vLLM-példánnyal, a HF-futások után); ez
    nem kapuja a HF-kivonásnak.
- **2026-10-28 17:41 — K05F2A indul** (`k05f2a_vezenylo.sh`): a D_dev, a D_fit (`fit`), a D_meta, a D_cal_prob és
  a D_cal_policy jellemzői, valamint a két kalibrációs szelet B1-permutációi; 50 630 forward.
  - **Az első shard** (17:56, D_dev, 1000 item): 116 MB jellemző (~116 KB/item), a várható vég 22:57.
  - **Ellenőrzés (CPU):**
    - 0/1000 hibás: a tenzoralakok rendben, NaN nincs;
    - a span-nevek a címkékkel egyeznek;
    - az attention-sor tömege a spanokon fejenként 1 (±0,02), vagyis a spanok a teljes promptot lefedik;
    - a B0 top-1 pontossága 0,797 ezen a részen.
- **2026-10-28 20:45 — éjszakai lánc** (K05EJ, `kor05/eszkozok/k05_ejszaka.sh`; Dani: reggel 9-ig számoljon a
  laptop nélkül).
  - **Sorrend:**
    1. megvárja a K05F2A-t; ha elbukik, egyszer újraindítja (a kész shardok kimaradnak);
    2. a C, a H és az A tartalmi fej a D_fit → D_dev jellemzőin (2 LR × 3 seed), majd a jóslatuk a D_dev-en, a
       D_meta-n és a két D_cal-on. GPU-n, HF-modell nélkül; 01:30 után új kar nem indul, hogy a K05F2B elférjen;
    3. K05F2B: a négy HO-teszt, a három célcsalád-minta és a T-hu-maradék kivonása, előbb kanonikusan (19 134
       forward, jellemzőkkel), aztán a B1-permutációkkal (57 402 forward), pecsételve;
    4. párhuzamosan a JEV-35B letöltése: `autotrust/JEV-35B`, revízió `a5d0d580bb9324f0f4c07dcba5c5ca91e813e7c9`,
       71,9 GB. A méretet és a 16 LFS-fájl sha256-ját a HF API-ból előre rögzített lista ellen ellenőrzi
       (`kor05/adat/jev_varhato.json`, `jev_letolt05.py`).
  - **Pecsét** (`pecset05.py`, 12. pont): a K05F2B a `cache/k05/pecset/` alá ír. A könyvtár a konténer root-jáé,
    700-as joggal, a spark-dev felhasználója nem látja. A `fej05.load_dir` a v1a rögzítése nélkül megáll a pecsét
    alatti úton. A futás végén a `lezar` sha256-manifestet ír (`kor05/rogzites/pecset/K05F2B.json`: fájlnevek,
    méretek, hash-ek, a kivonó kódjának hash-e; kiolvasás nincs benne). A naplók csak darabszámot és időt írnak.
  - **Pontosítás (felülírja a délutáni bejegyzést):**
    - **Mi változott:** a v1a a HO-kiolvasások megnyitása előtt kötelező. A kivonásuk pecsételve már előtte is
      futhat.
    - **Ok:** ez a 10. pont F2–F3 sorának („a HO-kiolvasások pecsételve”, majd „a v1a rögzítése; a pecsét
      feloldása”) és a 8.2 sorrendjének eredeti szövege; a délutáni, szigorúbb megfogalmazás ellentmondott nekik.
    - **Javítás:** a délutáni bejegyzés „a v1a után” fordulata hibás. A K\* és a hiperparaméterek választása a 8.2
      szerint a v1a előtt, a D_dev-en történik.
  - **Füstpróba valós adaton** (CPU, 1000 D_fit → 1000 D_dev item, `fej05.py tanit`): a C és az A kar lefut; az A
    paraméterszáma 957 444. A NLL-értékek 1000 itemen nem értelmezhetők (a ritka állapotokból 15–21 item jut).
  - **Tokenhossz a kitartott szeleteken** (perm 0, átlag): HO-termék 367, HO-routing 216, HO-routing-hu 328,
    HO-új 684, T-hu-maradék 314 (a D_fit-en 403). A K05F2B forwardjai így átlagban nem lassabbak a K05F2A-énál (a HO-új hosszabb, de kicsi).
  - **Óra:** a `py()` konténere eddig UTC-ben írta a várható véget, ezért a délutáni „22:57” helyi időben 23:57 volt.
    A `lib.sh` mostantól a gazdagép `/etc/localtime`-ját csatolja (a már futó K05F2A még UTC-ben ír).
  - **Indult** 20:44-kor. Becsült menet: K05F2A vége ~23:25, a fejek ~00:05-ig, a K05F2B ~08:15–08:50-ig (a
    B1-permutációk sebessége még nem mért). A JEV-letöltés ~20 MB/s-mal megy, ~22:00-ra kész.
  - **Reggel (laptop):** `eszkozok/sync.sh status`, majd `sync.sh back` és `sync.sh back05`. A fejek összegzése:
    `kor05/eredmenyek/F3/fejek/{C,H,A}/fej.json`; a D_dev-jóslatok: `kor05/eredmenyek/F3/predikciok/`; a lánc
    naplója: `logs/k05ej.log`, `k05fej.log`, `k05f2b.log`, `k05ej_jev.log`. A K05F2B, ha még fut, újraindítás nélkül
    befejeződik; ha elakadt, a `k05_ejszaka.sh` újraindítva a kész részeket kihagyja.
- **2026-10-29 07:15 — az éjszakai lánc eredménye.**
  - **Lefutott, hiba nélkül** (a naplókban 0 hiba, a spark-dev nem indult újra):
    - a K05F2A 23:26-kor kész (50 630 forward);
    - a fejek 23:28–23:44 között: a C ~1 perc, a H és az A ~7,5 perc a GPU-n, a jóslatokkal együtt;
    - a JEV-35B 21:02-re lent van: 16 perc letöltés, 44 fájl, 71,9 GB, a méret és a 16 LFS-sha256 egyezik;
    - a K05F2B 07:12-kor 70 414 / 76 536 forwardnál tart (a T-hu-maradék B1-része), a várható vég 07:45.
  - **A fejek a D_dev-en** (`fej.json`; makro tartalmi NLL, három seed átlaga, a választott LR-rel):

    | kar | paraméter | LR | makro NLL | MATCH | NO_MATCH | MISSING_DATA | OUT_OF_SCOPE |
    |---|---|---|---|---|---|---|---|
    | C | 34 948 | 1e-4 | 1,725 | 0,40 | 1,21 | 2,92 | 2,38 |
    | H | 952 580 | 1e-4 | 0,499 | 0,36 | 0,39 | 0,99 | 0,26 |
    | A | 957 444 | 1e-4 | 0,503 | 0,37 | 0,35 | 0,97 | 0,33 |

    - A legjobb epoch a H-nál és az A-nál a 2–3., a train NLL ~0,27–0,31: a fej gyorsan túltanul, a patience 3 állítja
      meg. A NO_MATCH NLL-je seedenként 0,24–0,60 között szór (132 item).
    - A 3. pont szabálya szerint (a D_dev makro NLL-je) a K\* a H lenne; az A különbsége a seedszórásnál kisebb. A
      választás formálisan a v1a-ban rögzül.
  - **Diagnosztika a D_dev-en** (`ddev_osszevet`, egyszeri; nem kalibrált, a τ a dev-en magán: in-distribution felső
    korlát, nem a v1a mérőszáma). MATCH/X-re összevont pontosság, seedátlag:

    | kar | összes | MATCH | NO_MATCH | MISSING_DATA | OUT_OF_SCOPE | lef@p95 (dev) |
    |---|---|---|---|---|---|---|
    | B0 | 0,839 | 0,841 | 0,841 | 0,842 | 0,724 | 0,661 |
    | C | 0,849 | 0,864 | 0,654 | 0,794 | 0,644 | 0,690 |
    | H | 0,869 | 0,868 | 0,874 | 0,882 | 0,914 | 0,764 |
    | A | 0,871 | 0,869 | 0,884 | 0,877 | 0,902 | 0,753 |

    A D_dev a D_fit családjaiból jön. A 03 tanulsága szerint az in-distribution nyereség nem jelzi előre a kitartott
    családokat, ezt a 05a HO-rétegei döntik el.
- **2026-10-29 délelőtt — az F1 lezárása, a JEV smoke-ja, a megbízhatósági fej, a kalibráció, az elemző próbája,
  a v1a vázlata.**
  - **F1, HF ↔ vLLM** (`egyezes_vllm05.py`, `kor05/eredmenyek/F1/hf_vllm/egyezes.json`): a HF-sorokat a 03 F2
    vLLM-kiolvasásaival vetettük össze; új vLLM-futás nem kellett, mert ugyanazok az (item, perm) párok.
    - 33 130 pár: a D_dev perm 0, a D_meta és a D_cal kanonikus, a D_cal B1-permutációi.
    - Egyezés: a top-1 96,7%-ban, az X-döntés 99,0%-ban azonos. A magabiztos (≥ 0,9) billenés 0,10%, a TV-távolság
      átlaga 0,035.
    - A pontosság HF-en 0,7343, vLLM-en 0,7344. A K0d 94%-ánál jobb egyezés. **Az F1 lezárva.**
  - **JEV-35B:**
    - **Licenc:** a rögzített revízión a kártya és a `LICENSE` szerint Apache-2.0; a CC-BY-NC a JPT-35B-A3B-é.
    - **Smoke** (`jev05.py smoke`, `kor05/eredmenyek/F0/jev_smoke/`): **átment.**
      - A címketokenek a fej choice-verbalizereivel azonosak.
      - A repó saját szervere (`serve_decide.py`, `/v1/decide`) és a mi kiolvasásunk 61 esetben (a README példája és
        30 D_dev-item, JEV-a és JEV-b) legfeljebb 6,7·10⁻⁸-nal tér el, a prompt tokenszáma azonos.
      - A két kiolvasási út (logprob_token_ids, allowed_token_ids) között az eltérés 6,7·10⁻⁸.
      - A README példájára a válasz „billing”, 0,9997-es valószínűséggel.
    - **Eltérés a 04-től:** a kártya ezen a revízión nem közöl esetenkénti kimenetet, így a „közölt döntések
      visszaadása” (04, kockázatok) helyett a repó saját szerverével vetettünk össze. Ez szigorúbb ellenőrzés.
    - **Kiolvasás** (`k05jev_vezenylo.sh`): GPU-memória 0,65, 6,4 kérés/s 32 párhuzamos kéréssel, ~188 ezer kérés.
      Sorrend: D_dev, D_cal_prob, D_cal_policy, majd a négy HO-teszt a pecsét alá (`K05JEV.json`).
  - **Megbízhatósági fej** (`megbizhatosag05.py`, `test_megbizhatosag05.py`; CPU-n, a JEV mellett):
    - A D_meta-n tanul, a belső validációs rész 20%-os, alapesetenként hash-elve.
    - Javaslatok seedenként: a C-nél SELECT ~5700, NONE ~290, DEFER ~10; a H-nál és az A-nál SELECT ~5450, NONE ~350,
      DEFER ~200.
    - A belső validáció AUROC-ja: C 0,81, H 0,86, A 0,86. A választott LR: C 3e-4, H és A 1e-4.
  - **Kalibráció és τ** (`kalib05.py`, `kor05/eredmenyek/F3/kalib/kalib_proba.json`):
    - A τ a D_cal_policy-n készült, alapesetenként egy itemmel (2140 alapeset).
    - A B0-nak, a B1-nek és a C-nek nincs igazolt munkapontja. A B1 200 legmagabiztosabb döntéséből 8 hibás, a
      szabály legfeljebb 4-et enged.
    - A H lefedettsége 0,35–0,43 (seedenként), a pontosság 0,963. Az A lefedettsége 0,35–0,40.
    - A szigorú és az enyhe helyesség itt azonos τ-t ad.
  - **Elemző** (`elemzes05.py`): a próba a D_dev-en futott, 2000 replikával (`kor05/eredmenyek/F3/proba_ddev/`).
    - A Δ SELECT-lef@95 a τ-szabály miatt bimodális. A H − B0 CI-je [−0,08; +0,55], mert a karok a CP-határon
      billegnek.
    - A ΔAURC (S+N) éles: H − B0 −0,030 [−0,052; −0,011]; H − C −0,016 [−0,029; −0,005]; A − H −0,002 [−0,008;
      +0,005].
  - **A v1a vázlata:** `kor05/rogzites/v1a/v1a-vazlat.md`. Benne a K\* = H, és öt nyitott döntés:
    - D1: az AURC társ-elsődleges végpont a 05a-ban;
    - D2: a NONE szigorú helyessége;
    - D3: a T-meta felépítése;
    - D4: a K\*-X;
    - D5: a JEV kalibrációja.
- **2026-10-29 ~09:00 — Dani: „D1-D5 ok”; önellenőrzés a döntésfüggő kód előtt** (`kor05/rogzites/v1a/v1a-vazlat.md`
  5. pont).
  - **Vakság:** rendben (pecsét, kapu, csoport-diszjunktság, csak nem kitartott adaton számolt számok).
  - **Javítva:** az AURC definíciója (a DEFER a rangsor végén hibaként; a 03-konvenció leíró), a bővülő CP-tábla,
    a JEV-b temperature-illesztése. A D_dev-próba az új AURC-val: H − B0 −0,024 [−0,041; −0,008], p = 0,002.
  - **Feloldva:** a H6 végpontja is a D1 (b) szerint (ΔAURC elsődleges, Δlef@95 leíró).
  - **A rögzítéskor a 8.2 és a 8.3 szövege módosul** (AURC társ-elsődleges a 05a-ban is; a pillanatképben).
  - A JEV kiolvasása 11,8 kérés/s-mal halad (prefix-cache); a D_dev kész, a D_cal_prob 09:00-ra, a HO-rétegek
    ~11:30-ra a pecsét alá.
- **2026-10-29 délután — a döntésfüggő kód kész; a rögzítésre vár.**
  - **Javítás menet közben:** a döntésfüggő kód az önellenőrzés utáni körben elmaradt, és csak Dani rákérdezése
    (12:16) után indult.
  - **K\*-X:** `fej05.py --kar HX`, a megbízhatósági fej és a kalibráció is. A D_cal_policy-n a munkapont 0,40–0,44.
  - **T-ág:** a `megbizhatosag05.py tmeta` (D3) és a `kalib05.t_tables` (B1-T, H-T-kal, H-T-meta). Az `elemzes05`
    rétegenként és karonként saját τ-szelettel dolgozik, a bootstrap a célcsalád-mintát is újramintázza.
  - **H6-referenciák:** az L1v (a 03 vLLM-es L1★-ja) és a G3 s1–s3 címkekarként, a 03 kiolvasásaiból (ismétlődő
    (item, perm) pár nincs).
  - **Ítéletszabály:** az elemzőben a D1 (b) szerint; Holm a szűrőrétegeken, a H6-ra a 2 × 3-ra.
  - **Rögzítés:** a `befagyaszt05.py` (manifest, rögzítés, ellenőrzés) és a `k05a_elemzes_lanc.sh` kész.
  - **Teljes próbafutás** a nem kitartott D_cal_policy-n, csereszeletekkel: 13 kar, 10 kontraszt, hiba nélkül.
  - **8.2 és 8.3:** átírva a D1 és a D5 szerint.
  - **Hátra van** Dani „mehet”-je a rögzítésre (a pecsét nyitása).
