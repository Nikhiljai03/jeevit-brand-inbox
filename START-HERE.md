# Start here, Nikhil

1. Extract the ZIP.
2. Open the `jeevit-brand-inbox` folder in VS Code.
3. Open Terminal in that folder. You need Python 3.10 or newer.
4. Run:

```sh
python -m brand_inbox analyze
python -m brand_inbox evaluate --strict
python -m unittest discover -s tests -v
```

5. Open `artifacts/run/report.html` in Chrome to see the results.

On Windows you can also run `run_demo.bat`. If `python` is unavailable, use `py -3` instead.

This first run is FREE OFFLINE RULES MODE. It is not a live AI run. There are no packages to install and no keys to enter.

To use a real local AI model, follow the Ollama setup in README.md. After installing Ollama and pulling the model:

```sh
python -m brand_inbox analyze --provider ollama --model qwen2.5:3b --timeout 180 --out artifacts/live
python -m brand_inbox evaluate --actual artifacts/live/analysis.json --out artifacts/live-evaluation
```

Before submitting: review the source, run the real model if possible, read its mistakes, and understand Dew Lab, QuickCash and AuralBuds. Do not describe the offline scores as live AI results. Your requested submission is a GitHub link; upload the project to your repository yourself. Nothing has been sent to the hiring team.

Optional hosted mode is experimental. README.md documents Groq API setup and `python -m brand_inbox analyze --provider api --out artifacts/api`. It sends selected email content to an external provider. Live Groq and Gemini smoke attempts did not process any emails; see the preserved Gemini failure in `examples/api-experimental/gemini-smoke/analysis.json`. Do not enable billing or assume a successful provider configuration. `.env` files are not loaded automatically; set the key privately in your terminal, never in chat, a command argument, or a committed file.
