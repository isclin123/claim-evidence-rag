"""Shared plotting style for figures that go into the paper.

Every figure script under this directory imports this module, so one change here
propagates to all paper figures. The palette and rcParams continue the style that
was already approved for the 2026-09-15 asset collection; this module is the
canonical entry point for new paper figures.

No data loading, no inference, no network access happens here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# ---------------------------------------------------------------- palette ----
# Method colours are fixed across the whole paper. Do not recolour a method
# because it happens to rank first in one figure.
# C00 is displayed as "PoisonedRAG", never as "Original".
METHOD_COLORS = {
    "C00": "#A7C7E2",  # PoisonedRAG
    "C06": "#DB631F",  # Claim-Evidence (main method)
    "C42": "#478B78",  # CorruptRAG-AS
}
METHOD_EDGES = {**METHOD_COLORS, "C00": "#326DA8"}
METHOD_NAMES = {
    "C00": "PoisonedRAG",
    "C06": "Claim-Evidence",
    "C42": "CorruptRAG-AS",
}

# Benign-context settings. Used when the x axis carries methods and the bars
# carry the context setting, so method colours stay free for method comparisons.
CONTEXT_COLORS = {"natural": "#A7C7E2", "defended": "#326DA8"}
CONTEXT_EDGES = {"natural": "#326DA8", "defended": "#173C66"}
# Fill for a difference annotation drawn on top of a bar (the ASR a setting
# removed). Near white on purpose: it marks an absence, so it must stay lighter
# than every data colour and never read as a third series.
CONTEXT_GHOST = "#F4F8FC"

MODEL_CODES = ["qwen35_9b", "llama31_8b", "mistral_7b", "qwen3_1_7b",
               "qwen3_4b", "qwen3_8b", "llama32_3b", "gemma3_4b"]
MODEL_NAMES = ["Qwen3.5 9B", "Llama 3.1 8B", "Mistral 7B", "Qwen3 1.7B",
               "Qwen3 4B", "Qwen3 8B", "Llama 3.2 3B", "Gemma 3 4B"]
MODEL_PRETTY = dict(zip(MODEL_CODES, MODEL_NAMES))

INK = "#26323E"
GRID = "#D8DEE6"
MUTED = "#4B5A6A"
SEQUENTIAL = LinearSegmentedColormap.from_list(
    "paper_level", ["#F8FBFD", "#D5E5F1", "#A7C7E2", "#326DA8", "#173C66"])
DIVERGING = LinearSegmentedColormap.from_list(
    "paper_difference", ["#B74E18", "#F0B589", "#FAFAF9", "#A7C7E2", "#326DA8"])

ASR_LABEL = "ASR (%)"  # defined once in the setup section; captions carry the caveat
DIFF_LABEL = "ASR difference (pp)"

# Figure widths in inches. The ICLR 2027 style file sets a 5.5in text width.
FULL_WIDTH = 5.5
TWO_THIRDS = 3.6
HALF_WIDTH = 2.7


def use_paper_style() -> None:
    """Apply the shared rcParams. Call once at the top of a figure script."""

    plt.rcParams.update({
        # Match the serif style used by typical conference paper templates.
        "font.family": "serif",
        "font.serif": [
            "Times New Roman",
            "Times",
            "Nimbus Roman",
            "DejaVu Serif",
        ],

        # Font sizes
        "font.size": 8.5,
        "axes.labelsize": 9,
        "axes.titlesize": 9,
        "legend.fontsize": 8.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,

        # Keep text as real vector fonts in exported files.
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",

        # Axes appearance
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.65,
        "axes.edgecolor": "#8190A0",

        # Text / tick colors
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,

        # Grid
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "axes.axisbelow": True,

        # Background
        "figure.facecolor": "white",
        "savefig.facecolor": "white",

        # Lines / markers
        "lines.linewidth": 1.5,
        "lines.markersize": 4.2,
    })


def short_title(ax, text: str) -> None:
    """In-figure topic title: left aligned, above the axes."""
    ax.set_title(text, loc="left", fontweight="bold", color=MUTED, pad=8)


def asr_axis(ax, ylabel: str = ASR_LABEL) -> None:
    """Percentage ASR axis: always 0-100 for this project's overviews."""
    ax.set_ylim(0, 100)
    ax.set_yticks(range(0, 101, 20))
    ax.set_ylabel(ylabel)
    ax.grid(axis="y")
    ax.tick_params(length=3, width=0.65)


def asr_axis_h(ax, xlabel: str = ASR_LABEL) -> None:
    """Horizontal-bar twin of asr_axis: ASR runs along x, categories along y."""
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 101, 20))
    ax.set_xlabel(xlabel)
    ax.grid(axis="x")
    ax.tick_params(length=3, width=0.65)


def bar_labels(ax, bars, values, fmt="{:.2f}", dy=1.5, **kwargs) -> None:
    """Print each value at its own bar end, never in a detached column."""
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + dy,
                fmt.format(value), ha="center", va="bottom", fontsize=8.5,
                color=INK, **kwargs)


def _text_outside_canvas(fig) -> list:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    clipped = []
    for text in fig.findobj(matplotlib.text.Text):
        if not (text.get_visible() and text.get_text()):
            continue
        box = text.get_window_extent(renderer)
        if not (box.width and box.height):
            continue
        if (box.x0 < -1 or box.y0 < -1
                or box.x1 > fig.bbox.width + 1 or box.y1 > fig.bbox.height + 1):
            clipped.append(text.get_text())
    return clipped


def save_figure(fig, folder, stem: str, formats=("pdf", "svg", "png")) -> dict:
    """Write the figure in every delivery format and return path -> sha256.

    PDF is the vector file the paper embeds; SVG is the editable twin; PNG is a
    600 dpi preview. Nothing here rasterises the PDF.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    clipped = _text_outside_canvas(fig)
    written = {}
    for ext in formats:
        path = folder / f"{stem}.{ext}"
        fig.savefig(path, dpi=600, facecolor="white")
        written[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"files": written, "text_outside_canvas": clipped}


def write_checks(folder, payload: dict) -> Path:
    """Save the self-check record next to the figure."""
    path = Path(folder) / "checks.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path


def sha256_of(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
