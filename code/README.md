# Runnable code

All inputs resolve relative to the package; no original workspace is required.

- `common.py`: frozen inputs, batch/cell definitions, context/request assembly.
- `constructions.py`: the three manuscript methods and frozen normalization.
- `corruptrag.py`: original CorruptRAG-AS template used in the experiment.
- `official_scorer.py`: recorded scoring logic and consistency vectors.
- `statistics_core.py`: numerical functions extracted verbatim from the frozen analyzer.
- `benign_preparation.py`: pure preparation prompt, seed derivation and mechanical
  checks from Appendix C.3; this module makes no calls and writes no files.

Reviewer entry points are under `tools/`. Both method-comparison batches
start with the full eight-model panel and the three fixed constructions.
