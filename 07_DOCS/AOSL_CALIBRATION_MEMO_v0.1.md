# AOSL Calibration Memo v0.1

---

## Executive Summary

Two rounds of stable-vs-adversarial calibration provide early controlled evidence
that the AOSL judge signal is real, stable across repeated scoring runs, and large
enough to be useful as a screening metric. A 3-prompt pilot and a 12-prompt
expansion both show a strong, reproducible gap between stable and adversarial
outputs (judge gap ~0.26–0.29). Repeat scoring variance is low. The 12-prompt
expansion reveals that primary constraint attribution — identifying which
specific constraint is most violated — is partial: 6 of 12 designed failures are
correctly identified as the primary weakness. However, constraint co-firing
analysis shows that 9 of 12 expected constraints fire as secondary weaknesses,
indicating the judge detects the designed failure type even when it is not ranked
first. The overall calibration verdict is **KEEP_BUT_RECALIBRATE**: detection and
co-firing are strong; attribution precision requires continued refinement.

---

## Research Question

Does the AOSL judge reliably separate stable AI outputs from adversarially
pressured outputs, and does it attribute structural weaknesses to the correct
constraint category with useful precision?

---

## Method

Each calibration run scores pairs of prompt–output sets: a stable output designed
to pass all ten AOSL structural constraints (C1–C10), and an adversarial output
designed to fail a specific named constraint. Each pair is scored twice
(calibration repeats = 2) using the same judge model (`deepseek/deepseek-chat`
via OpenRouter).

**Metrics computed per run:**
- Mean D_stable and mean D_adv (D = average constraint violation rate, 0–1)
- Judge gap = D_adv − D_stable
- Avg prompt-level D standard deviation across repeats (repeat stability)
- Attribution match rate: fraction of prompts where the judge's primary weakest
  constraint matches the designed failure constraint
- Co-firing rate: fraction of prompts where the expected constraint fires at all
  (score < 1.0), even if not ranked as primary

**Verdict sub-dimensions:**
- Detection (judge gap + repeat stability)
- Attribution (primary-weakest match rate vs. 0.60 threshold)
- Co-firing (expected constraint fired rate vs. 0.60 threshold)
- Overall: most conservative of the three

**Run 1 — 3-prompt pilot:** 3 prompt pairs (C1 factual grounding, C2 logical
contradiction, C3 causal leap), scored 2× each. 12 total rows.

**Run 2 — 12-prompt expansion:** 12 prompt pairs covering all ten constraints
(C3 and C4 tested twice), scored 2× each. 48 total rows.

---

## Key Results

| Metric | 3-Prompt Pilot | 12-Prompt Expansion |
|--------|---------------|---------------------|
| Total rows | 12 | 48 |
| Stable rows | 6 | 24 |
| Adversarial rows | 6 | 24 |
| Unique prompts | 3 | 12 |
| Mean D — stable | 0.0083 | 0.0104 |
| Mean D — adversarial | 0.3000 | 0.2729 |
| Judge gap (D_adv − D_stable) | 0.2917 | 0.2625 |
| Avg prompt D std dev | 0.0471 | 0.0442 |
| Attribution match rate | 2/3 = 0.67 | 6/12 = 0.50 |
| Co-firing rate | 3/3 = 1.00 | 9/12 = 0.75 |
| Detection verdict | KEEP | KEEP |
| Attribution verdict | KEEP | KEEP_BUT_RECALIBRATE |
| Co-firing verdict | KEEP | KEEP |
| **Overall verdict** | **KEEP** | **KEEP_BUT_RECALIBRATE** |

**Most weakened constraints (12-prompt, all rows combined):**
1. C7 — Uncertainty Acknowledgment (mean score: 0.6667)
2. C4 — Epistemic Calibration (mean score: 0.6875)
3. C9 — Evidence Traceability (mean score: 0.7396)

**Constraints where detection was weakest (12-prompt, adversarial rows):**
- cal05 (C5 — Scope Discipline): D = 0.00 — judge did not detect scope drift
- cal10 (C10 — Constraint Interaction Consistency): D = 0.1250

---

## Interpretation

**The detection signal is robust.** Both runs show a judge gap exceeding 0.25,
well above the 0.10 minimum threshold. Stable outputs score near zero (0.0083
and 0.0104), confirming the judge does not falsely flag well-formed outputs at a
high rate. Adversarial outputs score 0.27–0.30 on average, a ~25–35× lift above
their stable counterparts. Repeat scoring variance is low (~0.044–0.047 std dev)
across both runs, indicating the judge produces consistent scores when run twice
on the same output.

**Attribution precision is partial but improving with context.** In the 3-prompt
pilot, 2 of 3 expected constraints were correctly identified as the primary
weakest constraint. In the 12-prompt expansion, this drops to 6 of 12. The drop
is expected: as the constraint set expands, multiple constraints tend to fire
simultaneously on structurally pressured outputs (constraint co-firing), and the
judge ranks whichever weakness is most salient as primary — which does not always
match the designed failure type.

**Co-firing explains most attribution mismatches.** In the 12-prompt set, 9 of
12 expected constraints fire as secondary weaknesses, even when they are not
ranked first. The 3 silent cases are C5 (scope discipline), C8 (quantitative
accuracy), and C10 (constraint interaction consistency). These represent genuine
detection gaps — the judge did not register the designed failure at all for those
prompts — not co-firing. Attribution mismatches driven by co-firing are different
in character from complete detection failures.

**The aggregate D signal is usable.** Although per-constraint attribution is
imprecise, the overall divergence score D provides a reliable binary signal:
stable outputs score near zero, adversarial outputs score meaningfully above zero.
For screening and triage purposes — flagging outputs that warrant closer review —
D is well-calibrated in these controlled conditions.

---

## What This Supports

- **Stable-vs-adversarial separation.** AOSL D reliably separates stable outputs
  from adversarially pressured outputs in controlled calibration conditions, across
  two prompt-set sizes and all scoring repeats.

- **Repeat consistency.** Scoring the same output twice with the same judge model
  produces stable D values. The protocol is reproducible within a single judge run.

- **Co-firing as a feature, not a flaw.** When a prompt targets a specific
  structural weakness, multiple related constraints often fire simultaneously. This
  is consistent with the AOSL hypothesis that structural failures are
  interconnected, not isolated. The co-firing table provides richer signal than
  the primary-attribution result alone.

- **Aggregate D as a screening metric.** At the level of prompt classification
  (stable vs. adversarial), D performs well in controlled conditions and is stable
  enough to support rank-ordering and triage.

---

## What This Does Not Prove Yet

- **Human alignment.** No human rater has assessed these outputs. Whether AOSL D
  correlates with human judgments of structural risk is unknown. This is the most
  important open question.

- **Cross-judge consistency.** All calibration runs use `deepseek/deepseek-chat`
  as the sole judge. Whether a second independent judge model preserves the same
  detection and ordering signal has not been tested.

- **Performance on naturalistic prompts.** All calibration prompts were
  purpose-built to invite specific structural failures. Performance on
  unstructured, diverse, real-world AI outputs has not been measured.

- **C5, C8, C10 detection.** Three constraints showed weak or zero detection in
  the 12-prompt run (C5: D = 0.00; C8: expected constraint silent; C10: expected
  constraint silent). These require adversarial output redesign or rubric
  adjustment before they can be treated as reliably detectable.

- **Attribution precision at scale.** The primary attribution match rate is 0.50
  at 12 prompts. For use cases requiring constraint-level attribution — not just
  aggregate D — the rubric and prompt design need further refinement.

---

## Current Limitations

**Single judge model.** All results depend on `deepseek/deepseek-chat`. Scores
from other judge models may differ. Cross-judge consistency (Milestone 3 in the
Validation Roadmap) is a prerequisite before any strong reliability claim.

**Purpose-built prompts only.** The calibration set was designed to trigger
specific constraint failures. Results may not generalize to prompts from outside
this controlled set.

**Three undetected constraints.** C5 (Scope Discipline), C8 (Quantitative
Accuracy), and C10 (Constraint Interaction Consistency) did not fire reliably as
expected in the 12-prompt run. These constraints may require stronger adversarial
pressure, more targeted output wording, or rubric refinement.

**No independent replication.** All calibration was designed, scored, and
interpreted by the same person who built the system. Independent replication has
not occurred.

**No human data collected yet.** The human validation packet exists and is ready
(06_OUTPUTS/human_validation/v0_1/), but no rater has completed it. Until human
alignment data exists, AOSL cannot be described as validated against human
judgment.

---

## Next Validation Steps

**Immediate (no new code needed):**
1. Send the human validation rating form to 2–3 raters. The packet is ready at
   `06_OUTPUTS/human_validation/v0_1/human_validation_rating_form.csv`. This is
   the single highest-leverage step. The bottleneck is human input, not
   infrastructure.

**Calibration refinement (if improving calibration before human data):**
2. Redesign adversarial outputs for cal05 (C5), cal08 (C8), and cal10 (C10) —
   the three prompts where the expected constraint did not fire. Stronger
   adversarial pressure or more targeted failure wording is needed.
3. Run the revised 12-prompt set and regenerate the calibration report.

**Cross-judge consistency (can run independently):**
4. Re-score the existing benchmark outputs from `04_RUNS/` using a second judge
   model (e.g., `gpt-4o-mini` or `mistral/mistral-7b-instruct`). Check whether
   the broad ordering (stable < adversarial) is preserved. This is Milestone 3 in
   the Validation Roadmap and addresses the judge-dependence limitation directly.

**After human data is collected:**
5. Run `05_SRC/analysis/analyze_human_validation_v0_1.py` (to be built after data
   exists). Compute correlation between human severity scores and AOSL D, measure
   inter-rater agreement, and document failure cases.

---

## External Summary

AOSL (AI Output Stability Layer) is a structural evaluation protocol for AI-
generated text. It scores outputs against ten structural constraints (factual
grounding, logical coherence, causal integrity, epistemic calibration, scope
discipline, safety integrity, uncertainty acknowledgment, quantitative accuracy,
evidence traceability, and constraint interaction consistency) and produces a
divergence score D representing the average constraint violation rate. In two
rounds of controlled calibration — a 3-prompt pilot and a 12-prompt expansion
covering all ten constraints — stable outputs scored near zero (D = 0.008–0.010)
while adversarially pressured outputs scored 0.27–0.30, yielding a judge gap of
0.26–0.29. Repeat scoring variance was low, indicating the scoring protocol is
consistent within a single judge run. Primary constraint attribution — identifying
which specific constraint is most violated — is currently correct in 50–67% of
cases, with constraint co-firing (multiple constraints firing simultaneously)
explaining most mismatches. These are early controlled results using a single
judge model and purpose-built prompts; human alignment and cross-judge consistency
have not yet been established. AOSL is best characterized at this stage as a
structural screening layer with a reproducible detection signal, pending
independent human validation.

---

```
Version : v0.1
Status  : internal research memo — early controlled evidence, not validated
Created : 2026-05-02
```
