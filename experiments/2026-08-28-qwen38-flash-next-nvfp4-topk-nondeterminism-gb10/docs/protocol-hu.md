# Flash-Next NVFP4 @ vLLM — nemdeterminizmus temperature 0-n (vizsgálati jegyzőkönyv)

> Állapot: **ROOT CAUSE MEGERŐSÍTVE (2026-08-28 ~13:00): a QSA-indexer `persistent_topk` kernelje.** Nyitva: a javítás prefill-költségének csökkentése (1. mód 2,9× lassabb prefill) — 2./3. mód mérés alatt. Minden szám a `magyar-kie-eval/reports/*.json`-ból számolt
> (`src/szoras.py`, `src/reszletek.py`); a futásonkénti pontok a harness pontozójával, futásonként külön.
> Kapcsolódó: `osszevetes-negyes.md`, `04-F4-nvfp4-indulas.md`, `eredmenyek/02-magyar-eval-reszletek.md`.

## 0. Összefoglaló (2026-08-28, 21:20) — LEZÁRVA

| lépés | eredmény |
|---|---|
| tünet | Flash-Next NVFP4 @ vLLM: azonos greedy kérésre futásonként más kimenet — **13/50 item**, 5-nél a kinyert dátum/összeg is; kontrollok (IQ4_XS/llama.cpp, 35B FP8/vLLM MTP=2, 122B NVFP4/vLLM) **0/50** |
| mérés kizárva | temp 0 explicit, prompt statikus, `Running:` max 1 req, 3 futás/item, kontrollok azonos mércén (§2) |
| hol | a gondolkodás **0. tokenjénél** (magyar/angol nyitány) → a **prefill** logitjai változnak (§3.2) |
| `mtp0` | 11/13 instabil → MTP nem gyökérok (de az üres 16k-elszállás csak MTP alatt) |
| `cgnone` | 13/13 → cudagraph kizárva |
| **`topk` (1. mód: egzakt, teljes stabil sort)** | **0/13 instabil**; szonda **6/6 itemen 10/10 bitre azonos** logit → ⭐⭐⭐ **ROOT CAUSE: QSA-indexer `persistent_topk`** (§3.1c) |
| ára | prefill **2,9× lassabb** (2 370 → 820 tok/s) ⛔ |
| `topk2` (2. mód: `persistent_topk` + utólagos kanonikus rendezés) | **NEM elég**: 3/6 itemen 2–10 változat → a kernel a kiválasztott **HALMAZT** is változtatja, nem csak a sorrendet (§3.1d) |
| **`topk3` (3. mód: `torch.topk` radix-select + kanonikus rendezés)** | ⭐⭐ **6/6 itemen 10/10 bitre azonos**, a logitok = 1. mód; prefill **1 650–1 770 tok/s = a persistent 74 %-a** (1,35× a 2,9× helyett) → **EZ A JAVÍTÁS** (§3.1e) |
| **validáció a 3. móddal — fő suite** | ⭐⭐⭐ **98,00/100 (= elérhető max), 0/50 instabil, 0 formátumhiba, 0 csonkolás**; a stock 97-nél is jobb (T3-05 helyre állt); decode 24,9 tok/s (§3.5) |
| validáció — nehéz suite | **90,00/100**, 0/10 instabil — de a **T14-01 3/3 futáson EGYFORMÁN elszáll** (16 384 token, üres tartalom, azonos SHA) → §3.6 |
| validáció — HU-CH | 9/10 válasz; **HU-CH-09 üres elszállás** (a stock kernellel a CH-02 volt) |
| validáció — hosszú | **100,00/100** (5/5 item 20/20; a 217k-s T22 449 s) |
| ⛔⛔ **átértelmezés** | **az „üres elszállás" NEM a top-k tünete**: greedy+thinking **ismétlési hurok** (§3.6). A stock kernel zaja néha kimenekített belőle (1/150, véletlen); a determinisztikus prefill **reprodukálhatóvá** tette. Utóteszt (3. mód + MTP=0): **T14-01 hurok ELTŰNIK (10/10, 3/3 azonos)**; az MTP=2 a ~5. tokennél tér le a greedy pályáról → **az MTP nem greedy-ekvivalens ezen a modellen**. Mellékeredmény: azonos szerveren a HU-CH 10/10 + a T14-01 hurok bitre azonos két ülésben. Suite-szintű MTP=0 mérés fut (`tmux mtp0suite`) |
| **MTP-ekvivalencia (3. mód, MTP=0 vs MTP=2)** | fő: 97,00 vs 98,00, **9/50 itemen eltérő kimenet, 1 pont (T3-01, az MTP=0 a rosszabb)**; nehéz: 100,00 vs 90,00 (1/10 eltér: a T14-01 hurok); challenge: 9/10 eltér, a hurok ÁTVÁNDOROL (CH-09 → CH-07). Decode 14,8 vs 24,9. → **az MTP nem greedy-ekvivalens, de minőség-semleges; a hurok nem MTP-műtermék** (§3.7) |
| ⭐⭐⭐ **PROD-JAVASLAT** | `qwen38-flash-dgx-topk` image + `VLLM_QSA_EXACT_TOPK=3` + **MTP=2 marad** + PIECEWISE + **hurok-őr a reasoning-streamen** (ismétlés-arány → újrapróba T>0 / presence_penalty). Determinisztikus, 98/100 a fő suite-on, 74 % prefill, 25 tok/s decode |
| hátra | hurok-őr implementálás + mérés (protokoll-változás) (hurok-detektor + újrapróba T>0-val / `presence_penalty` / prompt-egyértelműsítés — mind protokoll-kérdés); `lfs.sha256` a 419 blobra; upstream issue (vLLM `persistent_topk`, #51782 mellé); a docai-evals `results/` + decision-record véglegesítése; cikk |

## 1. A tünet

A Flash-Next NVFP4 (RadixArk checkpoint, blazux `82ed48d` recept: vLLM `v0.1.dev20073` + mmap-PLE, `MTP=2`,
`PIECEWISE` cudagraph 12 splitting op-pal, `CTX=262144`, `SEQS=2`, `GPU_MEM=0.78`) **azonos greedy kérésre
futásonként más kimenetet ad**. A fő suite 50 itemjéből **13** ingadozik 3 futás között.

Ez önmagában „csak" reprodukálhatósági kérdés lenne. A gond az, hogy a harness a többségi kimenetet pontozza,
élesben viszont egyetlen válasz jön — ezért minden futást külön pontoztunk:

| item | többségi | futásonkénti pontok | |
|---|---|---|---|
| T1-01 | 9.00/10 | `[9.0, 9.0, 9.0]` | csak szöveg |
| T3-01 | 2.00/2 | `[2.0, 1.0, 2.0]` | **PONT IS** |
| T3-03 | 2.00/2 | `[2.0, 2.0, 1.0]` | **PONT IS** |
| T3-05 | 1.00/2 | `[1.0, 1.0, 2.0]` | **PONT IS** |
| T4-04 | 2.00/2 | `[2.0, 2.0, 2.0]` | csak szöveg |
| T5-03 | 2.00/2 | `[2.0, 0.0, 2.0]` | **PONT IS** |
| T6-01 | 2.00/2 | `[2.0, 2.0, 2.0]` | csak szöveg |
| T6-02 | 2.00/2 | `[2.0, 2.0, 1.0]` | **PONT IS** |
| T6-03 | 2.00/2 | `[2.0, 2.0, 2.0]` | csak szöveg |
| T6-04 | 2.00/2 | `[2.0, 2.0, 2.0]` | csak szöveg |
| T6-05 | 2.00/2 | `[2.0, 2.0, 2.0]` | csak szöveg |
| T7-09 | 1.00/2 | `[1.0, 1.0, 1.0]` | csak szöveg |
| T10-05 | 2.00/2 | `[2.0, 2.0, 2.0]` | csak szöveg |

**13 instabil itemből 5-nél a kinyert ÉRTÉK is változik** (dátum: 2026-11-10 ↔ 11-05, 10-27 ↔ 10-26; összeg: 6 300 000 ↔ 5 940 000).
A T3-05-nél a többség a ROSSZ válasz (`[1, 1, 2]`) → a többségi szavazás nem menekülési út.
Két futás (T5-03 2. futása; HU-CH-02) **16 384 tokent gondolkodott üres tartalommal** (`finish=length`).

Ugyanezen az itemsoron, ugyanazzal a harnessszel, mind gondolkodó módban:

| motor | instabil |
|---|---:|
| Flash IQ4_XS · llama.cpp | 0/50 |
| 35B FP8 · vLLM (prod image) · **MTP=2** · `reasoning-parser qwen3` | 0/50 |
| 122B NVFP4 · vLLM | 0/50 |
| **Flash NVFP4 · vLLM+mmap-PLE · MTP=2** | **13/50** |

Családonként: T1 1/1 · T2 0/5 · T3 3/5 · T4 1/5 · T5 1/5 · T6 5/5 · T7 1/9 · T8 0/5 · T9 0/5 · T10 1/5 — a T6 mind az 5 itemje, a T2/T8/T9 egyike sem → itemfüggő, nem szórás.

## 2. Önellenőrzés: a mérés kizárva mint ok (2026-08-28)

| ellenőrzés | lelet |
|---|---|
| a kérés greedy? | payload explicit `temperature: 0.0, top_p: 1` minden motoron (`harness.py:70`) |
| a három kérés azonos? | az `uz` a futás-ciklus ELŐTT épül egyszer; a harnessben nincs `random`/`datetime`; az itemek statikus JSONL |
| volt párhuzamos kliens? (köteg-összetétel!) | a teljes vLLM-naplóban `Running:` max **1 req**; a `mon` tmux üres; a porton 1 kapcsolat |
| `--folytat` szétcsúszás? | minden item pontosan 3 futás, 0 `hiba`; 12 instabil a 32k-s, 1 a 262k-s szerverülésből → mindkettőben |
| a kontrollok azonos mércén? | mind gondolkodott (kimeneti/tartalmi token-arány: 35B 55,5 · 122B 42,3 · IQ4_XS 13,8 · NVFP4 15,9), 3 futás, 16k keret |
| **korlát** | a 35B-kontroll MÁS vLLM-build (prod image vs `qwen38-flash-dgx`) → az „azonos motor" közelítő; a builden belüli okot csak az izoláció dönti el |

Hipotézis, amit MEGVIZSGÁLTAM ÉS ELVETETTEM: „a hosszabb dekódolás instabilabb". A prompt-hossz nem jelez előre
(instabil medián 6038 vs stabil 6072 token), a kimeneti hossz korrelál (690 vs 312) — DE a nehéz suite
egy **10,178 tokenes** generálása bitre azonos maradt 3 futáson, és a teljes nehéz suite 0/10 instabil. A hossz nem elégséges ok.

## 3. Izoláció — egyszerre egy kapcsoló

`./izolacio.sh` (the dev DGX Spark): a 13 instabil item × **5 futás** (nagyobb észlelési erő, mint a 3-futásos alap → a 0/13
konzervatív bizonyíték lenne). Minden más bitre azonos a baseline-nal. A harness a `reasoning_content`-et is tárolja
(`gondolkodas`, `gondolkodas_sha`) — a kérést és a pontozást nem érinti.

### 3.1 `ARM=mtp0` — spekulatív dekódolás KI · **KÉSZ**

| item | többségi | futásonkénti pontok | | első eltérés a gondolkodásban | eltérő gondolkodás |
|---|---|---|---|---|---|
| T1-01 | 9.00/10 | `[9.0, 9.0, 9.0, 9.0, 9.0]` | csak szöveg | 0. kar | 5/5 |
| T3-01 | 2.00/2 | `[2.0, 2.0, 1.0, 2.0, 2.0]` | **PONT IS** | 15. kar | 5/5 |
| T3-05 | 2.00/2 | `[1.0, 2.0, 2.0, 2.0, 2.0]` | **PONT IS** | 0. kar | 5/5 |
| T5-03 | 2.00/2 | `[2.0, 2.0, 0.0, 2.0, 0.0]` | **PONT IS** | 0. kar | 5/5 |
| T6-01 | 2.00/2 | `[2.0, 2.0, 2.0, 2.0, 2.0]` | csak szöveg | 15. kar | 5/5 |
| T6-02 | 2.00/2 | `[2.0, 1.0, 2.0, 1.0, 2.0]` | **PONT IS** | 15. kar | 5/5 |
| T6-03 | 2.00/2 | `[2.0, 2.0, 2.0, 2.0, 2.0]` | csak szöveg | 0. kar | 5/5 |
| T6-04 | 2.00/2 | `[2.0, 2.0, 2.0, 2.0, 2.0]` | csak szöveg | 15. kar | 5/5 |
| T6-05 | 2.00/2 | `[2.0, 2.0, 2.0, 2.0, 2.0]` | csak szöveg | 0. kar | 5/5 |
| T7-09 | 1.00/2 | `[1.0, 1.0, 1.0, 1.0, 1.0]` | csak szöveg | 27. kar | 5/5 |
| T10-05 | 2.00/2 | `[2.0, 2.0, 2.0, 2.0, 2.0]` | csak szöveg | 0. kar | 5/5 |

**11/13 instabil, 4-nél a pont is → az MTP NEM a gyökérok.** Két mellékhatása viszont mérve van:
- az „elszálló üres gondolkodás" hibamód MTP=2 alatt 1/150 futás, MTP=0 alatt **0/65** → az MTP saját hibamódot ad hozzá;
- decode 26.4 → **16.1 tok/s** válaszidőre (a spekuláció ára ezen a modellen).

### 3.1b `ARM=cgnone` — cudagraph NONE · **KÉSZ: 13/13 instabil, 5-nél a pont is** → kizárva.

### 3.1c ⭐⭐⭐ `ARM=topk` — egzakt, kanonikus top-k a `persistent_topk` helyett · **KÉSZ: 0/13 instabil**

MTP=2 és PIECEWISE VÁLTOZATLAN, csak a QSA-indexer top-k kernelje cserélve (`qwen38-flash-dgx-topk` image =
az installált `qsa.py` + `VLLM_QSA_EXACT_TOPK=1`; egységteszt a referencia-szemantikára zöld). Mind a 13 item
5/5 futáson bitre azonos — beleértve a T3-05-öt (rossz többség) és a T5-03-at (üres elszállás) is.

**Prefill-szonda** (`src/prefill_szonda.py`: max_tokens=1, top_logprobs=20, 10×, 4 instabil + 2 „stabil" item):

| | `persistent_topk` (cgnone-szerver) | **egzakt top-k** |
|---|---|---|
| top-20 logitvektor bitre azonos 10/10 | **0/6 item** (mind a 6-on 10 különböző változat, a „stabil" T2-01/T8-01-en is) | **6/6 item** |
| 0. token | T3-01 A/We, T10-05 A/The/We, T2-01 A/We | mindenhol 1 féle |
| top-2 rés | 0,0–3,6 nat között ingadozik | fix (pl. T6-02 1,625; T1-01 2,625) |
| prefill tok/s (3k–24k prompt) | 2 180–2 380 | **790–820 (2,9× lassabb)** ⛔ |
| decode tok/s (MTP=2) | 26,4 | 27,3 |

Következtetés: a prefill-nemdeterminizmus UNIVERZÁLIS volt (nem 13 itemé — a suite 13/50-e csak a látható rész),
a forrása a `persistent_topk` (atomicAdd-os slot-kiosztás, `persistent_topk.cuh`, 42 `atomicAdd`; nyitott
correctness-bug #51782). A 0,25–3 nat-os logit-eltérés nem float-zaj: a kiválasztott attention-KONTEXTUS változott.

**Nyitva — a javítás ára:** az 1. mód teljes `sort`-ja 2,9× lassítja a prefillt. A 2. mód (§3.1d) megbukott;
a 3. mód (`torch.topk` radix-select + kanonikus rendezés, egységteszten bitre azonos az 1. móddal) mérés alatt.

### 3.1d `topk2` — `persistent_topk` MARAD, csak a kimenet kanonikus rendezése · **KÉSZ: NEM ELÉG**

Ha a hiba csak az `atomicAdd`-os *slot-sorrendben* lenne, ez ~ingyen javítana. Szonda ugyanazon a 6 itemen:

| item | top-20 változat 10 futásból | 0. token | top-2 rés |
|---|---:|---|---|
| T3-01 | 2 | 1 féle | 0,25–1,125 |
| T6-02 | 2 | 1 féle | 1,5–2,5 |
| T1-01 | **1** ✅ | 1 féle | 2,0 |
| T10-05 | **10** | A/We | 0,125–1,625 |
| T2-01 | **1** ✅ | 1 féle | 0,625 |
| T8-01 | **1** ✅ | 1 féle | 1,125 |

Javult (6/6 → 3/6 item, 10 → 2 változat két itemen), de nem determinisztikus → **a kernel a kiválasztott index-HALMAZT
is változtatja**, nem csak a sorrendjét. Ez konzisztens a nyitott #51782-vel („silently drops top-k candidates when many
values share a coarse histogram bin"): a hisztogram-alapú radix-select a bin-határon versenyhelyzetben más jelölteket tart meg.
A T10-05 (24k prompt, a leghosszabb) a legrosszabb — a hosszabb sorozat több bin-ütközést ad.
→ A 2. mód elvetve; a javításnak a **kiválasztást** kell lecserélnie (1. vagy 3. mód).

### 3.1e ⭐⭐ `topk3` — `torch.topk` (radix-select) + kanonikus rendezés · **KÉSZ: determinisztikus, olcsó**

| | `persistent_topk` | 1. mód (teljes sort) | **3. mód (`torch.topk`)** |
|---|---|---|---|
| top-20 bitre azonos 10/10 | 0/6 item | 6/6 | **6/6** |
| logitok az 1. móddal | — | — | **azonosak** (T6-02 rés 1,625; T1-01 2,625; T10-05 1,125) |
| prefill, 3k prompt | 2 180 tok/s | 792 | **1 645** |
| prefill, 6k prompt | 2 350–2 370 | 819–820 | **1 756–1 760** |
| prefill, 24k prompt | 2 381 | 822 | **1 769** |
| lassulás | 1× | 2,9× | **1,35×** |

A 3. mód `torch.topk(sorted=False)` radix-selectet használ (nem teljes sort), majd a k kiválasztottat két stabil
rendezéssel kanonizálja (index növekvő → érték csökkenő). Egységteszten bitre azonos az 1. móddal; a szondán is.
**Ez a javítás:** `qwen38-flash-dgx-topk` image + `VLLM_QSA_EXACT_TOPK=3`, MTP=2 és PIECEWISE változatlan.
A maradék 26 % prefill-költség a QSA-indexer top-k-jának ára; egy natív determinisztikus kernel (FlashInfer #2661 mintájára,
§bővített 6.3) ezt is visszahozná — ez az upstream kérés tárgya.

### 3.5 Validáció a 3. móddal — teljes suite-ok (2026-08-28 13:43–, `flash-nvfp4-topk3`)

| suite | stock `persistent_topk` | **3. mód** | megjegyzés |
|---|---:|---:|---|
| fő (50×3) | 97,00 · 13/50 instabil · 1 csonkolt | **98,00 · 0/50 · 0** | egyetlen pont változott: T3-05 1→2 (a stock többsége a rossz dátum volt); mind a 13 korábban instabil item 3/3 azonos |
| nehéz (10×3) | 100,00 · 0/10 | **90,00 · 0/10 · 1 formátumhiba** | T14-01: 3/3 futás 16 384 token, üres tartalom, azonos SHA (§3.6) |
| HU-CH (10×1) | 1 üres (CH-02) | 1 üres (**CH-09**) | ugyanaz a hibamód, más tételen |
| hosszú (5×1) | 100,00 | **100,00** | T22 449 s, 10 129 kimeneti token |
| **fő (50×3), 3. mód + MTP=0** | — | 97,00 · 0/50 · 0 | 9/50 item más kimenet, mint MTP=2-vel; 1 pont (T3-01) az MTP=2 javára; decode 14,8 |
| **nehéz (10×3), 3. mód + MTP=0** | — | 100,00 · 0/10 · 0 | 1/10 eltér (a T14-01 hurok MTP=0-val nem jön elő — de a challenge-en a CH-07 igen) |
| decode tok/s (fő, MTP=2) | 26,4 | 24,9 | a prefill-többlet a válaszidő-alapú képletben |

### 3.6 ⛔⛔ Az „üres elszállás" egy MÁSIK hibamód: determinisztikus ismétlési hurok

A T14-01 3. módú gondolkodása 41 835 karakter; a vége ugyanaz a ~180 karakteres bekezdés **22×** ismételve
(„A "pontszám" lehet "5.4." vagy "5.4. pont". A feladat szövege: … A séma: "donto_pont": "pontszám". Ez valószínűleg…"),
az utolsó 4 000 karakter **7 %-a egyedi**; mindhárom futás gondolkodás-SHA-ja azonos. A modell a `donto_pont` mező
formátumán pörög és sosem zárja a gondolkodást → 16 384 token, üres `content`, `finish=length`.

Következtetések:
- Ez **nem a `persistent_topk` tünete**, hanem a greedy + thinking ismert Qwen-gyengesége (a Qwen saját ajánlása:
  thinking-módban ne greedy-vel). A stock kernel zaja néha kimenekítette a modellt a hurokból — ezért volt véletlen
  (1/150 a fő suite-ban, HU-CH-02); a determinisztikus prefill **reprodukálhatóvá** tette (3/3).
- A korábbi §3.1 mondat („az MTP saját hibamódot ad hozzá: az elszállás csak MTP alatt") **gyenge evidencián állt**
  (0/65 a `mtp0` karban, de más itemeken) — az utóteszt dönti el (`tmux utoteszt`: T14-01 + HU-CH-09, 3. mód + MTP=0, 3×).
- ⭐⭐ **Utóteszt (17:29): 3. mód + MTP=0 → T14-01 10/10, 3/3 azonos, NINCS hurok** (864 kimeneti token, helyes JSON).
  Az MTP=2 és az MTP=0 gondolkodása a **~5. tokennél** ágazik el („A felhasználó ” után: „magyar nyelvű kérést tett…”
  vs „egy JSON-sémát kért…”). Az MTP=0 a tiszta autoregresszív greedy, tehát **a spekulatív dekódolás ezen a
  modellen/buildben NEM kimenet-ekvivalens a greedy-vel** — a letérés vitte a modellt a hurokba. A hurok tehát két
  tényező együttese: MTP-műtermék (letérés) + a greedy-thinking hurokhajlam (nem zár). Suite-szintű mérés fut
  (`futtat-topk3mtp0.sh`: fő 50×3 + nehéz 10×3, 3. mód + MTP=0): hány itemen tér el a kimenet MTP-vel vs anélkül.
- ⛔⛔ **Challenge MTP=2 vs MTP=0 (3. mód, mindkettő determinisztikus): 9/10 tételen MÁS a kimenet** (csak HU-CH-08
  azonos) → az MTP pálya-eltérése általános. **A hurok nem tűnt el, átvándorolt**: HU-CH-09 MTP=0-val kizár (11 503 tok),
  viszont **HU-CH-07 MTP=0-val hurokba fut** (16 384 tok, üres; MTP=2-vel 2 033 tok, 626 kar). Hurok-arány mindkét
  módban ~1/10 → **a hurok a greedy+thinking sajátja, nem MTP-műtermék; az MTP csak azt dönti el, melyik bemenet esik
  bele.** A T14-01 „MTP=0-val eltűnik” egyedi eset volt. Következmény: MTP kikapcsolása NEM kezelés; hurok-őr kell.
- Mérnökileg a determinisztikus hiba a jobb: detektálható (ismétlés-arány a gondolkodásban) és kezelhető
  (újrapróba T>0-val vagy `presence_penalty`, vagy a prompt egyértelműsítése). A véletlen nem volt az.
- ⛔ A cikkben a „javítás után 0 elszállás" állítás NEM mondható; a helyes állítás: „a nemdeterminizmus megszűnt, és
  ezzel egy MÁSIK, eddig véletlennek látszó hiba reprodukálhatóvá vált".

### 3.7 Az MTP nem greedy-ekvivalens ezen a modellen — de minőség-semleges (suite-szintű mérés, 3. mód)

| | MTP=2 | MTP=0 | eltérő kimenet | eltérő pont |
|---|---:|---:|---:|---|
| fő (50×3) | **98,00** | 97,00 | **9/50** | 1: T3-01 (2 → 1, az MTP=0 a rosszabb) |
| nehéz (10×3) | 90,00 | **100,00** | 1/10 | 1: T14-01 (hurok csak MTP=2-vel) |
| HU-CH (10×1) | 1 hurok (CH-09) | 1 hurok (**CH-07**) | 9/10 | — |
| decode tok/s | **24,9** | 14,8 | | |
| instabil / csonkolt | 0 / 0 | 0 / 0 | | |

A spekulatív dekódolás elfogadás-logikája ezen a builden nem egzakt greedy (a T14-01-en a ~5. tokennél tér le), az
itemek ~18 %-án más a pálya — de a pontszámra ez zajszintű és irány nélküli (+1 / −10 / 0), a hurok pedig mindkét
módban ~1/10 a challenge-en. Következtetés: **MTP=2 marad** (40 % decode-előny), a hurkot **hurok-őr** kezeli, nem az
MTP kikapcsolása. Ez egyben upstream-jelentendő: az MTP greedy-ekvivalenciája a hibrid GDN+QSA modellen nem áll.

### 3.2 ⭐⭐ Az elágazás a gondolkodás **0. tokenjénél** van

13-ból 12 itemnél az első eltérés a **0. vagy ~6. tokennél** történik — nem felhalmozódó drift:

**T1-01**
```
0: 'A feladat egy JSON-sémának megfelelően kitölteni a szerződés indexálási záradéká'
1: "We need answer user's request. Need produce JSON only. Need analyze Hungarian do"
2: 'We need answer in Hungarian? User asks Hungarian. Need output only JSON schema. '
3: "We need answer user's request. Need produce JSON only. Need analyze Hungarian do"
4: "We need answer user's request in Hungarian? They ask Hungarian document processi"
```

**T3-01**
```
0: "We need answer user's request. Need produce final JSON only. Need solve Hungaria"
1: 'We need answer in Hungarian? User asks Hungarian. Need only JSON schema. Need co'
2: "We need answer user's request. Need produce final JSON only. Need solve Hungaria"
3: "We need answer user's request. Need produce final only JSON. Need solve Hungaria"
4: "We need answer user's request. Need produce final JSON only. Need solve date.\n\nD"
```

**T10-05**
```
0: 'A felhasználó azt kérdezi, hol találom meg azt a szabályt, amely a sűrített leve'
1: "We need answer user's question in Hungarian, based only on document. Need output"
2: 'A felhasználó azt kérdezi, hogy az iratcsomagban hol található az a szabály, ame'
3: 'A felhasználó egy konkrét kérdést tett fel: hol találom meg azt a szabályt, amel'
4: "We need answer user's question in Hungarian, only JSON schema. Need find rule th"
```

A modell futásonként **más nyelven kezd gondolkodni** (magyar „A feladat…" ↔ angol „We need…"), és ezt az első
token dönti el. Az első token a **prefill** kimenete. Determinisztikus prefill mellett egy 10⁻⁶-os holtverseny is
mindig ugyanúgy dől el; itt nem → **a prefill nemdeterminisztikus, a dekódolás csak örökli.** A 35B-n a 0. token
nem holtverseny (0/50), a Flash-en igen: a gondolkodási nyelv váltása a Qwen-thinking ismert jelensége, itt egy
apró numerikus zaj billenti.

### 3.3 Gyanúsítottak a 3.2 után

| # | gyanúsított | prefillben dolgozik? | státusz |
|---|---|---|---|
| 1 | MTP=2 (rejection sampler, `_rejection_kernel` JIT) | nem (decode) | **kizárva mint gyökérok**; saját hibamód (üres elszállás) |
| 2 | PIECEWISE cudagraph (`capture_sizes [1,2,4,8]`) | nem — a 6k-s prefill eager | **kizárva** (`cgnone` 13/13) |
| 3 | mmap-PLE gather 32 szál + pageable host→device másolás | **igen** (6k sor párhuzamosan) | okafogyott (a `topk` kar 32 szállal is 0/13) — a `w1` kar leállítva |
| 4 | **QSA-indexer `persistent_topk`** (atomicAdd slot-kiosztás; GB10-en ez fut a `cooperative_topk` helyett) | **igen** | ⭐⭐⭐ **MEGERŐSÍTETT ROOT CAUSE** — egzakt top-k: 0/13, szonda 6/6 bitre azonos |

A referencia-repo `d2854bf` frissítése és az issue #1 szála **nem említ nemdeterminizmust**; a jschmied-féle
c=1..96 párhuzamos futtatás korrektségi panasz nélkül ment → a 3. gyanúsított gyengült, de nem zárt.

### 3.4 Prefill-szonda — ELVÉGEZVE (eredmények a §3.1c/§3.1d táblákban)

`src/prefill_szonda.py`: azonos prompt, `max_tokens=1`, `top_logprobs=20`, 10×, 4 instabil + 2 „stabil" item — a
dekódolástól függetlenül méri a 0. token logit-szórását. Csak izolációs kör UTÁN futott (köteg-összetétel).
Kimenet: `reports/szonda-{cgnone,topk,topk2,topk3}.json`. Tanulság: **a suite-szintű „stabil" itemek is
nemdeterminisztikusak voltak** (T2-01, T8-01: 10/10 különböző logit) — a 3 futásos suite csak a holtverseny-közeli
itemeken tette láthatóvá; a szonda 10 kérése és a top-20 hash sokkal érzékenyebb mérce, mint a pontszám.

## 4. Mit jelent ez a DocAI-ra

- A Flash NVFP4 a `persistent_topk`-kal **nem KIE-motor** (tízből egy dokumentumon futásonként más összeg/dátum); a 3. módú top-k-val **determinisztikus, MTP-vel együtt**: fő 98/100 (= max), hosszú 100, nehéz 90 (egy hurok-item), 74 % prefill, 25 tok/s decode. **Prod-jelölt a hurok-őrrel** — a greedy+thinking hurok (~1/10 nehéz bemeneten) MTP nélkül is megvan, tehát detektálni és újrapróbálni kell (T>0 / presence_penalty), nem az MTP-t kikapcsolni.
- Az IQ4_XS/llama.cpp determinisztikus (0/50), de a T19-en kvantálási kárt szenved (3,33/10) és a 217k-s prompt 1 121 s.
- Ha az ok a 4. (QSA-kernel), a javítás upstream vLLM-oldali (determinisztikus/batch-invariáns kernelek), nem a miénk.
- A 35B FP8 (prod) 294/300, 0/50 instabil, már üzemel — a döntéshez ezt a viszonyítási alapot kell nézni.

## 5. Gotchák, amik ebből a körből jöttek

- ⛔⛔ **A többségi kimenet pontozása elfedi az instabilitás súlyát** — futásonként külön kell pontozni (`szoras.py`), és a többség lehet a rossz.
- ⛔⛔ **A `content` nem elég** — az elágazás a `reasoning_content`-ben van; enélkül a „hol" kérdés megválaszolhatatlan.
- ⛔ `CTX=32768` + 24 440-es prompt + 16 384 keret = HTTP 400 minden futáson → hamis 77,00; jel: `formatum_hiba: "nincs válasz"` mindenhol.
- ⛔ A hossz-korreláció csábító, de a nehéz suite megcáfolta — a nullhipotézist a saját adaton kell megbuktatni, mielőtt kimondod.
