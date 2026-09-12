# Round3 / A kar — prod-azonos kontrollmérés (SPARK-DEV, 2026-09-12)

> **Mit validálunk?** A round3 runbook (`2026-09-12-qwen38-gb10-vllm-stabilitas-validacios-runbook.md`)
> A karja: a jelenleg élesített recept (`spark/servers/vllm-qwen38-flash/`, blazux `e655b7d`) független
> kontrollmérése a SPARK-DEV-en, mielőtt bármelyik candidate (B: blazux v0.29, C: nyitott PR-ek) indulna.
> A prod (SPARK-BETA `night`-slot, `:8358`) a mérés alatt **érintetlen** — a SPARK-DEV külön példány.

## 0. Eltérés a runbooktól — a SPARK-DEV tényleges állapota

A runbook §4–5 egy futó `qwen38-flash` konténert és egy `/opt/vllm/qwen3.8-Flash-DGX` checkoutot (`./flash`
CLI) feltételez. A SPARK-DEV-en **egyik sincs**: a gép a round2 óta szabad, a GPU üres, és a recept nem
`./flash` scripttel, hanem a vendorozott compose-szal/`docker run`-nal indul. Az A kar ezért a leállított
`qwen38-det-a` konténer `docker inspect`-jéből visszanyert, **bájtra azonos** paraméterezéssel indult
(`qwen38-flash-dgx-up:e655b7d`, `VLLM_QSA_EXACT_TOPK=1`, prefix cache ON, MTP=2, 262 144 ctx).

## 1. Pinek

| mit | érték |
|---|---|
| gép | SPARK-DEV, NVIDIA GB10 (sm_121, `capability (12,1)`), ARM64, 128 GB unified |
| driver / CUDA | 580.173.02 / 13.0 |
| kernel | 6.17.0-1029-nvidia-aarch64 (konténer), host 6.17.0-1032-oem |
| image | `qwen38-flash-dgx-up:e655b7d` (a prod recept dev-másolata) |
| vLLM | `0.1.dev20073+g8e685d198` · torch `2.13.0+cu130` · flashinfer `0.6.17` · transformers `5.15.1` |
| checkpoint | `RadixArk/Qwen3.8-Flash-Next-NVFP4` snapshot `7b719225242aacd3dbd3f9407468c2ee9a9d2594` |
| MoE backend | `FLASHINFER_CUTLASS` (a #54945/#54948 érintett útja) |
| Mamba cache mód | `align` — a vLLM a prefix caching miatt automatikusan ezt választja |
| korpusz | `magyar-kie-eval`, corpus sha256 `c7589bae…` (a laptopon és a SPARK-DEV-en **bitre azonos**) |

⚠️ A `VLLM_PLE_MMAP*` és a `VLLM_QSA_EXACT_TOPK` a vLLM saját env-regiszterében ismeretlen
(`Unknown vLLM environment variable detected`) — ezeket a vendorozott patchek olvassák `os.environ`-ból.
Aktivációs bizonyíték a logban csak a PLE-re van (`PLE mmap patch applied to …`); az exact top-k
aktivációját **funkcionálisan** igazolja a §2 szonda (a stock kernel a round2 B-kontrollján 0/4 PASS-t adott).

## 2. Determinizmus-szonda (runbook §5.3) — a round2 bájtra reprodukálva

`logprob_szonda.py`, 4 item × 10 ismétlés, `temperature=0`, `max_tokens=48`, thinking OFF, top-20 logprob,
szigorúan sorosan. Nyers: `eredmenyek/round3-A-szonda-48tok.{json,log}`.

| item | prompt (kar) | változat / 10 | eredmény |
|---|---:|---:|---|
| T3-01 | 7 269 | 1 | ✅ PASS |
| T6-02 | 15 458 | 1 | ✅ PASS |
| T10-05 | 61 757 | 1 | ✅ PASS |
| T2-01 | 7 495 | 2 | ⛔ FAIL — az **1. futás** tér el, a 2–10. egymással azonos, eltérés a **0. tokennél** |

⭐ Ez **ugyanaz a mintázat, ugyanazon az itemen**, mint a round2 §3.1-ben (2026-09-03) — kilenc nappal
és két friss szerverindítással később. Tehát nem zaj, hanem determinisztikus mechanizmus.

⭐⭐ **A FAIL oka azonosítva:** a T2-01 és a T3-01 **ugyanazt a `D2.md`-t** használja, és a szonda a
T3-01-et futtatja előbb → a T2-01 „hideg" futása valójában **partial prefix-cache hit**.

⛔ **Figyelem — az első magyarázat megdőlt.** Kézenfekvő volna azt hinni, hogy a részleges hit út a
hibás. A célzott izoláló kísérlet (`02-partial-hit-kiserlet.md`) ennek az **ellenkezőjét** mutatta ki:
a részleges hites első futás adja a **helyes** (a teljesen cache-mentes úttal bitre egyező) eredményt,
és a **teljes** cache-hites futások térnek el. A jelenség tehát a **kérések közti** blokk-újrafelhasználáshoz
kötődik, nem a „hideg vs. meleg" tengelyhez; upstream-releváns:
[#53798](https://github.com/vllm-project/vllm/pull/53798) / [#54076](https://github.com/vllm-project/vllm/pull/54076).

## 3. Prefix-cache helyességi szonda (runbook §10)

`prefix_cache_szonda.py`: a korábban **nem érintett** `D6+D3+D4` (15 055 kar → 6 656 token) közös prefixre
cold → partial hit → 9× full hit. Nyers: `eredmenyek/round3-A-prefixcache.json`.

| út | prompt tok | teljes logprob-hash |
|---|---:|---|
| cold (suffix A) | 6 656 | `e23ff19cee1ece76` |
| partial (suffix B, 1.) | 6 655 | `7249c6a4a8b2c5d0` |
| full (2–10.) | 6 655 | `7249c6a4a8b2c5d0` ×9 |

✅ **PASS** — a partial és a full út **bitre azonos** logprob-listát ad. Vagyis a részleges hit önmagában,
tiszta felállásban nem tör el; a T2-01-nél látott eltéréshez a konkrét blokk-illeszkedés kell (§5).

⚠️ A `usage.prompt_tokens_details.cached_tokens` ezen a builden mindig `null`, a cache-hit arány csak a
`/metrics` `vllm:prefix_cache_hits_total` / `_queries_total` párosból olvasható.

## 4. QSA workspace memória-validáció (runbook §9)

`qsa_memoria_timeline.py`: egy szerverindításon belül 8K→16K→24K→32K→48K→64K, **lépcsőnként egyedi maggal**
(a `/tokenize` endpointtal ±2 %-ra kalibrált hossz), tehát minden lépcső tiszta cold prefill
(`prefix_cache_hits_total` végig 292 800 → **0 hit**). Nyers: `eredmenyek/round3-A-memoria.json`.

| cél | prompt tok | prefill ms | tok/s | host used előtte (MB) | utána (MB) |
|---:|---:|---:|---:|---:|---:|
| 8 000 | 8 024 | 4 622 | 1 736 | 107 557 | 107 494 |
| 16 000 | 16 019 | 8 776 | 1 825 | 107 560 | 107 539 |
| 24 000 | 24 027 | 12 876 | 1 866 | 107 569 | 107 565 |
| 32 000 | 32 022 | 17 062 | 1 877 | 107 570 | 107 568 |
| 48 000 | 48 025 | 25 491 | 1 884 | 107 570 | 107 569 |
| 64 000 | 64 028 | 35 271 | 1 815 | 107 566 | 107 141 |

✅ A memória **stabil platón marad** (±80 MB zaj a 107,5 GB körül), nincs lépcsőzetes növekedés, nincs
preemption, nincs worker-restart. A prefill sebessége nem romlik a kontextushosszal (1 736 → 1 884 tok/s).

⚠️ **Korlát:** GB10-en a `nvidia-smi --query-compute-apps=used_memory` `[N/A]`-t ad (unified memory), és a
torch caching allocator `reserved` értéke külső processzből nem olvasható. A mérés ezért host-szintű
(`free -m` used) proxy: azt bizonyítja, hogy a növekvő chunked prefill **nem kényszerít új
host/unified allokációt**, nem azt, hogy a torch-pool belső `reserved` értéke bitre változatlan.

## 5. T2-01 izoláló kísérletsor

Ld. `02-partial-hit-kiserlet.md` — tiszta / szennyezett / prefix-cache-off karok friss
szerverindításokon, majd a blokkhatár-hipotézis tesztje. Összefoglaló: `00-osszefoglalo.md`.
