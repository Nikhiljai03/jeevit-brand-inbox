# Assignment coverage

| TASK.md requirement | Implementation | Evidence |
|---|---|---|
| Five email categories | `policy.assess`; enum contract | All 15 expected labels; evaluation confusion matrix |
| Structured commercial details | `extraction`, `schemas`, optional `provider` | Original observations and exact source quotes in analysis.json |
| Group related emails and latest terms | `grouping` | E-01/E-02/E-11 one group; history and inherited terms; changed-brand tests |
| Profile-based risks | `policy` | FX, rate, deadline, exclusivity, prohibited category, gifting and rights checks |
| Next action and short draft | `policy.assess`, `policy.draft` | Selected expected actions and no-reply safety checks |
| Creator summary | `rendering` | Generated Markdown and read-only HTML |
| Own expected answers for 15 emails | `eval/expected_answers.json` | Authored before implementation; no runtime access |
| Honest evaluation | `evaluation`, `examples` | Offline results, stress failures, live-model limits |
| Fresh-clone instructions | `README.md`, `START-HERE.md` | Dependency-free source execution; fresh archive smoke checked |
| Model/code design explanation | `README.md`, `docs/ARCHITECTURE.md` | Explicit provider modes and deterministic policy |
| Rough cost/time and 1,000/day | README and benchmark.json | Measured offline latency; labeled live assumptions |
| Another-week plan | README | Evaluation, corrections, incremental ingestion, operations |
| AI tool disclosure | README | Generated work vs unverified human/model checks explicitly separated |
| No keys, .env.example | `.gitignore`, `.env.example` | No credentials needed or included |
| Treat content as untrusted | prefilter, schema/quote checks, no model tools, fixed drafts | Adversarial and escaping tests; documented limitations |
| Free/local inference option | Ollama adapter | Real HTTP contract tested with mock server; live model quality NOT verified |
| GitHub submission | Source project prepared | Applicant must create/push repository and share its URL |

The optional Ollama path is implemented but not a measured live AI submission. A reviewer can reproduce all offline results now. Before presenting it as an AI-model evaluation, run the local model command and retain its actual report, including failures.
