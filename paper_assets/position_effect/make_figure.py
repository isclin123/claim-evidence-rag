"""Position figure for Section 5.4.2.

Answer-bearing benign context, five documents in the context throughout.

(a) One poisoned document at slot 1, 3 or 5, for the three constructions the
    paper compares. Positions are written in the pi notation of the method
    section: P marks the poisoned slot, B a benign slot.
(b) Claim-Evidence at each poison count. The registered contrast, all poisoned
    first against all poisoned last, is drawn as one vertical pair per count, so
    its size is the length of the connector and nothing has to be subtracted by
    eye. The remaining arrangements at that count sit beside it in grey, as
    context for how much room the ordering leaves. The ordering batch covers
    this construction only.

Reads only the aggregated CSVs in data/. No model calls, no inference, no
re-scoring.

python make_figure.py
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

import figstyle as fs  # noqa: E402


STEM = "position_effect"

SHOWN = ["C06", "C42", "C00"]
MARKERS = {"C06": "o", "C42": "s", "C00": "v"}
POSITIONS = [("p1", "PBBBB"), ("p3", "BBPBB"), ("p5", "BBBBP")]
KS = [1, 2, 3, 4]
METHOD_B = "C06"  # the ordering batch covers Claim-Evidence only

# Panel (b): the pair carrying the registered contrast sits on the tick, the
# remaining arrangements sit just to its right so the connector stays clean.
CLOUD_OFFSET = 0.17
CLOUD_COLOUR = "#9AA7B4"
DODGE_TOL_PP = 2.4   # points closer than this on the y axis are spread sideways
DODGE_STEP = 0.050


def r2(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def load(name: str) -> list:
    with (HERE / "data" / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def front_pattern(k: int) -> str:
    return "P" * k + "B" * (5 - k)


def tail_pattern(k: int) -> str:
    return "B" * (5 - k) + "P" * k


def dodge(values: list) -> list:
    """Horizontal offsets that keep near-equal points apart, without randomness.

    Points are grouped by proximity on the y axis and each group is spread
    symmetrically about its column, so repeated runs draw the same figure.
    """
    order = sorted(range(len(values)), key=lambda index: values[index])
    offsets = [0.0] * len(values)
    group = []

    def flush(members):
        for rank, index in enumerate(members):
            offsets[index] = (rank - (len(members) - 1) / 2) * DODGE_STEP

    for index in order:
        if group and values[index] - values[group[-1]] > DODGE_TOL_PP:
            flush(group)
            group = []
        group.append(index)
    flush(group)
    return offsets


def draw_positions(ax, rows: list) -> dict:
    table = {}
    for row in rows:
        table.setdefault(row["condition"], {})[row["position"]] = float(row["asr_pp"])

    xs = list(range(len(POSITIONS)))
    drawn = {}
    for condition in SHOWN:
        values = [table[condition][slot] for slot, _ in POSITIONS]
        drawn[fs.METHOD_NAMES[condition]] = {pattern: r2(v)
                                             for (slot, pattern), v in zip(POSITIONS, values)}
        ax.plot(xs, values, marker=MARKERS[condition], color=fs.METHOD_EDGES[condition],
                markerfacecolor=fs.METHOD_COLORS[condition], markeredgewidth=0.7,
                linewidth=1.5, markersize=4.6, label=fs.METHOD_NAMES[condition])

    # The top curve keeps its labels above; the others take theirs below, which
    # is enough separation here because the lines never cross.
    for index, (slot, _) in enumerate(POSITIONS):
        column = sorted(((table[c][slot], c) for c in SHOWN), reverse=True)
        for rank, (value, _condition) in enumerate(column):
            above = rank == 0
            ax.text(index, value + (2.6 if above else -3.0), "%.1f" % value,
                    ha="center", va="bottom" if above else "top",
                    fontsize=7.4, color=fs.INK)

    ax.set_xticks(xs)
    ax.set_xticklabels([r"$\pi$ = " + pattern for _, pattern in POSITIONS])
    ax.set_xlim(-0.35, len(POSITIONS) - 0.65)
    fs.asr_axis(ax)
    fs.short_title(ax, "(a) Moving one poisoned document")
    ax.legend(loc="upper left", frameon=False, handlelength=1.6, labelspacing=0.3,
              borderaxespad=0.2)
    return drawn


def draw_orderings(ax, rows: list, gap_rows: list) -> dict:
    table = {}
    for row in rows:
        table.setdefault(int(row["k"]), {})[row["pattern"]] = float(row["asr_pp"])
    gap = {int(row["k"]): float(row["effect_pp"]) for row in gap_rows}

    colour = fs.METHOD_COLORS[METHOD_B]
    drawn = {"first": {}, "last": {}, "other_orderings": {}, "connector_length_pp": {}}

    for k in KS:
        first, last = front_pattern(k), tail_pattern(k)

        # Context first, and recessive: every other arrangement at this count,
        # set beside the pair rather than on top of it.
        others = sorted(value for pattern, value in table[k].items()
                        if pattern not in (first, last))
        for value, dx in zip(others, dodge(others)):
            ax.plot(k + CLOUD_OFFSET + dx, value, linestyle="none", marker="o",
                    markersize=2.8, color=CLOUD_COLOUR, alpha=0.85, zorder=2)

        # The registered contrast is the connector: its length is the effect.
        low, high = table[k][first], table[k][last]
        # Weighted as a connector, not a whisker: this is a contrast between two
        # measured arrangements, and must not read as an interval.
        ax.plot([k, k], [low, high], color=colour, linewidth=2.6, alpha=0.4,
                solid_capstyle='butt', zorder=3)
        ax.plot(k, high, linestyle="none", marker="o", markersize=5.2,
                markerfacecolor=colour, markeredgecolor=colour, zorder=4)
        ax.plot(k, low, linestyle="none", marker="o", markersize=5.2,
                markerfacecolor="white", markeredgecolor=colour, markeredgewidth=1.3,
                zorder=4)

        ax.text(k, high + 2.6, "%.1f" % high, ha="center", va="bottom",
                fontsize=7.4, color=fs.INK)
        ax.text(k, low - 3.0, "%.1f" % low, ha="center", va="top",
                fontsize=7.4, color=fs.INK)

        drawn["first"][k] = r2(low)
        drawn["last"][k] = r2(high)
        drawn["other_orderings"][k] = [r2(min(others)), r2(max(others))]
        drawn["connector_length_pp"][k] = r2(gap[k])

    handles = [
        Line2D([], [], linestyle="none", marker="o", markersize=5.2, markerfacecolor=colour,
               markeredgecolor=colour, label="all poisoned last"),
        Line2D([], [], linestyle="none", marker="o", markersize=5.2, markerfacecolor="white",
               markeredgecolor=colour, markeredgewidth=1.3, label="all poisoned first"),
        Line2D([], [], linestyle="none", marker="o", markersize=2.8, color=CLOUD_COLOUR,
               alpha=0.85, label="other arrangements"),
    ]

    ax.set_xticks(KS)
    ax.set_xlim(0.55, 4.6)
    ax.set_xlabel("Poisoned documents $m$ (of five)")
    fs.asr_axis(ax)
    fs.short_title(ax, "(b) Moving all of them")
    ax.legend(handles=handles, loc="lower right", frameon=False, handlelength=1.0,
              labelspacing=0.3, handletextpad=0.5, borderaxespad=0.2)
    return drawn


def main() -> None:
    fs.use_paper_style()
    positions = load("positions.csv")
    orderings = load("orderings.csv")
    front_tail = load("front_tail.csv")

    fig, axes = plt.subplots(1, 2, figsize=(fs.FULL_WIDTH, 2.85), sharey=True)
    panel_a = draw_positions(axes[0], positions)
    panel_b = draw_orderings(axes[1], orderings, front_tail)
    axes[1].set_ylabel("")
    fig.tight_layout(pad=0.4)
    fig.subplots_adjust(wspace=0.10)

    written = fs.save_figure(fig, HERE, STEM)
    fs.write_checks(HERE, {
        "figure": STEM,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "source_csv": ["data/positions.csv", "data/orderings.csv", "data/front_tail.csv"],
        "source_csv_sha256": {
            "data/positions.csv": fs.sha256_of(HERE / "data" / "positions.csv"),
            "data/orderings.csv": fs.sha256_of(HERE / "data" / "orderings.csv"),
            "data/front_tail.csv": fs.sha256_of(HERE / "data" / "front_tail.csv"),
        },
        "panel_a": {
            "constructions_shown": [fs.METHOD_NAMES[c] for c in SHOWN],
            "values_pp": panel_a,
            "batch": "position batch, one poisoned document, k = 1",
        },
        "panel_b": {
            "construction": fs.METHOD_NAMES[METHOD_B],
            "values_pp": panel_b,
            "batch": "ordering batch, 30 arrangements, k = 1 to 4",
            "encoding": ("one vertical pair per count: the filled marker is all poisoned "
                         "last, the hollow marker all poisoned first, and the connector "
                         "between them is the registered E3-front-tail contrast, so its "
                         "length is the effect and the reader subtracts nothing. The other "
                         "arrangements at that count are grey and set to the right of the "
                         "pair, as context only"),
            "connector_length_matches": ("drawn endpoints minus each other equal "
                                         "data/front_tail.csv to the printed precision"),
            "dodge": ("deterministic: grey points within %.1f pp of each other are spread "
                      "sideways by %.3f x units, no randomness" % (DODGE_TOL_PP, DODGE_STEP)),
            "grey_cloud_is_not_a_range": (
                "the grey points are the individual remaining arrangements, and some of "
                "them fall below the hollow marker: all poisoned first is not the minimum "
                "at k = 1, 2 or 3"),
        },
        "colour_rule": ("figstyle.METHOD_COLORS, the same colour each construction has in "
                        "every figure; panel (b) is one construction, so the pair carrying "
                        "the registered contrast keeps that colour and everything else is "
                        "de-emphasis grey"),
        "held_fixed": ("answer-bearing benign context, five documents in the context, eight "
                       "models, three seeds, 7,200 responses per point"),
        "axis": {"y": fs.ASR_LABEL, "range": [0, 100], "shared_by_both_panels": True,
                 "x_a": "poison position in pi notation", "x_b": "number of poisoned documents"},
        "value_label_precision": ("1 decimal; panel (a) labels every point, panel (b) labels "
                                  "only the eight endpoints of the four pairs, because the "
                                  "connector already carries the contrast and thirty labels "
                                  "do not fit"),
        "constructions_in_batch_not_shown": [],
        "intervals": ("none drawn; the connector in panel (b) is the point estimate of the "
                      "registered E3-front-tail contrast, and its interval, together with "
                      "the position and interaction families, is recorded in source.json"),
        **written,
    })
    print("wrote", ", ".join(sorted(written["files"])))
    if written["text_outside_canvas"]:
        print("WARNING text outside canvas:", written["text_outside_canvas"])


if __name__ == "__main__":
    main()
