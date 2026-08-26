# Mérés D — lefordíthatatlan fogalmak (a fordítási hipotézis direkt tesztje)

16 fogalom × 3 nyelv + 16 kontrollszó × 3 nyelv. A `native` és `distortion` komponenseket a bíráló komponensenként külön értékelte; a `manual_*` oszlop a saját ellenőrző körömé (runbook §4b: mind a 48 kötelező) — ebben a futásban **96 cella** ellenőrző felülírás.

## D1 — komponens-lefedettség

| forrásnyelv | prompt nyelve | native | distortion | hurokba esett |
|---|---|---|---|---|
| hu (8 fogalom) | hu ← **forrásnyelv** | 17/22 = **77%** [57%–90%] | 3/16 = 19% | 0/8 |
| hu (8 fogalom) | en | 16/22 = **73%** [52%–87%] | 2/16 = 12% | 1/8 |
| hu (8 fogalom) | zh | 13/22 = **59%** [39%–77%] | 5/16 = 31% | 7/8 |
| zh (8 fogalom) | hu | 24/24 = **100%** [86%–100%] | 1/16 = 6% | 0/8 |
| zh (8 fogalom) | en | 23/24 = **96%** [80%–99%] | 1/16 = 6% | 0/8 |
| zh (8 fogalom) | zh ← **forrásnyelv** | 22/24 = **92%** [74%–98%] | 0/16 = 0% | 3/8 |

### Párosított összevetés — forrásnyelv vs. angol (fogalmanként, előjelteszt)

- **hu-forrású fogalmak (n=8):** a forrásnyelv 1 fogalomnál jobb, 0-nél rosszabb az angolnál (előjelteszt p = 1.000) — átlagos különbség +0.12 komponens.
- **zh-forrású fogalmak (n=8):** a forrásnyelv 0 fogalomnál jobb, 1-nél rosszabb az angolnál (előjelteszt p = 1.000) — átlagos különbség -0.12 komponens.

## D1 kontroll — a hétköznapi szavak definíciója

Ha a nyelvek közti különbség a kontrollszavaknál IS megvan, akkor nem a lefordíthatatlanságból jön, hanem a modell általános nyelvi teljesítményéből.

| prompt nyelve | jó | részben | rossz | hurokba esett |
|---|---|---|---|---|
| hu | 9 | 6 | 1 | 0/16 |
| en | 16 | 0 | 0 | 0/16 |
| zh | 14 | 2 | 0 | 2/16 |

⛔⛔ **A kontroll fog: a magyar általánosan gyengébb** — hétköznapi szóra is csak 56% a jó definíció, szemben az angol 100%-kal (kínai 88%). A D1 nyelvek közti különbségét tehát **nem szabad** a lefordíthatatlanságnak tulajdonítani: a különbség jó része a generálás általános minőségéből jön.

## ⛔⛔ Az önértékelő toldalék — egy nyelvfüggő mérési hiba, ami majdnem eldöntötte a D1-et

A base modell a válasz után gyakran **saját feladat-promptot** ír (*„请判断回答是否正确…正确”*, *„A single-select problem: Is the question answered…”*), és ez a bírálót félrevezeti: egy mért esetben (撒娇/zh) a bíráló a toldalékra ítélt („a válasz csak a »helyes« szót tartalmazza”), és 0 komponenst adott egy olyan válaszra, amiben az első komponens egyértelműen benne van.

A jelenség **nyelvfüggő**: hu 0/86 = 0% · en 0/86 = 0% · zh 0/86 = 0% — tehát pont azokat a cellákat rontja, ahol a D1 meglepő eredménye született.

A `src/clean_answers.py` utólag levágja (generálni nem kell újra, a toldalék nem része a válasznak), és a bírálók a `text_clean` mezőt kapják. **A javítás hatása mérve:** a kínai-forrású fogalmak kínai nyelvű komponens-lefedettsége **58 % → 71 %**, a Mérés A `HU/en` cellája pedig 27 % → 20 % (ott a toldalék *fel*felé torzított). Ezt a lépést a módszertanban le kell írni.

## D3 — SAE: a fogalom vagy az angol közelítőszó felé húz?

A 10. rétegen (a Mérés C többlet-csúcsa), `union` halmazon. Három Jaccard fogalmanként:

| fogalom | forrás | J(forrás, saját angol kérdés) | J(forrás, angol KÖZELÍTŐSZÓ) | J(forrás, harmadik nyelv) |
|---|---|---|---|---|
| kaláka | hu | **0.528** | 0.367 | 0.521 |
| szeretet / szerelem | hu | **0.491** | 0.320 | 0.491 |
| magázás / tegezés | hu | **0.487** | 0.343 | 0.519 |
| puszi / csók | hu | **0.529** | 0.338 | 0.507 |
| honfoglalás | hu | **0.509** | 0.359 | 0.523 |
| sógor | hu | **0.419** | 0.329 | 0.385 |
| névnap | hu | **0.406** | 0.287 | 0.379 |
| ráér | hu | **0.479** | 0.349 | 0.452 |
| 关系 (guanxi) | zh | **0.464** | 0.434 | 0.392 |
| 面子 (mianzi) | zh | **0.482** | 0.412 | 0.403 |
| 缘分 (yuanfen) | zh | **0.475** | 0.400 | 0.401 |
| 热闹 (renao) | zh | **0.488** | 0.428 | 0.423 |
| 江湖 (jianghu) | zh | **0.490** | 0.408 | 0.419 |
| 撒娇 (sajiao) | zh | **0.471** | 0.393 | 0.417 |
| 上火 (shanghuo) | zh | **0.459** | 0.363 | 0.396 |
| 加油 (jiayou) | zh | **0.473** | 0.393 | 0.409 |

### D3b — a konfundálás-mentes változat (⛔ KONTROLLSZAVAS: ld. lent)

⛔⛔ **2026-08-26, bírálat nyomán:** ez a szakasz a fogalomhoz rendelt KONTROLLSZÓ (`control.en`: help, friendship…) promptját hasonlítja, NEM az `en_approx` közelítőszóét (mutual aid, love…) — tehát „szemantikai szomszéd”-tesztként olvasandó, a fordítási hipotézis tesztje az újramérés: `05_d3b_ujrameres.md` (`analyze_d3b.py`, protokoll: `d3b-protokoll.md`).

⛔⛔ A fenti tábla **nem tiszta**: a fogalom saját angol kérdése szó szerint tartalmazza magát a fogalmat (*„What does the Chinese concept '关系' (guanxi) mean?”*), az angol közelítőszó-prompt viszont nem — a magasabb Jaccard jöhet puszta token-egyezésből is. Tiszta kérdés: a forrásnyelvi fogalom közelebb van-e a **saját** angol közelítőszavához, mint **más fogalmak** angol közelítőszavaihoz? Itt egyik oldalon sincs szó szerinti egyezés.

| fogalom | J(forrás, SAJÁT angol közelítőszó) | J(forrás, MÁS fogalmak közelítőszavai, átlag) | többlet |
|---|---|---|---|
| kaláka | 0.367 | 0.370 | **-0.004** |
| szeretet / szerelem | 0.320 | 0.315 | **+0.005** |
| magázás / tegezés | 0.343 | 0.326 | **+0.018** |
| puszi / csók | 0.338 | 0.314 | **+0.024** |
| honfoglalás | 0.359 | 0.353 | **+0.006** |
| sógor | 0.329 | 0.302 | **+0.027** |
| névnap | 0.287 | 0.273 | **+0.014** |
| ráér | 0.349 | 0.327 | **+0.022** |
| 关系 (guanxi) | 0.434 | 0.406 | **+0.028** |
| 面子 (mianzi) | 0.412 | 0.401 | **+0.011** |
| 缘分 (yuanfen) | 0.400 | 0.398 | **+0.002** |
| 热闹 (renao) | 0.428 | 0.400 | **+0.029** |
| 江湖 (jianghu) | 0.408 | 0.388 | **+0.020** |
| 撒娇 (sajiao) | 0.393 | 0.394 | **-0.001** |
| 上火 (shanghuo) | 0.363 | 0.381 | **-0.018** |
| 加油 (jiayou) | 0.393 | 0.370 | **+0.023** |

Átlagos többlet: **+0.0127** — 13 fogalomnál pozitív, 3-nél negatív (előjelteszt p = 0.021).

⚠️ **A saját angol közelítőszó felé mérhető vonzás van** — ez a torzulás mechanisztikus jele, a fordítás-hipotézis mellett szól.


**Átlag:** saját angol kérdés 0.478 · angol közelítőszó 0.370 · harmadik nyelv 0.440.
A forrásnyelvi fogalom 16 esetben a SAJÁT angol kérdéséhez áll közelebb, 0 esetben az angol közelítőszóhoz (előjelteszt p = 0.000).

⭐ **A fogalom a saját fordításához húz, nem a szegényebb angol közelítéshez** — ez a fordítás-hipotézis ellen szól: a modell nem az angol közelítőszón keresztül éri el a fogalmat.

## D2 — logit lens: megjelenik-e az angol közelítés?

⛔ A Mérés B kimutatta, hogy a **naiv** logit lens a 0–23. síkon olvashatatlan ezen a modellen (a top-20 72%-a nem szó), ezért az eredeti kérdés („felbukkan-e a »noisy« a 15–25. rétegben?”) vele **nem tesztelhető** — csak a 24–31. sík.

⚠️ A **tuned lens** ezt a tartományt olvashatóvá tette (nem-szó arány 72% → 43%), tehát a kérdés most tesztelhető. **De:** a fordítót a végső eloszlás KL-jére tanítottuk, ezért előrehúzhat olyan tokent, ami a rétegben még nincs ott (ld. `03_meres_b_tuned.md` — a várt válasz mediánrangja már a 0. síkon 100 alá esik). A tuned oszlop tehát **felső korlát**, a naiv oszlop **alsó korlát**.

| fogalom | angol közelítés | naiv, 24–31. sík | tuned, első sík | tuned, hány síkon |
|---|---|---|---|---|
| kaláka | mutual aid / barn raising / helping out | – | – | – |
| szeretet / szerelem | love | – | – | – |
| magázás / tegezés | formal vs informal 'you' (T–V distinction) | – | – | – |
| puszi / csók | kiss | – | – | – |
| honfoglalás | conquest (of the Carpathian Basin) | – | – | – |
| sógor | brother-in-law | – | – | – |
| névnap | name day | – | – | – |
| ráér | to have time / to be free | – | – | – |
| 关系 (guanxi) | connections / networking | – | – | – |
| 面子 (mianzi) | face / reputation | – | – | – |
| 缘分 (yuanfen) | fate / destiny (in relationships) | – | – | – |
| 热闹 (renao) | lively / bustling / noisy | – | – | – |
| 江湖 (jianghu) | underworld / martial-arts world | – | – | – |
| 撒娇 (sajiao) | to act cute / to act spoiled | – | – | – |
| 上火 (shanghuo) | to have internal heat / inflammation | – | – | – |
| 加油 (jiayou) | go for it / come on / cheer up | – | – | – |

**0/16 fogalomnál** bukkan fel az angol közelítés valamelyik szava a nem-angol prompt KÉSŐI rétegeiben a naiv lensszel; a tuned lensszel — bármelyik síkon — **0/16**.

⭐⭐ **A KÖZÉPSŐ (0–23.) síkon egyetlen találat sincs: 0/32 prompt a naiv, 0/32 a tuned lensszel.** Épp ez volt a fordítási hipotézis legdirektebb tesztje — a Mérés B óta tudjuk, hogy a naiv lens itt vak, de a tuned lens **látja** ezt a tartományt (a 0–23. sík átlagos nem-szó aránya 72% → 43%), és **ott sem** hozza elő az angol közelítőszót. A talált néhány eset mind a 24. sík FÖLÖTT van, tehát abban a tartományban, ahol a modell már a válasz nyelve felé fordul.

⚠️ Ellenpróba-korlát: a tuned lens top-20-a **koncentráltabb** (4097 vs. 7081 különböző token az egész korpuszon), tehát kevesebb szót lát — a 0 találat részben ebből is jöhet. A naiv lens 0-ja viszont nem ilyen: az ő top-20-a tágabb, csak épp olvashatatlan.

⛔⛔ **A null-eredmény bizonyító ereje korlátos** — ld. a kör kontroll-riportját ([05_d2_kontroll.md](05_d2_kontroll.md), `src/d2_control.py`): az ANGOL prompton futó pozitív kontroll szerint a műszer érzékenysége alacsony, több fogalom jelöltszava a korpusz egyetlen top-20-jában sem fordul elő, és a szóillesztés írásjel-érzékeny (tisztított matcherrel a nulla törhet). A D2 tehát gyenge evidencia a fordítási útvonal ellen, nem perdöntő.


![D2](../figures_instruct/05_D2_angol_kozelites_savok.png)

![D1](../figures_instruct/05_D1_komponens_heatmap.png)

## A Mérés D ítélete a fordítási hipotézisről

A runbook három jóslatot fogalmazott meg. A mérés a **köztes** képhez áll legközelebb, de a „fordítás angolon keresztül” változatot két független jel is cáfolja:

1. ⭐⭐ **D3b (a konfundálás-mentes SAE-teszt): nincs vonzás az angol közelítőszó felé.** A forrásnyelvi fogalom nem áll közelebb a saját angol közelítéséhez (0.370), mint más fogalmak közelítőszavaihoz — az átlagos többlet +0.0127 (előjelteszt p = 0.02). Ha a modell az angol közelítésen keresztül érné el a fogalmat, itt pozitív, szignifikáns többletnek kellene lennie.
2. ⭐⭐ **D2: a KÖZÉPSŐ (0–23.) síkon 0/32 prompt találja meg az angol közelítőszót — és a tuned lensszel is 0/32.** A naiv lens ebben a tartományban vak (Mérés B), de a tuned lens LÁTJA (nem-szó arány 43%), és ott sem hozza elő. A mindössze 0/16 találat a **24. sík fölött** van, tehát ott, ahol a modell már a válasz nyelve felé fordul. Ez a fordítási hipotézis legdirektebb tesztje, és megbukik rajta.
3. ⚠️ **D1: a viselkedés szintjén az angol a legjobb** mindkét forrásnyelvnél (hu-forrás: hu 77% vs en 73%; zh-forrás: zh 92% vs en 96%) — **de ez a jel három konfundálóval terhelt**: (a) a kontroll szerint a magyar generálás általánosan gyengébb, (b) a kínai kérdés más keretet ad („一词” = szó, nem fogalom), (c) az önértékelő toldalék nyelvfüggően rontotta a bírálatot.

**Összefoglalva:** a *reprezentáció* szintjén nincs nyoma annak, hogy a modell az angol közelítésen keresztül érné el a lefordíthatatlan fogalmakat; a *viselkedés* szintjén viszont az angol válasz a leggazdagabb — de ezt a különbséget nagyrészt a nyelvi generálás minősége és a kérdés keretezése magyarázza, nem a fogalom hozzáférési útja.

⛔ **Korlát:** 8+8 fogalom, a `native`/`distortion` listákat én definiáltam, a kontrollszó-párosítás nem tökéletes. Ez kvalitatív-illusztratív mérés; a számszerű alapot a Mérés C adja.

