# Five-minute walkthrough

1. Run `python -m brand_inbox analyze` and open `artifacts/run/report.html`. Say clearly that this run is the offline baseline.
2. Show Dew Lab: three email IDs, latest INR 100,000, original INR 120,000 retained in history, baseline INR 110,000. The agency links by brand, reference, scope and dates.
3. Show Pixelon: USD 1,200 is INR 100,800, but smartphone exclusivity overrides commercial attractiveness.
4. Show QuickCash: assistant-directed instructions are quarantined. No invented INR 500,000 offer and no private details in a draft.
5. Show AuralBuds: above-base pay does not include perpetual advertising rights or whitelisting automatically.
6. Run the evaluator. Then show the stress report's failures so the perfect development score is not misleading.

## Questions to prepare for

- **Why rules and an LLM?** Rules make the supplied examples cheap and reproducible; the model handles language variation. Policy math must remain deterministic.
- **Is the offline mode AI?** No. It is explicitly labeled. Ollama is an optional real model path whose end-to-end quality still needs local measurement.
- **Is 15/15 meaningful?** It is a development regression result, not a blind benchmark. The stress set scores lower and exposes limited language coverage.
- **Why no embeddings for grouping?** Only 15 emails; corroborating fields are interpretable. Similarity alone can wrongly merge different campaigns.
- **Can prompt injection still work?** It may distort extraction. No model tools or automatic sending limit impact, and source validation helps auditing; there is no claim of perfect prevention.
- **Why not accept above-rate offers?** Rights, policy conflicts, past deadlines and missing essential terms matter as much as the number.
- **What is a gift worth?** Its stated retail value is not cash income. Gifting does not satisfy the cash rate card automatically.
- **What fails today?** Number words, abbreviations, some retractions, complex multi-campaign messages, unknown years/timezones and policy paraphrases.
- **How would you scale?** Cache by content/profile/prompt/model version, use a queue with bounded workers, measure actual token load and latency, and prioritize a human review queue.
- **How did you use AI coding tools?** ChatGPT/Codex generated implementation, tests and documentation. Describe your own later review truthfully; do not claim to have personally written or live-tested every part.
