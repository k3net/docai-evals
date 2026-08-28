# Qwen3.8-Flash-Next NVFP4 vLLM instabilitás – internetes kutatási jelentés

**Dátum:** 2026-08-28  
**Vizsgált környezet:** NVIDIA DGX Spark / GB10, Qwen3.8-Flash-Next, RadixArk NVFP4 checkpoint, vLLM, mmap PLE  
**Kiinduló implementáció:** [blazux/qwen3.8-Flash-DGX](https://github.com/blazux/qwen3.8-Flash-DGX)

## Vezetői összefoglaló

> **Frissítés 2026-08-28 13:00 — a jelentés fő hipotézise MÉRÉSSEL IGAZOLÓDOTT.** A `persistent_topk` egzakt, kanonikus top-k-ra cserélve (MTP=2 és cudagraph változatlan) a 13 instabil item 0/13-ra stabilizálódott, a prefill-szonda 6/6 itemen 10/10 bitre azonos logitvektort ad (előtte 6/6-on 10/10 különbözőt). Ára: az 1. mód (teljes sort) 2,9× lassabb prefill; a 2./3. mód (kanonikus rendezés a kernel után / `torch.topk`) mérés alatt. Részletek: `03-nvfp4-instabilitas.md` §3.1c.

A `temperature=0` mellett jelentkező változó kimenet nem egyedi jelenség: vLLM alatt több Qwen, MoE és kvantált modellnél dokumentáltak már azonos vagy nagyon hasonló greedy instabilitást. A pontos konfigurációra – Qwen3.8-Flash-Next + RadixArk NVFP4 + mmap PLE + egy GB10 – azonban nem található nyilvános hibajegy. A jelenlegi mérés ezért valószínűleg az első erős, ismételt reprodukció ezen a konkrét útvonalon.

A rendelkezésre álló eredmények alapján:

- az MTP nem az alapvető ok, mert kikapcsolva a 13 problémás mintából 11 továbbra is instabil maradt;
- az MTP vagy speculative útvonal ugyanakkor külön szerepet játszhat a 16 384 tokenig futó, üres tartalmú reasoning hibában;
- az mmap worker-race lehetséges, de a forráskód és a gyenge upstream smoke teszt alapján jelenleg kevésbé erős gyanúsított;
- a legerősebb QSA-specifikus hipotézis a GB10-en használt `persistent_topk` kiválasztási útvonal;
- a QSA split-K merge kernel valószínűleg nem vesz részt a hosszú prompt utáni első token prefill-számításában, ezért a JIT-logban látott kernelnév önmagában nem lokalizálja oda a hibát;
- determinisztikus KIE-feladathoz a jelenlegi Qwen3.8 NVFP4 recept még nem tekinthető üzembiztosnak; az ellenőrző mérésben stabil 35B FP8 útvonal jelenleg biztonságosabb.

## A helyi reprodukció összefoglalása

Azonos, egymás után küldött greedy kérések mellett:

- 50 mintából 13 legalább egyszer eltérő választ adott három futás során;
- 5 minta esetében az eltérés a kinyert értéket vagy a pontszámot is megváltoztatta;
- két futás 16 384 reasoning tokent használt fel, majd üres `content` mezővel fejeződött be;
- az eltérés gyakran már a reasoning első karakterénél vagy tokenjénél jelentkezett;
- egyes futások között magyar–angol nyelvváltás is történt;
- nem futott párhuzamos kliens, és a szerveren egyszerre csak egy kérés volt aktív.

Kontrollok:

| Modell és futtató | Eltérés |
| --- | ---: |
| llama.cpp IQ4_XS | 0/50 |
| 35B FP8, vLLM, MTP=2 | 0/50 |
| 122B NVFP4, vLLM | 0/50 |
| Qwen3.8 Flash NVFP4, vLLM | 13/50 |

Az MTP kikapcsolása után a 13 problémás mintából 11 továbbra is instabil volt, és 4 esetben a pontozás is változott. Ez erős bizonyíték arra, hogy az alapvető instabilitás nem az MTP-ből ered. Az MTP nélküli futásban ugyanakkor megszűnt a hosszú, üres reasoning runaway, így az külön hibaág lehet.

## Nyilvánosan dokumentált hasonló esetek

| Forrás | Hasonlóság | Megfigyelés |
| --- | --- | --- |
| [vLLM #17759](https://github.com/vllm-project/vllm/issues/17759) | magas | Qwen3-32B alatt egymás után futtatott, azonos `temperature=0` kérések eltérő válaszokat adnak. A hibajegy root cause nélkül, stale állapot miatt zárult. |
| [vLLM #27076](https://github.com/vllm-project/vllm/issues/27076) | magas | Qwen3-30B-A3B AWQ/Marlin esetén fix seed és greedy dekódolás mellett is változik a kimenet; a nem AWQ modell stabil. |
| [vLLM #3432](https://github.com/vllm-project/vllm/issues/3432) | közepes | Mixtral GPTQ offline ciklusban tíz azonos greedy kérésből több különböző kimenetet ad, miközben Transformers alatt stabil. |
| [vLLM #7779](https://github.com/vllm-project/vllm/issues/7779) | közepes | Online vLLM kiszolgálásnál már az első token logprobjai is változnak; az offline futás stabil. |
| [vLLM #53257](https://github.com/vllm-project/vllm/issues/53257) | **gyenge / más hibaosztály** (forrásból javítva 08-28) | DeepSeek-V4 Flash NVFP4, `temperature=0`, a ráta a konkurenciával nő. A bejelentő kifejezetten elhatárolja a redukciós-sorrend zajtól („This is not float non-determinism from reduction order"), `--enforce-eager` alatt is reprodukál, és a `dspark` spekulatív draft `probabilistic` mintavételére / seed-kezelésre vezeti vissza. Nálunk nincs konkurencia és MTP nélkül is instabil → nem ugyanaz a mechanizmus. |
| [SGLang #35860](https://github.com/sgl-project/sglang/issues/35860) | **nem releváns** (forrásból javítva 08-28) | Nem hibajegy, hanem „[Playground] Verified cell": egy igazolt konfigurációs cella **Qwen3.8-27B**-re (sűrű modell, nem Flash-Next), DFlash2 spekulációval, „greedy, deterministic stack" felirattal. Instabilitást nem jelent; a redukciós-sorrend mondat nem szerepel benne. |
| [RadixArk checkpoint discussion #3](https://huggingface.co/RadixArk/Qwen3.8-Flash-Next-NVFP4/discussions/3) | részleges | Ugyanezzel a checkpointtal, SGLang és NEXTN mellett hosszú, hibás ismétlődő tokenfolyamot (`!!!!…`) és tokenkeret-kimerülést jelentettek két DGX Sparkon. Ez a runaway hibához kapcsolódhat, de az MTP nélkül is megmaradó instabilitást nem magyarázza. |
| [vLLM #53919](https://github.com/vllm-project/vllm/issues/53919) · [#53912](https://github.com/vllm-project/vllm/issues/53912) (a HF #3 szálból, `joelafrite`) | **közepes — a runaway ághoz** (felvéve 08-28) | Qwen3.8-27B NVFP4, hybrid GDN + MTP k=2 + prefix caching, RTX 5090, vLLM 0.27.1: **16/288 sérült válasz spekulatív dekódolással**, ugyanaz a `!!!!…` szignatúra; a tanács: „disable speculative decoding first". Cross-engine párja a mi 16 384 tokenes üres-reasoning hibánknak, ami MTP=0 alatt 0/65-re tűnt el. |

## Miért nem garantál determinisztikus választ a `temperature=0`?

A `temperature=0` a dekóder tokenválasztását teszi greedyvé: az aktuális logitvektor legnagyobb értékű tokenje kerül kiválasztásra. Nem garantálja azonban, hogy a GPU minden forward passban bitazonos logitvektort állít elő.

Ha két token logitja nagyon közel van egymáshoz, az alábbiak bármelyike felcserélheti a sorrendjüket:

- eltérő párhuzamos redukciós sorrend;
- atomikus műveletek nem rögzített végrehajtási sorrendje;
- BF16 vagy NVFP4 kerekítési különbség;
- eltérő sparse-attention blokk- vagy expert-sorrend;
- nem determinisztikus kernelválasztás vagy autotuning;
- aszinkron végrehajtási vagy memória-élettartam hiba.

Ez összhangban áll azzal, hogy az eltérés sokszor már az első reasoning tokennél megjelenik. Egy korai tokeneltérés után a két autoregresszív futás természetes módon teljesen eltérő pályára kerülhet.

## A legerősebb forráskód-alapú hipotézis: QSA `persistent_topk`

A jelenlegi Qwen3.8 upstream fejlesztői ág QSA-kódja az SM120 eszközcsaládon nem a cooperative, hanem a `persistent_topk` implementációt választja. A GB10 SM121 architektúrája ebbe az eszközcsaládba tartozik:

- [QSA top-k útvonal kiválasztása](https://github.com/peakcrosser7/vllm/blob/release/qwen38next/vllm/models/qwen4_exp/nvidia/ops/qsa.py#L788-L799)
- [`persistent_topk` CUDA-implementáció](https://github.com/peakcrosser7/vllm/blob/release/qwen38next/csrc/libtorch_stable/persistent_topk.cuh)

A CUDA-kód több `atomicAdd` művelettel osztja ki a kiválasztott elemek kimeneti helyét. Emiatt azonos elemhalmaz mellett sem feltétlenül kanonikus az indexek sorrendje. A QSA sparse attention ezeket az indexeket közvetlenül fogyasztja; eltérő feldolgozási sorrend BF16-ban kismértékben megváltoztathatja az online softmax és az összegzés eredményét.

A `persistent_topk` komponenshez már dokumentáltak correctness hibát:

- [vLLM #51782 – persistent top-k candidate overflow](https://github.com/vllm-project/vllm/issues/51782)
- [vLLM #52149 – nyitott javítási PR](https://github.com/vllm-project/vllm/pull/52149)

Az ismert hiba bizonyos eloszlásoknál elveszíthet valódi top-k jelölteket, és az atomikus sorrend befolyásolhatja, mely jelöltek maradnak meg. Ez nem bizonyítja, hogy a rövidebb helyi promptnál pontosan ugyanez az overflow következik be. Azt viszont bizonyítja, hogy a selector tud végrehajtási sorrendtől függő és csendesen hibás eredményt adni.

A referencia-tesztek rendezés után hasonlítják össze a kiválasztott indexeket. Ez az elemhalmaz helyességét ellenőrzi, de nem bizonyítja az end-to-end sorrenddetermináltságot.

**Státusz:** erős, forráskódból levezetett hipotézis, még nem igazolt root cause.

## A QSA split-K merge hipotézis pontosítása

A jelenlegi forrás a QSA split számát a prefill sorainak számából határozza meg. Nagy prefillnél `target_splits=1` értéket választ; ilyenkor közvetlenül írja az eredményt, és kihagyja a merge kernelt:

- [QSA split-K döntési és merge logika](https://github.com/peakcrosser7/vllm/blob/release/qwen38next/vllm/models/qwen4_exp/nvidia/ops/qsa.py#L854-L938)

A több ezer tokenes prompt utáni első generált tokennél ezért valószínűleg nem a `_qsa_merge_splitk_kernel` okozza az eltérést. A `_splitk_kernel` JIT-név akkor is megjelenhet, ha a tényleges split-szám egy.

A konténerben használt csomag a `qwen3_8_flash_next` modulnevet viseli (nem `qwen4_exp`), de a kód azonos —
ellenőrizve az installált forrásban 08-28 (ld. „Az installált QSA-forrás ellenőrzése").

## mmap PLE és MoE értékelés

### mmap PLE

Az mmap implementáció a PLE-sorokat elkülönített kimeneti tartományokba írja, majd megvárja a worker-feladatok befejezését; első ránézésre nem látható nyilvánvaló adatverseny. Az upstream mmap PR egy 1000 soros referencia-összevetést és két azonos greedy futást közöl eltérés nélkül:

- [vLLM #54129 – mmap PLE támogatás](https://github.com/vllm-project/vllm/pull/54129)

Ez túl gyenge validáció ahhoz, hogy kizárja a hibát, ezért a `WORKERS=1` teszt indokolt. A jelenlegi bizonyítékok alapján azonban az mmap worker-race gyengébb hipotézis, mint a QSA top-k útvonal.

### NVFP4 MoE

A vLLM VLLM_CUTLASS NVFP4 MoE backendhez bekerültek batch-invariance ellenőrzések és ütemezési korlátozások:

- [vLLM #40372 – batch-invariant NVFP4 MoE](https://github.com/vllm-project/vllm/pull/40372)

Ez csak akkor csökkenti érdemben a MoE gyanúját, ha a szerver ténylegesen a VLLM_CUTLASS backendet használja.
**Ellenőrizve az indulási logban (08-28):** `Using 'FLASHINFER_CUTLASS' NvFp4 MoE backend out of potential backends:
['FLASHINFER_TRTLLM', 'FLASHINFER_CUTEDSL', 'FLASHINFER_CUTEDSL_BATCHED', 'FLASHINFER_CUTLASS', 'VLLM_CUTLASS',
'MARLIN', 'HUMMING', 'EMULATION']` → **nem a VLLM_CUTLASS**, a #40372 batch-invariáns út nálunk nem él; a MoE
gyanú NEM csökkent. (Kísérleti kar lehet: `VLLM_NVFP4_MOE_BACKEND=VLLM_CUTLASS` vagy a megfelelő kapcsoló, ha a
build ismeri — ekkor a #40372 útja tesztelhető.)

## Javasolt diagnosztikai sorrend

### 1. Meglévő izolációs tesztek befejezése

Ami ténylegesen fut (`./izolacio.sh`, the dev DGX Spark): minden kar **egyetlen változót** cserél a baseline-hoz
(MTP=2, PIECEWISE, WORKERS=32) képest, a 13 problémás mintán, 5 futással:

1. `mtp0` — MTP ki (**kész**: 11/13 instabil, 4-nél a pont is);
2. `cgnone` — `cudagraph_mode=NONE`, MTP=2 marad (**fut**; az első 3 item instabil);
3. `w1` — `VLLM_PLE_MMAP_WORKERS=1`, MTP=2 marad (beütemezve).

⚠️ Ez eltér a jelentés eredeti javaslatától (halmozott kizárás, MTP mindenhol ki). Az egyváltozós elrendezés
tisztább attribúciót ad; ha a `w1` sem hoz 0/13-at, jön a halmozott `mtp0+w1` kar, majd az 5. pont A/B-je.

### 2. Első token logitvizsgálata

Azonos, már renderelt prompttal:

- `max_tokens=1`;
- `temperature=0`;
- `top_p=1`;
- `top_logprobs=20`;
- 10–20 ismétlés.

Rögzítendő:

- kiválasztott első token ID és szöveg;
- a top 20 token ID-ja és logprobja;
- az első és második token közötti logit- vagy logprob-különbség;
- requestenként azonos prompt-byte-hash.

Ez igazolja, hogy már a prefill utáni logitvektor változik-e, de önmagában még nem lokalizálja a kernelt.

### 3. Az installált QSA-forrás ellenőrzése

```bash
docker exec qwen38-flash bash -lc \
'rg -n "persistent_topk|cooperative_topk|base_programs|target_splits" \
/usr/local/lib/python3.12/dist-packages/vllm/models/qwen3_8_flash_next \
/usr/local/lib/python3.12/dist-packages/vllm/models/qwen4_exp 2>/dev/null'
```

A konténer nevét szükség esetén módosítani kell.

**Elvégezve 2026-08-28 (konténer `qwen38-flash`, vLLM `0.1.dev20073+g8e685d198`):** az installált
`vllm/models/qwen3_8_flash_next/nvidia/ops/qsa.py` (1 115 sor) `:788–797` **ugyanaz a választási logika**
(`not current_platform.is_device_capability_family(120)` → `persistent_topk`), tehát a GB10-en ténylegesen a
`persistent_topk` fut. A split-K döntés is azonos: `:873` `target_splits = 1` nagy prefillnél, `:881`/`:935`
`if num_splits == 1` → a merge kernel kimarad. A 05:22-es `_qsa_merge_splitk_kernel` JIT tehát dekódolás közben
jött (`q.shape[0] = 1` → `base_programs` ≤ 512), nem a prefillben — a jelentés feltevése igazolódott.

### 4. QSA top-k sorrend és elemhalmaz mérése

Az utolsó prefill sor kiválasztott blokkindexeiről minden futásban két hash készüljön:

1. hash az indexek eredeti sorrendjében;
2. hash a rendezett indexekből.

Értelmezés:

| Eredmény | Következtetés |
| --- | --- |
| Az eredeti hash változik, a rendezett stabil | Ugyanaz az elemhalmaz, de változó sorrend; valószínű redukciósorrend-hatás. |
| Mindkét hash változik | Maga a top-k kiválasztás vagy a látható tokenhalmaz instabil. |
| Mindkét hash stabil, de a logitek változnak | A hiba a későbbi QSA attention, MoE vagy más prefill kernel felé tolódik. |

### 5. Döntő `persistent_topk` A/B teszt

Diagnosztikai célból a `persistent_topk` ideiglenesen cserélhető egzakt, rendezett `torch.topk(..., sorted=True)` műveletre. Ez lassabb lehet, de megfelelő izolációs teszt.

**Nem kell hozzá image-build:** a futó konténerben az installált
`/usr/local/lib/python3.12/dist-packages/vllm/models/qwen3_8_flash_next/nvidia/ops/qsa.py:797`
(`torch.ops._C.persistent_topk`) helyére egy egzakt, rendezett `torch.topk`-wrapper `docker cp`-vel bemásolható,
konténer-restart, és a 13 item × 5 futás eldönti. A §4 index-hash mérés ugyanebbe a wrapperbe tehető.

Ha a módosítás után a korábban problémás 13 minta ismételt futásban stabil lesz, a root cause a QSA selectorra vagy annak sorrendjére lokalizálható. Ha nem stabilizál, a vizsgálatot a QSA attention és a ténylegesen használt NVFP4 MoE kernel felé kell folytatni.

### 6. Szinkron végrehajtási kontroll

Egy külön futtatási kar:

```bash
CUDA_LAUNCH_BLOCKING=1
```

- ha ettől stabilizálódik, aszinkron race, hibás stream-szinkronizáció vagy memória-élettartam probléma valószínűbb;
- ha változatlanul instabil, numerikus redukciós vagy feldolgozási sorrendből eredő eltérés valószínűbb.

Ez a beállítás jelentősen lassíthat, és elfedhet egyes race-eket, ezért csak diagnosztikai kontrollként használható.

### 7. Backend rögzítése

Az indulási logból meg kell őrizni:

- QSA backend és kernelútvonal;
- NVFP4 MoE backend;
- attention backend;
- CUDA graph mód;
- speculative/MTP állapot;
- chunked-prefill paraméterek;
- vLLM és a konténer pontos commitja vagy image digestje.

**Rögzítve a naplóból (2026-08-28, `qwen38-flash`):**

| tétel | érték |
| --- | --- |
| vLLM | `0.1.dev20073+g8e685d198` (image `qwen38-flash-dgx`, bázis `vllm/vllm-openai:qwen38-flash-next@sha256:fc120ece…`) |
| QSA / attention backend | `QWEN38_FLASH_NEXT_EXP_QSA_STATE`; top-k: `persistent_topk` (family 120) |
| NvFp4 MoE backend | `FLASHINFER_CUTLASS` |
| unquantized MoE backend | `FlashInfer CUTLASS` → `FlashInferExperts` |
| sampler | FlashInfer top-p/top-k (`VLLM_USE_FLASHINFER_SAMPLER=1`) |
| CUDA graph | `PIECEWISE`, 12 splitting op, `capture_sizes [1, 2, 4, 8]` (a `cgnone` karban `NONE`) |
| MTP | `{"method":"mtp","num_speculative_tokens":2}`; „Fused multi-step draft decode is not supported by attention backend(s) QWEN38_FLASH_NEXT_EXP_QSA_STATE; falling back to rebuilding attention metadata between draft steps" (a `mtp0` karban ki) |
| chunked prefill | on, `max_num_batched_tokens 8192`, `max_num_seqs 2`, `max_model_len 262144`, prefix caching OFF |
| PLE | `VLLM_PLE_MMAP=1`, `WORKERS=32`, `PREWARM=1` |
| KV | bf16 (fp8-at a QSA elutasítja), pool 444 311 token (MTP=2) / 751 794 (MTP=0) |

## Upstream státusz és támogatottság

A Qwen3.8 vLLM modellintegráció és a GB10 mmap támogatás jelenleg nyitott fejlesztési munka:

- [vLLM #53896 – Qwen3.8 model support](https://github.com/vllm-project/vllm/pull/53896)
- [vLLM #54129 – mmap PLE](https://github.com/vllm-project/vllm/pull/54129)

A Qwen3.8 PR saját leírása szerint a fejlesztői ág review közben instabil lehet. A közölt validáció nem fedi le a single-GB10 + NVFP4 + mmap konfigurációt. A RadixArk checkpoint modellkártyája elsősorban SGLang futtatást és GB300/B300 hardvert említ, a checkpoint pedig candidate release-ként jelenik meg:

- [RadixArk/Qwen3.8-Flash-Next-NVFP4](https://huggingface.co/RadixArk/Qwen3.8-Flash-Next-NVFP4)

Az általános vLLM batch-invariance mód jelenleg béta funkció, és a Qwen3.8/Qwen4Exp útvonal nincs a dokumentáltan tesztelt modellkombinációk között:

- [vLLM batch invariance dokumentáció](https://docs.vllm.ai/en/latest/features/batch_invariance/)
- [vLLM #27433 – batch-invariance tracking](https://github.com/vllm-project/vllm/issues/27433)

A `VLLM_BATCH_INVARIANT=1` ezért hasznos kísérleti kar lehet, de nem tekinthető támogatott javításnak, és nem biztos, hogy felülírja a QSA saját top-k implementációját.

## Üzemeltetési döntés

Determinista információkinyeréshez a jelenlegi Qwen3.8-Flash-Next NVFP4 vLLM recept nem ajánlható éles használatra. A 13/50-es válaszszintű és 5/50-es eredményszintű eltérés túl nagy ahhoz, hogy egyszerű floating-point zajként figyelmen kívül lehessen hagyni.

Javasolt átmeneti stratégia:

1. a 35B FP8 stabil vLLM útvonal megtartása elsődleges KIE-kiszolgálóként;
2. a Qwen3.8 NVFP4 használata csak teszt- és hibakeresési környezetben;
3. az első token logprobjának és a QSA top-k hasheinek vizsgálata;
4. sikeres lokalizálás után minimális upstream reproducer és hibajegy készítése;
5. a Qwen3.8 model support, mmap PLE és `persistent_topk` upstream változásainak követése.

## Végső megállapítás

Mások már többször találkoztak a `temperature=0` ellenére változó vLLM-kimenet jelenségével, Qwen és kvantált MoE modelleknél is. A pontos helyi kombinációra nincs ismert publikus reprodukció. Az eddigi kísérletek kizárják az MTP-t mint egyetlen alapvető okot, és a jelenlegi forráskód alapján a QSA `persistent_topk` útvonal adja a legerősebb, célzottan tesztelhető hipotézist.
