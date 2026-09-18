# Claim-Evidence RAG: Reproducibility Staging Package

This is an initial **local organization package**, prepared for review and editing. It has not been uploaded, anonymized for submission, or cleared for redistribution. Original experiment directories are unchanged.

## Complete figure library

Figure labels have subsequently been shortened and unified; see [Method-name changes and model-group legend](METHOD_NAMES.md). This label/layout update preserves numerical results and the short filenames, but intentionally changes the affected image bytes. Its current audit is `provenance/method_label_update.json`; the earlier filename-only audit remains historical.

All current figure files and figure-topic folders now use short English names. Start with [Short-name and caption lookup](FIGURE_NAMES.md). Matching PDF, SVG and PNG exports share one filename stem. Existing image bytes are unchanged; no figures were redrawn in this rename.

Three older image paths were already absent before renaming. They are explicitly recorded in `provenance/figure_rename_manifest.json`, not silently restored. The current collection contains 640 image files. Historical counts below describe the earlier figure-cleanup delivery.

The figure collection now includes all unsealed standalone scientific figures found in the three experimental stages, their report versions, paper assets, and figure-specific previews, not only selected paper candidates.

- [Visual gallery](figure_gallery.html): browse the reviewed figures and 133 full-width publication panels.
- [Complete figure index](FIGURE_COLLECTION_INDEX.md): descriptive names and links, grouped by experiment.
- Publication-ready individual panels live under each experiment's `figures/panels/`, in PDF, editable SVG and 600-dpi PNG. Preserve their 5.5-inch width when inserting them; final manuscript-scale checking is still required. Collections and previews are under `figures/archive/`.
- All prior 244 image paths remain covered. Internal display codes have been removed, crowded labels corrected, and dense multi-panel layouts split into readable pages. Old multi-panel PNG paths are browsing overviews, not manuscript-ready montages.
- All 1,017 eligible source-image entries have verified derived destinations. Original source hashes and current destination hashes are distinguished in `provenance/complete_figure_source_manifest.json`; edited destinations are no longer byte-identical copies. Unmodified original artwork is backed up outside the release folder.
- See [Publication figure audit](PUBLICATION_FIGURE_REVIEW.md) for checks and limits. All experimental results, confidence intervals, configurations and scientific source data are unchanged. Sealed experiments and unrelated earlier stages remain excluded. Two report-page previews were converted to standalone graphics while retaining their numeric content.

The existing answer-informed experiment folder is currently named `answer_informed_defended_benign_context_evaluation`; this collection preserves that name. Older code/configuration references to its former name have not been migrated by this figure-only task. Figure coverage and hashes were verified; the full response workflow has not been revalidated after that folder rename.

## Organization

```text
claim-evidence-rag/
  natural_benign_context_evaluation/
  answer_informed_defended_benign_context_evaluation/
  poison_position_sensitivity/
  shared_dependencies/
  tools/
  provenance/
  README.md
```

Each experiment has `code`, `figures`, `configs`, `data`, `results`, and `docs`. Commercial models belong to the answer-informed evaluation. Shared question/document libraries and historical construction, scoring and plotting dependencies have their own folder.

All packaged file and directory names use English ASCII characters. User-facing arm and construction names are descriptive. Old identifiers remain only where required by byte-preserved historical source code, frozen statistical/figure data, and provenance. They are not blindly rewritten because doing so could change scientific meaning or break an audit trail.

## Tested offline workflow

Use Python 3.10 or newer. The following commands require only the standard library, do not access the internet, and do not call a model:

```bash
python tools/verify_package.py
python tools/reproduce_recorded_results.py
```

The first command checks file hashes, ASCII paths, response-text hashes, exact prompt hashes, coverage and missingness. The second recomputes target-substring hits from the preserved answers and writes per-model/per-dataset descriptive ASR tables to each experiment's `results/recomputed` folder. It does not pool batches or reinterpret missing outputs. The prompt records contain the exact text used, ready for a future independent runner. They are research inputs, not instructions to the package verifier.

## What is and is not reproducible yet

- Included: 951,300 local responses and 1,800 commercial trial slots (1,798 valid answers), frozen prompts, the 300-question document library, model/configuration extracts, frozen statistics, accepted figure assets and source-code references.
- Offline answer scoring and artifact integrity are tested in this package. Read `provenance/build_validation.json` and `provenance/offline_verification.json`.
- Historical code in `reference_sources` is retained byte-for-byte with renamed files. Imports and paths inside it still assume the original workspace. It is NOT a set of portable entrypoints. Do not execute these source snapshots directly.
- Full model generation, data retrieval, poison generation, statistical bootstrap/permutation reruns and the historical figure suite are **not yet wired into this layout**. Dependencies/model downloads are not installed automatically.
- Historical inferential results were copied, not re-estimated. Original internal identifiers remain in frozen tables and provenance, not on reviewed figures. The [three-method poison-count overview](answer_informed_defended_benign_context_evaluation/figures/three_method_count/three_method_count.md) has a plotting script and optional dependencies in `requirements-figures.txt`; its 15 points were checked against the frozen and independently scored results. The historical plotting-suite snapshots do not automatically reproduce the new publication styling; see the figure audit for the workspace rebuild boundary.
- Initial checks passed for 54,300 frozen question/condition prompts, all recorded response slots, and 1,893 descriptive values against the frozen results. These checks do not substitute for an independent full experiment rerun.
- Commercial products can change; rerunning them cannot promise identical outputs. Two platform-blocked outputs are missing, not zero-ASR outcomes.
- Unused/sealed follow-up experiments, private authorization records, conversation exports, browser session evidence, model weights, full corpora and credentials are not intentionally included. Source-code snapshots and provenance still need a final identity/secret review.

## Editing and publication

Start with the three experiment READMEs. `provenance/source_code_name_mapping.json` links new names to original sources; `provenance/source_manifest.json` records hashes. `provenance/package_manifest.json` checks the staged files. After intentional edits, review the changes and run `python tools/update_package_manifest.py` before using the integrity check; never change frozen scientific text just to make a check pass.

See [Publication checklist](PUBLICATION_CHECKLIST.md) and [Third-party notices](THIRD_PARTY_NOTICES.md). A root license is deliberately not asserted: code ownership and data redistribution permissions must be checked first. This staging folder is not an anonymous submission artifact yet.

The limited [publication preflight](provenance/publication_preflight.json) found no non-English paths and no matches to its limited credential patterns. Five historical reference scripts still contain local home-directory paths. Binary metadata, complete credential detection and legal permissions remain unreviewed.
