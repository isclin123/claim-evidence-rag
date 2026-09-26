# Environment

Offline checks were run with Python 3.13.11, NumPy 2.4.2, SciPy 1.17.1 and
Matplotlib 3.11.0 and pandas 3.0.3, pinned in `requirements.txt`. Verification and dry runs use
only the Python standard library. Statistical reproduction uses NumPy/SciPy;
figures use Matplotlib. Table generators emit LaTeX snippets; full compilation
requires LaTeX and the manuscript template. Available fonts can affect rendering.
The main figures use Times New Roman with Times/Nimbus Roman/DejaVu Serif
fallbacks; appendix figures use DejaVu Sans. Reproduction checks numerical
values and table text independently of font availability. Use
`python tools/verify_paper_outputs.py --strict-render` only when exact PNG
bytes are expected in the recorded font/platform environment.

Create `.venv` with `python -m venv .venv`. Activate it on PowerShell with
`.venv/Scripts/Activate.ps1`, or on macOS/Linux with `source .venv/bin/activate`.
Then run the README installation and verification commands.

## Local generation

The recorded runtime is Ollama 0.30.6. Exact tags/digests are in
`data/models.json`. Obtain weights separately. The runner never downloads
weights; it rejects digest drift unless `--allow-model-drift` is explicitly
set, and records the actual digest in the new run.

| Model code | Ollama tag |
|---|---|
| `qwen35_9b` | `qwen3.5:9b` |
| `llama31_8b` | `llama3.1:8b` |
| `mistral_7b` | `mistral:7b` |
| `qwen3_1_7b` | `qwen3:1.7b-q4_K_M` |
| `qwen3_4b` | `qwen3:4b-q4_K_M` |
| `qwen3_8b` | `qwen3:8b-q4_K_M` |
| `llama32_3b` | `llama3.2:3b-instruct-q4_K_M` |
| `gemma3_4b` | `gemma3:4b-it-q4_K_M` |

Batch choices: `natural`, `answer_bearing`, `count`, `position`, `ordering`.
Per-model calls are 2,700; 2,700; 9,000; 8,100; and 27,000 respectively.
Temperature 0.1; context limit 4,096; output limit 80 tokens; thinking off;
seeds 101/202/303. Exact system/user prompts are in `data/protocol.json`.

The runner uses local Ollama `/api/generate`, without conversation history,
retrieval or tools. It stops on errors and resumes verified completed keys.
Remove a stale `writer.lock` only after confirming the prior runner stopped.
Use a small `--limit` to check memory/runtime before a full run.

## Commercial protocol

The recorded access window is 14–15 September 2026. GPT-6 Astra used Codex CLI,
medium effort; Claude Opus 5 used web chat, high effort; DeepSeek V4.1 Flash
used web chat, thinking off. Each trial began a new session. Search/retrieval,
tools and memory were disabled in the recorded protocol. The interfaces did
not expose local temperature, token-limit or seed controls. Historical model
availability is not guaranteed. Follow exact prompts and preserve missing
responses separately in any new run; do not mix them into the frozen records.

Commercial accounts are not automated by this package. Offline reproduction
requires no accounts or model calls.
