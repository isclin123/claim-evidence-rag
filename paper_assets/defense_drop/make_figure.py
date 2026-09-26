"""ASR changes under answer-bearing benign context for PoisonedRAG and Claim-Evidence.

Reads only the aggregated CSV in data/. No model calls, no inference, no
re-scoring. Run it from anywhere:

python make_figure.py
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import matplotlib.pyplot as plt  # noqa: E402

import figstyle as fs  # noqa: E402


STEM = "defense_drop"
DATA_CSV = "asr.csv"

ORDER = ["C00", "C42"]

# Internal setting names in the CSV remain unchanged.
SETTINGS = [
    ("natural", "Natural benign context"),
    ("defended", "Defended benign context"),
]

# Labels displayed in the figure.
SHORT_LABELS = [
    ("natural", "Irrelevant"),
    ("defended", "Answer-Bearing"),
]


def load():
    with (HERE / "data" / DATA_CSV).open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    table = {}

    for row in rows:
        table[(row["construction_id"], row["setting"])] = {
            "asr": float(row["asr_percent"]),
            "name": row["construction"],
            "responses": int(row["responses"]),
        }

    return table


def main() -> None:
    fs.use_paper_style()
    table = load()

    # Square outer figure.
    fig, ax = plt.subplots(
        figsize=(fs.HALF_WIDTH, fs.HALF_WIDTH * 0.78)
    )

    width = 0.30
    offset = width / 2 + 0.02
    centers = list(range(len(ORDER)))

    # Draw grouped bars.
    for sign, (key, short) in zip((-1, 1), SHORT_LABELS):
        values = [table[(cid, key)]["asr"] for cid in ORDER]

        bars = ax.bar(
            [c + sign * offset for c in centers],
            values,
            width,
            color=fs.CONTEXT_COLORS[key],
            edgecolor=fs.CONTEXT_EDGES[key],
            linewidth=0.7,
            label=short,
            zorder=3,
        )

        # Show the ASR value above each bar.
        fs.bar_labels(
            ax,
            bars,
            values,
            dy=1.2,
        )

    # X axis.
    ax.set_xticks(centers)
    ax.set_xticklabels(
        [table[(cid, "natural")]["name"] for cid in ORDER]
    )

    ax.set_xlim(-0.5, len(ORDER) - 0.5)

    # Standard ASR y-axis styling.
    fs.asr_axis(ax)
    ax.set_ylim(0, 110)

    # Control the shape of the actual plotting region.
    # height / width = 0.85, so it looks slightly wider and less vertically long.
    ax.set_box_aspect(0.85)

    # Legend.
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(0.0, 1.02),
        frameon=False,
        handlelength=1.2,
        labelspacing=0.3,
        borderaxespad=0.1,
        fontsize=8.5,
    )

    fig.tight_layout(pad=0.35)

    # Save figure.
    saved = fs.save_figure(
        fig,
        HERE,
        STEM,
    )

    # Write reproducibility / validation information.
    fs.write_checks(
        HERE,
        {
            "generated_at": datetime.now(
                timezone.utc
            ).astimezone().isoformat(timespec="seconds"),

            "script": "make_figure.py",

            "input_csv": {
                name: fs.sha256_of(HERE / "data" / name)
                for name in sorted(
                    p.name
                    for p in (HERE / "data").glob("*.csv")
                )
            },

            "plotted_values": [
                {
                    "construction_id": cid,
                    "setting": key,
                    "asr_percent": table[(cid, key)]["asr"],
                    "responses": table[(cid, key)]["responses"],
                }
                for cid in ORDER
                for key, _ in SETTINGS
            ],

            "annotated_differences_pp": [
                {
                    "construction_id": cid,
                    "defended_minus_natural": round(
                        table[(cid, "defended")]["asr"]
                        - table[(cid, "natural")]["asr"],
                        6,
                    ),
                }
                for cid in ORDER
            ],

            "figure_size_inches": [
                fs.HALF_WIDTH,
                fs.HALF_WIDTH,
            ],

            "axes_box_aspect": 0.85,

            "y_axis": [0, 100],

            "orientation": (
                "vertical grouped bars, square outer figure "
                "with slightly wider-than-tall plotting area"
            ),

            "outputs": saved["files"],

            "text_outside_canvas": saved["text_outside_canvas"],

            "drop_annotation": (
                "Removed. No dashed difference boxes and no numeric "
                "percentage-point difference labels are displayed."
            ),

            "no_error_bars": (
                "descriptive point estimates only; "
                "the two settings are separate batches"
            ),

            "in_figure_title": (
                "removed on user request; "
                "topic is carried by caption.md"
            ),
        },
    )

    print("wrote", ", ".join(saved["files"]))

    if saved["text_outside_canvas"]:
        print(
            "WARNING text outside canvas:",
            saved["text_outside_canvas"],
        )


if __name__ == "__main__":
    main()
