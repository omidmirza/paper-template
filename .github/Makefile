# .github/Makefile - build the paper on a laptop. Overleaf does not use it.
# Run it from the top folder of the paper: make -f .github/Makefile [target]; make -f .github/Makefile help lists the targets.
# To type less, add alias pmake='make -f .github/Makefile' to your shell profile and run pmake, pmake help, ...
# Output: .github/build/, .github/pdf/ and .github/releases/, which git ignores, and the figures in figures/auto/, which you commit.
# Set PYTHON=... or PAPERKIT_PYTHON=... to a Python with matplotlib; the default is .github/.venv/bin/python if it exists, else python3.

PYTHON ?= $(or $(PAPERKIT_PYTHON),$(firstword $(wildcard .github/.venv/bin/python) python3))
ENTRY  ?= versions/arxiv.tex
export PAPERKIT_PYTHON := $(PYTHON)
M      := make -f .github/Makefile
AUTOFIG = PYTHONPATH=.github/python "$(PYTHON)" -m autofig
DATA_CMD ?= "$(PYTHON)" figures/src/simulate.py
BRANCH := $(shell git branch --show-current 2>/dev/null)
# live pulls from and pushes to the remote overleaf if there is one (its branch is master), else origin on the current branch.
LIVE_REMOTE ?= $(if $(filter overleaf,$(shell git remote 2>/dev/null)),overleaf,origin)
LIVE_BRANCH ?= $(if $(filter overleaf,$(LIVE_REMOTE)),master,$(or $(BRANCH),main))

.PHONY: all help figures data watch live release diff clean need-root

all: need-root
	bash .github/tools/build.sh

help:
	@echo "Run from the top folder of the paper: $(M) <target>"
	@echo "  (none)          build every file in versions/ to .github/pdf/, drawing each figure at its size in the paper"
	@echo "  figures         redraw the figures that the builds in .github/build/ ask for (run make again to include them)"
	@echo "  data            run figures/src/simulate.py, which writes figures/data/; then run make again to redraw the figures"
	@echo "  watch           rebuild ENTRY and redraw the figures on every save; commit new figures, push nothing"
	@echo "  live            as watch, but also commit changed .tex files, pull, and push (to overleaf, else origin)"
	@echo "  release TAG=v1  build all versions, tag the commit, write a tested arXiv zip to .github/releases/v1/"
	@echo "  diff OLD=v1     make a PDF that marks the changes since v1 (optional: NEW=<ref>, ENTRY=versions/...)"
	@echo "  clean           delete .github/build/ and .github/pdf/"
	@echo "Options: ENTRY=versions/<name>.tex (default $(ENTRY)), PYTHON=<python with matplotlib>"

figures: need-root
	$(AUTOFIG) make --builds .github/build

# data runs the experiment code, which writes the results that the figures read. For another command: $(M) data DATA_CMD='...'
data:
	$(DATA_CMD)

# watch commits new figures on the current branch and pushes nothing.
watch: need-root
	$(AUTOFIG) watch --entry $(ENTRY) --outdir .github/build

# live also pulls before each build, commits the changed .tex files with the figures, and pushes. Overleaf
# has one branch (master), so live with the overleaf remote runs on main only.
live: need-root
	@if [ "$(LIVE_REMOTE)" = overleaf ] && [ "$(BRANCH)" != main ]; then \
	  echo "live with the overleaf remote runs on main only (you are on $(BRANCH))"; exit 1; fi
	$(AUTOFIG) watch --entry $(ENTRY) --outdir .github/build --pull $(LIVE_REMOTE) --push $(LIVE_REMOTE) --remote-branch $(LIVE_BRANCH) --commit-sources

release: need-root
	@test -n "$(TAG)" || { echo "usage: $(M) release TAG=v1-arxiv"; exit 1; }
	bash .github/tools/release.sh $(TAG)

diff: need-root
	@test -n "$(OLD)" || { echo "usage: $(M) diff OLD=<tag or commit> [NEW=<ref>] [ENTRY=versions/...]"; exit 1; }
	bash .github/tools/diff.sh $(OLD) $(NEW) $(ENTRY)

need-root:
	@test -f main.tex || { echo "run this from the top folder of the paper: $(M)"; exit 1; }
	@test -f .github/tools/build.sh || { echo "no .github/tools here: copy the .github folder of the template"; exit 1; }

clean:
	rm -rf .github/build .github/pdf
