# Reproducibility scope

The fourteen-method preliminary comparison is documented in
[`preliminary/README.md`](preliminary/README.md). Its 100,800 responses and Excel
tables form a separate batch. The batch definitions and statistical families
below refer to the three-method follow-up experiments.

## Frozen inputs and batches

The same 300 questions (100 each from NQ, HotpotQA and MS MARCO) are used
locally. Inputs include questions, labeled correct/target answers, five released
base passages, both four-document benign libraries and the three constructions.
All 3,300 method documents are reconstructed byte-for-byte by the verifier.
The answer-bearing library preserves the recorded clean-corpus fallback slots.

| Batch | Cells | Responses |
|---|---|---:|
| `natural` | 3 methods; one poison first; retrieved benign context | 21,600 |
| `answer_bearing` | 3 methods; one poison first; answer-bearing context | 21,600 |
| `count` | 2 methods × 5 counts; poisons first | 72,000 |
| `position` | 3 methods × positions 1, 3, 5 | 64,800 |
| `ordering` | Claim–Evidence × all 30 P/B patterns | 216,000 |
| Commercial | 3 services × 60 questions × 2 methods × 5 counts | 1,800 scheduled; 1,798 valid |

Each local cell has 300 questions × 8 models × seeds 101/202/303 = 7,200
responses. Batches are independent, never pooled. Orderings comprise
5 + 10 + 10 + 5 patterns for poison counts 1–4. Poison and benign internal
orders remain fixed. `data/schedules.jsonl.gz` records the actual trial order
of the included manuscript methods.

## Scoring and statistics

The official scorer stringifies, strips surrounding whitespace, removes one
terminal period when length exceeds one, and lowercases. A hit is normalized
target containment in normalized response; it is not semantic adoption.
The scoring logic and consistency vectors match the recorded implementation.

Local statistics average seeds within questions and weight models/datasets
equally. Query clusters stay together across conditions. Registered inference
uses 10,000 dataset-stratified bootstrap draws (seed 2026082601), 100,000
studentized sign flips (seed 2026082602), and the original Holm families.
The natural and answer-bearing method comparisons both report all eight
models. The package does not include natural-context inferential contrasts;
their descriptive ASRs and per-model/per-dataset results remain reproducible.
Every retained local inferential contrast uses all eight models. The count
batch's k=1 is distinct from the method-comparison batch. Exploratory
per-position method comparisons retain their separate three-test family and
original resampling procedure.

Reported inference uses the full registered comparison families, including
contrasts not tabulated in the paper. `results/statistical_families.json`
provides anonymous auxiliary p values and frozen family-simultaneous critical
values. The count family contains ten comparisons (five reported and five
auxiliary); the position family contains twelve (four reported and eight
auxiliary). The baseline-position and ordering families contain two and four
comparisons, respectively.

`tools/reproduce.py --statistics` independently recomputes every retained
contrast's estimate, pointwise CI, raw p and standard error from the retained
responses. Recomputed raw p values plus frozen anonymous auxiliary p values
reproduce the original Holm correction. Simultaneous intervals use the
corresponding full-family critical value. **Auxiliary p values and their
full-family critical values are supplied calibration inputs; they cannot be
re-estimated from the released response records.** Critical values are
recomputed for families whose complete comparison responses are included.

## Commercial replication

`data/commercial_sample.json` gives the deterministic sample rule and all 60
identifiers. `data/commercial_prompts.jsonl.gz` contains 600 exact prompts,
shared across services. `results/responses/commercial.jsonl.gz` contains final
answers, status, access times and interface/mode. Session URLs and unrelated
account/browser artifacts are excluded.

Commercial analysis uses seed 20260914 and 10,000 question-bootstrap draws
stratified by dataset, shared across all conditions. Paired effects use complete
pairs. Exact two-sided McNemar tests and Holm-15/Holm-25 are recomputed; ten
unperformed comparisons enter Holm-25 as p=1 placeholders. Blocked trials stay
missing. The archived interfaces did not expose local sampling controls.

Seven commercial records had later capture revisions. This package uses the
revisions whose record/answer hashes match the frozen manuscript analysis.

## Rebuild versus rerun

Offline reproduction checks the recorded experiment. `tools/rerun.py --execute`
generates new local responses from the same frozen inputs, checks model digests,
uses independent requests and writes to `output/reruns/`. Identical seeds and
weights do not guarantee identical outputs across runtime/hardware changes.

Fresh corpus retrieval and stochastic input-library generation are outside this
fixed-input package. Supplied passages are the actual experimental inputs, not
regenerated replacements. Dataset corpus sizes are metadata; full corpora are
not required for the packaged fixed-context experiment.

`provenance/files.json` hashes the distributable files.

Third-party data and model terms remain in effect; this package does not
grant a new license to them.
