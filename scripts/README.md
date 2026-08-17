# Scoring and analysis tools

Small, dependency-light tools. Everything here is standard-library Python 3.10+ except the eval
card validator, which wants PyYAML (and optionally `jsonschema`).

| Script | What it does |
|---|---|
| [kie_normalizer.py](kie_normalizer.py) | The frozen cosmetic-normalisation rule set (v1.0). Library + self-test. |
| [score_kie.py](score_kie.py) | Raw and normalised field-level F1 for one or more runs, scored by identical code. |
| [counterparty_guard.py](counterparty_guard.py) | The deterministic business gate: did the model put our own company in the partner slot? |
| [mcnemar.py](mcnemar.py) | McNemar's exact test on the gate above, for two runs over the same documents. |
| [hu_prosody.py](hu_prosody.py) | Deterministic Hungarian verse prosody: syllable count, rhyme key, rhyme scheme, inflectional-rhyme detection. Library + self-test. |
| [validate_eval_cards.py](validate_eval_cards.py) | Validates every `experiments/*/eval-card.yaml` against the schema. |

## The one rule

**Tenant identity is a parameter, never a literal.** `counterparty_guard.py` and `mcnemar.py` take
`--own-tax` and `--own-name-hint` on the command line. Do not hard-code a real tax number or
company name into a script that lives in this repository — see [../docs/data-policy.md](../docs/data-policy.md).

## Quick start

```bash
python3 scripts/kie_normalizer.py           # self-test
python3 scripts/hu_prosody.py               # self-test, against Toldi's alexandrines

python3 scripts/score_kie.py runs/baseline runs/candidate

python3 scripts/counterparty_guard.py \
    --own-tax 87654321-2-08 \
    --own-name-hint "demó kereskedelmi" --own-name-hint "demo kereskedelmi" \
    runs/baseline runs/candidate

python3 scripts/mcnemar.py \
    --own-tax 87654321-2-08 --own-name-hint "demó kereskedelmi" \
    runs/baseline runs/candidate

python3 scripts/validate_eval_cards.py
```

## Input format

`score_kie.py`, `counterparty_guard.py` and `mcnemar.py` read *run directories* produced by our
internal harness. The harness itself is not published; its output format is, and it is deliberately
plain so that you can emit the same shape from your own runner:

```text
runs/<timestamp>__<label>/
├── summary.json                 # skipped by the scorer
└── <doc>_<trace>__header.json   # one file per scored document
```

Each document file carries the raw model response and the field-level comparison:

```json
{
  "vllm_response": { "output_text": "{\"partner_name\": {\"value\": \"...\"}, ...}" },
  "compare": {
    "fields": [
      { "field": "partner_name", "outcome": "tp",
        "gt_value": "Példa Logisztika Kft.", "pred_value": "Példa Logisztika Kft." }
    ]
  }
}
```

`outcome` is one of `tp`, `fp`, `fn`, `mismatch`, `tn` — defined in
[../docs/methodology.md](../docs/methodology.md#field-level-extraction-kie).

## Interpreting output

- **`score_kie.py`** prints raw F1, normalised F1, and how many mismatches were purely cosmetic.
  A large cosmetic count means the raw difference was about JSON formatting, not comprehension.
- **`counterparty_guard.py`** prints flagged-document counts per run. `tax and name agree` is the
  high-confidence subset; the `own_name_score=0` column shows how often the model also failed to
  recognise its own company, which is the signature of a genuine role confusion rather than a
  name-matching slip.
- **`mcnemar.py`** prints the discordant pairs and an exact two-sided p-value. Above 0.05, report
  point estimates and say the ordering is not established — do not promote it to a finding.

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu)*
