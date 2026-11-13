# Evaluation report

Mode: **ollama_live** · Model: qwen2.5:3b
- Coverage: 15/15
- Category correctness: 15/15; processed-only accuracy: 100.0%
- Key fields: 45/45
- Exact grouping: True
- Deal/risk/action checks: 36/36

Development fixture accuracy, not blind generalization. No live-model claim for rules_offline.

Numbers compare numerically; strings exact; lists order-insensitive. Risks checked for expected presence. Processing failures count against all-input accuracy.

## Mismatches

No mismatches on these checks. This does not establish generalization.

## Confusion matrix

| Expected | Predicted | Count |
|---|---|---:|
| deal_offer | deal_offer | 7 |
| needs_more_info | needs_more_info | 2 |
| not_a_fit | not_a_fit | 2 |
| scam_or_phishing | scam_or_phishing | 3 |
| spam | spam | 1 |
