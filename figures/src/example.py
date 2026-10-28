r"""Example figure: the step response in figures/data/example.csv (written by figures/src/simulate.py).
For a new figure, copy this file to figures/src/<name>.py and write \autofig{<name>} in the text."""
from pathlib import Path

import numpy as np

ASPECT = 0.62                       # height / width when \autofig sets neither aspect nor height
DATA = Path(__file__).resolve().parents[2] / "figures/data/example.csv"   # keep the path as one quoted string: make finds it there and redraws the figure when the file changes


def plot(fig, ax, s):
    d = np.genfromtxt(DATA, delimiter=",", names=True)
    ax.plot(d["t"], d["method_a"], **s.style("Method A", markevery=(1, 5)))
    ax.plot(d["t"], d["method_b"], **s.style("Method B", markevery=(3, 5)))
    ax.axhline(1, **s.style("Reference", lw=s.lw_ref, marker="None"))
    ax.set(xlim=(0, 10), ylim=(0, 1.15), xlabel=r"Time $t$ (s)", ylabel=r"Output $y$ (-)")
    ax.set_yticks([0, 0.5, 1])
    ax.set_yticklabels(["0", "0.5", "1"])
    s.legend(ax, loc="lower right")
