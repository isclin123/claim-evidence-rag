"""Section 5.4.1 table: the poison-count ladder the figure draws, as numbers,
with the paired contrast behind it. Generated from the same data/ as the
figure so the two can never drift apart.

Only the two manuscript constructions are included.

ASR and the difference are printed to one decimal, the precision the figure
labels use, because that is the only precision at which a reader subtracting
the two ASR columns lands on the difference column. The script checks that
before it writes; at two decimals three of the five rows would be off by 0.01.

Rounding is half-up on the exact decimal value, not Python's half-even on the
float, so the k = 4 lower bound prints as 8.63 the way the registered interval
was already printed and not as 8.62.

python make_table.py
"""

from __future__ import annotations

import csv
import hashlib
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "table_ladder.tex"

METHOD = "Claim-Evidence"
BASELINE = "PoisonedRAG"
ASR_DECIMALS = 1
CI_DECIMALS = 2


def quantise(text: str, decimals: int) -> Decimal:
    """Round the value as written in the CSV, half away from zero."""
    return Decimal(text).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def fmt_p(value: float) -> str:
    return "$<0.001$" if value < 0.001 else f"{value:.3f}"


# A title plus the minimum that keeps the columns readable: what was held fixed,
# how many responses, and which interval and test the last two columns are. The
# reading of the numbers belongs in the body text, not here. The composition of
# the Holm family and the batch discipline are recorded in
# table_checks.json, and the figure caption beside it carries the batch note.
CAPTION = (
    r"\caption{Attack success rate at each poisoned-document count, with the paired "
    r"Claim-Evidence minus PoisonedRAG difference. Answer-bearing benign context, "
    r"7{,}200 responses per ASR cell over 300 question clusters. Intervals are 95\% "
    r"pointwise cluster bootstraps and $p_H$ is Holm-adjusted within the registered "
    r"family; Table~\ref{tab:method_ci} gives the full inference.}"
)


def main() -> None:
    with (HERE / "data" / "ladder.csv").open(encoding="utf-8") as handle:
        ladder = {(row["construction"], int(row["k"])): row["asr_pp"]
                  for row in csv.DictReader(handle)}
    with (HERE / "data" / "contrasts.csv").open(encoding="utf-8") as handle:
        contrasts = list(csv.DictReader(handle))

    lines = [
        r"\begin{table}[t]\centering",
        CAPTION,
        r"\label{tab:count_ladder}",
        r"\small",
        r"\begin{tabular}{@{}lrrrrr@{}}",
        r"\toprule",
        r" & \multicolumn{2}{c}{ASR (\%)} & "
        r"\multicolumn{3}{c}{Claim-Evidence $-$ PoisonedRAG (pp)} \\",
        r"\cmidrule(lr){2-3}\cmidrule(l){4-6}",
        r"$k$ & PoisonedRAG & Claim-Evidence & Difference & 95\% CI & $p_H$ \\",
        r"\midrule",
    ]
    reconciled = []
    for row in contrasts:
        k = int(row["k"])
        if row["construction"] != METHOD or row["baseline"] != BASELINE:
            raise SystemExit("unexpected contrast in data/contrasts.csv: " + str(row))
        baseline = quantise(ladder[(BASELINE, k)], ASR_DECIMALS)
        method = quantise(ladder[(METHOD, k)], ASR_DECIMALS)
        effect = quantise(row["effect_pp"], ASR_DECIMALS)
        # A reader subtracting the two printed ASR columns has to land on the
        # printed difference. If it ever stops holding, fix the precision, not
        # the numbers.
        if method - baseline != effect:
            raise SystemExit(
                "k=%d: %s - %s does not print as %+s" % (k, method, baseline, effect))
        low = quantise(row["pw_low"], CI_DECIMALS)
        high = quantise(row["pw_high"], CI_DECIMALS)
        reconciled.append({"k": k, "poisonedrag_pp": str(baseline),
                           "claim_evidence_pp": str(method),
                           "difference_pp": f"{effect:+}",
                           "ci_95_pp": [str(low), str(high)]})
        lines.append(
            f"{k} & {baseline} & {method} & ${effect:+}$ & $[{low}, {high}]$ & "
            f"{fmt_p(float(row['holm_p']))} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    (HERE / "table_checks.json").write_text(json.dumps({
        "table": OUT.name,
        "label": "tab:count_ladder",
        "intended_location": "Section 5.4.1, beside the figure",
        "rows": len(contrasts),
        "source_csv": ["data/ladder.csv", "data/contrasts.csv"],
        "source_csv_sha256": {
            name: hashlib.sha256((HERE / "data" / name).read_bytes()).hexdigest()
            for name in ("ladder.csv", "contrasts.csv")
        },
        "tex_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
        "constructions_printed": [BASELINE, METHOD],
        "constructions_in_data_not_printed": [],
        "contrasts_printed": ["Claim-Evidence - PoisonedRAG"],
        "auxiliary_comparisons_in_original_family": 5,
        "holm_family": contrasts[0]["family"],
        "holm_family_items": int(contrasts[0]["family_items"]),
        "rounding": (
            "Half-up on the exact decimal value. ASR and the difference at 1 decimal, the "
            "precision of the figure labels, so that the printed difference equals the "
            "difference of the two printed ASR columns at every count; checked in "
            "make_table.py. At 2 decimals k = 1, 4 and 5 would be off by 0.01. Intervals "
            "at 2 decimals, as registered; the k = 4 lower bound is exactly 8.625 and "
            "prints as 8.63."),
        "interval": (
            "95% pointwise cluster bootstrap, 10,000 resamples; the family-simultaneous "
            "max-T band is in data/contrasts.csv and is deliberately not printed"),
        "p_values": (
            "Holm-adjusted sign-flip permutation p over the ten items of D4-method. "
            "k = 1..4 sit on the permutation floor 1/100001, so their <0.001 is a floor, "
            "not a point estimate; only k = 5 has a resolved p. Recomputed from the "
            "72,000 retained responses plus frozen auxiliary calibration by tools/reproduce.py and "
            "identical to the frozen family; see "
            "output/inference.json."),
        "reconciled_values_pp": reconciled,
        "requires": "booktabs",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT.name, "with", len(contrasts), "rows")


if __name__ == "__main__":
    main()
