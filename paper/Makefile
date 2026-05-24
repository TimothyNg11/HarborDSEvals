# Build the paper PDF. Requires a working TeXLive / MiKTeX installation.
#
# On Windows, MiKTeX is the easiest: https://miktex.org/download
# On Linux: apt install texlive-latex-extra latexmk
# On macOS: brew install --cask mactex
#
# Then: make pdf
#       make clean          (removes auxiliary files but keeps main.pdf)
#       make realclean      (removes everything including main.pdf)

LATEXMK := latexmk
PDFLATEX := pdflatex
BIBTEX := bibtex

# Auto-detect: prefer latexmk, fall back to pdflatex+bibtex+pdflatex+pdflatex.
HAS_LATEXMK := $(shell command -v $(LATEXMK) 2>/dev/null)

.PHONY: pdf clean realclean

pdf: main.pdf

ifdef HAS_LATEXMK
main.pdf: main.tex references.bib figures/multimodel_heatmap.png figures/intervention_delta.png
	$(LATEXMK) -pdf -bibtex -interaction=nonstopmode main.tex
else
main.pdf: main.tex references.bib figures/multimodel_heatmap.png figures/intervention_delta.png
	$(PDFLATEX) -interaction=nonstopmode main.tex
	$(BIBTEX) main
	$(PDFLATEX) -interaction=nonstopmode main.tex
	$(PDFLATEX) -interaction=nonstopmode main.tex
endif

# Sync figures from the canonical report/ location
figures/%.png: ../report/figures/%.png
	cp $< $@

clean:
	rm -f main.aux main.bbl main.blg main.log main.out main.toc main.fls main.fdb_latexmk main.synctex.gz

realclean: clean
	rm -f main.pdf
