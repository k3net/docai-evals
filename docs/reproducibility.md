# Reproducibility levels

Not every measurement can be re-run by an outside reader. Rather than pretending otherwise, each
experiment declares how far a third party can get with what is published here.

| Level | What is published | What you can do with it |
|---|---|---|
| **R1** | code + data + configuration + results | Re-run the measurement end to end and check our numbers |
| **R2** | code + synthetic data + aggregated results from a private corpus | Re-run the scoring logic on your own data; verify the method, not our numbers |
| **R3** | methodology + configuration + aggregated results | Reproduce the *setup* (launch flags, engine version, workloads) on your own hardware and compare shapes |

## The two R1 experiments

Two measurements here can be re-run end to end and checked against our numbers, and in both cases
for the same reason: the corpus is one we are allowed to publish.

### lora-vs-reranker-hu-verse

[lora-vs-reranker-hu-verse](../experiments/2026-08-14-lora-vs-reranker-hu-verse/) uses a public-domain
corpus: the complete poems of Arany János and Petőfi Sándor from the Hungarian Electronic
Library. The fetch script records the sha256 of each source archive, so you can verify you have the
same bytes — we re-ran it from a clean directory on 2026-08-17 and both hashes matched.

Everything except the training step runs on CPU, and the generated poems are published, so the
scoring can be repeated without a GPU or a model:

```bash
python3 code/evaluate.py --generations generations
python3 code/author_clf.py --score --generations generations
```

Those two commands reproduced every published table bit-for-bit, including the corpus hash
(`bd86fcf8520d4ca8`) and the 91.0 % author-classifier accuracy.

### where-knowledge-lives-hu-en-zh

[where-knowledge-lives-hu-en-zh](../experiments/2026-08-26-where-knowledge-lives-hu-en-zh/) asks
whether a multilingual model reaches Hungarian facts through English. Its corpus is not borrowed but
built for the purpose — 54 factual questions (15 Hungarian-only, 20 universal, 19 Chinese-only) and
16 untranslatable-concept probes, each asked in Hungarian, English and Chinese — so it ships in the
repository ([dataset/](../experiments/2026-08-26-where-knowledge-lives-hu-en-zh/dataset/)), together
with every prompt actually sent and every per-item judgement.

The model is public (`Qwen/Qwen3.5-9B-Base` and its instruct sibling), so the measurement is
repeatable end to end — but the generation and the SAE forward passes need a GPU. What a reader can
check without one is bounded and stated, not implied:

```bash
cd experiments/2026-08-26-where-knowledge-lives-hu-en-zh
pip install -r requirements.txt
python3 code/smoke_repro.py
```

That rebuilds all 290 prompts from the corpus, verifies the derived scoring column, and re-runs
Measurement A, Measurement B and the D2 control from a clean checkout — comparing each regenerated
report against the committed one byte for byte. The four analyses that need `results*/sae/`
(33–42 MB per round, not committed) are printed as skipped. CI runs this on every push
([`.github/workflows/reproduce.yml`](../.github/workflows/reproduce.yml)).

⛔ This is a check the repository failed for a while without anyone noticing: the scripts were moved
into `code/` and the corpus into `dataset/`, but their paths were not, so a clean clone died with
`FileNotFoundError` while the eval card still advertised R1. A reproducibility claim that nothing
exercises decays silently — hence the CI job.

## What R1 costs

A corpus you are allowed to publish. The rest of this repository does not have one.

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
