"""Section 5.3 main-text table: the three commercial services at k=1.

One row per service, so the section's whole result fits one float: what was
queried, how often the target string appeared under each construction, and the
paired difference with its interval.

The difference column is labelled "paired" on purpose. Claude's PoisonedRAG cell
has 59 valid responses after one platform block, so subtracting the two printed
percentages gives 25.7 while the paired difference over the 59 complete pairs is
25.4. The header word plus the caption sentence about the block explain that gap
without spending a line of prose on 0.26 pp.

Reads only data/k1.csv. No inference here: the interval and the adjusted p are
copied from the frozen delivery.

python make_table.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import figstyle as fs  # noqa: E402

OUT = "table_main.tex"
LABEL = "tab:commercial_k1"

BS = chr(92)  # backslash: keep LaTeX out of Python escape handling


def load() -> list:
    with (HERE / "data" / "k1.csv").open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def num(value: float) -> str:
    """Math mode for a negative bound so it prints a minus, not a hyphen."""
    return f"${value:.1f}$" if value < 0 else f"{value:.1f}"


def cell(hits: str, n: str, asr: str) -> str:
    return f"{hits}/{n} ({float(asr):.1f})"


def build(rows: list) -> tuple:
    lines, printed = [], {}
    for row in rows:
        diff = float(row["difference_pp"])
        low, high = float(row["ci_low_pp"]), float(row["ci_high_pp"])
        lines.append(
            f"{row['service']} & {row['interface']} & "
            f"{cell(row['c00_hits'], row['c00_n'], row['c00_asr_pp'])} & "
            f"{cell(row['c06_hits'], row['c06_n'], row['c06_asr_pp'])} & "
            f"${diff:+.1f}$pp [{num(low)}, {num(high)}] {BS}{BS}"
        )
        printed[row["service"]] = {
            "interface": row["interface"],
            fs.METHOD_NAMES["C00"]: {"hits": int(row["c00_hits"]),
                                     "n": int(row["c00_n"]),
                                     "asr_pp": round(float(row["c00_asr_pp"]), 1)},
            fs.METHOD_NAMES["C06"]: {"hits": int(row["c06_hits"]),
                                     "n": int(row["c06_n"]),
                                     "asr_pp": round(float(row["c06_asr_pp"]), 1)},
            "paired": {"pairs": int(row["pair_n"]), "difference_pp": round(diff, 1),
                       "ci_pp": [round(low, 1), round(high, 1)],
                       "holm25_p": float(row["p_holm25_preserved"]),
                       "passes_holm25": row["significant_holm25"] == "True"},
        }
    return lines, printed


def render(lines: list) -> str:
    # One sentence: what the table is. Conditions, denominators, the blocked
    # trial and the interval definition are carried by the Section 5.3 prose.
    caption = (
        "Attack success rate on three black-box commercial services at one "
        "poisoned document placed first, in the answer-bearing benign context."
    )
    head = [
        BS + "begin{table}[t]",
        BS + "centering",
        BS + "caption{" + caption + "}",
        BS + "label{" + LABEL + "}",
        BS + "small" + BS + "setlength{" + BS + "tabcolsep}{3.5pt}",
        BS + "begin{tabular}{@{}llccc@{}}",
        BS + "toprule",
        "Service & Interface & PoisonedRAG & Claim--Evidence & $"
        + BS + "Delta$ paired [95" + BS + "% CI] " + BS + BS,
        BS + "midrule",
    ]
    tail = [BS + "bottomrule", BS + "end{tabular}", BS + "end{table}", ""]
    return "\n".join(head + lines + tail)


def main() -> None:
    rows = load()
    lines, printed = build(rows)
    path = HERE / OUT
    path.write_text(render(lines), encoding="utf-8")
    (HERE / "table_checks.json").write_text(json.dumps({
        "table": OUT,
        "label": LABEL,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "source_csv": "data/k1.csv",
        "source_csv_sha256": fs.sha256_of(HERE / "data" / "k1.csv"),
        "condition": ("k=1, the poisoned document placed first, answer-bearing benign "
                      "context, 60 questions, one response per condition"),
        "values_printed": printed,
        "rounding": ("1 decimal, with exact hits and denominators beside it; the "
                     "eleven-row appendix table prints 2 decimals to match the frozen "
                     "delivery it is cross-checked against"),
        "unit_in_cell": ("pp is printed in each difference cell, matching the user's "
                         "Overleaf edit of 2026-09-21, so the repository file and the "
                         "compiled paper do not drift. The interval shares that unit and "
                         "does not repeat it."),
        "difference_column": ("paired, over complete pairs. Claude prints 59.3 and 85.0 "
                              "but its paired difference is 25.4, not 25.7, because the "
                              "blocked question leaves 59 complete pairs. The header says "
                              "paired; the prose says why, since the caption is one "
                              "sentence."),
        "caption_is_one_sentence": ("The reader needs six things that are no longer in the "
                                    "caption: the 60-question subset and one response per "
                                    "condition, the access dates, that cells are hits over "
                                    "valid responses, the blocked trial and its 59 "
                                    "denominator, what the interval is, and the pointer to "
                                    "the appendix. The Section 5.3 prose must carry all "
                                    "six."),
        "intervals_and_p_are_copied_not_recomputed": True,
        "not_in_this_table": ("pooled totals across k (they reuse the same 60 questions "
                              "five times and their /300 denominator collides with the "
                              "300-question panels elsewhere in the paper), per-dataset "
                              "rows, the k ladder, and the open-weight comparison"),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT)
    for service, payload in printed.items():
        print(" ", service, payload["paired"])


if __name__ == "__main__":
    main()
