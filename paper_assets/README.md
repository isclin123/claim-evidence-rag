# Paper assets

Reference copies of the paper's measured tables and figures, with their
source data and generators. The paper-to-file table is in the top-level
`README.md`. Table 2 (the 14-construction comparison) is produced separately
under `preliminary/`. Figure 4 is an illustrative example.

Run `python tools/reproduce.py --statistics --figures` from the package root.
Generated copies are placed in `output/paper_assets/`. Exact frozen responses,
inputs and reference exports remain unchanged. CSV files used by multiple
items are shared; they are dependencies, not additional experiments.
