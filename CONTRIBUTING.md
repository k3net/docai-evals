# Contributing

This repository is published as evidence for the write-ups on
**[docai.hu/blog](https://docai.hu/blog)**. The measurements themselves run on our own hardware
against corpora that cannot leave it, so contributions look different here than in a typical
open-source project.

## What is genuinely useful

1. **Methodology review.** If a scoring rule, a normalisation step or a statistical test is wrong
   or too generous, open an issue. We would rather correct a published number than defend it.
2. **Reproduction on other hardware.** The performance results are GB10-specific by design. A run
   of the same workload definitions (see [performance/](performance/)) on different silicon is the
   single most valuable thing an outside contributor can add.
3. **Hungarian ground truth.** Field-level ground truth for Hungarian business documents is the
   real bottleneck in this domain. If you have a document set you can share legally, get in touch
   via [docai.hu](https://docai.hu) or [k3.hu](https://k3.hu).
4. **Synthetic samples.** More fictional-but-realistic Hungarian invoice edge cases (reverse
   charge, EU VAT numbers, multi-currency, self-billing) are welcome under `evals/*/samples/`.

## What we cannot accept

- Real documents containing personal or company-confidential data — under any circumstance, in
  any issue, PR or attachment. See [docs/data-policy.md](docs/data-policy.md).
- Results that cannot be tied to a stated configuration, engine version and hardware.

## Adding a measurement

A new experiment directory must contain:

```text
experiments/<YYYY-MM-DD>-<technical-name>/
├── README.md            # the eight questions — see docs/methodology.md
├── eval-card.yaml       # machine-readable summary, validated against schemas/eval-card.schema.json
└── decision-record.md   # what product decision followed, and what would reopen it
```

Validate the card before opening a PR:

```bash
python3 scripts/validate_eval_cards.py
```

Directory names are technical and searchable (`qwen36-fp8-vs-nvfp4-quality`), not editorial. The
headline stays on the blog.

## Style

- Documentation in English; linked articles are in Hungarian.
- State the sample size next to every claim. If `n` cannot support the claim, say so instead of
  reporting the point estimate as a finding.
- Report negative and inconclusive results with the same weight as positive ones.
