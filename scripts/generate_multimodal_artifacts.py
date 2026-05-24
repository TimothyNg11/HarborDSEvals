"""Generate the multi-modal PNG artifacts used by Tasks 7, 9, and 10.

Each PNG carries information the agent cannot recover from the data file
alone (categorical mappings, weight-selection rules, sex/age coding). Real
federal publications routinely express these constraints in figures rather
than text, which is the failure mode we want the eval to expose.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Install matplotlib if not available.
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def task_07_sector_categories():
    """Mapping figure: detailed Table 12-1 columns -> 3-way NCSES categories."""
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=130)
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_title(
        "NCSES three-way sector categorization\nTable 12-1 (NSF 25-321)",
        fontsize=13, fontweight="bold", pad=12,
    )

    categories = [
        ("ACADEMIA",   ["4-year educational institution",
                         "Other educational institution",
                         "Private, nonprofit"],
                         "#2b7bd6"),
        ("INDUSTRY",   ["Private, for profit",
                         "Self-employed"],
                         "#d6a32b"),
        ("GOVERNMENT", ["Federal government",
                         "State or local government"],
                         "#2bb673"),
    ]

    y_start = 8.5
    for cat, members, color in categories:
        rect = patches.FancyBboxPatch(
            (0.5, y_start - 1.8), 2.6, 1.5, boxstyle="round,pad=0.05",
            facecolor=color, edgecolor="black", linewidth=1.5,
        )
        ax.add_patch(rect)
        ax.text(1.8, y_start - 1.05, cat, ha="center", va="center",
                color="white", fontsize=14, fontweight="bold")
        # Member columns
        for j, m in enumerate(members):
            mrect = patches.FancyBboxPatch(
                (4.0, y_start - 0.5 - j * 0.7), 5.6, 0.55,
                boxstyle="round,pad=0.02",
                facecolor="#f4f6fa", edgecolor=color, linewidth=1.4,
            )
            ax.add_patch(mrect)
            ax.text(4.2, y_start - 0.22 - j * 0.7, m, fontsize=10, va="center")
            ax.annotate(
                "", xy=(4.0, y_start - 0.22 - j * 0.7),
                xytext=(3.1, y_start - 1.05),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.4),
            )
        y_start -= 3.0

    ax.text(
        0.5, 0.4,
        'Note: the "Other" column (~0.3% of all employed) is excluded from '
        'all three categories.',
        fontsize=9, style="italic",
    )

    out = SAMPLES / "task_07_nsf_sdr_sector_trend" / "environment" / "data" / "figure_sector_categories.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote {out}")


def task_09_dietary_methodology():
    """Screenshot-style figure listing weight selection rules."""
    fig, ax = plt.subplots(figsize=(11, 7), dpi=130)
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    # Browser-chrome stripe
    chrome = patches.Rectangle((0, 9.4), 10, 0.6, facecolor="#e7eaf3", edgecolor="#aab2c5")
    ax.add_patch(chrome)
    ax.text(0.2, 9.7, "wwwn.cdc.gov  /  NHANES Tutorials  /  Variance Estimation Module",
            fontsize=9, color="#3b4663", va="center")

    ax.text(0.3, 8.9, "NHANES Dietary Data — Sample Weight Selection",
            fontsize=15, fontweight="bold")
    ax.text(0.3, 8.4, "Tutorial > Survey Design > Sample Weights for Dietary Data",
            fontsize=10, color="#5a6478")

    body = [
        ("Use WTDRD1 for analyses based on Day 1 24-hour recall.", "bold"),
        ("Use WTDR2D for analyses based on both Day 1 AND Day 2 recalls.", "normal"),
        ("Do NOT use WTMEC2YR for dietary-recall analyses — the MEC weight does not "
         "correct for the additional non-response in the dietary follow-up.", "normal"),
        ("", "normal"),
        ("Filter records on the recall-status flag DR1DRSTZ:", "bold"),
        ("    DR1DRSTZ = 1  =>  reliable, include in analysis", "normal"),
        ("    DR1DRSTZ = 2  =>  unreliable, exclude", "normal"),
        ("    DR1DRSTZ = 4  =>  reported but not codeable, exclude", "normal"),
        ("    DR1DRSTZ = 5  =>  not done, exclude", "normal"),
        ("", "normal"),
        ("Cases with WTDRD1 = 0 must be dropped before computing weighted statistics.",
         "italic"),
    ]
    y = 7.5
    for line, style in body:
        weight = "bold" if style == "bold" else "normal"
        styl = "italic" if style == "italic" else "normal"
        ax.text(0.3, y, line, fontsize=11, fontweight=weight, fontstyle=styl)
        y -= 0.5

    # Highlight callout
    box = patches.FancyBboxPatch(
        (0.3, 1.0), 9.4, 1.0,
        boxstyle="round,pad=0.08", facecolor="#fff7d6", edgecolor="#c9a23b",
    )
    ax.add_patch(box)
    ax.text(0.55, 1.5, "Common pitfall", fontsize=11, fontweight="bold", color="#7e6213")
    ax.text(
        0.55, 1.15,
        "Using WTMEC2YR (exam weight) for a dietary estimate is the single most "
        "common analytic error.",
        fontsize=10,
    )

    out = SAMPLES / "task_09_nhanes_dietary_weights" / "environment" / "data" / "docs" / "dietary_methodology.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote {out}")


def task_10_severe_obesity_definition():
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=130)
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.text(5, 9.4, "Severe Obesity — NCHS operational definition",
            ha="center", fontsize=16, fontweight="bold")
    ax.text(5, 8.7, "Adapted from NCHS Data Brief No. 508",
            ha="center", fontsize=11, color="#566077")

    rect = patches.FancyBboxPatch(
        (1.5, 6.0), 7.0, 2.0, boxstyle="round,pad=0.08",
        facecolor="#fce8eb", edgecolor="#c6444e", linewidth=1.8,
    )
    ax.add_patch(rect)
    ax.text(5, 7.4, "Severe obesity  =  BMI  >=  40 kg / m^2",
            ha="center", fontsize=18, fontweight="bold", color="#771218")
    ax.text(5, 6.6, "(Note: this is the BMI 40 threshold, not the BMI 30 obesity threshold.)",
            ha="center", fontsize=11, fontstyle="italic")

    ax.text(0.7, 4.8, "Age bands used in published NCHS estimates", fontsize=13, fontweight="bold")
    bands = [("20-39 years", "#3b6ad6"), ("40-59 years", "#2a8a4b"), ("60 years and older", "#a04ad6")]
    for i, (lbl, c) in enumerate(bands):
        rb = patches.FancyBboxPatch(
            (0.7 + i * 3.0, 3.0), 2.7, 1.3, boxstyle="round,pad=0.05",
            facecolor=c, edgecolor="black",
        )
        ax.add_patch(rb)
        ax.text(0.7 + i * 3.0 + 1.35, 3.65, lbl, ha="center", va="center",
                color="white", fontsize=13, fontweight="bold")

    ax.text(
        0.7, 1.6,
        "Use the examination component sample weight WTMEC2YR (BMI is a physical-exam\n"
        "measurement). Drop records with WTMEC2YR = 0 or with missing BMXBMI.",
        fontsize=10,
    )

    out = SAMPLES / "task_10_nhanes_compound_subgroups" / "environment" / "data" / "docs" / "severe_obesity_definition.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote {out}")


def task_10_sex_coding():
    fig, ax = plt.subplots(figsize=(7, 4), dpi=130)
    ax.axis("off")
    ax.text(0.5, 0.9, "DEMO_L variable: RIAGENDR", fontsize=15, fontweight="bold",
            transform=ax.transAxes, ha="center")
    ax.text(0.5, 0.8, "Sex (recoded)", fontsize=12, transform=ax.transAxes, ha="center")

    rows = [("Value", "Label"), ("1", "Male"), ("2", "Female"),
            (".", "Missing")]
    y = 0.6
    for v, lab in rows:
        r = patches.Rectangle((0.20, y - 0.06), 0.6, 0.10,
                              transform=ax.transAxes,
                              facecolor="#eef2fb" if v != "Value" else "#3b6ad6",
                              edgecolor="black")
        ax.add_patch(r)
        col_v = "white" if v == "Value" else "black"
        weight = "bold" if v == "Value" else "normal"
        ax.text(0.30, y, v, transform=ax.transAxes, fontsize=12, va="center", color=col_v, fontweight=weight)
        ax.text(0.45, y, lab, transform=ax.transAxes, fontsize=12, va="center", color=col_v, fontweight=weight)
        y -= 0.12

    out = SAMPLES / "task_10_nhanes_compound_subgroups" / "environment" / "data" / "docs" / "sex_coding.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote {out}")


if __name__ == "__main__":
    task_07_sector_categories()
    task_09_dietary_methodology()
    task_10_severe_obesity_definition()
    task_10_sex_coding()
    print("all artifacts generated")
