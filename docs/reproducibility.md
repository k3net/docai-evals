# Reproducibility levels

Not every measurement can be re-run by an outside reader. Rather than pretending otherwise, each
experiment declares how far a third party can get with what is published here.

| Level | What is published | What you can do with it |
|---|---|---|
| **R1** | code + data + configuration + results | Re-run the measurement end to end and check our numbers |
| **R2** | code + synthetic data + aggregated results from a private corpus | Re-run the scoring logic on your own data; verify the method, not our numbers |
| **R3** | methodology + configuration + aggregated results | Reproduce the *setup* (launch flags, engine version, workloads) on your own hardware and compare shapes |

## Why most experiments here are R2 or R3

The quality evaluations run on Hungarian business documents belonging to our customers. Invoices
carry company names, tax numbers, bank accounts, addresses and often personal names. That corpus
cannot be published — not with redaction, not with pseudonymisation, not under an NDA-shaped
licence. What can be published is everything else: the scoring code, the normalisation rules, the
field-type definitions, synthetic examples with the same structure, and the aggregate results.

The performance experiments split. Those that ran through the engine's own benchmark tool on
synthetic prompts are **R2**: the exact invocation is published
([performance/harness.md](../performance/harness.md)), the workloads contain no customer data, and
the environment snapshot (engine version, library versions, image digest, resolved config) is
recorded with every result — so the measurement is repeatable, even though the numbers are
hardware-specific.

The rest are R3, because they measure a specific machine (DGX Spark GB10) with a specific engine
build and no published run harness. The launch flags, engine versions and workload definitions are
still here, so the *setup* is reproducible; the numbers are not, because your silicon is not ours.
Where a result is hardware-specific we say so explicitly — that is the whole point of several of
these measurements.

## What R3 still buys you

A lot, in practice:

- **The failure modes.** Which kernel backends refuse to load on `sm_121a`, which flag
  combinations crash, which engine version is needed for a mixed-precision checkpoint. This is
  where most of the wall-clock time in these experiments actually went.
- **The decision rules.** Each experiment fixes its accept/reject threshold *before* the run
  (for example: "if the TTFT gain is under 5 %, keep the current value"). You can disagree with
  the threshold and re-decide from the same numbers.
- **The negative results.** A vendor recommendation that does not transfer to your architecture is
  worth knowing about before you spend a week on it.

## Declaring a level

Every `eval-card.yaml` carries:

```yaml
reproducibility:
  level: R2
  code: published        # published | partial | internal
  data: synthetic-only   # public | synthetic-only | private
  results: aggregated    # full | aggregated
```

If you re-run any of this on other hardware, we would like to hear about it — see
[../CONTRIBUTING.md](../CONTRIBUTING.md).

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu)*
