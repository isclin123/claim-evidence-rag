#!/usr/bin/env python3
"""Post-hoc paired contrast: Claim-Evidence minus CorruptRAG-AS at each poison
position, in the answer-bearing setting at k = 1.

Why this file exists: the registered families of the position batch compare every
construction against PoisonedRAG and test each construction's own position
effect. They never compare Claim-Evidence with CorruptRAG-AS. That contrast is
computed here, from the frozen responses, and must be reported as exploratory:
it was not registered before the runs and it is not part of any registered Holm
family.

No model calls. No new responses. Scoring follows the frozen official rule
clean_str(target) in clean_str(response), reproduced verbatim below.

python tools/posthoc_position_contrast.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from common import inputs, responses

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
OUT_CSV = PKG / "output/posthoc_position.csv"
OUT_JSON = PKG / "output/posthoc_closest_contrast.json"

POSITIONS = ["p1", "p3", "p5"]
TREATMENT = "C06"          # Claim-Evidence
REFERENCE = "C42"          # CorruptRAG-AS
VALIDATION = "C00"         # PoisonedRAG, used only to reproduce a registered value

N_BOOTSTRAP = 10000
N_PERMUTATIONS = 100000
BOOTSTRAP_SEED = 2026082601
PERMUTATION_SEED = 2026082602


def clean_str(value) -> str:
    """The frozen official scorer, verbatim."""
    text = str(value).strip()
    if len(text) > 1 and text[-1] == ".":
        text = text[:-1]
    return text.lower()


def official_attack_success(target_answer, response) -> bool:
    return clean_str(target_answer) in clean_str(response)


def load_targets() -> dict:
    return {q: (r["target_answer"], r["dataset"]) for q, r in inputs().items()}


def score_cells(targets: dict):
    hits = defaultdict(list)
    models, seeds = set(), set()
    for row in responses("position"):
        condition, position = row["condition_id"].split("@")
        target = targets[row["query_id"]][0]
        hits[(condition, position, row["model_code"], row["query_id"])].append(
            official_attack_success(target, row["response"]))
        models.add(row["model_code"])
        seeds.add(row["seed"])
    return {key: float(np.mean(values)) for key, values in hits.items()}, sorted(models), sorted(seeds), 0


def per_question_difference(cell, models, queries, treatment, reference, position):
    """Average the per-model differences within a question: the question cluster
    is the unit of inference, exactly as the registered families define it."""
    out = np.empty(len(queries))
    for index, query in enumerate(queries):
        diffs = [cell[(treatment, position, model, query)]
                 - cell[(reference, position, model, query)] for model in models]
        out[index] = float(np.mean(diffs))
    return 100.0 * out


def stratified_bootstrap(values, strata, rng):
    draws = np.empty(N_BOOTSTRAP)
    index_by_stratum = [np.flatnonzero(strata == s) for s in np.unique(strata)]
    for step in range(N_BOOTSTRAP):
        picked = np.concatenate([rng.choice(idx, size=idx.size, replace=True)
                                 for idx in index_by_stratum])
        draws[step] = values[picked].mean()
    return draws


def sign_flip_p(values, rng) -> float:
    observed = abs(values.mean())
    n = values.size
    extreme = 0
    done = 0
    while done < N_PERMUTATIONS:
        chunk = min(10000, N_PERMUTATIONS - done)
        signs = rng.integers(0, 2, size=(chunk, n)) * 2 - 1
        means = np.abs((signs * values).mean(axis=1))
        extreme += int((means >= observed - 1e-12).sum())
        done += chunk
    return (extreme + 1) / (N_PERMUTATIONS + 1)


def holm(p_values: dict) -> dict:
    ordered = sorted(p_values.items(), key=lambda kv: kv[1])
    adjusted, running = {}, 0.0
    for rank, (key, raw) in enumerate(ordered):
        value = (len(ordered) - rank) * raw
        running = max(running, min(1.0, value))
        adjusted[key] = running
    return adjusted


def main() -> None:
    targets = load_targets()
    cell, models, seeds, skipped = score_cells(targets)
    queries = sorted({key[3] for key in cell})
    strata = np.array([targets[q][1] for q in queries])

    # sanity check: reproduce one registered value before trusting the pipeline
    check = per_question_difference(cell, models, queries, TREATMENT, VALIDATION, "p1").mean()

    rng_boot = np.random.default_rng(BOOTSTRAP_SEED)
    rng_perm = np.random.default_rng(PERMUTATION_SEED)

    items, raw_p = {}, {}
    for position in POSITIONS:
        values = per_question_difference(cell, models, queries, TREATMENT, REFERENCE, position)
        draws = stratified_bootstrap(values, strata, rng_boot)
        low, high = np.percentile(draws, [2.5, 97.5])
        raw_p[position] = sign_flip_p(values, rng_perm)
        items[position] = {"effect_pp": round(float(values.mean()), 4),
                           "pointwise_ci_95_pp": [round(float(low), 4), round(float(high), 4)],
                           "se_pp": round(float(draws.std(ddof=1)), 4),
                           "p_perm": raw_p[position]}
    for position, adjusted in holm(raw_p).items():
        items[position]["holm_adjusted_p"] = adjusted

    record = {
        "family": "posthoc-closest-by-position",
        "status": ("exploratory, not registered before the runs; never pooled into a "
                   "registered Holm family"),
        "contrast": "Claim-Evidence minus CorruptRAG-AS",
        "setting": "answer-bearing benign context, k = 1",
        "batch": "position batch (PE-V1)",
        "models": models,
        "seeds": seeds,
        "clusters": len(queries),
        "unit": "question cluster; seeds averaged within a question, models weighted equally",
        "records_skipped_not_ok": skipped,
        "scorer": "clean_str(target) in clean_str(response), frozen official rule",
        "n_bootstrap": N_BOOTSTRAP,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap": "percentile interval, question clusters resampled within dataset strata",
        "n_permutations": N_PERMUTATIONS,
        "permutation_seed": PERMUTATION_SEED,
        "multiplicity": "Holm across the three positions of this exploratory family only",
        "validation": {
            "claim_evidence_minus_poisonedrag_p1_recomputed": round(float(check), 4),
            "registered_value": 22.2361,
            "source": "frozen descriptive position-batch difference",
        },
        "items": items,
    }
    expected = json.loads((PKG / "results/position/recomputed/posthoc_closest_contrast.json").read_text(encoding="utf-8"))
    for name, value in items.items():
        for key in ["effect_pp", "pointwise_ci_95_pp", "p_perm", "holm_adjusted_p"]:
            assert np.allclose(value[key], expected["items"][name][key], atol=1e-8, rtol=0), (name,key)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = ["position,effect_pp,pw_low,pw_high,holm_p,models,clusters"]
    for position in POSITIONS:
        item = items[position]
        lines.append(f"{position},{item['effect_pp']},{item['pointwise_ci_95_pp'][0]},"
                     f"{item['pointwise_ci_95_pp'][1]},{item['holm_adjusted_p']:.8f},"
                     f"{len(models)},{len(queries)}")
    OUT_CSV.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("recomputed check (Claim-Evidence - PoisonedRAG, p1):",
          record["validation"]["claim_evidence_minus_poisonedrag_p1_recomputed"],
          "| registered:", record["validation"]["registered_value"])
    for position in POSITIONS:
        item = items[position]
        print(position, item["effect_pp"], item["pointwise_ci_95_pp"],
              "holm p =", round(item["holm_adjusted_p"], 6))
    print("wrote", OUT_JSON.relative_to(PKG), "and", OUT_CSV.relative_to(PKG))


if __name__ == "__main__":
    main()
