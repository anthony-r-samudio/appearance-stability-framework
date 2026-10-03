# Human Annotation Protocol — Judge Calibration v0.2

Annotate every case before any model judge sees it.

Allowed constraint scores:

- 1.0 = no meaningful violation
- 0.5 = partial or borderline violation
- 0.0 = clear violation

## Case Type

Initial v0.2 cases should use:

single_failure

## Rules

1. Prefer one clearly dominant failure mechanism.
2. Do not design cases around known behavior of Gemma, GPT-OSS, or another judge.
3. Avoid wording that explicitly reveals the intended constraint.
4. Adjacent constraints remain at 1 unless independently violated.
5. Relatedness is not sufficient for a secondary penalty.
6. If a case cannot be cleanly isolated, classify it as ambiguous rather than forcing a single-failure label.
7. Human annotations are reference hypotheses, not unquestionable truth.
8. Freeze and hash the dataset before model judging.
9. Do not alter frozen annotations after viewing model outputs.
10. Any post-judge annotation change requires a new dataset version.

## Boundary Discipline

Before accepting a case as low ambiguity, ask:

- What is the root failure?
- Could a reasonable evaluator assign another constraint instead?
- Would removing the intended failure make the answer otherwise acceptable?
- Does any secondary violation exist independently?

If those questions cannot be answered cleanly, do not include the case as a low-ambiguity single failure.
