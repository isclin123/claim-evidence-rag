# Paper assets

`../PAPER_MAP.md` maps every included item to the 34-page manuscript.
Only Tables 2-26 and Figures 1 and 3-13 are included. Table 1 and Figure 2
are excluded by author instruction. Figure 3 is illustrative.

Run `python tools/reproduce.py --statistics --figures` from the package root.
Generated copies are placed in `output/paper_assets/`. Exact frozen responses,
inputs and reference exports remain unchanged. CSV files used by multiple
items are shared; they are dependencies, not additional experiments.
