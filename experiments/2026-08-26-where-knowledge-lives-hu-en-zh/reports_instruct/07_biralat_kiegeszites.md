# 07 — Bírálati kiegészítés: púp-kontraszt · item-klaszteres próbák · HU átmeneti mátrix

Futás: **2026-08-26 08:53** (rendszeridő) · `src/analyze_extra.py` · numpy 2.4.4 · scipy 1.17.1. Kizárólag a meglévő mérési adatból (GPU nélkül); minden szám a kódból jön, a dolgozat értékei csak reprodukciós ellenőrzésként szerepelnek.

Ez a fájl: az (1) mérés **ezen kör** SAE-adatán (3. kör — Qwen3.5-9B (instruct), chat-sablon); a (2)–(3) mérés a három kört együtt veti össze, ezért mindkét riportban azonos.

---

## (1) SAE púp-alak kontraszt — 3. kör — Qwen3.5-9B (instruct), chat-sablon

**Képlet.** Rétegenként (0..31) a kérdés-tokenek feature-UNIÓJA; matchedᵢ(ℓ) = Jaccard az item két nyelvi változata között; véletlen(ℓ) = az ugyanazon csoport összes rendezett (i, j), i ≠ j itempárjának Jaccard-átlaga ugyanazon a nyelvpáron (`itertools.permutations`, mint az `analyze_c.py`-ben); többletᵢ(ℓ) = matchedᵢ(ℓ) − véletlen(ℓ). Sávok: KORAI = 0–3., KÖZÉP = 8–12., KÉSŐI = 28–31. réteg átlaga; kontraszt₁ = KÖZÉP − KORAI, kontraszt₂ = KÖZÉP − KÉSŐI itemenként. CI: item-szintű bootstrap (2000×, seed 0); előjelteszt: pontos kétoldali binomiális a nem-nulla különbségeken; Wilcoxon: `scipy.stats.wilcoxon` (kétoldali), Holm a 9 cellára kontrasztonként. ⛔ A 9 cella nem független replikáció (azonos itemek, modell, SAE).

Reprodukció az `analyze_c.py` `peaks` blokkjával (early = 0–2. réteg, peak = max): **OK — mind a 9 cella bitre egyezik**

### Sáv-átlagok a többleten

| csoport | nyelvpár | n item | KORAI (0–3.) | KÖZÉP (8–12.) | KÉSŐI (28–31.) |
|---|---|---|---|---|---|
| ZH | zh–en | 19 | +0.1002 | **+0.1029** | +0.0744 |
| ZH | zh–hu | 19 | +0.0702 | **+0.0760** | +0.0540 |
| ZH | en–hu | 19 | +0.1493 | **+0.1488** | +0.1161 |
| HU | zh–en | 15 | +0.1488 | **+0.1720** | +0.1344 |
| HU | zh–hu | 15 | +0.0753 | **+0.1015** | +0.0810 |
| HU | en–hu | 15 | +0.0952 | **+0.1259** | +0.0907 |
| UNI | zh–en | 20 | +0.0772 | **+0.1427** | +0.0774 |
| UNI | zh–hu | 20 | +0.0282 | **+0.1018** | +0.0463 |
| UNI | en–hu | 20 | +0.0455 | **+0.1507** | +0.0723 |

### kontraszt₁ = KÖZÉP − KORAI

| csoport | nyelvpár | átlag | bootstrap 95 % CI | előjel (+/−) | p (előjel) | p (Wilcoxon) | p (Holm) |
|---|---|---|---|---|---|---|---|
| ZH | zh–en | +0.0027 | [-0.0065, +0.0108] | 13/6 | 0.167 | 0.332 | 0.664 |
| ZH | zh–hu | +0.0058 | [-0.0012, +0.0129] | 13/6 | 0.167 | 0.080 | 0.240 |
| ZH | en–hu | -0.0005 | [-0.0117, +0.0097] | 9/10 | 1.000 | 1.000 | 1.000 |
| HU | zh–en | +0.0232 | [+0.0069, +0.0413] ✅ | 12/3 | 0.035 ✅ | 0.015 ✅ | 0.060 |
| HU | zh–hu | +0.0262 | [+0.0114, +0.0424] ✅ | 12/3 | 0.035 ✅ | 0.005 ✅ | 0.027 ✅ |
| HU | en–hu | +0.0307 | [+0.0165, +0.0449] ✅ | 12/3 | 0.035 ✅ | 0.002 ✅ | 0.009 ✅ |
| UNI | zh–en | +0.0655 | [+0.0553, +0.0766] ✅ | 20/0 | 1.9e-06 ✅ | 1.9e-06 ✅ | 1.7e-05 ✅ |
| UNI | zh–hu | +0.0736 | [+0.0625, +0.0843] ✅ | 20/0 | 1.9e-06 ✅ | 1.9e-06 ✅ | 1.7e-05 ✅ |
| UNI | en–hu | +0.1052 | [+0.0927, +0.1177] ✅ | 20/0 | 1.9e-06 ✅ | 1.9e-06 ✅ | 1.7e-05 ✅ |

### kontraszt₂ = KÖZÉP − KÉSŐI

| csoport | nyelvpár | átlag | bootstrap 95 % CI | előjel (+/−) | p (előjel) | p (Wilcoxon) | p (Holm) |
|---|---|---|---|---|---|---|---|
| ZH | zh–en | +0.0285 | [+0.0213, +0.0361] ✅ | 19/0 | 3.8e-06 ✅ | 3.8e-06 ✅ | 2.3e-05 ✅ |
| ZH | zh–hu | +0.0219 | [+0.0163, +0.0287] ✅ | 19/0 | 3.8e-06 ✅ | 3.8e-06 ✅ | 2.3e-05 ✅ |
| ZH | en–hu | +0.0327 | [+0.0248, +0.0406] ✅ | 19/0 | 3.8e-06 ✅ | 3.8e-06 ✅ | 2.3e-05 ✅ |
| HU | zh–en | +0.0376 | [+0.0290, +0.0484] ✅ | 15/0 | 6.1e-05 ✅ | 6.1e-05 ✅ | 1.8e-04 ✅ |
| HU | zh–hu | +0.0205 | [+0.0084, +0.0329] ✅ | 13/2 | 0.007 ✅ | 0.004 ✅ | 0.004 ✅ |
| HU | en–hu | +0.0352 | [+0.0273, +0.0440] ✅ | 15/0 | 6.1e-05 ✅ | 6.1e-05 ✅ | 1.8e-04 ✅ |
| UNI | zh–en | +0.0652 | [+0.0571, +0.0733] ✅ | 20/0 | 1.9e-06 ✅ | 1.9e-06 ✅ | 1.7e-05 ✅ |
| UNI | zh–hu | +0.0555 | [+0.0468, +0.0650] ✅ | 20/0 | 1.9e-06 ✅ | 1.9e-06 ✅ | 1.7e-05 ✅ |
| UNI | en–hu | +0.0783 | [+0.0689, +0.0889] ✅ | 20/0 | 1.9e-06 ✅ | 1.9e-06 ✅ | 1.7e-05 ✅ |

### Összegzés — hány cellában „púp”?

- **Mindkét kontraszt CI-je pozitív (CI alsó széle > 0): 6/9 cella** — HU zh–en, HU zh–hu, HU en–hu, UNI zh–en, UNI zh–hu, UNI en–hu.
- Csak KÖZÉP > KORAI: 0 — –.
- Csak KÖZÉP > KÉSŐI: 3 — ZH zh–en, ZH zh–hu, ZH en–hu.
- Egyik sem: 0 — –.
- Holm-korrigált Wilcoxon p < 0,05 MINDKÉT kontrasztra: 5/9 — HU zh–hu, HU en–hu, UNI zh–en, UNI zh–hu, UNI en–hu.

Olvasat: a „púp” állítás (a többlet a középső sávban nagyobb, mint a korai ÉS a késői sávban) csak abban a cellában áll, ahol mindkét kontraszt CI-je a nulla fölött van. Ahol csak a KÖZÉP − KÉSŐI pozitív, ott a görbe monoton csökkenő is lehet (a korai többlet már magas, pl. szó szerinti token-egyezés miatt), nem púp.

---

## (2) Item-klaszteres párosított próba a post-training pontosság-változásra

**Képlet.** Ítélet = `manual`, ha nem üres, különben `final`; helyes = `helyes`. Klaszterezetlen: McNemar a diszkordáns (item_id, lang) párokon, pontos kétoldali binomiális p (azonos a `compare_rounds.py`-vel). Klaszteres: itemenként nettó = javult − romlott a 3 nyelven együtt; (a) item-blokkos permutáció — az item nettójának előjelét flippeljük (10000×, seed 0), statisztika T = Σ nettó, p kétoldali = P(|T*| ≥ |T|); (b) item-szintű bootstrap (2000×, seed 0) 95 % CI a nettó javulásra (darab és százalékpont a válaszok számára vetítve).

### Reprodukció — pontossági mátrix (base kör, `manual`→`final`)

| kör / csoport | hu | en | zh | dolgozat (hu / en / zh) | |
|---|---|---|---|---|---|
| base **ZH** | 42 % | 53 % | 63 % | 42 % / 53 % / 63 % | OK |
| base **HU** | 7 % | 13 % | 20 % | 7 % / 13 % / 20 % | OK |
| base **UNI** | 90 % | 100 % | 100 % | 90 % / 100 % / 100 % | OK |

A másik két kör (nem ellenőrzési cél, tájékoztatásul):

| kör / csoport | hu | en | zh |
|---|---|---|---|
| instruct + nyers **ZH** | 47 % (9/19) | 68 % (13/19) | 58 % (11/19) |
| instruct + nyers **HU** | 7 % (1/15) | 20 % (3/15) | 13 % (2/15) |
| instruct + nyers **UNI** | 85 % (17/20) | 100 % (20/20) | 100 % (20/20) |
| instruct + chat **ZH** | 58 % (11/19) | 58 % (11/19) | 63 % (12/19) |
| instruct + chat **HU** | 20 % (3/15) | 27 % (4/15) | 33 % (5/15) |
| instruct + chat **UNI** | 100 % (20/20) | 100 % (20/20) | 100 % (20/20) |

### Reprodukció — McNemar (item_id, lang) egységen

| lépés | mi változik | javult | romlott | p (McNemar) | dolgozat |
|---|---|---|---|---|---|
| base→chat | súlyok + promptozás együtt | 16 | 4 | 0.012 | 16 / 4, p = 0.012 → OK |
| base→nyers | csak a súlyok (azonos nyers prompt) | 9 | 7 | 0.804 | 9 / 7 → OK |
| nyers→chat | csak a promptozás (azonos súlyok) | 13 | 3 | 0.021 | 13 / 3 → OK |

Reprodukció: javult/romlott **OK mindhárom lépésre**; a dolgozat p = 0,012 értéke **OK**.

### Klaszterezetlen és klaszteres p egymás mellett (mind a 162 válasz, 54 item)

| lépés | javult | romlott | nettó | p McNemar (162 pár) | p permutáció (54 item-blokk) | bootstrap 95 % CI nettó (db) | CI (százalékpont) | itemek nettó ≠ 0 |
|---|---|---|---|---|---|---|---|---|
| **base→chat** | 16 | 4 | +12 | 0.012 ✅ | **0.030** ✅ | [+3.0, +22.0] | [+1.9, +13.6] | 14/54 |
| **base→nyers** | 9 | 7 | +2 | 0.804 | **0.809** | [-6.0, +10.0] | [-3.7, +6.2] | 13/54 |
| **nyers→chat** | 13 | 3 | +10 | 0.021 ✅ | **0.020** ✅ | [+3.0, +18.0] | [+1.9, +11.1] | 10/54 |

Csoportonként (a klaszteres p itt még kisebb blokkszámon áll: ZH 19, HU 15, UNI 20 item):

| lépés | csoport | javult | romlott | p McNemar | p permutáció | bootstrap CI nettó (db) |
|---|---|---|---|---|---|---|
| base→chat | ZH | 7 | 3 | 0.344 | 0.361 | [-2.0, +10.0] |
| base→chat | HU | 7 | 1 | 0.070 | 0.190 | [+0.0, +13.0] |
| base→chat | UNI | 2 | 0 | 0.500 | 0.493 | [+0.0, +5.0] |
| base→nyers | ZH | 6 | 3 | 0.508 | 0.531 | [-3.0, +9.0] |
| base→nyers | HU | 1 | 1 | 1.000 | 1.000 | [-3.0, +3.0] |
| base→nyers | UNI | 2 | 3 | 1.000 | 1.000 | [-5.0, +3.0] |
| nyers→chat | ZH | 3 | 2 | 1.000 | 1.000 | [-2.0, +4.0] |
| nyers→chat | HU | 7 | 1 | 0.070 | 0.124 | [+1.0, +12.0] |
| nyers→chat | UNI | 3 | 0 | 0.250 | 0.252 | [+0.0, +6.0] |

Az itemenkénti nettó eloszlása (hány item mozdult ennyit a 3 nyelvén együtt):

| lépés | nettó -3 | nettó -2 | nettó -1 | nettó +0 | nettó +1 | nettó +2 | nettó +3 |
|---|---|---|---|---|---|---|---|
| base→chat | 0 | 0 | 3 | 40 | 7 | 4 | 0 |
| base→nyers | 0 | 0 | 6 | 41 | 6 | 1 | 0 |
| nyers→chat | 0 | 0 | 1 | 44 | 7 | 2 | 0 |

Olvasat: a klaszteres p a bírálat 9. pontjának válasza — az item 3 nyelvi változata nem független megfigyelés. Ha a permutációs p is 0,05 alatt marad, az irány a pszeudoreplikáció kiszűrése után is áll; ha fölé megy, a dolgozat állítását ennek megfelelően kell gyengíteni.

---

## (3) Hallucinációs átmeneti mátrix — HU-csoport (8.2)

**Képlet.** A 45 HU-válasz (15 item × 3 nyelv) kategóriája körönként (ítélet = `manual`, különben `final`). A dolgozat szótára: „magabiztos kitaláció” = `hallucinacio`; „kitérés / nem-válasz” = `helytelen`; „helyes vagy részben” = `helyes` + `reszben`. Átmeneti mátrix: ugyanazon válasz kategóriája a két körben. Csonkolatlan érzékenység: csak azok a válaszok, ahol `truncated == 0` MINDKÉT körben. Item-blokkos permutáció: dᵢ = #kategória(1. kör) − #kategória(2. kör) az item 3 nyelvén együtt, T = Σ dᵢ, az item előjele flippel (10000×, seed 0); p egyoldali = P(T* ≥ T) (a „csökken” irány), p kétoldali = P(|T*| ≥ |T|); bootstrap 95 % CI a T-re (2000×, seed 0).

### Reprodukció — kategória-darabszámok a három körben

| kategória | base + nyers | instruct + nyers | instruct + chat | dolgozat | |
|---|---|---|---|---|---|
| helyes | 6 | 6 | 12 | | |
| reszben | 2 | 3 | 5 | | |
| helytelen | 14 | 10 | 3 | | |
| hallucinacio | 23 | 26 | 25 | | |
| **magabiztos kitaláció (= hallucinacio)** | 23 | 26 | 25 | 23 → 26 → 25 | OK |
| **kitérés / nem-válasz (= helytelen)** | 14 | 10 | 3 | 14 → 10 → 3 | OK |
| **helyes vagy részben** | 8 | 9 | 17 | 8 → 9 → 17 | OK |
| csonkolt (`truncated = 1`) a 45-ből | 12 | 22 | 30 | | |

Reprodukció: **OK — a dolgozat mindhárom sora kijön**.

### base→chat

**Teljes (n = 45)** (sor: kiinduló kategória → oszlop: új kategória)

| ↓ ebből \ ebbe → | helyes | reszben | helytelen | hallucinacio | Σ sor |
|---|---|---|---|---|---|
| **helyes** | **5** | 0 | 0 | 1 | 6 |
| **reszben** | 0 | **1** | 1 | 0 | 2 |
| **helytelen** | 4 | 2 | 0 | 8 | 14 |
| **hallucinacio** | 3 | 2 | 2 | **16** | 23 |
| Σ oszlop | 12 | 5 | 3 | 25 | 45 |

**Csonkolatlan érzékenység — `truncated = 0` mindkét körben (n = 12 válasz, 8 item)** (sor: kiinduló kategória → oszlop: új kategória)

| ↓ ebből \ ebbe → | helyes | reszben | helytelen | hallucinacio | Σ sor |
|---|---|---|---|---|---|
| **helyes** | **1** | 0 | 0 | 1 | 2 |
| **reszben** | 0 | 0 | 0 | 0 | 0 |
| **helytelen** | 3 | 1 | 0 | 1 | 5 |
| **hallucinacio** | 1 | 0 | 1 | **3** | 5 |
| Σ oszlop | 5 | 1 | 1 | 5 | 12 |

| statisztika | minta | T = Σ dᵢ (csökkenés) | p egyoldali (csökken) | p kétoldali | bootstrap 95 % CI |
|---|---|---|---|---|---|
| kitérés (`helytelen`) darabszám-csökkenése | teljes (n = 45, 15 item) | +11 | 0.020 ✅ | 0.037 ✅ | [+3.0, +19.0] |
| kitérés (`helytelen`) darabszám-csökkenése | csonkolatlan (n = 12, 8 item) ⚠️ | +4 | 0.129 | 0.247 | [+1.0, +8.0] |
| kitaláció (`hallucinacio`) darabszám-csökkenése | teljes (n = 45, 15 item) | -2 | 0.744 | 0.834 | [-10.0, +5.0] |
| kitaláció (`hallucinacio`) darabszám-csökkenése | csonkolatlan (n = 12, 8 item) ⚠️ | +0 | 0.683 | 1.000 | [-4.0, +4.0] |

⚠️ 8 item-blokk mellett az előjelflip-permutációnak csak 2^8 = 256 különböző mintázata van, a percentilis bootstrap pedig durva: a CI és a p ott egymásnak ellent is mondhat — a kis részmintán a mátrix iránya olvasandó, nem a próba.

### nyers→chat

**Teljes (n = 45)** (sor: kiinduló kategória → oszlop: új kategória)

| ↓ ebből \ ebbe → | helyes | reszben | helytelen | hallucinacio | Σ sor |
|---|---|---|---|---|---|
| **helyes** | **5** | 0 | 0 | 1 | 6 |
| **reszben** | 0 | **2** | 0 | 1 | 3 |
| **helytelen** | 2 | 0 | **1** | 7 | 10 |
| **hallucinacio** | 5 | 3 | 2 | **16** | 26 |
| Σ oszlop | 12 | 5 | 3 | 25 | 45 |

**Csonkolatlan érzékenység — `truncated = 0` mindkét körben (n = 7 válasz, 6 item)** (sor: kiinduló kategória → oszlop: új kategória)

| ↓ ebből \ ebbe → | helyes | reszben | helytelen | hallucinacio | Σ sor |
|---|---|---|---|---|---|
| **helyes** | **1** | 0 | 0 | 0 | 1 |
| **reszben** | 0 | 0 | 0 | 0 | 0 |
| **helytelen** | 1 | 0 | 0 | 2 | 3 |
| **hallucinacio** | 1 | 0 | 1 | **1** | 3 |
| Σ oszlop | 3 | 0 | 1 | 3 | 7 |

| statisztika | minta | T = Σ dᵢ (csökkenés) | p egyoldali (csökken) | p kétoldali | bootstrap 95 % CI |
|---|---|---|---|---|---|
| kitérés (`helytelen`) darabszám-csökkenése | teljes (n = 45, 15 item) | +7 | 0.103 | 0.203 | [-1.0, +16.0] |
| kitérés (`helytelen`) darabszám-csökkenése | csonkolatlan (n = 7, 6 item) ⚠️ | +2 | 0.318 | 0.627 | [-2.0, +5.0] |
| kitaláció (`hallucinacio`) darabszám-csökkenése | teljes (n = 45, 15 item) | +1 | 0.497 | 1.000 | [-8.0, +8.0] |
| kitaláció (`hallucinacio`) darabszám-csökkenése | csonkolatlan (n = 7, 6 item) ⚠️ | +0 | 0.690 | 1.000 | [-4.0, +4.0] |

⚠️ 6 item-blokk mellett az előjelflip-permutációnak csak 2^6 = 64 különböző mintázata van, a percentilis bootstrap pedig durva: a CI és a p ott egymásnak ellent is mondhat — a kis részmintán a mátrix iránya olvasandó, nem a próba.

### base→nyers

**Teljes (n = 45)** (sor: kiinduló kategória → oszlop: új kategória)

| ↓ ebből \ ebbe → | helyes | reszben | helytelen | hallucinacio | Σ sor |
|---|---|---|---|---|---|
| **helyes** | **5** | 0 | 0 | 1 | 6 |
| **reszben** | 0 | **1** | 1 | 0 | 2 |
| **helytelen** | 0 | 2 | **6** | 6 | 14 |
| **hallucinacio** | 1 | 0 | 3 | **19** | 23 |
| Σ oszlop | 6 | 3 | 10 | 26 | 45 |

**Csonkolatlan érzékenység — `truncated = 0` mindkét körben (n = 20 válasz, 13 item)** (sor: kiinduló kategória → oszlop: új kategória)

| ↓ ebből \ ebbe → | helyes | reszben | helytelen | hallucinacio | Σ sor |
|---|---|---|---|---|---|
| **helyes** | **1** | 0 | 0 | 0 | 1 |
| **reszben** | 0 | **1** | 0 | 0 | 1 |
| **helytelen** | 0 | 0 | **3** | 4 | 7 |
| **hallucinacio** | 1 | 0 | 1 | **9** | 11 |
| Σ oszlop | 2 | 1 | 4 | 13 | 20 |

| statisztika | minta | T = Σ dᵢ (csökkenés) | p egyoldali (csökken) | p kétoldali | bootstrap 95 % CI |
|---|---|---|---|---|---|
| kitérés (`helytelen`) darabszám-csökkenése | teljes (n = 45, 15 item) | +4 | 0.182 | 0.358 | [-2.0, +10.0] |
| kitérés (`helytelen`) darabszám-csökkenése | csonkolatlan (n = 20, 13 item) | +3 | 0.183 | 0.378 | [-1.0, +7.0] |
| kitaláció (`hallucinacio`) darabszám-csökkenése | teljes (n = 45, 15 item) | -3 | 0.939 | 0.449 | [-8.0, +2.0] |
| kitaláció (`hallucinacio`) darabszám-csökkenése | csonkolatlan (n = 20, 13 item) | -2 | 0.941 | 0.623 | [-6.0, +2.0] |

Olvasat: a mátrix mutatja, hova KERÜLT a base kör kitérése (a `helytelen` sor oszlopai) — ha zöme a `hallucinacio` oszlopba, a „kitérés → magabiztos kitaláció” átalakulás; ha a `helyes`/`reszben` oszlopba, valódi javulás. A csonkolatlan részminta a bírálat felvetését teszteli: a kitérés eltűnése nem a levágott bizonytalankodó folytatás műterméke-e. ⛔ A csonkolatlan részminta kicsi (base→chat: 12 válasz), ezért ott a p-érték ereje korlátozott; a mátrix-irány az informatív.

