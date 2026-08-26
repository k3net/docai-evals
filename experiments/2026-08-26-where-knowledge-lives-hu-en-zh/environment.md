# env.md — Fázis 0 zárása (mérve 2026-08-24, spark-dev)

> A runbook §0 kötelező kimenete. Minden szám **mérés**, nem model card-idézet;
> a nyers adat: [reports/00_env.json](reports/00_env.json),
> [reports/00_token_lengths.csv](reports/00_token_lengths.csv),
> [reports/00_smoke_template.json](reports/00_smoke_template.json),
> [reports/00_smoke_think.json](reports/00_smoke_think.json).

## Futtatókörnyezet

| | |
|---|---|
| Gép | **GPU-node** (belső hálózat), NVIDIA **GB10**, aarch64, 121 GB egyesített memória, driver 580.173.02 |
| Compute capability | **sm_121a** (`torch.cuda.get_device_capability() == (12, 1)`) |
| Futtatás | **konténer**, nem venv: `lora-train:3` → [code/run_spark.sh](code/run_spark.sh) |
| torch / CUDA | 2.11.0+cu130 / 13.0 |
| transformers | 5.6.0 (`qwen3_5` natív támogatással) |
| flash-linear-attention | 0.5.2 (triton — **működik** a GB10-en) |
| Munkakönyvtár | `spark-dev:~/lang-study` (a konténerben `/work`), `HF_HOME=/work/hf` |
| Modellsúlyok | 19,3 GB (base) + 68,7 GB (SAE, 32 réteg) letöltve, anonim HF-letöltéssel |

⛔ **A runbook §0 `python -m venv && pip install torch` lépése ezen a gépen zsákutca** — a
GB10/aarch64-re nincs működő pip-torch. A ház bevált útja a konténer (ld. `clf-study`,
`lora-study`), ezért `code/run_spark.sh` a belépőpont minden GPU-s lépéshez.

## ⛔ GB10-gotcha: `causal_conv1d` szegmenshiba

A legelső forward pass **`Fatal Python error: Segmentation fault`**-tal megöli a folyamatot,
**traceback nélkül** (`modeling_qwen3_5.py:466` → `causal_conv1d/cpp_functions.py:104`). A Qwen3.5
rétegeinek 75 %-a GatedDeltaNet lineáris figyelem, ennek konvolúciós lépését a `causal_conv1d`
CUDA-kernel gyorsítja — a wheel nem erre az architektúrára készült.

Ha `| tail`-lel néznéd a kimenetet, a hiba **némán** eltűnik: a pipeline exit kódja a `tail`-é (0).

Megoldás: [code/gb10_patch.py](code/gb10_patch.py) — a `from_pretrained` **előtt** kinullázza a
kernel-referenciákat, a transformers a matematikailag azonos `F.silu(conv1d(x))` ágra esik.
A patch nélkül a rétegek `__init__`-je már eltárolta a kernelt, utólag hiába nullázod.
A triton-alapú `fla` kernelek **nem** hibásak, azokat nem kapcsoljuk ki (`fla=False`).

Ár: a 12 tokenes prompt első forward passa 21 s (kernelfordítás), utána a generálás ~10 token/s.

## Modell — Qwen/Qwen3.5-9B-Base

| | |
|---|---|
| Architektúra a configban | `Qwen3_5ForConditionalGeneration` (multimodális burok) → `AutoModelForCausalLM` **`Qwen3_5ForCausalLM`**-et ad |
| Rétegek | **32** (24 `linear_attention` + 8 `full_attention`, minden 4.) |
| Hidden dim | **4096** · head_dim 256 · `rms_norm_eps` 1e-6 |
| Vocab | **248 320** (a tokenizer 248 044 + speciális tokenek) |
| Kontextus | 262 144 |
| `lm_head` | `[248320, 4096]`, **`tie_word_embeddings = False`** → a logit lens a saját `lm_head.weight`-tel megy, nem az embeddinggel |
| Elérési utak | rétegverem `model.layers`, záró norm `model.norm` |
| Betöltés | bf16, ~76–83 s, ~18 GB |

## ⛔ `hidden_states` indexelés — mérve, nem feltételezve

`output_hidden_states=True` → **33** elem. Rétegenként összevetve a `resid_post` hookkal:

- `hidden_states[i+1] == resid_post(i)` **bitre azonos** (max abs diff = 0.0) az `i = 0…30` rétegekre,
- `hidden_states[32] ≠ resid_post(31)`: **max abs diff = 119,875** — a HF az utolsó elemre **már
  ráengedte a záró RMSNormot**.

Következmény kettő, mindkettő a runbook szövegét érinti:
1. a **logit lensnél** a 32. elemre **nem szabad újra** normalizálni (a többire kötelező) — kétszeres
   norm ~az utolsó réteg görbéjét torzítaná el, épp ott, ahol a H1 „visszafordulást" jósol;
2. a **31. réteg SAE-jéhez** a `hidden_states` nem használható, oda hook kell.

Ezért a `run.py` mind a 32 rétegen **hookkal** menti a `resid_post`-ot, és nem a `hidden_states`-ből dolgozik.

**Indexelés-ellenőrzés** (a runbook §1 „volt már ilyen hiba" pontja): ugyanazon item három nyelvének
16. rétegbeli utolsó-token vektora **nem azonos** — cos(hu,en) = 0,809 · cos(hu,zh) = 0,858.

## SAE — Qwen/SAE-Res-Qwen3.5-9B-Base-W64K-L0_50

| | |
|---|---|
| Típus | `topk_sae`, **k = 50**, `d_model` 4096, `d_sae` **65 536** (16× tágítás), fp32 |
| Hook-pont | **`resid_post`** |
| Rétegek | ⭐ **mind a 32** (`layer0.sae.pt` … `layer31.sae.pt`), 2,15 GB/réteg, összesen 68,7 GB |
| Kulcsok | `W_enc` (65536, 4096) · `W_dec` (4096, 65536) · `b_enc` (65536,) · `b_dec` (4096,) |
| Encoder-képlet | **`f = TopK₅₀(x @ W_enc.T + b_enc)`** — `x − b_dec` kivonás **nincs** benne (a hivatalos README szerint; ez eltér a klasszikus OpenAI TopK-SAE-től, a módszertanban így kell leírni) |

Ellenőrizve egy valódi prompt utolsó tokenjén: pontosan **50 aktív** feature, és a rekonstrukciós
relatív hiba `‖x − (W_dec·f + b_dec)‖² / ‖x‖²` = **0,0023 (L0) · 0,1608 (L15) · 0,1660 (L31)**.
Ez a szám a **hook-pont bizonyítéka**: rossz tenzoron (pl. pre-norm vagy MLP-kimenet) nagyságrenddel
nagyobb lenne.

⭐ **A runbook §4 „ha az SAE csak egy rétegre van" korlátja tárgytalan.** Mind a 32 rétegre van SAE,
ezért a Jaccard-átfedés **rétegenkénti görbeként** mérhető — ugyanazon az x tengelyen, mint a logit lens.
A két módszer nem „kiegészíti" egymást, hanem **ugyanarra a kérdésre ad két független választ**.

## Tokenhossz-tábla (mind a 258 prompt)

| csoport / fajta | n item | hu | en | zh | hu/zh |
|---|---|---|---|---|---|
| ZH / fact | 19 | 37,9 | 26,0 | 16,4 | **2,31×** |
| HU / fact | 15 | 29,7 | 23,5 | 20,5 | 1,45× |
| UNI / fact | 20 | 26,1 | 15,3 | 13,2 | 1,97× |
| UNT / unt | 16 | 26,0 | 20,1 | 15,5 | 1,68× |
| UNT / ctrl | 16 | 19,9 | 14,8 | 10,1 | 1,98× |
| **mind** | 86 | **28,2** | **19,9** | **15,0** | **1,87×** |

(átlagos prompt-tokenszám; leghosszabb: hu 53, en 33, zh 25)

A runbook „hu ≈ 2–3× zh" jóslata **nagyjából igazolódott** (1,87× átlagban, 2,31× a ZH-csoportnál).
A magyar HU-csoportnál a legkisebb az arány (1,45×) — ott a kérdésekben sok a tulajdonnév.
**Ez a diszkusszió korlát-ábrája** (7. ábra), és a D1-nél mérési torzítás forrása is (lásd lent).

## Smoke — generálás három nyelven

`ZH01` (várt: Fujian), zero-shot, greedy, 60 token:

- **hu** → *„…népszerűsége elsősorban a kínai déli tartományokban, különösen Fujian (福建设) és Guangdong (广东)…"* — helyes, de bőbeszédű
- **en** → `**Fujian**` — 6 token, kész
- **zh** → *„法主公信仰主要在中国福建省受到崇拜。"* majd **saját maga folytatja új „问题：" blokkal**

Két gyakorlati következmény, amit a runbook §1 nem említ:
1. **stop-szekvencia kell**: a generált szöveget a következő `\nKérdés:` / `\nQuestion:` / `\n问题：`
   előtt el kell vágni, különben a modell által kitalált kérdés-válasz párok is bekerülnek a pontozásba;
2. **a válasz gyakran teljes mondat** — a pontozás nem lehet string-egyezés, csak judge + ellenőrző kör (ahogy a runbook írja).

## ⛔ A „Base" checkpoint `<think>` blokkot nyit — és ez megette volna a D-mérést

A modell base létére **post-trained viselkedést mutat**: definíciós kérdésre belső monológot kezd
(`<think>\nHmm, the user is asking…`). A hat zero-shot UNT-promptból **négy** így indult, és a
runbook §4b 120 tokenes kerete **teljes egészében a monológra ment volna el — nulla értékelhető
válasszal**. A faktuális promptoknál ritka (1/18).

Két javítást mértem össze (`reports/00_smoke_template.json`, `00_smoke_think.json`):

| beavatkozás | `<think>`-nyitás | mellékhatás |
|---|---|---|
| eredeti (zero-shot) | 4/6 UNT · 1/18 fact | a D-mérés használhatatlan |
| 2-shot minta-Q/A | 1/6 UNT · 2/18 fact | ⛔ a rövid mintaválaszok **levágják a definíció hosszát** („közös pénz") → pont a D1 komponens-lefedettséget rontanák |
| **`<think>` token tiltása** (`bad_words_ids=[[248068]]`) | **0/18** | nincs — a válaszok teljes, tagolt definíciók mindhárom nyelven |

**Döntés: a `<think>` token (id **248068**) tiltása generáláskor**, a runbook zero-shot sablonja marad.
Ez nyelvek között szimmetrikus beavatkozás, egy sorban dokumentálható a módszertanban, és nem nyúl
a prompthoz. (A `</think>` = 248069 nem tiltott.)

## Token-keret — 40/120 helyett 200/500

- **fact 40 → 200**, **unt/ctrl 120 → 500** — két körben mérve.
- Első kör (smoke): 40 tokennél a teljes mondatos magyar válasz elvágódik; 200 tokenes kerettel a hu és en UNT-válaszok **mind** a keretbe ütköztek
  (`n_new == 200`), a zh 96 tokennél magától megállt. ⛔ **Azonos token-keret mellett a magyar válasz
  szisztematikusan kevesebb tartalmat hordoz** (1,87× tokenizációs aszimmetria) — fix kerettel a D1
  `native_hit` nyelvfüggően torzulna, és a „magyarul kevesebb komponens jelenik meg" eredmény a
  tokenizáció műterméke lenne, nem a reprezentációé. Bőkezű keret + a futtatás jegyezze fel, ha egy
  válasz mégis a keretbe ütközött (`truncated: true`) — az elemzésben ezt jelezni kell.
- ⛔⛔ **Második kör (a teljes futás, 258 prompt): a 60/300-as keret sem volt elég** — 91/258 válasz ütközött
  a keretbe, nyelvfüggően: faktuálisnál **hu 54 % · zh 30 % · en 24 %**, az UNT/kontroll 300-as keretén
  **zh 44 %** (a kimeneti oldalon a kínai a leghosszabb, a bemenetin a magyar — a két aszimmetria NEM
  ugyanaz). Végleges: **fact 200 · UNT/kontroll 500**. Greedy mellett a keret növelése a magától megállt
  válaszokat nem érinti (azonos determinisztikus prefix), ezért csak a csonkoltakat futtattuk újra
  (`run.py --only-truncated`).

## Fázis 0 — checklist

- [x] rétegek száma (32), hidden dim (4096), vocab (248 320)
- [x] SAE rétegei: **mind a 32**, `resid_post` — a rétegenkénti SAE-mérés lehetséges
- [x] SAE encoder-képlet: `TopK₅₀(x @ W_enc.T + b_enc)`, ellenőrizve (50 aktív, rekonstrukciós hiba)
- [x] tokenhossz-tábla mind a 258 promptra, csoport × nyelv
- [x] smoke: 3 nyelv × greedy generálás — értelmes válaszok
- [x] `prompts.jsonl` — **258 sor** (162 fact + 48 unt + 48 ctrl)
- [x] futtatókörnyezet és a két blokkoló gotcha (`causal_conv1d`, `hidden_states[-1]`) írásban

**Fázis 1 (`run.py`) indulhat.** A protokoll, amit visz: hook mind a 32 rétegen · greedy · seed 0 ·
`bad_words_ids=[[248068]]` · keret 60/300 · stop-szekvencia-vágás · `truncated` jelzés.
