# Négyes összevetés — Flash IQ4_XS · Flash **NVFP4** · 35B FP8 · 122B NVFP4 (2026-08-28)

> Azonos mérce: greedy (`temperature=0`), 16 384 tokenes válaszkeret, minden item 3× (a hosszú suite 1×),
> a többségi kimenet pontozva. Minden szám a `reports/*.json`-ból `src/riport.py`-jal SZÁMOLT.
> Az NVFP4 oszlop a blazux/qwen3.8-Flash-DGX `82ed48d` receptjével (vLLM + mmap-PLE, MTP=2, PIECEWISE) ment
> a the DGX Spark-en, `CTX=262144`. Az első NVFP4-kör (`CTX=32768`) 77,00-ja HTTP 400-műtermék volt — ld. `04-F4-nvfp4-indulas.md`.

## Pontszámok (65 item / 300 pont)

| Suite | Flash IQ4_XS · llama.cpp | **Flash NVFP4 · vLLM** | 35B FP8 · vLLM | 122B NVFP4 · vLLM | Max |
|---|---:|---:|---:|---:|---:|
| fő (T1–T10) | **98,00** | 97,00 | 96,00 | 97,00 | 100 (98 elérhető) |
| nehéz (T11–T20) | 91,33 | **100,00** | 98,00 | 98,00 | 100 |
| hosszú (T21–T25, 217k) | **100,00** | **100,00** | **100,00** | 80,00 | 100 |
| **összesen** | 289,33 | **297,00** | 294,00 | 275,00 | 300 |

## Ami a NVFP4-kör eldöntött

- ⭐⭐ **A T19 kontrafaktuális bukása (IQ4_XS 3,33/10) KVANTÁLÁSI KÁR volt, nem modell-tulajdonság**: NVFP4-en 10,00/10, három futáson bitre azonosan.
  Az IQ4_XS-smoke két hibája (CJK-szivárgás `amely输入`, csonka `„szakért”`) szintén eltűnt.
- ⭐ A fő suite 1 pontja: **T3-05** — a három futásból kettő tévedett (`[1, 1, 2]`), a többség a ROSSZ válasz. Ez nem értési hiba, hanem az alábbi instabilitás tünete.
- ⭐ Hosszú suite: a 217k-s prompt NVFP4-en **157 s** medián (llama.cpp 1 121 s → **7,1×**), a 35B 69 s. A T22 teljes-átfésülős összegzés 20/20 (a 122B-n 0).

## ⛔⛔ Az NVFP4-konfiguráció NEMDETERMINISZTIKUS temperature 0-n

Fő suite: **13/50 item** ingadozik 3 futás között. Futásonként külön pontozva (`szoras.py`, mert élesben nincs többségi szavazás):

| | |
|---|---|
| instabil item | 13 |
| ebből a **pont is** ingadozik | **5** — T3-01 (11-10 ↔ 11-05), T3-03 (10-27 ↔ 10-26), T3-05, T5-03 (egy futás 16 384 token ÜRES tartalommal), T6-02 (6 300 000 ↔ 5 940 000) |
| csak a szövegezés tér el | 8 (pl. T6-03 `4.2.` / `4.2. pont` / `4.2`) |

Ugyanez a HU-CH challenge-ben: **HU-CH-02 = 0 karakter, `finish=length`** (16 384 token gondolkodás, válasz nélkül).

Kontrollok azonos harnessszel, azonos itemekkel, mind gondolkodó módban: IQ4_XS/llama.cpp **0/50** · 35B FP8/vLLM **MTP=2** **0/50** · 122B NVFP4/vLLM **0/50**.
A nehéz suite NVFP4-en 0/10 instabil (egy 10 178 tokenes generálás is bitre azonos) → nem a hossz okozza; a T6 család **5/5**, a T3 3/5 → ott csapódik ki, ahol a döntés szoros.

**Önellenőrzés (2026-08-28), a mérés kizárva mint ok:** payload explicit `temperature 0.0`; a prompt a futás-ciklus előtt épül, nincs időbélyeg; a vLLM-naplóban a `Running:` maximuma **1 req** (nem volt párhuzamos kliens); minden item pontosan 3 futás, 0 hiba; az eltérés a **gondolkodásban** keletkezik (T3-01: 765/570/1069 kimeneti token, a tartalom 65 karakter mindháromszor). Korlát: a 35B-kontroll más vLLM-build.
Nyom: futás közben JIT-fordult a `_rejection_kernel` (MTP) és a `_qsa_merge_splitk_kernel` (split-K redukció, 05:22, a mérés közepén).

**Izoláció (`~/eval/izolacio.sh`, egyszerre egy változó, a 13 instabil item × 5 futás) — LEZÁRVA 08-28:**

| kar | instabil | pont is | decode tok/s | következtetés |
|---|---:|---:|---:|---|
| alap (MTP=2, PIECEWISE, `persistent_topk`) | 13/50 (3 futás) | 5 | 26,4 | — |
| `mtp0` | 11/13 | 4 | 16,1 | MTP nem gyökérok (de az üres 16k-elszállás csak MTP alatt: 1/150 vs 0/65) |
| `cgnone` | 13/13 | 5 | 27,4 | cudagraph kizárva |
| **`topk`** (egzakt kanonikus top-k, MTP=2 + PIECEWISE marad) | **0/13** | **0** | 27,3 | ⭐⭐⭐ **ROOT CAUSE: QSA-indexer `persistent_topk`** |

Prefill-szonda (`src/prefill_szonda.py`, max_tokens=1, top_logprobs=20, 10×): `persistent_topk` → **6/6 itemen 10 különböző logitvektor** (a „stabil" T2-01/T8-01-en is; rés 0–3,6 nat); egzakt top-k → **6/6 itemen 10/10 bitre azonos**. Az elágazás a gondolkodás 0. tokenjénél volt (magyar/angol nyitány), mert a PREFILL logitjai változtak.
⛔ Ára: az 1. mód (teljes sort) prefillje 2,9× lassabb; a 2. mód (csak rendezés) MEGBUKOTT (a halmaz is változik); **a 3. mód (`torch.topk` + kanonikus) a javítás: 6/6 bitre azonos, prefill 74 %.**
**Validáció a 3. móddal (08-28):** fő **98,00 · 0/50 instabil · 0 csonkolt** (stock 97 · 13 · 1) · nehéz **90,00** (T14-01 3/3 egyformán elszáll: determinisztikus ISMÉTLÉSI HUROK, nem top-k tünet — a stock zaja néha kimenekített belőle) · HU-CH-09 üres · hosszú **100,00** → **a 3. móddal 288/300** (98+90+100) a stock 297-tel szemben — a 9 pont különbség EGYETLEN determinisztikus hurok (T14-01).
**MTP-ekvivalencia (3. mód, MTP=0):** fő 97 (9/50 más kimenet, 1 pont az MTP=2 javára), nehéz 100 (a T14 hurok nem jön elő, de a challenge CH-07 MTP=0-val hurkol), decode 14,8 vs 24,9 → **MTP=2 marad + hurok-őr.** Végleges: `../qwen3.8-flash-next/eredmenyek/03-nvfp4-instabilitas.md` §0. Részletek: `../qwen3.8-flash-next/eredmenyek/03-nvfp4-instabilitas.md`.

## Mellékmetrikák (fő suite, medián)

| | IQ4_XS | **NVFP4** | 35B | 122B |
|---|---:|---:|---:|---:|
| Kimeneti tok/s (válaszidőre) | 24,5 | 26,4 | 60,4 | 25,3 |
| Válaszidő ms | 15 440 | 17 021 | 26 723 | 40 317 |
| Kimeneti token | 307 | 368 | 1 608 | 992 |
| Csonkolt futás | 0 | 1 | 0 | 0 |

## Referencia-repo frissülés (`d2854bf`, 2026-08-27)

Csak doksi + `serve.sh` alapértékek (CTX 262144, SEQS 8, GPU_MEM 0.85, MTP 2, YaRN-ág 500k-ig); a patch és a Dockerfile változatlan → a the DGX Spark runtime naprakész.
⛔⛔ Issue #1 tanulsága: **a méret+darabszám kapu (a mi F3-unk) NEM elég** — 2 méretre helyes, tartalomra sérült shard „fluent token salad"-ot ad minden konfigban. Teendő: `lfs.sha256` a 419 blobra (a mérések UTÁN, mert a 126 GiB olvasás kiüti a PLE page cache-t).
`--kv-cache-dtype fp8`-at a QSA elutasítja → a KV-felezés kar nem létezik. `--max-num-seqs 2` mellett az aggregát tok/s mérés 4×-esen alálő (c=48: 266,8 tok/s) — a single-stream számaink érvényesek, aggregátot ne idézzünk belőlük.
