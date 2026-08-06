# Decision record — how the 122B is served

**Date:** 2026-05-22 · **Status:** in force · **Experiment:**
[qwen35-122b-nvfp4-bringup-gb10](README.md)

## Decision

The 122B runs on its own node and its own port, with a fixed configuration:

| Setting | Value | Why |
|---|---|---|
| Context | 262k | Long multi-document analysis is the use case |
| Memory utilisation | 0.75 | 0.85 OOMs during load; 0.75 is stable |
| KV cache | FP8 | Doubles the pool at no measurable quality cost here |
| Concurrent sequences | 4 | Matches the KV budget at full context |
| Speculative decoding | draft 2 | Without it the model is ~3.3× slower than the 35B and the use case thins out |
| Loader | default | `fastsafetensors` OOMs without GDS on this platform |
| Input | text-only | Explicit; extraction with images stays on the 35B |
| MoE backend | engine auto-selection | Mixed 4-bit main + BF16 draft cannot be served by one quantised backend |

*What the model should be used **for** is a separate decision — see
[35b-vs-122b-business-tasks](../2026-05-22-35b-vs-122b-business-tasks/decision-record.md).*

## Operational conditions

1. **Monitor speculative acceptance.** It is the leading indicator that a checkpoint or engine
   change silently disabled the draft path. Zero means the draft weights are not loaded — not that
   speculation stopped helping.
2. **Health-check startup windows must allow ~22 minutes.** Anything shorter reports the service as
   unhealthy during a normal cold start, which trains people to ignore the signal.
3. **Do not rebuild the image casually.** A restart during working hours is a visible outage for
   scheduled jobs, and torch.compile caches are version-keyed — a rebuild means a full cold start.
4. **Never swap models while the node is serving another workload.** Drain first.

## What we would revisit

- **Native FP4 compute on `sm_121a`.** Marlin is weight-only by design; if the platform gains FP4
  tensor-core dispatch, a 2–3× decode gain is plausible, which would move this model into the
  interactive range and reopen every use-case decision made against it.
- **4-bit FlashInfer MoE support** on this architecture — potentially +20–60 % decode.
- **An FP8 checkpoint of the same model.** The FP8 path is more mature here than the 4-bit one.
- **A mid-size distillate** — the plausible sweet spot between complex reasoning and interactive
  speed.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) ·
[Article (HU): 122B-os modell egy DGX Sparkon: élesben mérve](https://docai.hu/blog/qwen35-122b-spark)*
