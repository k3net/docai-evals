# Round3 / B kar — a blazux v0.29 bundle független GB10-validációja (spark-dev, 2026-09-12)

> A runbook §6: a `blazux/qwen3.8-Flash-DGX` `v0.29` profilja a **hivatalos** `vllm/vllm-openai:v0.29.0`
> alapra rétegzi a GB10-patchkészletet. Ez a legkisebb kockázatú candidate — és egyben az első
> alkalom, hogy a receptet a szerzőn kívül más is végigméri ezen a hardveren.

## 1. Pinek

| mit | érték |
|---|---|
| recept-checkout | `blazux/qwen3.8-Flash-DGX` @ **`c57881509af3dad83a28e59662fe3c4d29381628`** (2026-09-11, „Add ./flash") |
| candidate image | `qwen38-flash-dgx:v029-validation-20260912T120351Z` — image id **`cc6a1af569eb`**, 22,1 GB |
| alap | `vllm/vllm-openai:v0.29.0` → a konténerben `vllm.__version__ == 0.29.0` |
| det top-k kernel | `jschmied/qwen38-flash-next-gb10` @ **`e0ef69d4f5575dad00d34e05479eaf4c6547bace`**, sha256-pinelt fájlokkal, `DET_ARCH=121a` |
| checkpoint | azonos az A karral: snapshot `7b719225242aacd3dbd3f9407468c2ee9a9d2594` |
| gép | ugyanaz a spark-dev, ugyanaz a driver/CUDA (580.173.02 / 13.0) |

## 2. `./flash doctor v0.29` — minden zöld

ARM64 + GB10 felismerve, 119 GiB szabad unified memória, Docker 29.2.1 + NVIDIA runtime, más
nagy GPU-konténer nem fut, a 18300-as port szabad, a checkpoint a helyén. Nyers: `eredmenyek/B-doctor.txt`.

⚠️ A `v0.29` **profil** alapértelmezése `MODE=hybrid` + `YARN=1` + `CTX=500000`. Ezt **szándékosan nem**
követtük: a hybrid mód (NVFP4 expert + blockwise-fp8 side layer) és a YaRN két további változót vezetne
be az A karhoz képest, és a kérdésünk egyváltozós (mit csinál **ugyanaz a konfiguráció** az új image-en).
A mérés ezért `MODE=nvfp4`-nek megfelelő tiszta checkpointtal, `CTX=262144`-gyel, YaRN nélkül fut.

## 3. Build

`docker build --pull -f Dockerfile.v0.29` — a buildlog (`eredmenyek/B-docker-build.log`) visszaigazolja
mind a hét lépést:

```
ple_layer.py patched OK          fla shmem gate patched        fla num_warps pinned
mamba block_size fix applied OK  modelopt.py hooked OK         qsa.py hooked OK
built: /opt/llm/kernel-det/build/_C_det.so   op: _C_det.persistent_topk   qsadet wired OK
```

## 4. ⛔ Első indítás: CUDA-graph hiba — a csomagátnevezés gyakorlati ára

Az A karral **bájtra azonos** `-cc.splitting_ops` listával indítva a motor a graph capture-nél elhasalt:

```
vllm_ple_mmap.py:289  ids_np = ids.detach().to("cpu", non_blocking=False)...
RuntimeError: Cannot copy between CPU and CUDA tensors during CUDA graph capture
              unless the CPU tensor is pinned.
```

Az ok: a splitting-op **nevek** a csomagátnevezéssel megváltoztak, és a nem illeszkedő névlista miatt a
lemezről olvasó PLE-lookup **bekerült a CUDA graphba**:

| preview (A kar) | v0.29 (B kar) |
|---|---|
| `vllm::qwen3_8_flash_next_ple_short_conv` | `vllm::qwen4_exp_ple_short_conv` |
| `vllm::qwen3_8_flash_next_qsa_with_output` | `vllm::qwen4_exp_qsa_with_output` |
| `vllm::ple_mmap_lookup` | `vllm::ple_mmap_lookup_ids` |
| — | `vllm::qwen4_exp_compute_ple_ngram_ids` (új, 13. elem) |

A recept ezt maga kezeli: a két Dockerfile `qwen38.base` **image-címkét** tesz, és a `serve.sh` abból
választja a listát. Aki — mint mi — közvetlen `docker run`-nal indít, annak ezt kézzel kell átvenni.

⭐ Ez a `03-C-kar-pr-kompatibilitas.md` §2 leletének **üzemi vetülete**: a `qwen3_8_flash_next` →
`qwen4_exp` átnevezés nemcsak a patchek alkalmazhatóságát, hanem a **futtatási paramétereket** is
eltöri, csendben, egy CUDA-graph hibáig. Nyers log: `eredmenyek/B-container-failed-splitops.log`.

## 5. Aktivációs bizonyíték

A helyes listával indított szerver logja:

```
PLE mmap patch (v0.29 layout) applied to vllm.models.qwen4_exp.nvidia.ple_layer.Qwen4ExpNGramEmbedding
Mamba cache mode is set to 'align' for Qwen4ExpForConditionalGeneration ... when prefix caching is enabled
Setting attention block size to 1600 tokens to ensure that attention page size is >= mamba page size.
QSADET active: /opt/llm/kernel-det/_C_det.so
```

⭐ A `QSADET active` sor **fail-closed aktivációs bizonyíték** a determinisztikus top-k kernelre
(vllm#55122) — nem csak az env-változó megléte. A blokkméret itt is **1600**, mint az A karon.

A konténer saját környezete a build eredetét is elárulja:

```
vllm 0.29.0 · torch 2.13.0+cu130 · CUDA 13.0
VLLM_IMAGE_TAG=vllm/vllm-openai:v0.29.0
VLLM_BUILD_COMMIT=98dff2a81d747d1dba01a47f939f48c3526d4206
```

⭐ A `VLLM_BUILD_COMMIT` **bájtra egyezik** azzal a commit-SHA-val, amit a v0.29.0 tagre a GitHub
API-ból kaptunk (`03-…` §2) — a kiadás eredete így kétszeresen igazolt.

## 6. Mérések — minden az A karral azonos paraméterezéssel

### 6.1 Smoke

Ugyanaz a magyar kérdés, `temperature=0`: a válasz **karakterre azonos** az A karéval (93 completion
token). A det-kernel és az exact `torch.topk` tehát ezen a prompton ugyanoda fut ki.

### 6.2 Determinizmus-szonda — ⛔ a jelenség VÁLTOZATLANUL fennáll

`logprob_szonda.py`, 4 item × 10, `max_tokens=48`, thinking OFF, top-20 logprob.
Nyers: `eredmenyek/round3-B-szonda-48tok.{json,log}`.

| item | A kar (preview + exact topk) | **B kar (v0.29.0 + det-kernel)** |
|---|---|---|
| T3-01 | ✅ PASS (1 hash / 10) | ✅ PASS |
| T6-02 | ✅ PASS | ✅ PASS |
| T10-05 | ✅ PASS | ✅ PASS |
| T2-01 | ⛔ FAIL — az 1. futás eltér, eltérés a 0. tokennél | ⛔ **FAIL — ugyanaz a mintázat** |

⭐⭐⭐ **Ez a kör legfontosabb kontrollja.** A cross-request prefix-cache eltérés fennáll:

- **más image-en** (hivatalos `vllm/vllm-openai:v0.29.0` vs. a pinelt preview),
- **más vLLM-verzión** (`0.29.0` vs. `0.1.dev20073+g8e685d198`),
- **más top-k úton** (determinisztikus CUDA-kernel vs. python `torch.topk` fallback),
- **más modellcsomag-elnevezéssel** (`qwen4_exp` vs. `qwen3_8_flash_next`).

Vagyis a jelenség nem a preview image sajátja, és nem az exact-topk megoldás mellékhatása.

### 6.3 Blokkhatár-szonda — a megjósolt eset a B karon is előjön

**Mindkét kar ugyanazon a szerverindításon** (ez az A karnál nem sikerült — ott két indításra esett):

| kar | prefix | A / B prompt | teljes blokkok | eredmény |
|---|---|---:|---|---|
| ELTÉRŐ | D6 (3 002 tok) | 3 086 / 3 267 | **1 vs 2** | ⛔ **FAIL** (B#1 eltér, B#2–6 azonos) |
| AZONOS | D3 | 3 264 / 3 346 | 2 vs 2 | ✅ **PASS** (6/6) |

### 6.4 Memória és prefill — ⭐ a det-kernel +21…28 %

Azonos lépcsők, lépcsőnként egyedi maggal (tiszta cold prefill):

| prompt tok | A prefill | **B prefill** | A tok/s | **B tok/s** | nyereség |
|---:|---:|---:|---:|---:|---:|
| 8 024 | 4 622 ms | **3 827 ms** | 1 736 | **2 097** | **+21 %** |
| 16 019 | 8 776 ms | **7 021 ms** | 1 825 | **2 282** | **+25 %** |
| 24 027 | 12 876 ms | **10 478 ms** | 1 866 | **2 293** | **+23 %** |
| 32 022 | 17 062 ms | **13 652 ms** | 1 877 | **2 346** | **+25 %** |
| 48 025 | 25 491 ms | **20 473 ms** | 1 884 | **2 346** | **+25 %** |
| 64 028 | 35 271 ms | **27 654 ms** | 1 815 | **2 315** | **+28 %** |

Memória: sík plató (106 382 → 106 439 MB, ±60 MB), lépcsős növekedés nélkül — mint az A karon.
Hibajel a teljes B-logban: **0** (OOM / illegal memory / preemption / worker-restart).

⭐ Ez **független megerősítése** a round2 §3.4 leletének (ott 3 itemen, itt 6 kontextushosszon): a
determinizmus ára a kernellel gyakorlatilag eltűnik. A jelenlegi éles megoldásunk (`EXACT_TOPK=1`)
ehhez képest **20–28 %-ot hagy az asztalon a prefillben**, változatlan determinizmus mellett.

## 7. Következtetés

| kérdés | válasz |
|---|---|
| A v0.29 bundle működik-e GB10-en, függetlenül reprodukálva? | ✅ igen — build, indulás, koherens magyar válasz, 0 hibajel |
| Jobb-e a jelenlegi éles image-nél? | ✅ **prefillben 21–28 %-kal**, azonos determinizmus mellett |
| Megoldja-e a cross-request prefix-cache eltérést? | ⛔ **nem** — a jelenség bájtra ugyanúgy fennáll |
| Élesíthető-e ez alapján? | ⚠️ **nem ebben a körben**: a KIE-minőséget (50-es suite) újra kell mérni, mert a det-kernel más szöveget adhat (round2 §3.5), és a `night`-slot deployja külön szál (`docai-0061`) |
