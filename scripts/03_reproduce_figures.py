#!/usr/bin/env python3
"""Reproduce final V2 manuscript figures in publication style.

The numerical results are read from the existing package. No FE analyses or
model fitting are repeated. Only the figure rendering and output filenames are
handled here.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


EXPORT_DPI = 1000

TARGET_ORDER = ["DamageState", "StiffnessLoss", "ResidualCapacity"]
TARGET_LABELS = ["Damage state", "Stiffness loss", "Residual capacity"]
TARGET_MAP = dict(zip(TARGET_ORDER, TARGET_LABELS))

MODEL_ORDER = [
    "Bayesian network",
    "Logistic regression",
    "Random forest",
    "Gradient boosting",
    "Majority-class baseline",
]

COLORS = {
    "Bayesian network": "#4C78A8",
    "Logistic regression": "#F58518",
    "Random forest": "#54A24B",
    "Gradient boosting": "#E45756",
    "Majority-class baseline": "#9D9D9D",
}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10.5,
    "axes.titlesize": 12.5,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "axes.linewidth": 1.0,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=EXPORT_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


def finish_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.35)
    ax.set_axisbelow(True)


def find_result(results: Path, *names: str) -> Path:
    for name in names:
        p = results / name
        if p.exists():
            return p
    raise FileNotFoundError(
        "None of the required result files were found:\n" +
        "\n".join(str(results / name) for name in names)
    )


def plot_fig5(df: pd.DataFrame, outdir: Path) -> None:
    cols = [
        "max_story_drift_ratio",
        "stiffness_loss_frac",
        "post_peak_strength_ratio",
    ]
    corr = df[cols].corr(method="pearson")

    fig, ax = plt.subplots(figsize=(6.1, 5.2))
    im = ax.imshow(corr.values, vmin=-1.0, vmax=1.0, cmap="coolwarm")
    ax.set_xticks(range(3))
    ax.set_yticks(range(3))
    # Manuscript terminology; inclined x labels avoid overlap with the axis.
    ax.set_xticklabels(TARGET_LABELS, rotation=28, ha="right", rotation_mode="anchor")
    ax.set_yticklabels(TARGET_LABELS)

    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center")

    ax.set_title("Correlations among target-defining response quantities", pad=10)
    cbar = fig.colorbar(im, ax=ax, fraction=0.048, pad=0.04)
    cbar.set_label("Pearson correlation")
    save(fig, outdir / "fig5_target_correlations.png")


def plot_fig6(df: pd.DataFrame, outdir: Path) -> None:
    order = ["beam", "balanced", "column"]
    labels = ["Beam-oriented", "Balanced", "Column-oriented"]
    vals = [
        df.loc[df["MechTarget"].astype(str).str.lower() == key,
               "column_to_beam_curvature_ratio"].astype(float).to_numpy()
        for key in order
    ]

    fig, ax = plt.subplots(figsize=(6.2, 4.8))
    bp = ax.boxplot(
        vals,
        tick_labels=labels,
        showfliers=False,
        patch_artist=True,
        widths=0.55,
        medianprops=dict(color="black", linewidth=1.2),
        whiskerprops=dict(color="black", linewidth=1.0),
        capprops=dict(color="black", linewidth=1.0),
        boxprops=dict(edgecolor="black", linewidth=1.0),
    )
    for patch, color in zip(bp["boxes"], ["#4C78A8", "#54A24B", "#E45756"]):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)

    ax.set_yscale("log")
    ax.set_ylabel(r"Column-to-beam section-curvature ratio, $R_{CB}^{\kappa}$")
    ax.set_title("Member-response stratification by prescribed mechanism family", pad=10)
    finish_axes(ax)
    save(fig, outdir / "fig6_member_response_stratification.png")


def load_leakage(results: Path) -> pd.DataFrame:
    # Preferred compact leakage table if present.
    for name in ("leakage_effect.csv", "table2_leakage_effect.csv"):
        p = results / name
        if p.exists():
            q = pd.read_csv(p)
            if {"Target", "Model", "FullEvidence", "LeakageControlled", "LeakageScore"}.issubset(q.columns):
                return q

    # Fall back to the dedicated V2 figure tables used by the package.
    f7 = find_result(results, "fig7_bn_macro_f1.csv")
    f8 = find_result(results, "fig8_leakage_scores.csv")
    a = pd.read_csv(f7)
    b = pd.read_csv(f8)

    # If either table already contains the complete leakage schema, use it.
    for q in (a, b):
        if {"Target", "Model", "FullEvidence", "LeakageControlled", "LeakageScore"}.issubset(q.columns):
            return q

    raise ValueError(
        "The available Fig. 7/Fig. 8 result tables do not contain the expected "
        "leakage columns. Keep the original V2 result CSVs in results/."
    )


def plot_fig7_fig8(results: Path, outdir: Path) -> None:
    leak = load_leakage(results)
    x = np.arange(3)

    bn = leak[leak["Model"] == "Bayesian network"].set_index("Target").loc[TARGET_ORDER]
    width = 0.34
    fig, ax = plt.subplots(figsize=(6.5, 4.7))
    b1 = ax.bar(x-width/2, bn["FullEvidence"], width,
                label="Full evidence", color="#A0CBE8", edgecolor="black", linewidth=0.8)
    b2 = ax.bar(x+width/2, bn["LeakageControlled"], width,
                label="Leakage-controlled", color="#4C78A8", edgecolor="black", linewidth=0.8)
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x()+bar.get_width()/2, h+0.015, f"{h:.3f}",
                    ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x, TARGET_LABELS)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Macro F1")
    ax.set_title("Bayesian-network performance before and after same-scalar leakage control", pad=10)
    ax.legend(frameon=False)
    finish_axes(ax)
    save(fig, outdir / "fig7_bn_leakage_effect.png")

    fig, ax = plt.subplots(figsize=(7.6, 4.9))
    models = ["Bayesian network", "Logistic regression", "Random forest", "Gradient boosting"]
    width = 0.16
    for i, model in enumerate(models):
        q = leak[leak["Model"] == model].set_index("Target").loc[TARGET_ORDER]
        ax.bar(x+(i-1.5)*width, q["LeakageScore"], width,
               label=model, color=COLORS[model], edgecolor="black", linewidth=0.7)
    ax.set_xticks(x, TARGET_LABELS)
    ax.set_ylabel("Leakage score")
    ax.set_title("Same-scalar leakage scores across predictive models", pad=10)
    ax.legend(frameon=False, ncol=2)
    finish_axes(ax)
    save(fig, outdir / "fig8_leakage_scores.png")


def plot_fig9(results: Path, outdir: Path) -> None:
    p = find_result(results, "fig9_leakage_controlled_model_comparison_v2.csv", "fig9_model_comparison.csv")
    df = pd.read_csv(p)

    target_col = "Target"
    model_col = "Model"
    f1_col = "MacroF1" if "MacroF1" in df.columns else "Macro F1"

    x = np.arange(3)
    width = 0.14
    fig, ax = plt.subplots(figsize=(8.0, 4.9))
    present_models = [m for m in MODEL_ORDER if m in set(df[model_col].astype(str))]
    for i, model in enumerate(present_models):
        q = df[df[model_col] == model].copy()
        # Accept either manuscript labels or compact target identifiers.
        q[target_col] = q[target_col].replace(TARGET_MAP)
        q = q.set_index(target_col).loc[TARGET_LABELS]
        ax.bar(
            x + (i-(len(present_models)-1)/2)*width,
            q[f1_col], width, label=model,
            color=COLORS.get(model), edgecolor="black", linewidth=0.7,
        )
    ax.set_xticks(x, TARGET_LABELS)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Macro F1")
    ax.set_title("Leakage-controlled model comparison", pad=10)
    ax.legend(frameon=False, ncol=2)
    finish_axes(ax)
    save(fig, outdir / "fig9_model_comparison.png")


def plot_fig10(results: Path, outdir: Path) -> None:
    candidates = [
        results / "fig10_reliability_bin_values_v2.csv",
        results / "reliability_bins.csv",
        results / "bn_reliability_bins.csv",
    ]
    p = next((p for p in candidates if p.exists()), None)
    if p is None:
        print("Fig. 10 skipped: no reliability-bin CSV found in results/.")
        return

    rb = pd.read_csv(p)
    # Normalize common column names from the stored variants.
    ren = {}
    for col in rb.columns:
        lc = col.lower().replace(" ", "").replace("_", "")
        if lc in {"target", "condition", "conditionindicator"}: ren[col] = "Target"
        elif lc in {"meanconfidence", "confidence", "meanpredictedconfidence"}: ren[col] = "MeanConfidence"
        elif lc in {"empiricalaccuracy", "accuracy", "observedaccuracy"}: ren[col] = "EmpiricalAccuracy"
    rb = rb.rename(columns=ren)
    if not {"Target", "MeanConfidence", "EmpiricalAccuracy"}.issubset(rb.columns):
        print("Fig. 10 skipped: reliability-bin CSV schema not recognized.")
        return

    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.8), sharex=True, sharey=True)
    for ax, target, color in zip(axes, TARGET_ORDER, ["#4C78A8", "#54A24B", "#E45756"]):
        q = rb[rb["Target"].replace(TARGET_MAP).isin([TARGET_MAP[target]])].copy()
        if q.empty:
            q = rb[rb["Target"] == target].copy()
        q = q.sort_values("MeanConfidence")
        ax.plot([0,1], [0,1], "--", color="gray", linewidth=1.0)
        ax.scatter(q["MeanConfidence"], q["EmpiricalAccuracy"], s=28,
                   color=color, edgecolor="black", linewidth=0.4, zorder=3)
        ax.set_title(TARGET_MAP[target])
        ax.set_xlim(0,1); ax.set_ylim(0,1.02)
        ax.set_xlabel("Mean predicted confidence")
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.35)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[0].set_ylabel("Empirical accuracy")
    save(fig, outdir / "fig10_posterior_calibration.png")


def plot_fig15(results: Path, outdir: Path) -> None:
    p = find_result(results, "fig15_experimental_posteriors_v2.csv", "experimental_posteriors_v2.csv")
    df = pd.read_csv(p)

    # Normalize the compact publication table if necessary.
    specimen = next(c for c in df.columns if c.lower() in {"specimen", "frame", "id"})
    dmg = next((c for c in df.columns if "significant" in c.lower() and "damage" in c.lower()), None)
    stiff = next((c for c in df.columns if "substantial" in c.lower() and "stiff" in c.lower()), None)
    if dmg is None or stiff is None:
        raise ValueError("Fig. 15 CSV must contain significant-damage and substantial-stiffness-loss probabilities.")

    x = np.arange(len(df)); width = 0.33
    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    b1 = ax.bar(x-width/2, df[dmg], width, label="Significant damage",
                color="#4C78A8", edgecolor="black", linewidth=0.8)
    b2 = ax.bar(x+width/2, df[stiff], width, label="Substantial stiffness loss",
                color="#F58518", edgecolor="black", linewidth=0.8)
    for bars in (b1,b2):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x()+bar.get_width()/2, h+0.013, f"{h:.3f}",
                    ha="center", va="bottom", fontsize=9)
    labels = [str(v).replace("DJ1", "DJ-1").replace("DJ2", "DJ-2") for v in df[specimen]]
    ax.set_xticks(x, labels)
    ax.set_ylim(0,1.08)
    ax.set_ylabel("Posterior probability")
    ax.set_title("Experimental condition assessment", pad=10)
    ax.legend(frameon=False)
    finish_axes(ax)
    save(fig, outdir / "fig15_experimental_posteriors.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()

    dataset = args.dataset.resolve()
    results = args.results.resolve()
    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    if not dataset.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset}")
    if not results.exists():
        raise FileNotFoundError(f"Results directory not found: {results}")

    df = pd.read_csv(dataset)
    required = [
        "MechTarget",
        "max_story_drift_ratio",
        "stiffness_loss_frac",
        "post_peak_strength_ratio",
        "column_to_beam_curvature_ratio",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing dataset columns: {missing}")

    plot_fig5(df, outdir)
    plot_fig6(df, outdir)
    plot_fig7_fig8(results, outdir)
    plot_fig9(results, outdir)
    plot_fig10(results, outdir)
    plot_fig15(results, outdir)

    print("\nPublication figures generated successfully.")
    print(f"Output directory: {outdir}")
    print(f"Resolution: {EXPORT_DPI} dpi")


if __name__ == "__main__":
    main()
