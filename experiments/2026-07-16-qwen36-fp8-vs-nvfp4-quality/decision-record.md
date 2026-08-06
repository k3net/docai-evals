# Decision record — stay on FP8

**Date:** 2026-07-16, revised the same week after the counterparty gate · **Status:** in force ·
**Experiments:** [qwen36-fp8-vs-nvfp4-quality](README.md) ·
[invoice-counterparty-role](../2026-07-16-invoice-counterparty-role/)

## Decision

The production extraction and chat model stays on **FP8**. No NVFP4 checkpoint is adopted, despite
a +40 % aggregate throughput, +69 % single-stream extraction speed and ~10 GiB of freed memory.

## The three gates

We set them out before the measurements, and the decision followed them mechanically:

| Gate | Question | Outcome |
|---|---|---|
| **1 — serving** | Can we run the candidate in production at all? | ✅ Green — a container-level image change, isolated to one service |
| **2 — validation** | Does it hold up on a representative corpus? | ❌ **Failed** — ~2× the counterparty error rate on 100 real invoices |
| **3 — canary** | Does it survive sustained real traffic? | Never started; gate 2 is a knockout |

Gate 1 deserves a note, because it was the one everybody expected to be the blocker: the older
production engine build genuinely could not load one candidate (it quantises a layer the old
loader does not handle), but a pinned newer container ran it cleanly, and the change touches one
container rather than a fleet. Serving was not the problem. Capability was.

## Why speed did not win

The trade on offer was: 40–69 % more speed, 10 GiB more memory headroom, in exchange for roughly
doubling the rate at which the model confuses the two companies on an invoice.

That field drives invoice direction, tax-authority matching and bookkeeping. An extraction error
there is not a degraded answer — it is a wrong ledger entry that a human has to find later. We
have no latency problem that this trade would solve; production runs at 1–3 concurrent requests
with sub-second time to first token.

So the answer is no, and it is not close.

## What we learned about our own evaluation

This is the part worth keeping:

1. **A small generic benchmark reported equivalence for a model that had a 2× regression in a
   business-critical field.** Not through error — through corpus composition. The failure needs
   documents where the tenant's own company appears repeatedly, and the test corpus had none.
2. **Aggregate F1 dilutes concentrated failures.** The counterparty error spreads across seven
   fields out of twenty-five and averages away.
3. **The tidy story was wrong too.** Raw F1 ordered the candidates by quantisation aggressiveness,
   which suggested a dose-response. On the larger corpus, pairwise McNemar tests could not
   distinguish the three candidates from each other (all p ≫ 0.05) while two of the three were
   significantly worse than FP8. The defensible claim is about the *format*, not a dose — and we
   published that, rather than swapping one unsupported story for another.

Both practices are now standing rules: representative-corpus validation before any model change,
and a deterministic business gate alongside every aggregate quality metric.
See [../../docs/methodology.md](../../docs/methodology.md).

## What would reopen it

- **A less aggressive or Hungarian-calibrated NVFP4 checkpoint** — one that leaves the layers
  carrying entity reasoning at 8 bits, or is calibrated on a Hungarian invoice corpus.
- **Moving the decision out of the model.** If own-vs-partner is resolved by deterministic
  post-processing against the tenant's own registered identity — which we already store — then the
  model's name-matching weakness stops mattering and the speed becomes free. This is the more
  robust architecture regardless of quantisation, and it is the path we would take first.
- **A larger cross-tenant differential corpus** plus either of the above, re-running gate 2.

Until then: FP8, with no quality risk and no latency problem.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) ·
[Article (HU): Negyven százalékkal gyorsabb, és mégsem váltunk](https://docai.hu/blog/nvfp4-kvantalas-miert-nem-valtottunk)*
