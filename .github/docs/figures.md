# Figures

Each figure is drawn at the width it takes in the paper. The rules are in [FIGURE_RULES.md](FIGURE_RULES.md).

## 1. Write the plot

Copy `figures/src/example.py` to `figures/src/<name>.py` and edit `plot`.

```python
ASPECT = 0.62                      # height / width when \autofig sets neither aspect nor height
DATA = Path(__file__).resolve().parents[2] / "figures/data/example.csv"

def plot(fig, ax, s):              # s: the sizes for this slot
    d = np.genfromtxt(DATA, delimiter=",", names=True)
    ax.plot(d["t"], d["method_a"], **s.style("Method A", markevery=(1, 5)))
    ax.axhline(1, **s.style("Reference", lw=s.lw_ref, marker="None"))
    ax.set(xlabel=r"Time $t$ (s)", ylabel=r"Output $y$ (-)")
    s.legend(ax, loc="lower right")
```

- `s.style(name)` returns the colour, line style and marker of a method in `figures/src/methods.py`.
- Line widths: `s.lw`, `s.lw_noisy`, `s.lw_ref`. Font sizes: `s.fs_label`, `s.fs_tick`, `s.fs_legend`.
- Write a percent sign as `$\%$`.

## 2. Place it

```latex
\autofig{example}    \autofig[aspect=0.38]{response}    \autofig[height=4cm]{example}
```

Never scale it. [autofig_latex.md](autofig_latex.md) lists the options.

## 3. Build it

Run these in the top folder of the paper.

```sh
make -f .github/Makefile            # all versions and figures; stops when a figure breaks a rule
make -f .github/Makefile figures    # figures only
make -f .github/Makefile data       # runs figures/src/simulate.py
make -f .github/Makefile watch      # rebuilds on every save
make -f .github/Makefile live       # as watch, and also pulls and pushes
```

A figure is redrawn when its file, `methods.py` or a data file it names as `"figures/data/<file>"` changes.
To run your own experiment code, pass it to make: `make -f .github/Makefile data DATA_CMD='python my_run.py'`.

## Overleaf

Overleaf cannot run Python. Build on your laptop, commit and push `figures/auto/`, then on Overleaf press "Pull GitHub changes into Overleaf".
Until then the slot shows the figure drawn for another size, scaled and in a red frame, or a red "missing" box.
