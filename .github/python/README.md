# autofig

Python code that draws each figure at the size of its LaTeX slot.
[figures.md](../docs/figures.md) shows how to add a figure; [FIGURE_RULES.md](../docs/FIGURE_RULES.md) has the rules.

Run the commands in the top folder of the paper, the one that holds `figures/`.
They need Python 3.10 or newer, TeX Live and ghostscript.

```sh
python3 -m venv .github/.venv
.github/.venv/bin/pip install -r .github/python/requirements.txt
export PYTHONPATH=.github/python
.github/.venv/bin/python -m autofig make                        # draw new or changed figures
.github/.venv/bin/python -m autofig raw                         # "before" figures with matplotlib defaults
.github/.venv/bin/python -m autofig check figures/auto/*.pdf    # check figure files against the rules
.github/.venv/bin/python -m autofig audit .github/pdf/review.pdf    # check figure text in the compiled paper
.github/.venv/bin/python -m autofig watch --entry main.tex      # rebuild on every change and commit new figures
```

`make -f .github/Makefile` runs `autofig make` during the build. `make -f .github/Makefile watch` runs `autofig watch`.
