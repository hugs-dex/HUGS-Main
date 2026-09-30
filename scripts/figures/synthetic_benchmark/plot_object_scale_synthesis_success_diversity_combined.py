#!/usr/bin/env python3
"""Plot object-scale synthesis counts, success rates, and scene-level wrist PCA."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import Patch

if __package__:
    from .synthesis_figure_data import (
        DEFAULT_RUNS, GRASP_TYPES, Method, compute_pca, load_method,
        public_method_label, scale_sort_key, selected_modes,
        summarize_run_from_raw, write_figure_data,
    )
else:
    from synthesis_figure_data import (
        DEFAULT_RUNS, GRASP_TYPES, Method, compute_pca, load_method,
        public_method_label, scale_sort_key, selected_modes,
        summarize_run_from_raw, write_figure_data,
    )

OUTPUT_STEM = "object_scale_synthesis_success_diversity_combined"
GRASP_LABELS = {
    "right_two": "Single-Two", "right_three": "Single-Three",
    "right_full": "Single-Full", "both_three": "Both-Three", "both_full": "Both-Full",
}
GRASP_COLORS = {
    "right_two": "#82A0CB", "right_three": "#C39B64", "right_full": "#71B8B2",
    "both_three": "#C26A73", "both_full": "#9D8AAC",
}
METHOD_COLORS = {
    "Heur-Fix": "#82A0CB", "Heur-Single": "#C39B64", "Heur-Multi": "#71B8B2",
    "HUGS-Single": "#B0A4BC", "HUGS": "#8E789D",
}
DASHED_METHODS = {"Heur-Fix", "Heur-Single", "HUGS-Single"}
GRID_COLOR = "#E7E4DE"
TEXT_COLOR = "#242424"


def scale_label(scale: str) -> str:
    try:
        return str(int(round(float(scale) * 100)))
    except ValueError:
        return scale


def style_axis(axis: plt.Axes, scales: list[str]) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    for name in ("left", "bottom"):
        axis.spines[name].set_color("#B8B8B8")
        axis.spines[name].set_linewidth(0.6)
    axis.tick_params(colors=TEXT_COLOR, width=0.6, length=3)
    axis.tick_params(axis="x", labelsize=5.2, pad=1.0)
    axis.tick_params(axis="y", labelsize=6.0, pad=0.8)
    axis.set_xlim(-0.5, len(scales) - 0.5)
    axis.set_xticks(range(len(scales)))
    axis.set_xticklabels([scale_label(scale) for scale in scales])
    axis.grid(axis="y", color=GRID_COLOR, linewidth=0.55)
    axis.set_axisbelow(True)
    for boundary in np.arange(len(scales) - 1) + 0.5:
        axis.axvline(boundary, color=GRID_COLOR, linewidth=0.45, zorder=0)


def count_grid(method_count: int) -> tuple[int, int]:
    columns = 3 if method_count in (3, 6) else min(2, method_count)
    return math.ceil(method_count / columns), columns


def draw_counts(subfig, methods: list[Method], scales: list[str]) -> None:
    available = {g for method in methods for counts in method.counts.values() for g in counts}
    types = [g for g in GRASP_TYPES if g in available]
    rows, columns = count_grid(len(methods))
    axes = subfig.subplots(rows, columns, sharex=True, sharey=True, squeeze=False)
    maximum = max((m.average_count(s, g, "evaluated_grasps")
                   for m in methods for s in scales for g in types), default=0.0)
    width = 1.0 / max(len(types), 1)
    for axis, method in zip(axes.flat, methods):
        for index, grasp_type in enumerate(types):
            positions = np.arange(len(scales)) - 0.5 + width / 2 + index * width
            for kind, alpha in (("evaluated_grasps", 0.6), ("successful_grasps", 1.0)):
                heights = [method.average_count(s, grasp_type, kind) for s in scales]
                axis.bar(positions, heights, width, color=GRASP_COLORS[grasp_type],
                         alpha=alpha, edgecolor="none")
        axis.set_title(f"Method: {method.label}", loc="left", fontsize=6,
                       fontweight="bold", pad=0.2)
        axis.set_ylim(0, maximum * 1.08 if maximum else 1)
        style_axis(axis, scales)
        axis.tick_params(axis="y", labelsize=7.0, pad=1.2, labelleft=True)
    for axis in list(axes.flat)[len(methods):]:
        axis.set_visible(False)
    for axis in axes[:, 0]:
        axis.set_ylabel("Grasps per scene", fontsize=7, labelpad=0.8)
    for axis in axes[-1]:
        if axis.get_visible():
            axis.set_xlabel("Object scale (cm)", fontsize=7, labelpad=0.8)
    subfig.text(0.055, 0.995, "(a) Averaged Synthesis Budgets and Success Counts Per Scene",
                ha="left", va="top", fontsize=6.8, fontweight="bold")
    type_handles = [Patch(facecolor=GRASP_COLORS[g], label=GRASP_LABELS[g]) for g in types]
    count_handles = [Patch(facecolor=TEXT_COLOR, alpha=alpha, label=label)
                     for alpha, label in ((0.6, "Attempts"), (1.0, "Successful"))]
    for handles, anchor in ((type_handles, 0.948), (count_handles, 0.895)):
        legend = subfig.legend(handles=handles, loc="upper right",
                               bbox_to_anchor=(0.998, anchor), ncol=len(handles),
                               frameon=False, fontsize=5.8, columnspacing=0.52,
                               handlelength=0.9, handletextpad=0.25)
        legend.set_in_layout(False)
    subfig.subplots_adjust(left=0.065 if len(methods) == 3 else 0.047,
                           right=0.998, bottom=0.095, top=0.790,
                           wspace=0.11, hspace=0.18)


def build_series(methods: list[Method]) -> tuple[list, list]:
    """Derive HUGS-Single while reading each HUGS evaluation record only once."""
    single = next((m for m in methods if m.label == "Heur-Single"), None)
    modes = selected_modes(single) if single is not None else None
    success, diversity = [], []
    for method in methods:
        derive_single = method.label == "HUGS" and modes is not None
        pca, single_pca = compute_pca(method, modes if derive_single else None)
        if derive_single:
            success.append(("HUGS-Single", method.success_rates(modes)))
            diversity.append(("HUGS-Single", single_pca))
        success.append((method.label, method.success_rates()))
        diversity.append((method.label, pca))
    return success, diversity


def draw_metrics(subfig, success: list, diversity: list, scales: list[str]) -> None:
    axes = subfig.subplots(1, 2)
    ylabels = (r"Success rate (%) $\uparrow$", r"Variance ratio (%) $\downarrow$")
    for axis, series, ylabel, maximum in zip(axes, (success, diversity), ylabels, (100, 105)):
        for index, (label, values) in enumerate(series):
            color = METHOD_COLORS.get(label, f"C{index % 10}")
            axis.plot(range(len(scales)), [values.get(s, math.nan) for s in scales],
                      color=color, label=label, linestyle="--" if label in DASHED_METHODS else "-",
                      marker="o", markerfacecolor="white", markeredgewidth=0.9,
                      linewidth=1.0, markersize=3.0)
        axis.set_ylim(0, maximum)
        style_axis(axis, scales)
        axis.set_xlabel("Object scale (cm)", fontsize=7, labelpad=0)
        axis.set_ylabel(ylabel, fontsize=7, labelpad=0.8)
    for x, title in ((0.275, "(b) Grasp Success Rate Across Object Scales"),
                     (0.755, "(c) Diversity of Grasp Poses")):
        subfig.text(x, 0.995, title, ha="center", va="top", fontsize=6.8, fontweight="bold")
    handles, labels = axes[0].get_legend_handles_labels()
    legend = subfig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.900),
                           ncol=len(labels), frameon=False, columnspacing=0.5,
                           handlelength=2.35, handletextpad=0.22, fontsize=5.8)
    legend.set_in_layout(False)
    subfig.subplots_adjust(left=0.060, right=0.998, bottom=0.17, top=0.770, wspace=0.15)


def plot_figure(methods: list[Method], success: list, diversity: list) -> plt.Figure:
    scales = sorted({s for method in methods for s in method.counts}, key=scale_sort_key)
    fig = plt.figure(figsize=(5.5, 3.6))
    top, bottom = fig.subfigures(2, 1, height_ratios=(2.3, 1.3), hspace=0)
    draw_counts(top, methods, scales)
    draw_metrics(bottom, success, diversity, scales)
    return fig


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hand", choices=tuple(DEFAULT_RUNS), default="shadow")
    parser.add_argument("--runs", nargs="+", help="Run names or JSON paths; defaults depend on --hand.")
    parser.add_argument("--labels", nargs="+", help="Display labels matching --runs in order.")
    parser.add_argument("--figure-data-dir", type=Path,
                        help="Directory containing or receiving <run>_figure_data.json files.")
    parser.add_argument("--stats-root", type=Path,
                        help="Public HUGS-DexGraspBench output root for refresh and PCA.")
    parser.add_argument("--output-dir", type=Path,
                        help="Defaults to HUGS-Main/outputs/figures/synthetic_benchmark/<hand>.")
    parser.add_argument("--formats", nargs="+", choices=("pdf", "png", "svg"), default=["pdf"])
    parser.add_argument("--dpi", type=int, default=600)
    parser.add_argument("--diversity-feature", choices=("wrist",), default="wrist",
                        help="12D wrist pose PCA; wrist_joint is outside this figure's scope.")
    parser.add_argument("--font-family", default="DejaVu Serif")
    parser.add_argument("--font-files", type=Path, nargs="+",
                        help="Optional local font files to register (e.g. Times New Roman).")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--include-both-three", dest="include_both_three", action="store_true", default=True)
    group.add_argument("--exclude-both-three", dest="include_both_three", action="store_false")
    cache_group = parser.add_mutually_exclusive_group()
    cache_group.add_argument("--refresh-figure-data", action="store_true",
                             help="Rebuild schema-v2 caches from public evaluation records.")
    cache_group.add_argument("--load-figure-data", action="store_true",
                             help="Use existing caches without rescanning evaluation records.")
    args = parser.parse_args(argv)
    args.runs = args.runs or list(DEFAULT_RUNS[args.hand])
    if args.labels is not None and len(args.labels) != len(args.runs):
        parser.error("--labels must have the same number of entries as --runs")
    if args.dpi <= 0:
        parser.error("--dpi must be positive")
    args.output_dir = args.output_dir or (
        Path(__file__).resolve().parents[3] / "outputs/figures/synthetic_benchmark" / args.hand)
    repo_root = Path(__file__).resolve().parents[3]
    args.figure_data_dir = args.figure_data_dir or (repo_root / "outputs/figure-data/synthetic_benchmark" / args.hand)
    args.stats_root = args.stats_root or (repo_root.parent / "HUGS-DexGraspBench" / "output")
    if not args.refresh_figure_data and not args.load_figure_data:
        args.refresh_figure_data = True
    return args


def main() -> None:
    args = parse_args()
    for font in args.font_files or []:
        font_manager.fontManager.addfont(str(font))
    font_manager.findfont(args.font_family, fallback_to_default=False)
    plt.rcParams.update({
        "font.family": args.font_family, "font.size": 9,
        "axes.labelcolor": TEXT_COLOR, "axes.titlecolor": TEXT_COLOR,
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })
    methods = []
    for index, run in enumerate(args.runs):
        path = Path(run) if Path(run).suffix == ".json" else args.figure_data_dir / f"{run}_figure_data.json"
        if args.refresh_figure_data and Path(run).suffix != ".json":
            data = summarize_run_from_raw(run, args.stats_root, args.hand, args.include_both_three)
            path = write_figure_data(data, args.figure_data_dir)
        label = args.labels[index] if args.labels else None
        methods.append(load_method(path, args.hand, label or public_method_label(run),
                                   args.include_both_three, args.stats_root))
    if len({m.label for m in methods}) != len(methods):
        raise ValueError("Method labels must be unique; use --labels for custom comparisons.")
    success, diversity = build_series(methods)
    fig = plot_figure(methods, success, diversity)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for extension in args.formats:
        path = args.output_dir / f"{OUTPUT_STEM}.{extension}"
        fig.savefig(path, dpi=args.dpi)
        print(path)
    plt.close(fig)


if __name__ == "__main__":
    main()
