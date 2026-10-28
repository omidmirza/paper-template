"""Watch loop: a source file changes -> LaTeX -> new figure variants -> LaTeX again -> git commit (-> push).

CLI: python -m autofig watch --entry main.tex [--outdir .github/build] [--interval 2] [--pull overleaf]
     [--push overleaf] [--remote-branch master] [--commit-sources] [--once]
Each step prints one line. --once builds once and exits (for tests).
If a pull fails or files have merge conflicts, the loop prints one line and waits for the next
commit (HEAD changes) before it builds again. --commit-sources also commits the changed .tex
files with the figure commit, so a layout change made on the laptop reaches Overleaf too.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

from . import engine
from .requests import collect

WATCHED = (".tex", ".py", ".bib", ".sty", ".cls")
SKIP = {".git", "build", "auto", "raw", "pdf", "releases", "__pycache__", ".venv"}


def log(step, msg):
    print(f"[{time.strftime('%H:%M:%S')}] {step:<7} {msg}", flush=True)


def snapshot(root: Path) -> dict:
    """{path: (mtime, size)} of the source files under root."""
    out = {}
    for p in root.rglob("*"):
        if p.suffix in WATCHED and p.is_file() and not SKIP.intersection(p.relative_to(root).parts[:-1]):
            st = p.stat()
            out[str(p)] = (st.st_mtime_ns, st.st_size)
    return out


def git(*args, check=False):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r


def latexmk(entry: str, outdir: str, force=False) -> bool:
    out = Path(outdir) / Path(entry).stem
    cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", f"-outdir={out}", entry]
    r = subprocess.run(cmd + (["-g"] if force else []), capture_output=True, text=True)
    log("latex", f"{entry} -> {out}/{Path(entry).stem}.pdf " + ("ok" if r.returncode == 0 else
                 f"FAILED (see {out}/{Path(entry).stem}.log)"))
    return r.returncode == 0


def conflicts() -> bool:
    """True if git has unmerged files (conflict markers in the sources)."""
    return bool(git("ls-files", "-u").stdout.strip())


PAUSED = "paused"
PAUSE_MSG = "commit your changes, or resolve the conflict and commit. Paused until the next commit."


def iteration(a, branch):
    """One build. Returns the made figures, or PAUSED if a pull failed or conflicts exist."""
    if conflicts():
        log("git", "merge conflict: " + PAUSE_MSG)
        return PAUSED
    if a.pull:
        r = git("pull", "--no-edit", a.pull, a.remote_branch or branch)
        if r.returncode != 0 or conflicts():
            log("pull", f"{a.pull} FAILED: " + PAUSE_MSG)
            return PAUSED
        log("pull", f"{a.pull}/{a.remote_branch or branch}: " + (r.stdout.strip().splitlines() or ["?"])[-1])
    latexmk(a.entry, a.outdir)
    made, failed = engine.make(collect([a.outdir]), a.specs, strict=True)
    log("make", f"{len(made)} figure(s) made, {failed} failed")
    if not made:
        return made
    latexmk(a.entry, a.outdir, force=True)
    if git("rev-parse", "--is-inside-work-tree").returncode != 0:
        log("git", "not a git repository: no commit")
        return made
    auto = sorted({str(Path(p).parent) for p in Path(".").glob("**/auto/*.pdf") if ".git" not in p.parts}) \
        or ["figures/auto"]
    git("add", "--", *auto)
    if git("diff", "--cached", "--quiet").returncode == 0:
        log("git", "figures unchanged in git: no commit")
        return made
    msg = "Redraw figures: " + ", ".join(f"{n} at {w:g} pt" for n, w in made)
    if getattr(a, "commit_sources", False):
        git("add", "-u", "--", "*.tex")             # changed .tex files that git already tracks
        tex = git("diff", "--cached", "--name-only", "--", "*.tex").stdout.split()
        if tex:
            msg += " (with " + ", ".join(tex) + ")"
    r = git("commit", "-q", "-m", msg)
    log("commit", msg if r.returncode == 0 else f"FAILED: {r.stderr.strip()[:200]}")
    if a.push and r.returncode == 0:
        r = git("push", "-q", a.push, f"HEAD:{a.remote_branch or branch}")
        log("push", f"{a.push} {a.remote_branch or branch} " + ("ok" if r.returncode == 0 else
                                                                 f"FAILED: {r.stderr.strip()[:200]}"))
    return made


def main(a) -> int:
    root = Path(".")
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "main"
    log("watch", f"entry {a.entry}, every {a.interval:g} s" + (", once" if a.once else "") +
        (f", pull {a.pull}" if a.pull else "") + (f", push {a.push}" if a.push else ""))
    seen = None
    paused = None                                    # HEAD at the moment the loop paused
    while True:
        if paused is not None:
            head = git("rev-parse", "HEAD").stdout.strip()
            if head == paused or conflicts():
                time.sleep(a.interval)
                continue
            log("watch", "new commit: building again")
            paused, seen = None, {}
        if a.pull and not a.once and seen is not None:
            r = git("fetch", "-q", a.pull)
            ahead = git("rev-list", "--count", f"HEAD..{a.pull}/{a.remote_branch or branch}").stdout.strip()
            if r.returncode == 0 and ahead not in ("", "0"):
                log("pull", f"{ahead} new commit(s) on {a.pull}")
                seen = {}                            # force a build after the pull
        now = snapshot(root)
        if now != seen:
            if seen:
                changed = sorted(set(now.items()) ^ set(seen.items()))
                log("change", ", ".join(sorted({Path(p).name for p, _ in changed}))[:120])
            if iteration(a, branch) == PAUSED:
                if a.once:
                    return 1
                paused = git("rev-parse", "HEAD").stdout.strip()
            seen = snapshot(root)
        if a.once:
            return 0
        time.sleep(a.interval)
