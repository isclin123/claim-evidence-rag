# Commands

- `python tools/verify_package.py`: hashes, method texts, matrices and prompts.
- `python tools/reproduce.py`: rescore every response and verify point estimates.
- `python tools/reproduce.py --statistics --figures`: also recompute reported
  inference and rebuild figures/tables in `output/`.
- `python tools/rerun.py --batch answer_bearing --model qwen35_9b --limit 3`:
  prepare an offline dry run; `--execute` makes local model calls.
- `python tools/score_reruns.py`: score new responses in `output/reruns/`,
  reporting whether each experiment matrix is complete.
- `python tools/posthoc_position_contrast.py`: reproduce the separate exploratory
  three-position contrast; already called by `reproduce.py --statistics`.
- `python tools/verify_paper_outputs.py`: verify all 37 included manuscript
  artifacts after rebuilding; use `--strict-render` for exact PNG comparison.

No command except `rerun.py --execute` calls a model.
