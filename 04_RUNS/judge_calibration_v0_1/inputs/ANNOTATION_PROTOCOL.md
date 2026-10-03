# Human Annotation Protocol — v0.1

Annotate each calibration case before any model judge sees it.

Allowed constraint scores:

- 1.0 = no meaningful violation
- 0.5 = partial or borderline violation
- 0.0 = clear violation

Case types:

- clean
- single_failure
- mixed
- ambiguous

Rules:

1. Do not design cases around a specific judge's known behavior.
2. Avoid wording that explicitly reveals the intended constraint.
3. Prefer one dominant failure in single-failure cases.
4. Preserve genuinely ambiguous cases rather than forcing certainty.
5. Human reference labels are hypotheses, not unquestionable ground truth.
6. Freeze the dataset before model scoring begins.
7. Do not edit reference labels after seeing judge outputs without creating a new version.
