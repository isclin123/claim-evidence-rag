# Preliminary: fourteen-method single-poison comparison

This release provides **14 methods × 300 questions × 8 local models × 3 response
seeds = 100,800 responses**. Every request has one poison in the first position
and the same four frozen answer-bearing benign passages. NQ, HotpotQA and
MS MARCO each contribute 100 questions. Seeds are 101, 202 and 303.

Download the [Excel results](results/preliminary_results.xlsx). The workbook has
two worksheets: a fourteen-method summary and 336 model–dataset result rows.
ASR cells are numeric percentages. Differences from PoisonedRAG are percentage
points and use the matching model and dataset. Results are descriptive and
apply to the released panel. No significance test is attached to its ranking.

## Methods

| ID | Construction |
|---|---|
| C00 | PoisonedRAG |
| C03 | instruction-aware |
| C04 | query-first |
| C05 | QA-fact |
| C06 | Claim-Evidence |
| C32 | M_full |
| C35 | L2_AB |
| C36 | L3_ABC |
| C37 | L4_ABC_just |
| C38 | PC_naturalized_M |
| C39 | PC_evidence_M |
| C40 | PC_scoped_reason_M |
| C41 | PC_repeat3_M |
| C42 | CorruptRAG-AS |

## Offline reproduction

From the repository root, with Python 3.11–3.13:

```bash
python preliminary/tools/verify.py
python preliminary/tools/reproduce.py
python preliminary/tools/test_runner.py
```

These commands need only the Python standard library and make zero model or
network calls. The verifier rebuilds all 4,200 poison texts, checks the complete
response matrix, exact prompts, response hashes and model digests, and rescores
each response with the official normalized target-substring scorer. The
reproducer checks all 504 aggregate rows against the frozen reference and writes
`output/preliminary/preliminary_results.xlsx` plus machine-readable `asr.json`.
Excel formulas, styles, filters and group borders are retained when the
recomputed counts and formula caches are written into the supplied workbook.

## Rerun on local Ollama

```bash
# Offline request inspection; does not connect to Ollama.
python preliminary/tools/rerun.py --model all --limit 3

# Generate new responses for the full panel.
python preliminary/tools/rerun.py --model all --execute

# Score the newly generated complete panel and write its Excel workbook.
python preliminary/tools/reproduce.py --reruns
```

The runner requires the exact tags and digests in `data/models.json` and uses
`data/protocol.json`: temperature 0.1, 80 output tokens, 4096 context tokens and
thinking disabled. The recorded runtime was Ollama 0.30.6. A single model can be
selected by its key, for example `--model qwen35_9b`. Existing responses resume
only after their configuration, keys and hashes are checked. Files are written
under `output/preliminary/reruns/`. Incomplete matrices fail scoring explicitly.
Identical weights and seeds do not guarantee identical outputs across hardware
or runtime versions.

## Files and input boundary

- `code/constructions.py`: the fourteen deterministic construction functions.
- `code/common.py`: exact prompt and request assembly.
- `code/evaluation.py`, `code/official_scorer.py`: completeness checks and scoring.
- `data/inputs.jsonl.gz`: all 300 questions, four benign passages per question,
  fourteen poisons and the frozen construction components.
- `data/schedule.json`: recorded order of the released requests, 12,600 per model.
- `results/responses/`: response text, model/seed metadata, timestamps and hashes.
- `results/expected_asr.json`: 504 aggregate reference rows, including marginal
  totals. Only the 336 model–dataset rows are mutually disjoint observations.
- `results/preliminary_results.xlsx`: the readable result tables.

Construction begins from frozen base passages, structured clause slots and
extracted evidence/rebuttal sentences. It preserves the recorded padding and
slot-selection behavior exactly. Stochastic input generation and the earlier
lexical extraction procedure are outside this fixed-input reproduction.
The supplied inputs are the actual texts used for the responses. This comparison
does not run poisoned retrieval or measure end-to-end retrieval exposure.

Each method has 7,200 responses. Each model–dataset–method row has 300 responses
(100 questions × 3 seeds), rather than 300 independent questions. The balanced
panel makes pooled ASR equal to the equally weighted model/dataset/seed mean.
Target-string containment is the metric; it does not establish semantic adoption.
The other experiments at the repository root retain their own independent
batches and three-method follow-up scope.
