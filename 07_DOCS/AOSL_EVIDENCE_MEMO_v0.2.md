# AOSL Evidence Memo v0.2

## Metadata

| Field          | Value                                                                                           |
|----------------|-------------------------------------------------------------------------------------------------|
| Date           | 2026-05-02                                                                                      |
| Project        | AI Output Stability Layer                                                                       |
| Framework      | Appearance Stability Framework                                                                  |
| Constraint set | C1–C10                                                                                          |
| Status         | Early validation evidence — not production proof                                                |
| Scope          | Controlled validation runs across stable, pressured, synthetic, cross-generator, and cross-judge conditions |

---

## 1. Executive Summary

AOSL now has early controlled evidence that divergence rises under structural pressure,
appears across more than one generator model, and remains directionally elevated under a
second independent judge model.

This does not yet prove production readiness, naturalistic traffic performance, or reliable
per-constraint attribution.

Five conditions have now been scored in controlled tests. The results form a clean ordered
separation from stable real outputs to intentionally flawed synthetic outputs. Two generator
models (DeepSeek and Llama) both show elevated divergence under structural pressure, and a
second judge model (Gemini) scores those same pressured Llama outputs at an elevated level
relative to the known stable baselines.

---

## 2. Evidence Ladder

```
DS stable  <  Llama stable  <  Llama pressured  <  DS pressured  <  synthetic flawed
  0.0117   <    0.0250      <      0.0722        <    0.0939      <      0.2050
```

All five points are ordered in the expected direction. Both pressured conditions sit above
both stable baselines and below the synthetic flawed ceiling. This ordering is preserved
across two generator models and is consistent with a second judge model on the Llama
pressured condition.

---

## 3. Baseline and Validation Table

| Condition             | Dataset                    | Generator                        | Judge                      | Mean D | Repeats | Key interpretation                                    |
|-----------------------|----------------------------|----------------------------------|----------------------------|--------|---------|-------------------------------------------------------|
| DeepSeek stable       | real_model_validation_30   | deepseek/deepseek-chat           | deepseek/deepseek-chat     | 0.0117 | 1       | Near-zero divergence on stable real outputs           |
| Llama stable          | real_model_validation_30   | meta-llama/llama-3.1-8b-instruct | deepseek/deepseek-chat     | 0.0250 | 1       | Near-zero divergence from second generator on stable prompts |
| Llama pressured       | real_failure_validation_30 | meta-llama/llama-3.1-8b-instruct | deepseek/deepseek-chat     | 0.0722 | 3       | Elevated divergence; 2.9× above Llama stable floor   |
| DeepSeek pressured    | real_failure_validation_30 | deepseek/deepseek-chat           | deepseek/deepseek-chat     | 0.0939 | 3       | Elevated divergence; 8.0× above DeepSeek stable floor |
| Synthetic flawed      | validation_30              | synthetic hand-crafted           | deepseek/deepseek-chat     | 0.2050 | 1       | Intentional failures; upper reference point           |
| Llama pressured (Gemini) | real_failure_validation_30 | meta-llama/llama-3.1-8b-instruct | google/gemini-2.0-flash-001 | 0.1350 | 1    | Elevated under second judge; scale unresolved         |

All DeepSeek-judge runs: cheap judge mode, 0 errors. Gemini-judge run: standard mode (800 max tokens), 0 errors, 30 rows.

---

## 4. What v0.2 Adds Beyond v0.1

- v0.1 established initial ordered separation using one generator (DeepSeek) across three
  conditions: stable real, pressured real, and synthetic flawed.

- v0.2 adds the **Llama stable baseline** (real_model_validation_30, Llama generator,
  DeepSeek judge, mean D = 0.0250). This confirms Llama's unpressured outputs score
  near-zero, close to the DeepSeek stable floor.

- v0.2 adds the **Llama pressured-real 3-repeat result** (real_failure_validation_30,
  Llama generator, DeepSeek judge, mean D = 0.0722, avg prompt std dev = 0.0197,
  verdict KEEP_BUT_RECALIBRATE).

- v0.2 adds a **cross-generator ordered separation**: both generators show elevated
  divergence under pressure and near-zero divergence on stable prompts.

- v0.2 adds an **initial zero-error Gemini judge run** on Llama pressured outputs
  (30 rows, 0 errors, mean D = 0.1350). This is the first cross-judge directional result.

- v0.2 upgrades the status from "single-generator early evidence" to "early cross-generator
  and directional cross-judge evidence."

---

## 5. Cross-Generator Finding

**Core claim: The pressured-real signal is not limited to one generator model.**

- DeepSeek pressured-real Mean D = 0.0939 (3-repeat, DeepSeek judge)
- Llama pressured-real Mean D = 0.0722 (3-repeat, DeepSeek judge)
- Both pressured runs are above their own stable baselines.
- Llama pressured (0.0722) is 2.9× above the Llama stable floor (0.0250).
- DeepSeek pressured (0.0939) is 8.0× above the DeepSeek stable floor (0.0117).
- Both pressured runs remain below the synthetic flawed ceiling (0.2050).

The two stable baselines are close to each other (gap = 0.0133), confirming that both
generators behave similarly on unpressured prompts. The DeepSeek pressured lift is larger
relative to its stable floor (~8.0×) than the Llama pressured lift (~2.9×), suggesting
Llama may respond differently to structural pressure, or its inherent output style partially
absorbs the pressure signal.

This supports generator-side generalization of the divergence signal. It does not prove
universality across all models or prompt types.

---

## 6. Cross-Judge Finding

**Core claim: The pressured-real signal remains directionally elevated under an independent
Gemini judge.**

- DeepSeek judge on Llama pressured outputs (3-repeat): Mean D = 0.0722
- Gemini judge on the same Llama pressured outputs (1-repeat): Mean D = 0.1350
- Gemini scored all 30 rows with 0 errors.
- Both judges produce Mean D well above the known stable baselines (0.0117 and 0.0250).

Both judges agree in direction: Llama pressured outputs are divergent. The Gemini judge
scores them approximately 1.9× higher than DeepSeek. This difference in magnitude is
unresolved. No Gemini-scored stable baseline exists yet, so the Gemini scale cannot be
normalized against a shared reference floor.

Both judges identify C7 (Uncertainty Acknowledgment) and C4 (Epistemic Calibration) as
the primary failure-detecting constraints.

Attribution match rates remain weak under both judges: DeepSeek 0.32, Gemini 0.08. Exact
constraint routing should not be used for diagnostics under either judge at this stage.

This is directional cross-judge evidence. It is not full judge-independence proof.

---

## 7. What AOSL Can Claim Now

- AOSL can detect aggregate divergence differences between stable, pressured, and synthetic
  flawed outputs in controlled tests.
- The ordered separation (stable < pressured < synthetic flawed) holds across two generator
  models using the same judge.
- The pressured-real signal appears across at least two generator models (DeepSeek and
  Llama 3.1 8B Instruct).
- The pressured-real signal remains directionally elevated under a second judge model
  (Gemini 2.0 Flash) with zero errors on all 30 rows.
- Aggregate Mean D is more reliable than per-constraint attribution at this stage.
- Repeat stability is acceptable: avg prompt std dev = 0.0197 (Llama pressured) and
  0.0281 (DeepSeek pressured), both within the 0.1 limit.
- AOSL is currently a research validation framework, not a production audit standard.

---

## 8. What AOSL Cannot Claim Yet

- Cannot claim production readiness. Scoring behavior under real input diversity, latency,
  cost, and edge-case handling have not been characterized.
- Cannot claim naturalistic traffic performance. All prompt sets are purpose-built for
  structural pressure. Behavior on naturalistic prompts is untested.
- Cannot claim universal model generalization. Two generators have been tested. Whether the
  signal extends to other architectures, sizes, or training regimes is unknown.
- Cannot claim final judge independence. The Gemini run is 1 repeat with no shared stable
  baseline. Cross-judge scale calibration is unresolved.
- Cannot claim reliable exact C1–C10 attribution. Attribution match rates of 0.32
  (DeepSeek judge) and 0.08 (Gemini judge) are both below the 0.6 threshold. Individual
  constraint scores should not be used for constraint-specific diagnostics.
- Cannot claim regulatory-grade audit validity. The framework has not been reviewed for
  compliance, fairness, or adversarial robustness.

---

## 9. Current Weak Points

- Gemini judge has only 1 repeat. No prompt-level standard deviation is available for
  the Gemini judge condition.
- Gemini judge scale differs from DeepSeek (approximately 1.9× higher on the same
  outputs). Without a Gemini-scored stable baseline, this difference cannot be normalized.
- Attribution match rates remain weak, especially for the Gemini judge (0.08). Constraint
  routing is unreliable across both judges.
- The pressure prompt set is purpose-built. All 30 prompts embed structural failure
  invitations. The degree to which this generalizes to naturalistic prompts is unknown.
- Stable baselines are still limited. Both stable baselines are 1-repeat single-pass
  estimates. Prompt-level repeatability for the stable conditions has not been measured.
- No large-scale naturalistic benchmark exists. All evidence comes from controlled,
  purpose-built datasets of 30 prompts.

---

## 10. Next Required Experiments

1. Run the Gemini judge on Llama pressured outputs with 3 repeats. Measure prompt-level
   standard deviation and confirm the 1-repeat signal holds under repeated Gemini scoring.

2. Run the Gemini judge on stable Llama outputs (real_model_validation_30, Llama generator).
   This creates a Gemini-scale stable baseline and allows the Gemini pressured score to be
   properly normalized.

3. Run the Gemini judge on DeepSeek pressured outputs (real_failure_validation_30, DeepSeek
   generator). If Gemini also detects elevated D on DeepSeek generator outputs, the
   cross-judge evidence extends to both generators.

4. Add confidence intervals and effect sizes across generator and judge conditions. A
   statistical comparison script is needed before any effect-size claims can be made.

5. Build a small naturalistic prompt benchmark. Until detection is confirmed on prompts
   not designed to elicit failures, the system's real-world generalization is untested.

6. Only after experiments 1–5 are complete should product or demo claims be considered.

---

## 11. Founder-Ready Summary

AOSL is showing early controlled evidence that structurally pressured AI outputs produce
higher divergence than stable outputs. The signal now appears across DeepSeek and Llama
generators and remains directionally elevated when judged by Gemini instead of DeepSeek.
This is not production proof yet, but it is a meaningful validation step toward testing
whether surface-fluent outputs can be systematically audited for structural instability.

---

```
Version : v0.2
Status  : early cross-generator and directional cross-judge evidence — not production proof
Scope   : two generators, two judges, two stable baselines, two pressured conditions, one synthetic set
Updated : 2026-05-02
Prior   : AOSL_EVIDENCE_MEMO_v0.1.md (single-generator, single-judge evidence)
```
