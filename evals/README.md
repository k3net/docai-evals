# Evaluation suites

An *eval* here is a measuring instrument: a task, a scoring rule and a set of known limits. An
*experiment* is one use of that instrument to compare specific systems. Keeping them apart is what
makes results comparable across dates — when the instrument changes, the version changes with it.

| Suite | Task | Scoring | Used by |
|---|---|---|---|
| [hu-invoice-kie](hu-invoice-kie/) | Strict-JSON field extraction from Hungarian invoices | Field-level P / R / F1, raw and normalised | model comparisons, quantisation comparisons |
| [counterparty-role](counterparty-role/) | Which of the two companies on the invoice is the partner | Deterministic gate + McNemar's exact test | quantisation decision, prompt changes |
| [chat-business-scenarios](chat-business-scenarios/) | Tool selection and multi-step financial reasoning | Tool-call checks + LLM judge against a rubric | model comparisons, agent-loop changes |

Inference performance is measured separately — see [../performance/](../performance/).

## What every suite states

1. **What it measures** — and, more importantly, what it does *not*.
2. **How a unit is scored** — with the equality rule for each field type.
3. **What ground truth means here** — who validated it and what could be wrong with it.
4. **Known blind spots** — the failure modes this instrument cannot see.

Point 4 is the reason `counterparty-role` exists at all: `hu-invoice-kie` was blind to a
business-critical error class, we found out the hard way, and the fix was a second instrument
rather than a tweak to the first one.

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu)*
