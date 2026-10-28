"""Draw figures at the size of their LaTeX slot. Run python -m autofig <command> in the paper folder.

make   draw every figure size that .github/build/**/*.afg asks for and that is missing or out of date
raw    draw each figure with matplotlib defaults, for comparison, to figures/raw/<name>.pdf
check  check figure PDFs against the figure rules
audit  compare the smallest text in each figure of a compiled paper with the body text
watch  on every change, compile LaTeX, redraw the figures and commit new ones (push with --push)
"""
import argparse
import sys


def parser():
    p = argparse.ArgumentParser(prog="python -m autofig", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make", help="draw the figures that are missing or out of date")
    m.add_argument("--builds", action="append", help="folder(s) or .afg file(s) to read (default: .github/build)")
    m.add_argument("--specs", default="figures/src")
    m.add_argument("--force", action="store_true", help="draw every requested figure again")
    m.add_argument("--no-strict", action="store_true", help="save figures that break a rule, with a warning")
    r = sub.add_parser("raw", help="draw the figures with matplotlib defaults, for comparison")
    r.add_argument("names", nargs="*")
    r.add_argument("--specs", default="figures/src")
    r.add_argument("--out", default="figures/raw")
    c = sub.add_parser("check", help="check figure PDFs against the figure rules")
    c.add_argument("pdfs", nargs="+")
    c.add_argument("--body", type=float, help="body size in pt (default: from <pdf>.json, else 10)")
    c.add_argument("--width", type=float, help="expected width in pt (default: from <pdf>.json)")
    a = sub.add_parser("audit", help="compare the figure text in a compiled paper with the body text")
    a.add_argument("pdf")
    a.add_argument("--body", type=float, help="body size in pt (default: detected)")
    a.add_argument("--json", help="write the per-figure table to this file")
    w = sub.add_parser("watch", help="rebuild on every change and commit new figures")
    w.add_argument("--entry", required=True)
    w.add_argument("--outdir", default=".github/build")
    w.add_argument("--specs", default="figures/src")
    w.add_argument("--interval", type=float, default=2.0)
    w.add_argument("--pull", help="git remote to pull from before each build (e.g. overleaf)")
    w.add_argument("--push", help="git remote to push new figure commits to")
    w.add_argument("--remote-branch", help="branch on the remote (default: current branch; Overleaf: master)")
    w.add_argument("--commit-sources", action="store_true",
                   help="also commit changed .tex files (tracked by git) with each figure commit")
    w.add_argument("--once", action="store_true", help="build once, then exit")
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if args.cmd == "make":
        from .engine import main as run
        args.builds = args.builds or [".github/build"]
    elif args.cmd == "raw":
        from .raw import main as run
    elif args.cmd == "check":
        from .check import main as run
    elif args.cmd == "audit":
        from .audit import main as run
    else:
        from .watch import main as run
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
