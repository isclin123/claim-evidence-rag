# Claim–Evidence reproducibility package

This package reproduces the experiments in **ICLR_2027_Rag_Poisoning (15).pdf**
(34 pages, including Appendices A–F). It contains **PoisonedRAG,
Claim–Evidence and CorruptRAG-AS** on NQ, HotpotQA and MS MARCO.
Tables 2–26 and Figures 1 and 3–13 have explicit file mappings in `PAPER_MAP.md`.
Table 1 and the conceptual Figure 2 are excluded by author instruction.

Upload the **contents of this folder** as the GitHub repository root, including
the `.jsonl.gz` data/response files, `.gitignore`, and `.gitattributes`.
`.gitattributes` preserves the exact bytes used by the integrity manifest.
No original project folders, model weights, caches, or `output/` files are needed.

The method comparison evaluates **8 local models × 3 fixed methods** in
each benign-context setting. The remaining batches evaluate poison count,
position, document ordering and commercial transfer. All local batches use
the same eight-model panel.

## Quick start

Use Python 3.11–3.13. From this folder:

```bash
python -m venv .venv
# Activate .venv using the command for your operating system.
python -m pip install -r requirements.txt
python tools/verify_package.py
python tools/reproduce.py --statistics --figures
```

Verification checks file hashes, all 3,300 method documents, the complete
experimental matrices, the three-method/eight-model scope and recorded prompt hashes. Reproduction rescores
responses, recomputes reported inference and rebuilds plots/LaTeX tables.
Both commands make **zero model or network calls**. Output goes into `output/`.
For a faster point-estimate check, omit `--statistics --figures`.

## Rerun response generation

Install Ollama and a matching model from `data/models.json`, then run:

```bash
python tools/rerun.py --batch answer_bearing --model qwen35_9b --limit 3
python tools/rerun.py --batch answer_bearing --model qwen35_9b --execute
```

The first command is an offline dry run. `--execute` calls local Ollama with
the frozen inputs, exact prompt, settings, seeds and retained trial order.
Repeat for all eight models and five batches in `ENVIRONMENT.md`.
After generation, run `python tools/score_reruns.py` to score the new responses;
incomplete experiment matrices are explicitly labeled in its output.
Commercial services use a manual protocol; exact prompts and recorded responses
are supplied for offline replication.

| Folder | Contents |
|---|---|
| `data/` | 300 questions, both benign libraries, base/constructed passages, protocol, digests, schedules, commercial sample/prompts |
| `code/` | Three builders, context assembly, official scorer and statistical primitives |
| `results/` | 396,000 local responses, 1,798 valid commercial responses and 2 blocked trials, frozen numerical targets |
| `paper_assets/` | Main-text figures/tables and directly referenced supplements, with source data and generators |
| `tools/` | Verification, offline reproduction, asset rebuilding and local reruns |
| `provenance/` | File manifest and extraction hashes |

See [PAPER_MAP.md](PAPER_MAP.md) for paper-to-file mapping and
[REPRODUCIBILITY.md](REPRODUCIBILITY.md) for the statistical calibration boundary.
The experiment starts from the frozen input library; it does not redownload
corpora or regenerate stochastic input libraries. Table 1 and the conceptual Figure 2 are excluded by author instruction.
