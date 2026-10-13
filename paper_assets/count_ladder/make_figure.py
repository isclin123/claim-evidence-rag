"""Poison-count figure for Section 5.4.1.

Answer-bearing benign context. The context always holds five documents: k of
them are poisoned and come first, the remaining 5 - k are benign, so k = 5
leaves no benign document at all.

(a) ASR of PoisonedRAG and Claim-Evidence at every count. Only these two are
    drawn: the j-th poisoned document of both is built from the j-th released
    adversarial passage, so the count is the single variable that changes.
(b) The same difference per model. Eight thin lines, one per open-weight model,
    deliberately unlabelled -- the panel is about the spread and where it
    closes, and the per-model values live in the appendix table. The thick line
    is their mean.

Reads only the aggregated CSVs in data/. No model calls, no inference, no
re-scoring.

python make_figure.py
"""

from __future__ import annotations

import csv
import sys
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import matplotlib.pyplot as plt  # noqa: E402

import figstyle as fs  # noqa: E402


STEM = "count_ladder"
LADDER_CSV = "ladder.csv"
GAP_CSV = "per_model_gap.csv"

COUNTS = [1, 2, 3, 4, 5]
# Drawn highest first so the legend order matches the curve order on the plot.
SHOWN = ["C06", "C00"]
MARKERS = {"C06": "o", "C00": "v"}
IN_DATA_NOT_SHOWN = []

SPAGHETTI = "#9EABBA"  # neutral grey: these lines carry models, not methods
MEAN_COLOR = fs.METHOD_COLORS["C06"]  # the mean is the Claim-Evidence margin

def r2(value: float) -> float:
    """Two decimals, half away from zero, so the record matches the frozen tables."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def load_ladder() -> dict:
    with (HERE / "data" / LADDER_CSV).open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    table = {}
    for row in rows:
        table.setdefault(row["condition"], {})[int(row["k"])] = float(row["asr_pp"])
    return table


def load_gaps() -> dict:
    with (HERE / "data" / GAP_CSV).open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    table = {}
    for row in rows:
        table.setdefault(row["model"], {})[int(row["k"])] = float(row["gap_pp"])
    return table


def draw_levels(ax, table: dict) -> dict:
    drawn = {}
    for condition in SHOWN:
        values = [table[condition][k] for k in COUNTS]
        drawn[fs.METHOD_NAMES[condition]] = {k: r2(v)
                                             for k, v in zip(COUNTS, values)}
        ax.plot(COUNTS, values, marker=MARKERS[condition],
                color=fs.METHOD_EDGES[condition],
                markerfacecolor=fs.METHOD_COLORS[condition],
                markeredgewidth=0.7, linewidth=1.5, markersize=4.6,
                label=fs.METHOD_NAMES[condition])

    # One value per point. The curves close to within 1.4 pp at k = 5, so when
    # the two points nearly touch the lower label moves beside its marker
    # instead of under it, where it would land on the other curve.
    for k in COUNTS:
        high, low = table["C06"][k], table["C00"][k]
        ax.text(k, high + 2.6, "%.1f" % high, ha="center", va="bottom",
                fontsize=7.6, color=fs.INK)
        if high - low < 8:
            ax.text(k - 0.12, low, "%.1f" % low, ha="right", va="center",
                    fontsize=7.6, color=fs.INK)
        else:
            ax.text(k, low - 3.0, "%.1f" % low, ha="center", va="top",
                    fontsize=7.6, color=fs.INK)

    ax.set_xticks(COUNTS)
    ax.set_xlim(0.65, 5.35)
    fs.asr_axis(ax)
    ax.set_xlabel("Poisoned documents $m$ (of five)")
    fs.short_title(ax, "(a) ASR, answer-bearing context")
    ax.legend(loc="upper left", frameon=False, handlelength=1.6,
              labelspacing=0.3, borderaxespad=0.2)
    return drawn


def label_slot(value: float, occupied: list, clearance: float = 2.4,
               limits: tuple = (-10, 50)) -> float:
    """Nearest height that clears the model lines, never far from its own point.

    Labels stay within five points of the marker they belong to; if the lines
    leave no gap that close, the label goes just above the marker and may cross
    a grey line, which is legible because those lines are light and thin.
    """
    for step in [2.6 + 0.3 * index for index in range(9)]:
        for candidate in (value + step, value - step):
            if not limits[0] + clearance < candidate < limits[1] - clearance:
                continue
            if all(abs(candidate - other) >= clearance for other in occupied):
                return candidate
    return value + 3.0


def draw_gaps(ax, gaps: dict) -> dict:
    models = list(gaps)
    for index, model in enumerate(models):
        values = [gaps[model][k] for k in COUNTS]
        ax.plot(COUNTS, values, color=SPAGHETTI, linewidth=0.85,
                solid_capstyle="round",
                label="Open-weight models" if index == 0 else None)

    mean = [sum(gaps[m][k] for m in models) / len(models) for k in COUNTS]
    ax.axhline(0, color=fs.MUTED, linewidth=0.7, linestyle=(0, (4, 3)))
    # The mean of this difference is the Claim-Evidence margin, so it carries
    # that method's colour; the model lines stay neutral grey.
    ax.plot(COUNTS, mean, marker="o", color=MEAN_COLOR, markerfacecolor="white",
            markeredgecolor=MEAN_COLOR, markeredgewidth=1.3, linewidth=2.3,
            markersize=4.8, zorder=4, label="Mean")

    # Every mean point is labelled, with no backing box, so each label is placed
    # in the nearest vertical gap that clears the model lines at that count.
    for k, value in zip(COUNTS, mean):
        occupied = [gaps[m][k] for m in models] + [value]
        ax.text(k, label_slot(value, occupied), "%+.1f" % value, ha="center",
                va="center", fontsize=7.6, color=fs.INK, zorder=5)

    ax.set_xticks(COUNTS)
    ax.set_xlim(0.65, 5.35)
    ax.set_ylim(-10, 50)
    ax.set_yticks(range(-10, 51, 10))
    ax.set_ylabel("Claim-Evidence $-$ PoisonedRAG (pp)")
    ax.set_xlabel("Poisoned documents $m$ (of five)")
    ax.grid(axis="y")
    ax.tick_params(length=3, width=0.65)
    fs.short_title(ax, "(b) Difference per model")
    ax.legend(loc="upper right", frameon=False, handlelength=1.6,
              labelspacing=0.3, borderaxespad=0.2)
    return {"mean_pp": {k: r2(v) for k, v in zip(COUNTS, mean)},
            "per_model_pp": {fs.MODEL_PRETTY[m]: {k: r2(gaps[m][k])
                                                  for k in COUNTS}
                             for m in models},
            "models_drawn": len(models)}


def main() -> None:
    fs.use_paper_style()
    table = load_ladder()
    gaps = load_gaps()
    fig, axes = plt.subplots(1, 2, figsize=(fs.FULL_WIDTH, 2.75))
    levels = draw_levels(axes[0], table)
    spread = draw_gaps(axes[1], gaps)
    fig.tight_layout(pad=0.4)
    fig.subplots_adjust(wspace=0.28)

    written = fs.save_figure(fig, HERE, STEM)
    fs.write_checks(HERE, {
        "figure": STEM,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "source_csv": ["data/" + LADDER_CSV, "data/" + GAP_CSV],
        "source_csv_sha256": {
            LADDER_CSV: fs.sha256_of(HERE / "data" / LADDER_CSV),
            GAP_CSV: fs.sha256_of(HERE / "data" / GAP_CSV),
        },
        "constructions_shown": [fs.METHOD_NAMES[c] for c in SHOWN],
        "constructions_in_data_not_shown": [fs.METHOD_NAMES[c]
                                            for c in IN_DATA_NOT_SHOWN],
        "colour_rule": ("panel (a) uses figstyle.METHOD_COLORS, the same colour "
                        "each construction has in every figure; panel (b) carries "
                        "models, not methods, so its lines are neutral grey and "
                        "the mean line carries the Claim-Evidence colour, because that is whose margin it is"),
        "panel_a_values_pp": levels,
        "panel_b_values_pp": spread,
        "held_fixed": ("answer-bearing benign context, poisoned documents first, "
                       "five documents in total, eight models, three seeds"),
        "axis": {
            "a": {"y": fs.ASR_LABEL, "range": [0, 100]},
            "b": {"y": "Claim-Evidence - PoisonedRAG (pp)", "range": [-10, 50], "zero_line": True},
            "x": "poisoned document count k, 1 to 5, shared by both panels",
        },
        "value_label_precision": ("1 decimal; panel (a) labels every point and panel "
                                  "(b) labels the mean at every count"),
        "model_labels": ("deliberately absent: the panel is about the spread and "
                         "where it closes; per-model values go to the appendix table"),
        "batch": "ladder batch PD-V4; its k = 1 readings differ from the "
                 "construction-comparison batch by 0.14 and 0.26 pp",
        "intervals": "none drawn; the registered paired contrasts belong in the appendix",
        **written,
    })
    print("wrote", ", ".join(sorted(written["files"])))
    if written["text_outside_canvas"]:
        print("WARNING text outside canvas:", written["text_outside_canvas"])


if __name__ == "__main__":
    main()
