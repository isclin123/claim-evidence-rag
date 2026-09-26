"""Regenerate the Section 5.2 grouped LaTeX table from local source CSVs.

Run: python make_table.py
Requires only Python's standard library; no plotting or model calls.
"""

import csv
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORDER = [("C06", "Claim--Evidence"), ("C42", "CorruptRAG-AS"), ("C00", "PoisonedRAG")]
SETTINGS = ("irrelevant", "answer_bearing")
DATASETS = ("nq", "hotpotqa", "msmarco")
CAPTION = r"""ASR (\%) of Claim--Evidence, PoisonedRAG, and CorruptRAG-AS,
with one poisoned document placed first among five supplied documents.
Each dataset-specific entry aggregates 2,400 responses over 100 questions,
eight models, and three seeds. Overall averages the three datasets
(7,200 responses), using the aggregation described in
Section~\ref{sec:experimental_setup}.
Bold indicates the highest ASR in each column."""


def main():
    source = HERE / "data/asr.csv"
    with source.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    cells = {(row["setting"], row["condition"]): row for row in rows}
    if len(cells) != len(rows):
        raise ValueError("Duplicate setting/condition in source CSV")
    dataset_source = HERE / "data/by_dataset.csv"
    with dataset_source.open(encoding="utf-8", newline="") as handle:
        dataset_rows = list(csv.DictReader(handle))
    dataset_cells = {(r["setting"], r["condition"], r["dataset"]): r
                     for r in dataset_rows}
    expected_keys = {(s, c, d) for s in SETTINGS for c, _ in ORDER for d in DATASETS}
    if len(dataset_rows) != 18 or set(dataset_cells) != expected_keys:
        raise ValueError("Expected exactly 18 unique dataset cells")
    values = {}
    for condition, name in ORDER:
        values[name] = []
        for setting in SETTINGS:
            row = cells[(setting, condition)]
            if int(row["responses"]) != 7200:
                raise ValueError("Caption requires 7,200 responses per cell")
            overall = Decimal(row["asr_pp"])
            dataset_values = []
            for dataset in DATASETS:
                record = dataset_cells[(setting, condition, dataset)]
                if tuple(int(record[k]) for k in ("questions", "models", "seeds", "responses")) != (100, 8, 3, 2400):
                    raise ValueError("Dataset counts do not match caption")
                dataset_values.append(Decimal(record["asr_pp"]))
            if abs(sum(dataset_values) / 3 - overall) > Decimal("0.00001"):
                raise ValueError("Dataset means do not match original overall ASR")
            values[name].extend(dataset_values + [overall])
    maxima = [max(row[col] for row in values.values()) for col in range(8)]
    def display(value):
        return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    body = []
    for _, name in ORDER:
        formatted = [
            r"\textbf{" + display(value) + "}" if value == maxima[col]
            else display(value)
            for col, value in enumerate(values[name])
        ]
        body.append(name + " & " + " & ".join(formatted) + r" \\")
    tex = r"""% Requires \usepackage{booktabs} in the preamble.
\begin{table}[htbp]
  \centering
  \caption{""" + CAPTION + r"""}
  \label{tab:method_asr}
  \small
  \setlength{\tabcolsep}{4pt}
  \begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}l*{8}{c}@{}}
    \toprule
    & \multicolumn{4}{c}{Irrelevant benign context}
    & \multicolumn{4}{c}{Answer-bearing benign context} \\
    \cmidrule(lr){2-5} \cmidrule(lr){6-9}
    Method & NQ & HotpotQA & MS MARCO & Overall
           & NQ & HotpotQA & MS MARCO & Overall \\
    \midrule
""" + "\n".join("    " + row for row in body) + r"""
    \bottomrule
  \end{tabular*}
\end{table}
"""
    target = HERE / "table_main.tex"
    target.write_text(tex, encoding="utf-8")
    checks = {
        "asset": "method_asr", "kind": "table",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_csv": "data/asr.csv",
        "source_csv_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_rows_retained": len(rows), "displayed_cells": 24,
        "dataset_source_csv": "data/by_dataset.csv",
        "dataset_source_csv_sha256": hashlib.sha256(dataset_source.read_bytes()).hexdigest(),
        "dataset_rows": len(dataset_rows),
        "construction_order": [name.replace("--", "-") for _, name in ORDER],
        "settings": list(SETTINGS),
        "columns_per_setting": list(DATASETS) + ["overall"],
        "values_shown_pp": {name.replace("--", "-"): [display(x) for x in row]
                            for name, row in values.items()},
        "responses_per_dataset_cell": 2400,
        "responses_per_overall_cell": 7200,
        "precision": "2 decimals; ROUND_HALF_UP; overall from unrounded source",
        "bold_rule": "largest descriptive mean in each column; no significance claim",
        "table_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    }
    (HERE / "table_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Wrote table_main.tex and table_checks.json")


if __name__ == "__main__":
    main()
