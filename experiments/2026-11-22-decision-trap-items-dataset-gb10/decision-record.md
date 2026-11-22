# Decision record — publish the trap items as a dataset; keep computable steps in code; treat missing data as an open problem

**Date:** 2026-11-22 · **Status:** proposed, awaiting the owner's approval ·
**Experiment:** [decision-trap-items-dataset-gb10](README.md) · **Previous decision:**
[verified-chain-and-checking-head-gb10](../2026-11-08-verified-chain-and-checking-head-gb10/decision-record.md)

## Decision

1. **The synthetic trap items are published as a dataset** (`k3dani/hu-decision-trap-items`, CC BY 4.0), with a
   reference baseline. This replaces the long-term goal of a public general decision model, which three rounds
   (01, 03, 09) did not support.
2. **The rule "compute what can be computed in code" stands.** Thinking raises the calculation-trap result from
   42.3 % to 95.1 % on one model, at a median of about 1,700 generated tokens per item. The code chain of the previous
   package reached 97.5–98.9 % on trap items of the same construction without that cost and with a verifiable result.
   The two numbers come from different item subsets and prompt frames and are not a tested comparison.
3. **Missing data is an open problem, and thinking is not the fix.** On items where the deciding signal is absent the
   model picks an option 79–82 % of the time without thinking and 92–95 % with it. No prompt, head or mode tried in
   rounds 05–10 or here removes this.

## What would reopen it

- A second model or a second generator showing a different pattern on the same items.
- A human audit of the round 08 part of `natural`, or a second annotator, finding label errors above the reported rates.
- Real-data evidence that the missing-data failure is rare enough in product traffic not to matter.

## What this record does not decide

- Whether thinking should be enabled in any product path.
- Anything about real documents: every item here is synthetic.
