# Evaluation report

Mode: **rules_offline** · Model: none
- Coverage: 8/8
- Category correctness: 8/8; processed-only accuracy: 100.0%
- Key fields: 12/12
- Exact grouping: True
- Deal/risk/action checks: 0/0

Development fixture accuracy, not blind generalization. No live-model claim for rules_offline.

Numbers compare numerically; strings exact; lists order-insensitive. Risks checked for expected presence. Processing failures count against all-input accuracy.

## Mismatches

No mismatches on these checks. This does not establish generalization.

## Confusion matrix

| Expected | Predicted | Count |
|---|---|---:|
| deal_offer | deal_offer | 5 |
| needs_more_info | needs_more_info | 1 |
| not_a_fit | not_a_fit | 1 |
| scam_or_phishing | scam_or_phishing | 1 |
