# Round3 / C kar — a nyitott vLLM PR-ek kompatibilitási kapuja (2026-09-12)

> A runbook §7.1 kapuja: *„A `#56500` PR a mozgó vLLM `main` kódbázisára készült. Ne tekintsd
> automatikusan kompatibilisnek a v0.29 csomaggal."* Ez a fejezet ezt a kaput **eldönti**, mielőtt
> bárki több órás ARM64 buildbe kezdene. Minden állítás a GitHub API-ból és a futó konténerből
> származó közvetlen tény, nem becslés.

## 1. A PR-ek pinjei (2026-09-12, `api.github.com/repos/vllm-project/vllm/pulls/…`)

| PR | állapot | head SHA | fájl | +/− | tárgy |
|---|---|---|---|---:|---|
| [#55450](https://github.com/vllm-project/vllm/pull/55450) | **merged** (base `main`) | `f94db729c259` | 3 | +100/−1 | Retire Mamba states across null gaps |
| [#56500](https://github.com/vllm-project/vllm/pull/56500) | open | `866c7ba3cf4d` | 4 | +104/−15 | Reuse bounded QSA prefill logits workspace |
| [#55122](https://github.com/vllm-project/vllm/pull/55122) | open | `a7188289eb86` | 3 | +854/−297 | Make `persistent_topk` deterministic |
| [#54948](https://github.com/vllm-project/vllm/pull/54948) | open | `4b27a2b980d9` | 2 | +10/−0 | `VLLM_FLASHINFER_MOE_FUSED_FINALIZE` kapcsoló |
| [#53798](https://github.com/vllm-project/vllm/pull/53798) | open | `af5357c2b90b` | 6 | +64/−23 | Seed align-mode Mamba `state_idx` |
| [#54076](https://github.com/vllm-project/vllm/pull/54076) | open | `244edeed3dc8` | 4 | +287/−17 | Mamba block size for align-mode chunk splitting |
| [#54129](https://github.com/vllm-project/vllm/pull/54129) | open | `50a061f792f3` | 16 | +10077/−95 | disk-backed (mmap) PLE table |
| [#55334](https://github.com/vllm-project/vllm/pull/55334) | open | `5d2003bfc81c` | 2 | +74/−1 | FP8 PLE n-gram table ModelOpt NVFP4 alatt |

## 2. ⛔ A kapu eredménye: a #56500 EGYIK karra sem rétegezhető rá

A #56500 négy fájlt módosít, ebből a **fő hunk** (a chunk-loop átírása előfoglalt workspace-re) a
`vllm/models/qwen4_exp/nvidia/ops/qsa_indexer.py`-ban van. Ez a fájl:

| kódbázis | modellcsomag | `ops/` tartalma | `qsa_indexer.py` |
|---|---|---|---|
| **A kar** — pinelt preview image (`e655b7d`, vLLM `0.1.dev20073+g8e685d198`) | `vllm/models/qwen3_8_flash_next` | `qsa.py`, `qsa_pre_indexer.py`, `hc.py` | ⛔ nincs |
| **B kar** — `vllm/vllm-openai:v0.29.0` (tag commit `98dff2a81d74`, 2026-09-08) | `vllm/models/qwen4_exp` | `qsa.py`, `qsa_pre_indexer.py`, `hc.py` | ⛔ nincs |
| upstream `main` | `vllm/models/qwen4_exp` | `qsa_indexer.py`, … | ✅ van (2026-09-02, [#54513](https://github.com/vllm-project/vllm/pull/54513) óta) |

A v0.29.0 `ops/qsa.py` a **régebbi szerkezetet** viszi — bájtszinten ugyanazt a mintát, mint a mi pinelt
preview image-ünk:

```python
_LOGITS_WORKSPACE_BYTES = 128 * 1024 * 1024     # v0.29.0 ops/qsa.py:14 ÉS a pinelt image ops/qsa.py:16
_TOPK_WORKSPACE_BYTES = 1024 * 1024
...
def qsa_select_paged_tokens(...):
    rows_per_chunk = max(1, _LOGITS_WORKSPACE_BYTES // max(columns * 4, 1))
    topk_workspace = torch.empty((_TOPK_WORKSPACE_BYTES,), dtype=torch.uint8, device=q.device)
```

A #56500 viszont a `qsa_select_paged_prefill` / `_prefill_logits` párost írja át, és a
`envs.VLLM_SPARSE_INDEXER_MAX_LOGITS_MB` (512 MB) plafonra épül — **ez a függvénypár egyik karon sem
létezik**. Vagyis a patch nem „konfliktusos", hanem **céltalan**: nincs mire alkalmazni.

⭐ Ugyanakkor a **befogadó infrastruktúra megvan** a pinelt image-ben is: a
`vllm.v1.worker.workspace.current_workspace_manager` importálható, és a
`VLLM_SPARSE_INDEXER_MAX_LOGITS_MB=512` env is regisztrált. Egy kézzel visszaportolt változat tehát
elvben lehetséges — de a runbook §2.6 szabálya szerint („ha bármely patch nem alkalmazható tisztán,
állj meg annál a karnál") ezt **nem** tesszük meg dokumentálatlanul, és a mérés (§3) amúgy sem indokolja.

### ⭐ Empirikus megerősítés a lebuildelt v0.29 image-ben (2026-09-12)

A B kar buildje után a fenti — addig csak a GitHub API-ból ismert — állítások **közvetlenül**
ellenőrizhetők lettek a `qwen38-flash-dgx:v029-validation-…` (`cc6a1af569eb`) image-ben:

```
vllm.__version__                         0.29.0
vllm/models/                             …, qwen4_exp        (a preview image-ben: qwen3_8_flash_next)
vllm/models/qwen4_exp/nvidia/ops/        __init__.py  hc.py  qsa.py  qsa_pre_indexer.py
   → qsa_indexer.py (a #56500 célfájlja)  NINCS
vllm/models/qwen4_exp/nvidia/ops/qsa.py:15   _LOGITS_WORKSPACE_BYTES = 128 * 1024 * 1024
```

Vagyis a v0.29.0 kiadás a **régi** indexer-szerkezetet viszi, 128 MB-os modul-konstanssal — a #56500
sem fájlszinten, sem szemantikailag nem rétegezhető rá. A kapu tehát **empirikusan is zárt**.

## 3. A #56500 által célzott tünet a mi konfigurációnkon NEM jelentkezik

Az A kar §9 memória-timeline-ja (ld. `01-A-kar-prodkontroll.md` §4) 8K→64K növekvő chunked prefillen
**stabil platót** mutat (107,5 GB ±80 MB), lépcsős növekedés, preemption és worker-restart nélkül, és a
prefill sebessége nem romlik (1 736 → 1 884 tok/s). Ennek oka a kódból is látszik: a mi águnk plafonja
**128 MB** (`_LOGITS_WORKSPACE_BYTES`), nem a main 512 MB-os `VLLM_SPARSE_INDEXER_MAX_LOGITS_MB`-je,
és a chunkolás ugyanabból a caching-allocator poolból szolgál ki.

→ **Negatív eredmény, de publikálható:** a #56500 memória-platója a GB10 + NVFP4 + 128 MB-plafonos
receptünkön nem reprodukálható tünetre javít; a PR haszna a mi konfigurációnkban nem mérhető.

## 4. Mit jelent ez a többi PR-re?

| PR | rétegezhető a v0.29 bundle-re? | megjegyzés |
|---|---|---|
| #55122 det top-k | **már benne van** | a `Dockerfile.v0.29` 8. lépése („deterministic top-k kernel") beépíti — a B kar validálása egyben a #55122 release-alapú validálása |
| #54948 MoE fused-finalize | ✅ valószínű | `vllm/envs.py` + `flashinfer_cutlass_moe.py`, mindkettő megvan a v0.29.0-ban |
| #53798 / #54076 align fix | ✅ valószínű | `v1/worker/gpu/model_states/*`, `v1/core/sched/scheduler.py` — megvannak |
| #55334 FP8 PLE loader | ✅ valószínű | `qwen4_exp/nvidia/ple_layer.py` megvan |
| #54129 mmap PLE | ⚠️ tárgytalan | a recept saját `vllm_ple_mmap.py`-ja ezt már megoldja; a PR 16 fájl / +10 077 sor |
| #56500 QSA workspace | ⛔ **nem** | §2 |

⚠️ A „valószínű" sorok **fájlszintű** megléten alapulnak; tiszta merge-próbát csak a klónon lehet futtatni.

## 5. Következmény a végrehajtási sorrendre

A runbook §17 lépései 7–8 (C kar) a fenti kapu miatt **nem indíthatók a v0.29 bundle-ön**. A C kar
egyetlen értelmes formája egy friss `main`-ből épített image volna, ami viszont a RadixArk NVFP4
checkpoint betöltéséhez a **#55334-et**, a 48 GiB PLE-táblához pedig a **#54129-et vagy a recept saját
mmap-megoldását** igényli — két nyitott PR + többórás ARM64 build. Ez külön menet; a jelen körben a
publikálható mérföldkő a runbook §18 első két pontja (a bundle független validációja + a #56500
memória-platójának **cáfolata a mi konfigurációnkon**).
