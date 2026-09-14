# Round4 — a cross-request prefix-cache eltérés gyökéroka: a kimaradó 1600-as Mamba-checkpoint

**2026-09-14 · SPARK-DEV (GB10) · kiindulás: a 09-13-i külső elemzés
(`prefix-cache-hibakereses-2026-09-13.md`)**

## 0. Összefoglaló

A round3-ban megfigyelt jelenség — *„a teljes prefix-cache hit megváltoztatja a greedy logitokat, ha a
közös előtagot más hosszúságú kérés írta be"* — mechanizmusa **azonosítva és GPU-n reprodukálva**.

⛔⛔ **Az ok nem a QSA top-k és nem a cache-út önmagában, hanem egy kimaradó állapotmentés a
schedulerben.** MTP (`use_eagle=True`) mellett a `Scheduler._mamba_block_aligned_split` egy teljes
blokkal visszaveszi az utolsó menthető pozíciót:

```python
last_cache_position = request.num_tokens - request.num_tokens % block_size
if self.use_eagle:
    last_cache_position = max(last_cache_position - block_size, 0)
```

Ezért **egy 2 × blokkméret (= 3200 token) alatti kérés egyetlen prefill-darabban fut le, és nem ment
1600-as Mamba/GDN-checkpointot** — hiába írja be a KV-blokkjait. Ha ezután egy hosszabb (≥ 3200
tokenes) kérés érkezik ugyanarra a közös előtagra, az **maga állítja elő és menti** az 1600-as
állapotot; a saját ismétlésekor viszont a KV-blokkokat az *első* kérés példányából kapja vissza
(`BlockHashToBlockMap` duplikátum esetén az elsőként beillesztettet adja), az állapotot pedig a
sajátjából → **eltérő eredetű tenzorok egyesülnek**, és ez numerikusan megjelenik a logitokban.

## 1. Mit igazolt a forráselemzés (CPU)

A `_mamba_block_aligned_split` függvényt a **ténylegesen futó image** forrásából emeltük ki
(`qwen38-flash-dgx:v029-validation-20260912T120351Z`, a recept kétsoros patchével együtt), nem
upstream checkoutból. A round3 mind a nyolc mért esetére lefuttatva:

| eset | A | ír ckpt? | B | ír ckpt? | jóslat | round3 mért |
|---|---:|---|---:|---|---|---|
| T2-01 (D2) | 3169 | **nem** | 3227 | igen | FAIL | **FAIL** |
| D6 eltérő | 3086 | **nem** | 3267 | igen | FAIL | **FAIL** |
| D6 azonos | 3307 | igen | 3371 | igen | PASS | **PASS** |
| D3 azonos (B kar) | 3264 | igen | 3346 | igen | PASS | **PASS** |
| D1 eltérő | 4689 | igen | 4870 | igen | PASS | **PASS** |
| T5-01 | 2155 | nem | 2182 | **nem** | PASS | **PASS** |
| T4-01 (tiszta) | 1859 | nem | 1859 | **nem** | PASS | **PASS** |
| T9-01 / D5 | 24384 | igen | 24404 | igen | PASS | **PASS** |

**8/8.** Ez feloldja a round3 nyitott ellentmondását is: a D1 (2 vs 3 blokk) azért PASS, mert ott az
A kérés már megírta az 1600-as checkpointot — vagyis **nem a blokkszám-eltérés a változó, hanem hogy
az első kérés ment-e állapotot a közös határon.**

Szonda: `eszkozok/checkpoint_szonda_cpu.py` (AST-kiemelés, GPU és modell nélkül).

## 2. A GPU-kísérlet terve

A mechanizmusból éles, olcsó jóslat adódik: a küszöb **pontosan 2 × blokkméret = 3200 token**, és
`A` hosszának néhány tokenes megváltoztatása — változatlan közös prefix és változatlan `B` mellett —
át kell billentse az eredményt.

| cella | A | B | jóslat | indoklás |
|---|---|---|---|---|
| 1 | < 3200 | ≥ 3200 | **FAIL** | A nem ment állapotot, B igen → vegyes eredet |
| 2 | ≥ 3200 | ≥ 3200 | PASS | mindkettő ment → azonos eredet |
| 3 | < 3200 | < 3200 | PASS | egyik sem ment → nincs hibrid találat |
| 4 | ≥ 3200 | < 3200 | PASS | — |

Közös prefix: `D6.md` (3052 token a chat-sablonnal), cellánként külön `cache_salt` és külön
kitöltő-mag, így egy szerverindításon belül nem szennyezik egymást.

⭐ A round3-as szondák két hiányosságát is pótoltuk (a külső elemzés jogos kritikája):
a tényleges **`cached_tokens`** rögzítése (`--enable-prompt-tokens-details`) és a **nyers top-20**
lista mentése API-sorrendben és token-azonosító szerint kanonizálva is.

## 3. Kontroll kar — a javítatlan v0.29 image

Szerver: `qwen38-flash-dgx:v029-validation-20260912T120351Z`, a 09-12-i B-karral azonos
paraméterezés (`QSADET active`, blokkméret 1600, MTP `num_speculative_tokens=2`), + a
`--enable-prompt-tokens-details` kapcsoló. Friss indítás, minden cella ×4 ismétlés.

| cella | A tok | B tok | jóslat | **mért** | B `cached_tokens` |
|---|---:|---:|---|---|---|
| 1 — A alatt, B felett | **3196** | 3259 | FAIL | ⛔ **FAIL** | `[0, 1600, 1600, 1600]` |
| 2 — A felett, B felett | **3205** | 3259 | PASS | ✅ **PASS** | `[0, 1600, 1600, 1600]` |
| 3 — A alatt, B alatt | 3097 | 3160 | PASS | ✅ **PASS** | `[0, 0, 0, 0]` |
| 4 — A felett, B alatt | 3205 | 3160 | PASS | ✅ **PASS** | `[0, 0, 0, 0]` |

**4/4.** A döntő pár az 1. és a 2. cella: a `B` kérés bitre azonos hosszú, a közös prefix azonos,
egyedül az `A` kérés hossza tér el **9 tokennel** (3196 vs 3205) — és ez billenti FAIL-ből PASS-ba.

⭐⭐ **`B#1 cached_tokens = 0`.** Ez az a motor-szintű adat, ami a round3-ból hiányzott: hiába írta be
`A` ugyanazt az első 1600 tokent, a `B` **első** futása **nulla** találatot kap. A round3-as
„részleges hit" értelmezés tehát téves volt — **nulla** hit, azaz a `B#1` valójában hideg futás; ez
magyarázza, miért egyezik bitre a teljesen cache-mentes karral. Az eltérés pontosan attól a futástól
jelenik meg, ahol a `cached_tokens` 1600-ra ugrik.

⭐ A 3. és 4. cella `cached_tokens = 0` sorozata mutatja, hogy a küszöb alatti kérés **egyáltalán nem
kap hibrid találatot** — a jelenséghez nem elég a KV-blokkok egyezése.

### 3.1 A logprobok valóban elmozdulnak

A külső elemzés jogosan vetette fel, hogy a hash-eltérés jöhetne holtversenyes jelöltek puszta
sorrendcseréjéből is. A nyers top-20 listákból (1. cella, `B#1` vs `B#2`):

| token | jelölthalmaz | argmax | max \|Δ logprob\| a közös jelölteken | eltérő értékű közös jelölt |
|---|---|---|---:|---|
| #0 | 19/20 közös (egy jelölt cserélődik) | azonos | **0,745** | 19/19 |
| #1 | 19/20 közös | azonos | **0,664** | 19/19 |
| #2 | 18/20 közös | azonos | **1,062** | 18/18 |

Tehát **numerikus elmozdulás**, nem reprezentációs artefakt; a kanonizált (token-azonosító szerint
rendezett) hash is két változatot ad. Az argmax ezen a prompton stabil maradt — ezért volt a látható
válaszszöveg mind a tíz futáson azonos a round3-ban is.

## 4. Javított kar — a `#54076` szűk backportja

Ugyanaz az image, ugyanazok a kapcsolók, **egyetlen sor** cserélve a scheduler forrásában
(konténerindításkor, a naplóban `BOUNDARY FIX (vllm#54076 szuk backport) APPLIED OK`):

```diff
-            next_block_boundary if start % block_size != 0 else 0,
+            0 if use_internal_checkpoint else next_block_boundary,
```

Ez a `vllm#54076` (nyitott PR, 4 fájl, +287/−17) szemantikájának szűk átvétele, **nem a teljes PR**.
Az upstream PR kommentje ugyanezt a mechanizmust mondja ki: *„a k blokkot átívelő darab a k−1 belső
állapot-rekeszt véglegesen null-ként hagyja"*.

### 4.1 A 2×2 mátrix

| cella | A tok | B tok | kontroll kar | **javított kar** | B `cached_tokens` (javított) |
|---|---:|---:|---|---|---|
| 1 — A alatt, B felett | 3196 | 3259 | ⛔ **FAIL** | ✅ **PASS** | `[0, 1600, 1600, 1600]` |
| 2 — A felett, B felett | 3205 | 3259 | ✅ PASS | ✅ PASS | `[0, 1600, 1600, 1600]` |
| 3 — A alatt, B alatt | 3097 | 3160 | ✅ PASS | ✅ PASS | `[0, 0, 0, 0]` |
| 4 — A felett, B alatt | 3205 | 3160 | ✅ PASS | ✅ PASS | `[0, 0, 0, 0]` |

### 4.2 ⭐⭐ És az eredeti bukó eset is

A round3 **eredeti** esetét (T3-01 ×1, majd T2-01 ×10 a közös `D2.md`-n, 3169 / 3227 token) a
round3-as `t201_partial_hit.py` szondával, változatlanul lefuttatva a javított karon:

```
T2-01 #1..#10  hash=c05aff295d7b8b7d   (10/10 azonos)
[=] PASS — 1 változat, az 1. eltér a többitől: False
```

Ez a konfiguráció eddig **két különböző stacken** (pinelt preview image és hivatalos v0.29.0 +
det-kernel), **három mérési körben** bukott, mindig ugyanazzal a mintázattal. Az egysoros
határmegállítással megszűnik.

### 4.3 Finomítás: nem pusztán az „eltérő eredet" a baj

A javított karon az 1. cella `cached_tokens` mintázata **változatlan** (`B#1` = 0, `B#2+` = 1600),
vagyis a blokkok eredete továbbra is vegyes, az eredmény mégis bitre azonos. A magyarázat ezért
pontosabban:

⛔ **a menthető állapot hiánya azt engedi meg, hogy a közös 0–1599 blokk KV-ját egy 3196 tokenes
egyetlen darab írja be, miközben az állapotot egy 1600 tokenes darab állítja elő.** Ugyanarra a
tokenekre más darabolási alak más numerikát ad. A javítás azért működik, mert **minden kérés
ugyanott, blokkhatáron zárja a darabjait** → a beírt tenzorok alakfüggetlenül egyeznek.

⚠️ Ez a mondat a mért viselkedésből következtetés, nem tenzorszintű bizonyíték: a rétegenkénti
összehasonlítás (melyik az első numerikusan eltérő művelet) **nem történt meg**.

## 5. Mi marad nyitva

- ⚠️ **Az első numerikusan eltérő tenzor helye ismeretlen.** A gyökérok a schedulerben van, de hogy
  a darabolási alak melyik kernelben (NVFP4-projekció / MoE, GDN prefill, QSA split-K profil) váltja
  ki az eltérést, külön tenzortrace kérdése.
- ⚠️ **A logprob-hash szerverindítások között nem stabil** (qwen38_prefix_cache_cross_request_logit_elteres),
  ezért a kontroll és a javított kar hash-ei **nem hasonlíthatók össze egymással**; minden
  következtetés indításon belüli.
- ⚠️ **Teljesítményár nem mérve.** A minden blokkhatárnál megálló prefill több scheduler-lépést és
  kernelindítást okoz; a round3-as prefill-sweepet (8K–64K) a javított karon nem futtattuk újra.
- ⚠️ **Minőségi suite nem futott** a javított karon (külön mérési szál).
- A teljes `#54076` (4 fájl, +287/−17) további változtatásokat is visz; mi ebből **egy sort** vettünk
  át kísérleti célra. Éles átvétel csak a teljes PR mergelése után, upstream úton.

## 6. Reprodukció

```bash
# 1) CPU-forrásszonda (GPU nélkül, a futó image forrásán)
python3 eszkozok/checkpoint_szonda_cpu.py eredmenyek/forras/scheduler-v029-recept-patchelt.py

# 2) GPU, kontroll kar (a 09-12-i B-kar image változatlanul, + --enable-prompt-tokens-details)
python3 eszkozok/checkpoint_szonda.py --url http://SPARK-DEV:18381 \
  --model qwen38-flash-next-nvfp4 --korpusz <korpusz> --doc D6 \
  --cellak 1,2,3,4 --ismetles 4 --mag c1 --out eredmenyek/round4-ctrl.json

# 3) GPU, javított kar: ugyanaz az image, a scheduler egy sora cserélve konténerindításkor
#    (ld. eredmenyek/kiszolgalo-naplok/fix-inspect.json -> Cmd)
```

Nyers bizonyíték: `eredmenyek/round4-ctrl-smoke.json`, `round4-ctrl-cellak234.json`,
`round4-fix-cellak1234.json`, `round4-fix-t201-szennyezett.json`,
`eredmenyek/kiszolgalo-naplok/` (2 konténernapló + 2 inspect), `eredmenyek/forras/`.
