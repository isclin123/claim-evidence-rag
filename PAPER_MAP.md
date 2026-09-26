# Manuscript-to-package map

Reference: `ICLR_2027_Rag_Poisoning (15).pdf`, 34 pages. The manuscript SHA-256 and machine-readable inventory are in `provenance/paper_items.json`.

Only the three manuscript constructions, NQ/HotpotQA/MS MARCO, the five local batches and commercial transfer are included. Table 1 and the conceptual Figure 2 are excluded by author instruction. Figure 3 is an editable illustrative transcription.

| Paper item | Package file |
|---|---|
| Table 2 | `paper_assets/benign_coverage/table_benign_coverage.tex` |
| Table 3 | `paper_assets/method_asr/table_main.tex` |
| Table 4 | `paper_assets/commercial_m1/table_main.tex` |
| Table 5 | `paper_assets/count_ladder/table_ladder.tex` |
| Table 6 | `paper_assets/appendix/tables/construction_inputs.tex` |
| Table 7 | `paper_assets/appendix/tables/poison_lengths.tex` |
| Table 8 | `paper_assets/appendix/tables/benign_coverage.tex` |
| Table 9 | `paper_assets/appendix/tables/benign_lengths.tex` |
| Table 10 | `paper_assets/appendix/tables/fallback_queries.tex` |
| Table 11 | `paper_assets/appendix/tables/models.tex` |
| Table 12 | `paper_assets/appendix/tables/generation_settings.tex` |
| Table 13 | `paper_assets/appendix/tables/experiment_coverage.tex` |
| Table 14 | `paper_assets/appendix/tables/method_inference.tex` |
| Table 15 | `paper_assets/appendix/tables/count_inference.tex` |
| Table 16 | `paper_assets/appendix/tables/position_inference.tex` |
| Table 17 | `paper_assets/appendix/tables/main_by_model.tex` |
| Table 18 | `paper_assets/appendix/tables/count_by_model.tex` |
| Table 19 | `paper_assets/appendix/tables/count_by_dataset.tex` |
| Table 20 | `paper_assets/appendix/tables/position_by_model.tex` |
| Table 21 | `paper_assets/appendix/tables/all_orderings_1.tex` |
| Table 22 | `paper_assets/appendix/tables/all_orderings_2.tex` |
| Table 23 | `paper_assets/appendix/tables/commercial_protocol.tex` |
| Table 24 | `paper_assets/appendix/tables/commercial_counts.tex` |
| Table 25 | `paper_assets/appendix/tables/commercial_inference.tex` |
| Table 26 | `paper_assets/appendix/tables/commercial_bounds.tex` |
| Figure 1 | `paper_assets/defense_drop/defense_drop.pdf` |
| Figure 3 | `paper_assets/construction_example/example.tex` |
| Figure 4 | `paper_assets/count_ladder/count_ladder.pdf` |
| Figure 5 | `paper_assets/position_effect/position_effect.pdf` |
| Figure 6 | `paper_assets/appendix/figures/local_model_heterogeneity.pdf` |
| Figure 7 | `paper_assets/appendix/figures/local_count_heterogeneity.pdf` |
| Figure 8 | `paper_assets/appendix/figures/local_arrangements_m1_m4.pdf` |
| Figure 9 | `paper_assets/appendix/figures/local_arrangements_m2.pdf` |
| Figure 10 | `paper_assets/appendix/figures/local_arrangements_m3.pdf` |
| Figure 11 | `paper_assets/appendix/figures/commercial_ladder.pdf` |
| Figure 12 | `paper_assets/appendix/figures/commercial_paired_intervals.pdf` |
| Figure 13 | `paper_assets/appendix/figures/commercial_dataset_ladders.pdf` |

Appendix A/C exact templates, including the benign-generation prompt, are in `paper_assets/appendix/templates/`; full model identities are in `paper_assets/appendix/model_identities.csv`.

Run `python tools/reproduce.py --statistics --figures` to rescore responses, verify numerical inputs, and regenerate the artifacts under `output/paper_assets/`. The archive contains 25 included tables, 11 measured-result figures and one illustrative figure. LaTeX snippets retain paper cross-reference labels; they are not a full manuscript project.
