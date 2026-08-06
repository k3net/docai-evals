# Data policy

What may leave the measurement machine, and what may not.

The corpora behind these evaluations are real Hungarian business documents belonging to our
customers: invoices, payroll records, contracts, bank statements. They contain company names, tax
numbers, bank account numbers, addresses and personal names. The policy below is what makes it
possible to publish anything at all.

## Never published

- **Real customer documents** — in any form: source file, OCR text, extracted JSON, screenshot.
- **Personal data** — names, addresses, identifiers, salary figures. Redaction is not accepted as
  a substitute; the document stays on the machine.
- **Company-confidential data** — customer, supplier and partner identities, transaction values,
  bank details, contract terms.
- **Tenant-identifying constants in code** — an own-company tax number or name is a **parameter**
  of a published script, never a literal in it.
- **Internal APIs, infrastructure, production secrets** — hostnames, tokens, VPN addresses,
  database credentials, internal service topology.
- **Undocumented or non-comparable numbers** — a result whose configuration, engine version and
  hardware cannot be stated is not published, even if it is flattering.

## Published

- Evaluation methodology, scoring rules and their version.
- Scoring, normalisation and significance-testing code.
- Run configurations: launch flags, engine versions, sampling parameters, hardware.
- **Synthetic sample documents** and their ground truth — fictional, written for this repository.
- **Aggregated results**: counts, rates, F1 values, throughput figures, p-values.
- Plots derived from aggregates.
- Negative results and failed hypotheses.
- The product decision each measurement produced, and what would reopen it.

## The aggregation rule

A published figure must not be invertible to a document or a person. In practice:

- Counts and rates over a corpus: **yes** (`18 of 100 documents flagged`).
- Per-document result tables from private corpora: **no** — including "anonymised" document
  identifiers, which are still a join key against our own systems.
- Field-level examples: **only** from synthetic samples.

Some early internal reports in our own history contain per-document tables with real company
names. Those reports are not published here, and the corresponding experiment READMEs carry only
the aggregate versions. If you find a real name anywhere in this repository, that is a bug —
please report it (see [../CONTRIBUTING.md](../CONTRIBUTING.md)).

## Synthetic samples

Everything under `evals/*/samples/` is fictional: made-up company names, structurally valid but
unallocated tax numbers, invented amounts and dates. They exist so that the *shape* of the task —
field set, JSON structure, Hungarian formatting conventions, the own-vs-partner distinction — is
inspectable without any real data. They are not a benchmark corpus and results on them are not
comparable to the results in `experiments/`.

## Third-party contributions

Do not attach real documents to issues or pull requests. If you want a document set evaluated,
contact us through [docai.hu](https://docai.hu) or [k3.hu](https://k3.hu) instead.

## Regulatory context

DocAI — operated by [K3Net Kft.](https://k3.hu) — acts as a data processor for its customers under
GDPR, and the platform is used for processing that falls under the EU AI Act's transparency
obligations. Publishing aggregate
evaluation results is compatible with both; publishing the underlying documents would not be.

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu)*
