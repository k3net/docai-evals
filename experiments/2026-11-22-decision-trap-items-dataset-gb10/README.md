# A dataset of decision trap items, and what thinking does and does not fix on it (Qwen3.6-35B-A3B-FP8, GB10)

**Date:** 2026-11-22 · **Status:** published · **Reproducibility:** R1 ·
**Dataset:** [k3dani/hu-decision-trap-items](https://huggingface.co/datasets/k3dani/hu-decision-trap-items) (Hugging Face, CC BY 4.0) ·
**Previous experiment:** [verified-chain-and-checking-head-gb10](../2026-11-08-verified-chain-and-checking-head-gb10/README.md)

## 1. What was the measurement for?

The previous package reported two failures of an LLM used as a decision step, on synthetic items it did not publish:
the model picks the option that matches on the surface where a calculation is needed, and it picks an option where
the text lacks what the decision needs. That package promised a dataset. This one delivers it: 21,067 synthetic items
in Hungarian and English, with a reference baseline that anyone can re-run.

The baseline also answers a question the earlier rounds never asked, because every read-out there ran with thinking
off: **does thinking remove either failure?**

## 2. On what task and dataset?

Multiple-choice decision items: a text, a question, 3–6 options, and one of four labels (`MATCH`, `NO_MATCH`,
`MISSING_DATA`, `OUT_OF_SCOPE`). Three families: bank transaction to open invoice, fault report to diagnosis, expense
claim to policy clause.

| config | items | content |
|---|---:|---|
| `calc_traps` | 1,273 (test) | all `MATCH`; a decoy option matches on the surface, the right one needs one calculation step (a fifth, small type has the amount in words and a near-twin decoy) |
| `minimal_pairs` | 684 (test), 342 pairs | the two members differ only in whether the deciding sentence is about the claimed amount |
| `interpretation` | 1,968 train / 2,184 test | units of three items with the deciding signal and one without |
| `natural` | 5,984 train / 8,974 test | natural mix of the four labels; reference point, not a trap set |

Every item is synthetic: code produces the plan (facts, options, answer, label), Muse-Glimmer-30B writes the text
from the plan, code checks the text against the plan. No customer data. The dataset card lists the fields, the
construction, the audits and the known limitations; `results/data.sha256` pins the released files.

Changes made for the release, all before the baseline ran:

- **A leaked prompt example was replaced.** Two example company names from the generator prompt appeared in 94 % of
  the Hungarian fault-report texts. They were replaced in 2,529 items by generated names (deterministic;
  `code/e_export.py`). The earlier rounds measured the original texts.
- **89 items were removed** after an independent fact-check of the dataset card and a comparison of the names with
  our internal customer records: 25 named a real bank, 15 named another real organisation or carried an invented
  company name that matched a real company, 23 carried a malformed e-mail address or a real-looking domain, 1 used a
  historical person's name, 25 were unit or pair partners of those. No e-mail address, tax number or account number
  in the texts matched a real one. The baseline had already run; its per-item answers were filtered to the released items, no item was re-run.
- **Item ids were made opaque.** The original ids spelled out the label.
- **The `interpretation` set was cut to one family.** The bank and fault parts had 6.7 % and 10.0 % label errors in
  audited samples before cleaning, and only audited units had been removed.
- **`calc_traps` got a blind human audit**, which it never had: 60 items, stratified by trap type and language,
  0 disagreements (one-sided 95 % upper bound 4.9 %; `results/audit_calc_traps.json`). One of the 60 was among the
  items removed later.

## 3. Which models and configurations were compared?

One model: Qwen3.6-35B-A3B, FP8, vLLM 0.30.0 on a DGX Spark (GB10). One read per item, options in the stored order,
`code/baseline.py` (standard library only).

- **Frames.** Two-state: the options plus one exit ("none of the above"). Four-state: the options plus three exits
  (no suitable option / data missing / outside the task).
- **Modes.** `direct`: thinking off, temperature 0, the first token is the answer. `think`: thinking on, the
  model-card sampling (temperature 0.6, top-p 0.95, top-k 20), a seed derived from the item id, at most 4,096 tokens.
- **Text-only baseline.** Character TF-IDF with logistic regression predicting the label from the surface text
  (`code/e_baseline.py`).

The thinking runs cover `calc_traps`, `minimal_pairs` and a fixed sample of `interpretation` units (150 drawn, 147
left after the removals; ids in `results/think_sample_interpretation.json`).

## 4. Which metrics?

Fixed before the run (2026-11-20), all descriptive, Wilson 95 % intervals, no hypothesis test:

- accuracy, and the share of answers that pick a wrong option;
- on `calc_traps`, both by trap type;
- on `minimal_pairs` and `interpretation`, the share of undecidable members on which the model picks an option;
- on `natural`, accuracy by label.

A truncated or unparseable thinking answer counts as no answer, and as an error.

## 5. What was the result?

All runs completed without request errors: 26,352 direct reads and 2,572 thinking reads before the removals; one
thinking answer hit the token limit. The numbers below are on the released items.

**Thinking removes most calculation traps** (four-state frame):

| trap type | n | direct: correct | think: correct |
|---|---:|---:|---:|
| currency | 258 | 15.9 % | 100.0 % |
| net vs gross | 260 | 38.1 % | 100.0 % |
| unit conversion | 368 | 52.2 % | 99.7 % |
| partial payment | 327 | 46.5 % | 81.7 % |
| amount in words | 60 | 90.0 % | 96.7 % |
| all | 1,273 | 42.3 % [39.6; 45.0] | 95.1 % [93.7; 96.1] |

**Thinking does not remove the missing-data failure; the share is higher with it.** How often the model picks an
option on the member that cannot be decided:

| config | direct | think |
|---|---:|---:|
| `minimal_pairs`, 342 members | 78.7 % [74.0; 82.7] | 91.8 % [88.4; 94.3] |
| `interpretation`, 546 members direct, 147 think | 82.4 % [79.0; 85.4] | 95.2 % [90.5; 97.7] |

Both members of a minimal pair are right in 2.0 % of pairs (direct) and 5.3 % (think).

**Natural mix** (direct, 8,974 items): 83.7 % with the two-state frame, 77.5 % with the four-state frame. With four
states `MISSING_DATA` rises from 26.2 % to 38.4 % and `OUT_OF_SCOPE` falls from 99.6 % to 27.4 %; in the two-state
frame every non-`MATCH` label is scored against the single exit, so the two columns do not measure the same thing.

**Text-only baseline:** `interpretation` AUROC 0.9995 (the undecidable member is recognisable from the surface);
`natural` accuracy 63.2 % against a 60.0 % majority; `minimal_pairs` AUROC 0.672 with 5-fold cross-validation grouped
by matched scenario pair.

**A structural finding on `minimal_pairs`.** Its 33 scenarios form 17 groups (16 matched pairs and one single): the deciding
sentence of one scenario is the neutral sentence of its partner. Cross-validation grouped by scenario reverses the
surface signal (text-only AUROC 0.13 on the released items, 0.02 before the removals). The dataset carries a `scenario_group` field for this reason.

Full tables: `results/summary.md`, `results/summary.json`; per-item answers: `results/raw/`.

## 6. What product decision followed?

See [decision-record.md](decision-record.md).

## 7. What are the limits of the measurement?

- One model, one quantisation, one engine build, one machine. One sample per item in the thinking runs; the
  direct–think difference is descriptive.
- Synthetic items from one generator model in three narrow families. Trap items are constructed: they do not measure
  how often the mistake happens in real traffic.
- In four of the five `calc_traps` types the decoy is the option a surface comparison picks, trap type maps
  one-to-one to family, and the right band is fixed per type. The thinking result says the model
  can do these calculations when it reasons, not that it will notice the need for one in a real document.
- The numbers here are not comparable with the previous package's: that used a different prompt frame, the BF16
  model, four option orders, and the texts before the name replacement.
- `interpretation` labels are recognisable from surface features. `minimal_pairs` controls that signal but does not
  remove it (0.672); its filter was built from the errors of its own first audit, and its second audit was quick.
- Template groups are shared across configs (86 of the 329 `calc_traps` groups with `natural` train).
- Human audits are by one annotator, the project owner. The `interpretation` train split had no human audit. The round 08 part of `natural` had no blind audit. The pilot part of
  `calc_traps` (328 items) was not hash-frozen at generation time.
- The thinking run on `interpretation` is a sample of 147 units.

## 8. Which DocAI article belongs to it?

None yet. Background: [Amit ki lehet számolni](https://docai.hu/blog/amit-ki-lehet-szamolni)
([English](https://docai.hu/en/blog/dont-train-what-you-can-compute)).

## Verify

```bash
# 1. the released files are the ones measured
sha256sum -c /path/to/this/package/results/data.sha256   # run in the root of the downloaded dataset

# 2. re-score the published per-item answers
python3 code/baseline.py score --items data/calc_traps/test.jsonl --pred results/raw/calc_traps.f4.think.jsonl

# 3. re-run a baseline against your own OpenAI-compatible endpoint
python3 code/baseline.py run --items data/calc_traps/test.jsonl --out out.jsonl --frame 4 --mode direct \
        --url http://127.0.0.1:8000 --model <your-model>
```

## Layout

```text
code/baseline.py      the reference baseline (run, score)
code/e_baseline.py    summary of all runs and the text-only baseline
code/e_export.py      how the release was assembled from the round 06–08 item files (name replacement, opaque ids, checks)
code/e_audit.py       the blind audit sheet and its evaluation
code/ke2.sh           the run script as executed
results/              summary, per-item answers, export and check reports, audit result, data hashes
```
