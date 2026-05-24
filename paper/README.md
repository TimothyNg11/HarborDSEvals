# Paper: The Rule-Precedence Misread

`main.tex` is the source for the companion paper to [FINDINGS.md](../FINDINGS.md).
The two share results (`results/multimodel_baseline.csv` and `results/intervention.csv`)
but differ in style: the paper is concise (~6 pages), FINDINGS.md goes deeper into
per-task post-mortems, verbatim trajectories, and engine cross-validation.

## Building the PDF

A working LaTeX installation is required. The Makefile auto-detects `latexmk` and falls
back to a manual `pdflatex → bibtex → pdflatex → pdflatex` sequence.

**Windows.** Install MiKTeX from <https://miktex.org/download>. On first build it will
prompt to download missing packages.

**Linux.** `apt install texlive-latex-extra latexmk` (Debian/Ubuntu).

**macOS.** `brew install --cask mactex`.

Then:

```sh
cd paper
make pdf
```

Output: `main.pdf` alongside `main.tex`.

## Files

- `main.tex` — paper source
- `references.bib` — bibliography
- `figures/` — copies of `report/figures/{multimodel_heatmap,intervention_delta}.png`
- `Makefile` — build target

The figures are committed into both `report/figures/` and `paper/figures/` to keep the
paper directory self-contained. They are regenerated from `results/per_task_rewards.json`
by `scripts/make_result_figures.py`.

## Reproducibility

Every numeric claim in the paper traces back to:

- `results/multimodel_baseline.csv` — 10 tasks × 2 models pass@3
- `results/intervention.csv` — 5 tasks × 2 models, baseline vs. intervention delta
- `results/intervention_prompt.diff` — the verbatim 6-line block used as the intervention
- `results/per_task_rewards.json` — raw rewards arrays per (task, model, condition)
