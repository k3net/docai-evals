# Draft — upstream issue for vllm-project/vllm (do not file before the full-suite validation is in)

**Title:** `[Bug] Qwen3.8-Flash-Next QSA indexer: persistent_topk makes prefill logits non-deterministic at temperature 0 on GB10 (sm_121) — selected set varies, not only order`

## Summary

On a single DGX Spark (GB10, `sm_121a`), Qwen3.8-Flash-Next (RadixArk NVFP4 checkpoint) served with vLLM returns
**different logits for byte-identical prompts** at `temperature=0`, `max_tokens=1`, single request in flight.
The divergence is in the **prefill**, and it disappears when the QSA sparse-attention indexer's
`torch.ops._C.persistent_topk` call is replaced by an exact `torch.topk` with canonical tie ordering — with
MTP and CUDA graphs unchanged.

## Environment

- vLLM `0.1.dev20073+g8e685d198` (image built `FROM vllm/vllm-openai:qwen38-flash-next@sha256:fc120ece…`
  + the PLE-mmap patch from blazux/qwen3.8-Flash-DGX `82ed48d`; the mmap patch does not touch the QSA path)
- GB10 / DGX Spark, driver 580.173.02, kernel 6.17.0-1029-nvidia, 121 GiB unified
- Model: `RadixArk/Qwen3.8-Flash-Next-NVFP4`; `--max-model-len 262144 --max-num-seqs 2 --no-enable-prefix-caching
  --enable-chunked-prefill --max-num-batched-tokens 8192 -cc.cudagraph_mode=PIECEWISE --speculative-config
  {"method":"mtp","num_speculative_tokens":2}`; NvFp4 MoE backend `FLASHINFER_CUTLASS`
- Code path: `vllm/models/qwen3_8_flash_next/nvidia/ops/qsa.py::qsa_select_paged_tokens` — on capability family 12x
  `use_cooperative_topk` is False, so `persistent_topk` is used.

## Reproduction (no model-specific data needed)

Send the same ~6k-token chat prompt 10 times, `temperature=0, top_p=1, max_tokens=1, logprobs=true, top_logprobs=20`,
one request at a time. Compare the top-20 (token, logprob) lists.

| | stock `persistent_topk` | `torch.topk` + canonical order |
|---|---|---|
| prompts with 10/10 byte-identical top-20 vectors | **0 / 6** | **6 / 6** |
| first-token identity | flips between runs on 3/6 prompts | fixed |
| top-2 gap between runs | varies by up to 3 nat | constant |
| prefill throughput, 6k-token prompt | 2 360 tok/s | 1 760 tok/s |

End-to-end effect on a 50-item Hungarian extraction suite (3 runs per item): 13 items with differing greedy output,
5 of them with a different extracted date/amount; 0/50 on Qwen3.6-35B-FP8 (vLLM, MTP=2) and on the same Flash-Next
checkpoint via llama.cpp.

## Isolation

- speculative decoding off → still non-deterministic (11/13 items)
- `cudagraph_mode=NONE` → still non-deterministic (13/13)
- **`persistent_topk` output re-ordered canonically after the kernel (set untouched) → still non-deterministic on 3/6
  prompts** ⇒ the kernel's *selected set* varies, not only the slot order
- exact top-k (full stable sort, or `torch.topk` + two stable sorts) → deterministic on 6/6, MTP=2 + PIECEWISE unchanged

This is consistent with #51782 (`persistent_topk` silently drops candidates when many values share a coarse histogram
bin): the bin-boundary race picks different candidates on different launches. The longest prompt (24k tokens) is the
worst affected.

## Patch used for the test

One-file overlay on the installed `qsa.py` (attached: `qsa_exact_topk.patch`), env-switched:
`VLLM_QSA_EXACT_TOPK=3` = `torch.topk(sorted=False)` then stable sort by index, then stable sort by value descending;
`-1` padding for `length < k`, matching `tests/models/qwen4_exp/test_qsa_reference.py::_qsa_relative_topk_reference`.

## Ask

A deterministic (index-ordered tie-break) path in `persistent_topk`, as FlashInfer added for its sparse-attention top-k
in flashinfer-ai/flashinfer#2661, or a documented flag to route the QSA indexer to an exact selection. Happy to test a
branch on GB10.

*(Attach: `prefill_szonda.py`, the four `szonda-*.json`, `qsa_exact_topk.patch`. Add the full-suite numbers with the
fix once the validation run has finished.)*
