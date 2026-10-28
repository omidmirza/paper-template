"""figures/src/simulate.py - example experiment code. It writes its results to figures/data/.

This example simulates the step response of two first-order closed loops (Method A and Method B) and
writes figures/data/example.csv, which figures/src/example.py reads. Run it with `make -f .github/Makefile data` or
`python figures/src/simulate.py`. Then `make -f .github/Makefile` redraws the figure.
"""
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]           # the paper folder
OUT = ROOT / "figures" / "data" / "example.csv"
DT, T_END = 0.25, 10.0                                # sample time and length of the run (s)
TAU = {"method_a": 1.5, "method_b": 4.0}              # closed-loop time constant of each method (s)


def main():
    y = {k: 0.0 for k in TAU}                         # outputs start at rest; the reference steps to 1
    rows = []
    for i in range(round(T_END / DT) + 1):
        rows.append([f"{i * DT:g}"] + [f"{y[k]:.4f}" for k in TAU])
        for k, tau in TAU.items():                    # exact discrete step of dy/dt = (1 - y) / tau
            y[k] += (1.0 - math.exp(-DT / tau)) * (1.0 - y[k])
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["t"] + list(TAU))
        w.writerows(rows)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} rows")


if __name__ == "__main__":
    main()
