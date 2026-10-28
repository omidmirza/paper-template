"""Read the figure requests that autofig.sty writes to <jobname>.afg (one slot per line).

Line format: name=step w=252.00 h=0.00 f=10 family=serif compact=0 base=figures/auto/step_w2520_f100 job=main
Use: reqs = collect([".github/build"]) -> list of Request, one per distinct base (all *.afg below each dir,
plus *.afg files given directly, plus *.afg in the current folder).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

REQUIRED = ("name", "w", "base")


@dataclass
class Request:
    name: str
    w: float                 # slot width, TeX pt
    h: float = 0.0           # slot height, TeX pt (0 = spec ASPECT)
    f: float = 10.0          # body size, TeX pt
    family: str = "serif"
    compact: bool = False
    base: str = ""           # output path without .pdf, relative to the paper root
    jobs: list = field(default_factory=list)

    def key(self):
        return dict(w=round(self.w, 2), h=round(self.h, 2), f=round(self.f, 2), family=self.family,
                    compact=self.compact)


def parse_line(line: str, where: str = "") -> Request | None:
    line = line.strip()
    if not line or line.startswith(("#", "%")):
        return None
    kv = dict(tok.split("=", 1) for tok in line.split() if "=" in tok)
    missing = [k for k in REQUIRED if k not in kv]
    if missing:
        raise ValueError(f"{where}: request without {', '.join(missing)}: {line!r}")
    num = lambda k, d: float(str(kv.get(k, d)).removesuffix("pt"))   # "252.0pt" and "252.0" both work
    return Request(name=kv["name"], w=num("w", 0), h=num("h", 0), f=num("f", 10),
                   family=kv.get("family", "serif"), compact=kv.get("compact", "0") in ("1", "true"),
                   base=kv["base"], jobs=[kv.get("job", "?")])


def afg_files(sources) -> list[Path]:
    files = set(Path(".").glob("*.afg"))
    for src in sources:
        p = Path(src)
        files.update([p] if p.is_file() else p.rglob("*.afg") if p.is_dir() else [])
    return sorted(files)


def collect(sources) -> list[Request]:
    """All requests, merged by base (the base encodes w, h, f and family)."""
    out: dict[str, Request] = {}
    for f in afg_files(sources):
        for i, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
            r = parse_line(line, f"{f}:{i}")
            if r is None:
                continue
            old = out.get(r.base)
            if old is None:
                out[r.base] = r
            elif old.key() != r.key():
                print(f"autofig: warning: {r.base} requested with different settings "
                      f"({old.key()} vs {r.key()} in {f}); using the first", file=sys.stderr)
            elif r.jobs[0] not in old.jobs:
                old.jobs += r.jobs
    return list(out.values())
