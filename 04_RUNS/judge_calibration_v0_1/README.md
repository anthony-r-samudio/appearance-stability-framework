# AOSL Judge Calibration v0.1

Purpose:
Test whether AOSL judges can correctly score known clean and intentionally flawed outputs.

Primary questions:
1. False-positive rate on clean controls
2. Correct failure attribution
3. Per-constraint agreement
4. Repeatability at temperature 0
5. Cross-judge disagreement patterns

Initial scope:
- 20 frozen calibration cases
- human reference annotations created before model scoring
- GPT-OSS 20B first
- additional judges only after local baseline is verified

Do not scale until calibration behavior is understood.
