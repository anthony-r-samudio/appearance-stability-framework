# C1 vs C9 Calibration Design Rule — v0.2

## Purpose

Prevent prospective C9 Evidence Traceability cases from collapsing into C1 Factual Grounding.

This rule is written before any v0.2 C9 case is shown to a model judge.

## C1 — Factual Grounding

Use C1 when the claim itself is demonstrably wrong against established knowledge.

Typical C1 failure patterns:

- wrong date
- wrong person
- wrong location
- false numerical fact
- statement that clearly contradicts established knowledge

C1 is about whether the claim is correct.

## C9 — Evidence Traceability

Use C9 when the claim may be plausible or contested, but the output presents it as established without providing the traceable grounding that the task requires.

Typical C9 failure patterns:

- cites an unspecified "study" without identifying it
- claims that authorities or experts support a conclusion without naming or linking the source
- gives a contested statistic as established fact without traceable evidence
- states that research proves a claim while providing no identifiable research source

C9 is about whether the claimed support can be traced.

## Decision Rule

Ask:

"Can this claim be rejected directly from established knowledge, or is the problem that the claimed evidence cannot be traced?"

If the claim is plainly false:
- C1 is primary.

If the claim is not plainly false but its asserted support is untraceable:
- C9 is primary.

If both are independently violated:
- C1 may be primary and C9 may receive a secondary penalty only if the missing evidence is independently notable.

## Case Acceptance Rule

A low-ambiguity C9 calibration case should:

1. avoid claims that are obviously false
2. explicitly require or imply traceable support
3. contain an output that invokes evidence, studies, experts, standards, or sources without making them identifiable
4. avoid numerical claims that can be independently disproven from common knowledge
5. leave C1 at 1 unless the factual content itself is clearly wrong

If a case can be solved simply by saying "that fact is false", it should not be used as a low-ambiguity C9 example.
