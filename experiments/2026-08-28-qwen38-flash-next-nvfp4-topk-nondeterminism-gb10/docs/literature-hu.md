# Flash-Next NVFP4 @ vLLM — nemdeterminizmus temperature 0-n (vizsgálati jegyzőkönyv)

> Állapot: **ROOT CAUSE MEGERŐSÍTVE (2026-08-28): a QSA-indexer `persistent_topk` kernelje** — részletek és szonda-számok a `03-nvfp4-instabilitas.md` §3.1c-ben; ez a fájl a bővített irodalmazást tartalmazza. Minden szám a `magyar-kie-eval/reports/*.json`-ból számolt
> (`src/szoras.py`, `src/reszletek.py`); a futásonkénti pontok a harness pontozójával, futásonként külön.
> Kapcsolódó: `osszevetes-negyes.md`, `04-F4-nvfp4-indulas.md`, `eredmenyek/02-magyar-eval-reszletek.md`.

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
| 1 | MTP=2 (rejection sampler, `_rejection_kernel` JIT) | nem (decode) | **kizárva mint gyökérok**; saját hibamód (üres elszállás). Az upstream MTP×cudagraph hibák (§6.4) FULL cudagraphot ill. TurboQuant KV-t igényelnek — nálunk egyik sincs |
| 2 | PIECEWISE cudagraph (`capture_sizes [1,2,4,8]`) | nem — a 6k-s prefill eager | **kizárva** (`cgnone` 13/13) |
| 3 | mmap-PLE gather 32 szál + pageable host→device másolás | **igen** (6k sor párhuzamosan) | okafogyott (egzakt top-k 32 szállal is 0/13) |
| 4 | **QSA-indexer `persistent_topk`** (atomicAdd, GB10-en ez fut) | **igen** | ⭐⭐⭐ **MEGERŐSÍTETT ROOT CAUSE** (egzakt top-k → 0/13; szonda 6/6 bitre azonos) — a §6.3 FlashInfer determinisztikus top-k iránya a megfelelő upstream javítás |
| 5 | **NVFP4 mint felnagyító** — HIPOTÉZIS: szűkíti a logit-réseket, így a meglévő kernelzaj gyakrabban billenti a top-1-et | (az FP4-GEMM split-K maga is lehet zajforrás) | **ÚJ, §6.1 alapján — nem bizonyított.** Külső megfigyelés ugyanezzel a mintázattal (NVFP4 instabil / FP8 stabil, Nemotron-3, Spark), de ott sem mérte senki; a §3.4d rés-mérés a tesztje |

A referencia-repo `d2854bf` frissítése és az issue #1 szála **nem említ nemdeterminizmust**; a jschmied-féle
c=1..96 párhuzamos futtatás korrektségi panasz nélkül ment → a 3. gyanúsított gyengült, de nem zárt.

### 3.4 Következő lépések

**(a) A hiányzó kontroll — ez dönti el a kérdést.** A mostani kontrolljaim (35B FP8, 122B NVFP4) egyszerre más
architektúrán, más builden ÉS más kvantáláson futnak — három változó egyszerre. Kell egy negyedik cella:
**`Qwen/Qwen3.8-Flash-Next-FP8`, ugyanezen a builden, ugyanezen a 13 itemen, 5 futás.** Ez egyetlen változót hagyna:

| eredmény | következtetés |
|---|---|
| 0/13 instabil | az NVFP4 a felnagyító (5. gyanúsított) → a §6.1-es külső eset ismétlődik; a javítás kvantálás-oldali |
| 11–13/13 instabil | a QSA/GDN kernel a zajforrás (3./4. gyanúsított), a kvantálás ártatlan |

⛔⛔ **Ez a cella ezen a hardveren NEM fut le.** A `03-kvantalas-es-memoria.md`-ben a mért tenzortérképből számoltuk:
a nem-PLE súly FP8-ban **113,73 GiB**, a keret **112,16 GiB** — a PLE-mmap már bele van számolva, és így is 1,57 GiB-tel
nem fér, KV-nak nulla marad. Egy másik kvantáló NVFP4-checkpointja (Inferact, primitive-ai) vagy a W4A16 más változót
cserélne (kvantáló ill. séma), nem a precizitást. Az egyetlen-változós kontroll tehát nálunk nem létezik; ami marad,
az a (d) prefill-szonda közvetett bizonyítéka.

**(b) `VLLM_BATCH_INVARIANT=1` próba.** Várhatóan `not supported for GDN_ATTN` hard errorral elszáll (§6.2) —
de maga a hibaüzenet is jelentendő lelet: dokumentálja, hogy ezen a modellen a hivatalos determinizmus-út zárva van.

**(c) A QSA-indexer determinisztikus útjának ellenőrzése a futó image-ben** — a FlashInfer #2661 merged (§6.3);
kérdés, hogy a vLLM-build Flash-Next sparse-indexere használja-e (`grep deterministic` a konténerben a
`sparse_attn_indexer` kódján). Olcsóbb bármelyik mérésnél, és ha nem használja, kész a javítási irány.

**(d) Közvetlen prefill-szonda, ha a `w1` sem hoz 0/13.** Azonos prompt, `max_tokens=1`, `logprobs=5`, 10× — a
dekódolástól függetlenül mutatja a 0. token logit-szórását és a holtverseny szélességét. Csak a körök UTÁN, hogy ne
torzítsa a köteg-összetételt. **Kiegészítés a §6.1 után:** ne csak azt mérjem, *változik-e* a top-2 rés, hanem hogy
*mekkora*. Ha a rés nagyságrendje egybeesik a mért kernelzajjal → az 5. gyanúsított (NVFP4 mint felnagyító)
közvetlen bizonyítéka. Ha a top-2 rés futásonként változik → prefill-kernel (4.); ha stabil, de a token vált → a gather (3.).

## 4. Mit jelent ez a DocAI-ra

- A Flash NVFP4 pontszáma a négy közül a legjobb (297/300), **de így nem KIE-motor**: tízből egy dokumentumon futásonként más összeg/dátum.
- Az IQ4_XS/llama.cpp determinisztikus (0/50), de a T19-en kvantálási kárt szenved (3,33/10) és a 217k-s prompt 1 121 s.
- Ha az ok a 4. (QSA-kernel), a javítás upstream vLLM-oldali (determinisztikus/batch-invariáns kernelek), nem a miénk.
- **Új (§6.2):** a vLLM batch-invariáns módja NEM fedi le a spekulatív dekódolást és a prefix cachinget (az NVFP4-ről
  és a sparse attentionről nem nyilatkozik), a GDN-rétegeken pedig hard errorral elszáll. Vagyis erre a modellre **jelenleg nincs támogatott
  determinizmus-út vLLM alatt** — ez nem hangolási kérdés, hanem lefedettségi hiány. KIE-motorként ez önmagában NO-GO.
- A 35B FP8 (prod) 294/300, 0/50 instabil, már üzemel — a döntéshez ezt a viszonyítási alapot kell nézni.

## 5. Gotchák, amik ebből a körből jöttek

- ⛔⛔ **A többségi kimenet pontozása elfedi az instabilitás súlyát** — futásonként külön kell pontozni (`szoras.py`), és a többség lehet a rossz.
- ⛔⛔ **A `content` nem elég** — az elágazás a `reasoning_content`-ben van; enélkül a „hol" kérdés megválaszolhatatlan.
- ⛔ `CTX=32768` + 24 440-es prompt + 16 384 keret = HTTP 400 minden futáson → hamis 77,00; jel: `formatum_hiba: "nincs válasz"` mindenhol.
- ⛔ A hossz-korreláció csábító, de a nehéz suite megcáfolta — a nullhipotézist a saját adaton kell megbuktatni, mielőtt kimondod.
- ⛔ **A kontrollcella nem ér semmit, ha egyszerre több változóban tér el a kezelt cellától** (§3.4a) — a 35B/122B kontroll
  három változót cserél egyszerre, ezért nem tud különbséget tenni „kvantálás" és „kernel" között. ÉS: az egyetlen-változós
  cella (Flash FP8) a saját memóriaszámításunk szerint nem fér el a Sparkon — ezt a javaslat előtt kellett volna megnézni.
- ⛔ **Irodalmazásnál az issue CÍMÉT és a lezáró fixet is olvasd, ne csak a tünetet** — a #40880 háromtényezős (TurboQuant),
  a #27433 TODO-listáján nincs NVFP4/sparse attention; mindkettőt túl tágan idéztük az első vázlatban (forrásból javítva 08-28).

## 6. Külső visszhang — mit jelentettek mások (irodalmazás 2026-08-28)

**Pontosan ezt a kombinációt (Flash-Next NVFP4 + GB10 + mmap-PLE) senki nem jelentette nyilvánosan.** A blazux README,
a hivatalos vLLM-recept és a HF-diszkussziók egyike sem említ determinizmust. A négy gyanúsított viszont
külön-külön dokumentált — és a lényeg az, hogy egyik sincs lefedve a hivatalos determinizmus-úton.

### 6.1 A legközelebbi eset: ugyanez NVFP4-en, ugyanezen a hardveren

Az NVIDIA fórumon `sertitto` a mi mintázatunkat írja le: **Nemotron-3-Nano-30B-A3B-NVFP4**, DGX Sparkon,
`temperature=0` + `seed 42` + `VLLM_BATCH_INVARIANT=1` + FlashInfer — és futásonként más kimenet. A döntő mondata:
**ugyanennek a modellcsaládnak az FP8 változatán determinisztikus volt.** Ez a mi 35B FP8 = 0/50 vs Flash NVFP4 = 13/50
kontrasztunk, független forrásból, ugyanazon a GPU-n.

A szálban adott magyarázat („kisebb kvant → nagyobb variabilitás") fizikailag pongyola. A mi HIPOTÉZISÜNK rá:
**a 4 bit önmagában nem okoz nemdeterminizmust, hanem összeszűkíti a logit-réseket**, így a már meglévő kernelzaj
gyakrabban billenti át a top-1-et — ez illene a §3.2 mechanizmusához (a 0. token holtversenye nem *keletkezik* az
NVFP4-től, csak *láthatóvá* válik). ⚠️ Nem bizonyított: a fórumon senki nem mérte, és az NVFP4-GEMM-kernelek
(CUTLASS/FlashInfer FP4, split-K) **maguk is** lehetnek redukciós-sorrend-függők, azaz zajforrások. A §3.4d rés-mérés
dönti el. → 5. gyanúsított a §3.3-ban, hipotézisként.

Ugyanez a felhasználó **gpt-oss-120b-n el is érte a bit-azonosságot Sparkon**:
`VLLM_BATCH_INVARIANT=1` + `VLLM_ENABLE_V1_MULTIPROCESSING=0` + `--max-num-seqs 1` + `--no-enable-prefix-caching`
+ `--attention-backend FLASHINFER` + `--quantization mxfp4 --mxfp4-backend CUTLASS`. A GB10 tehát nem akadály —
de az út MXFP4-en és sűrű attentionön vezet, nem a miénken.

### 6.2 ⭐⭐ A batch-invariáns út a mi modellünkön el van zárva

A vLLM batch-invariancia tracking issue (#27433) nyitott TODO-listáján (2026-08-28-án ellenőrizve) ott van:
**`Speculative decoding support (this might be hard)` · `Prefix caching support`** (+ FLASHINFER_MLA, AMD, XPU).
⚠️ Az NVFP4 és a sparse attention **NINCS** a listán — sem lefedettként, sem hiányként; róluk az issue nem mond semmit.
Tehát a 2. és az 1. gyanúsított biztosan lefedetlen, a 4. és 5. státusza az issue-ból nem dönthető el.

Ennél konkrétabb: **vLLM #42960** — `VLLM batch_invariant mode is not supported for GDN_ATTN`, hard error a
Qwen3-Next / Qwen3.6 hibrid Mamba+GDN modelleken. A Flash-Next **négyből három rétege GDN**, tehát ha kontrollnak
bekapcsolnánk a determinisztikus módot, valószínűleg el sem indul. Következmény: **nincs „kapcsold be a
determinizmust és nézd meg" mérésünk** — ezért lett a §3.4b önálló lépés, és ezért NO-GO a §4-ben.

### 6.3 A 4. gyanúsított nem spekuláció — dokumentált, és van rá javítás

**FlashInfer #2584**: a top-k kernelek **atomicokat használnak a holtversenyes elemekre**, a kimenet
szálütemezéstől függ — nevesítve a sparse attention indexerekben (DSA indexer). A GLM-5 paper szerint ez
RL-tréningben néhány lépés alatt drasztikus romlást és éles entrópiaesést okozott. Az issue **le van zárva a #2661
PR-rel**: determinisztikus tie-break index szerint (kisebb index nyer), opcionális flag mögött, hogy ne fizessen
érte, akinek nem kell.

Ez módosítja a §3.3 4. sorát: nem „a mi kapcsolóinkkal nem javítható", hanem **meg kell nézni, a Flash-Next
QSA-indexere megkapta-e ezt a determinisztikus utat.** És ez magyarázza az architektúra-specifikusságot is:
a 35B/122B-n nincs ilyen kernel → 0/50.

A DeepSeek-V4-Flash determinisztikus-inference projekt kimondja, amit a §3.2-ben mértünk:
*„variable-length padding or dynamic kernel selection can introduce floating-point summation order changes…
even at `temperature=0`"* — vagyis **bs=1-nél is**, a köteg-összetételtől függetlenül. Ez a §2 „max 1 req"
ellenőrzésünket nem érvényteleníti, hanem megmagyarázza, miért nem volt elég: a fixed-shape padding az ő kerülőútjuk.

### 6.4 Az MTP-mellékhatásunk is ismert hibamód

**vLLM #40880** (lezárva): MTP × **TurboQuant KV-kvantálás** × cudagraph capture Qwen3-Next hibriden **degenerált
kimenet** — csonkolt generálás (a várt „silver platypus 22" helyett csak „silver"). ⚠️ Háromtényezős hiba, a harmadik
tényezőt (3-bites TurboQuant KV) mi nem használjuk; a lezáró fix (#40914) **TurboQuant-specifikus**, a gyökérok egy
`cu_seqlens_k = cu_seqlens_q` első-chunk-prefill feltevés volt (a bejelentő „SSM/conv állapot" gyanúja nem igazolódott).
Workaround ott: `cudagraph_mode NONE` (33 TPS a 85 helyett).

A TurboQuant NÉLKÜLI MTP×cudagraph mechanizmus a **#53051** (2026-08-20, nyitott): egy prefill FULL cudagraphba
diszpécselődik, ha a prompt pontosan `1+k` token (`_is_uniform_decode` puszta alak-ellenőrzés) → néma GDN-állapotvesztés.
**De csak `FULL`/`FULL_AND_PIECEWISE` módban; „PIECEWISE vagy `--enforce-eager` → helyes kimenet."**

Mi PIECEWISE-en futunk, 6k-s promptokkal → **egyik precedens sem a mi esetünk**; a tanulság fordított: a PIECEWISE
mindkét ismert hiba JÓ oldalán van. A `cgnone` kör így kizárás-értékű marad, de a `mtp0+cgnone` együttes cella
igénye (korábbi §3.4c) ezekből NEM következik — törölve.

### 6.5 Amit senki nem írt le

**A gondolkodási nyelv futásonkénti váltását ugyanarra a promptra** sehol nem találtam jelentve. Ez a mi leletünk,
és ez a legjobb egysoros demója a jelenségnek — a per-run pontozással együtt (13/50, ebből 5 értékhordozó)
erősebb bizonyíték, mint bármi a fórumokon. **Érdemes issue-t nyitni vele** a blazux repóban és/vagy a vLLM-ben.

### 6.6 Források

| # | forrás |
|---|---|
| 6.1 | [Why nemotron 3 NVFP4 models are not deterministic using vLLM?](https://forums.developer.nvidia.com/t/why-nemotron-3-nvfp4-models-are-not-deterministic-using-vllm/372685) · [Deterministic gpt-oss-120b using vLLM on a DGX Spark](https://forums.developer.nvidia.com/t/deterministic-gpt-oss-120b-using-vllm-on-a-dgx-spark/370811) |
| 6.2 | [vLLM #27433 — Batch Invariant Feature and Performance Optimization](https://github.com/vllm-project/vllm/issues/27433) · [vLLM #42960 — Batch-invariant support for GDN_ATTN](https://github.com/vllm-project/vllm/issues/42960) · [vLLM Batch Invariance dokumentáció](https://docs.vllm.ai/en/latest/features/batch_invariance/) |
| 6.3 | [FlashInfer #2584 — Deterministic top-k kernels for sparse attention](https://github.com/flashinfer-ai/flashinfer/issues/2584) · [kingcharlezz/deterministic-inference-b300-deepseekv4flash](https://deepwiki.com/kingcharlezz/deterministic-inference-b300-deepseekv4flash/1.2-key-concepts-and-terminology) |
| 6.4 | [vLLM #40880 — MTP × TurboQuant × CUDA graph capture degenerate output on Qwen3-Next hybrid](https://github.com/vllm-project/vllm/issues/40880) · [vLLM #53051 — Prefill misdispatched into spec-decode FULL cudagraph (prompt == 1+k tokens), silent GDN state loss](https://github.com/vllm-project/vllm/issues/53051) |
| háttér | [Defeating Nondeterminism in LLM Inference — Thinking Machines Lab](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) · [LLM-42: Enabling Determinism in LLM Inference with Verified Speculation](https://arxiv.org/abs/2601.17768) |
| recept | [blazux/qwen3.8-Flash-DGX](https://github.com/blazux/qwen3.8-Flash-DGX) · [Qwen3.8-Flash-Next vLLM recept](https://recipes.vllm.ai/Qwen/Qwen3.8-Flash-Next) |
