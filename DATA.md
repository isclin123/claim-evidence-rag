# Data and reproduction contract

The fourteen-method preliminary inputs and responses are under `preliminary/`.
See [`preliminary/README.md`](preliminary/README.md) for its data schema,
construction boundary and Excel reproduction command. The root-level files
described below belong to the three-method follow-up batches.

The package starts with the **actual frozen inputs used in the paper**. Full
Wikipedia/MS MARCO corpora are not needed for the fixed-context experiments.
`data/datasets.json` records the manuscript's corpus-size metadata; it is not
a recount of a newly downloaded corpus. The 300 included question identifiers
and their processed texts are in `data/inputs.jsonl.gz`.

Each input row contains the dataset and question ID, question, labeled correct
answer, target answer, five ordered base passages, both four-document benign
libraries, slot provenance, and documents for exactly three constructions.
The original labels and the 14 fallback slots are retained. NQ, HotpotQA and
MS MARCO each contribute 100 questions. Do not replace the frozen texts when
checking the published results.

`code/constructions.py` rebuilds the 3,300 attack documents byte-for-byte.
`code/common.py` builds all five-document contexts and exact local requests.
`data/protocol.json` contains the local answer-generation prompts and settings.
Appendix C.3's preparation specification is in `data/benign_preparation.json`;
`code/benign_preparation.py` preserves its pure prompt, seed and validation
functions. Those functions make no model calls. Fresh stochastic preparation
and corpus retrieval are outside the fixed-input runner.

`results/responses/*.jsonl.gz` holds individual frozen responses rather than
only scores. Each local record includes its batch-specific condition, model,
question, seed, response and recorded hashes. `data/schedules.jsonl.gz` stores
the retained trial order for each batch/model. The names `natural` and
`answer_bearing` correspond to the manuscript's irrelevant and answer-bearing
contexts. Legacy field `k`/`K` in count files denotes the paper's poison count
**m**, not context depth; the context depth is always five.

`data/commercial_sample.json` contains the deterministic 60-question subset.
`data/commercial_prompts.jsonl.gz` contains all 600 prompts shared across the
three services. Commercial records retain `status`, `final_answer`, timestamps,
and interface metadata. Two blocked trials have no valid response; they remain
missing. The verifier checks sampling and all 1,800 scheduled keys.

`results/expected_*.json` and figure CSVs are numerical reference targets.
Offline reproduction independently rescores all responses before checking
these targets. `results/statistical_families.json` additionally contains
anonymous scalar calibration inputs required by the manuscript's original
multiplicity families. Their scope and limitations are in `REPRODUCIBILITY.md`.

Tables retain the manuscript's printed rounding: registered local inference
uses decimal half-up formatting; descriptive tables and exploratory intervals
retain their original formatting. Unrounded results remain available in JSON
and CSV. Formatting never alters the scorer or inferential values.

Only package-local inputs are read by the reviewer commands. Third-party
dataset and model terms continue to apply; no new license to those materials
is granted here.
