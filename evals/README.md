# Evaluation suites

An *eval* here is a measuring instrument: a task, a scoring rule and a set of known limits. An
*experiment* is one use of that instrument to compare specific systems. Keeping them apart is what
makes results comparable across dates — when the instrument changes, the version changes with it.

| Suite | Task | Scoring | Used by |
|---|---|---|---|
| [hu-invoice-kie](hu-invoice-kie/) | Strict-JSON field extraction from Hungarian invoices | Field-level P / R / F1, raw and normalised | model comparisons, quantisation comparisons |
| [counterparty-role](counterparty-role/) | Which of the two companies on the invoice is the partner | Deterministic gate + McNemar's exact test | quantisation decision, prompt changes |
| [chat-business-scenarios](chat-business-scenarios/) | Tool selection and multi-step financial reasoning | Tool-call checks + LLM judge against a rubric | model comparisons, agent-loop changes |
| [hu-verse-prosody](hu-verse-prosody/) | Hungarian verse form: syllable count, rhyme, rhyme scheme | Deterministic, no model call — plus an independent author classifier as a style proxy | fine-tuning vs. selector comparison |

Inference performance is measured separately — see [../performance/](../performance/).

## What every suite states

1. **What it measures** — and, more importantly, what it does *not*.
2. **How a unit is scored** — with the equality rule for each field type.
3. **What ground truth means here** — who validated it and what could be wrong with it.
4. **Known blind spots** — the failure modes this instrument cannot see.

Point 4 is the reason `counterparty-role` exists at all: `hu-invoice-kie` was blind to a
business-critical error class, we found out the hard way, and the fix was a second instrument
rather than a tweak to the first one.

`hu-verse-prosody` adds a fifth thing the others cannot do, and it is worth reading for that alone:
**it validates the instrument against external truth and a control group before any system is
compared with it.** The syllable counter is checked against works known independently to be written
in twelve-syllable lines; the rhyme detector is checked against the same lines re-paired across
stanzas, where the vocabulary is identical and only the intent to rhyme is missing. That is possible
because the corpus is public and the ground truth is literary-historical fact. On customer invoices
there is no equivalent external truth — which is exactly why the practice is documented where it
*was* possible.

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu)*
