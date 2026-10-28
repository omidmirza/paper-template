#!/usr/bin/env bash
# release.sh - build all versions, make an arXiv zip and test it, tag the commit, and save it all in .github/releases/<tag>/.
# Usage: bash .github/tools/release.sh <tag> [--entry versions/arxiv.tex] [--commit] [--no-tag] [--push]
#   arxiv.zip holds one flattened main.tex (comments removed), main.bbl, and the other files the build read:
#   the figures, and the .sty (comments removed) and .cls files from .github/tex, placed next to main.tex.
#   The zip is compiled in a temporary folder with pdflatex alone, as arXiv does, and must give the same page count.
#   --commit   commit the figures and refs/extended_labels.tex if the build changed them
#   --no-tag   do not tag (a trial run; uncommitted changes are then allowed)
#   --push     push the tag to origin

set -euo pipefail
PK_NAME=release
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

TAG=""; ENTRY=""; COMMIT=0; DOTAG=1; PUSH=0
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) pk_usage; exit 0 ;;
    --entry) ENTRY="${2:?--entry needs a file}"; shift ;;
    --commit) COMMIT=1 ;;
    --no-tag) DOTAG=0 ;;
    --push) PUSH=1 ;;
    -*) die "unknown option $1 (see --help)" ;;
    *) [ -z "$TAG" ] || die "one tag only"; TAG="$1" ;;
  esac
  shift
done
[ -n "$TAG" ] || { pk_usage; die "missing <tag> (e.g. v1-arxiv, conference-2026-11)"; }
case "$TAG" in *[!A-Za-z0-9._-]*) die "tag '$TAG': use letters, digits, . _ - only" ;; esac

ROOT="$(pk_find_root)"; cd "$ROOT"
command -v zip >/dev/null && command -v unzip >/dev/null || die "zip/unzip not found"
INGIT=0; git rev-parse --git-dir >/dev/null 2>&1 && INGIT=1
if [ "$DOTAG" = 1 ]; then
  [ "$INGIT" = 1 ] || die "not a git repository: run bash .github/tools/setup_git.sh, or use --no-tag"
  git rev-parse -q --verify "refs/tags/$TAG" >/dev/null && die "tag $TAG already exists"
  [ -z "$(git status --porcelain --untracked-files=no)" ] || die "uncommitted changes: commit first, then release"
fi

# arXiv entry: --entry, else versions/*arxiv*, else versions/*extended*, else main.tex.
if [ -z "$ENTRY" ]; then
  for pat in 'versions/*arxiv*.tex' 'versions/*extended*.tex' 'main.tex'; do
    for f in $pat; do [ -f "$f" ] && { ENTRY="$f"; break 2; }; done
  done
fi
[ -f "$ENTRY" ] || die "arXiv entry not found: $ENTRY"
STEM="$(basename "$ENTRY" .tex)"

# 1. Build everything.
"$PK_TOOLS/build.sh"
if [ "$INGIT" = 1 ] && [ -n "$(git status --porcelain -- figures refs)" ]; then
  if [ "$COMMIT" = 1 ]; then
    git add -A figures refs && git commit -q -m "Figures and references for release $TAG" && log "committed the redrawn figures and refs"
  elif [ "$DOTAG" = 1 ]; then
    git status --short -- figures refs >&2
    die "the build changed figures/refs (above). Commit them: git add -A figures refs && git commit -m \"Figures for $TAG\"  (or rerun with --commit)"
  fi
fi

# 2. arXiv folder: the flattened main.tex, the .bbl, and every other file the build read, except .tex, .bib, .aux and .bbl files.
OUT=".github/releases/$TAG"; STAGE="$(mktemp -d "${TMPDIR:-/tmp}/paperkit-arxiv.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$OUT" "$STAGE/src"
pk_flatten "$ENTRY" > "$STAGE/src/main.tex"
log "flattened $ENTRY with $PK_FLATTENER (comments stripped)"

[ -f ".github/build/$STEM/$STEM.bbl" ] && cp ".github/build/$STEM/$STEM.bbl" "$STAGE/src/main.bbl"
FLS=".github/build/$STEM/$STEM.fls"; [ -f "$FLS" ] || die "missing $FLS (latexmk -recorder output)"
n=0; PHYS="$(pwd -P)"
while IFS= read -r f; do
  f="${f#./}"; f="${f#"$ROOT"/}"; f="${f#"$PHYS"/}"     # .github/ is found by an absolute path (latexmkrc)
  case "$f" in /*|.github/build/*|*.tex|*.bib|*.aux|*.bbl) continue ;; esac
  case "$f" in .github/ai/*) continue ;; esac   # not part of the paper; editmarks builds without it
  [ -f "$f" ] || continue
  d="$f"; case "$f" in .github/*) d="$(basename "$f")" ;; esac   # packages and classes next to main.tex
  mkdir -p "$STAGE/src/$(dirname "$d")"
  case "$f" in .github/*.sty) pk_strip_comments "$f" > "$STAGE/src/$d" ;; *) cp "$f" "$STAGE/src/$d" ;; esac
  n=$((n + 1))
done < <(sed -n 's/^INPUT //p' "$FLS" | sort -u)
[ -f refs/extended_labels.tex ] && grep -q 'extended_labels' "$STAGE/src/main.tex" && { mkdir -p "$STAGE/src/refs"; cp refs/extended_labels.tex "$STAGE/src/refs/"; }
log "arXiv files: main.tex, main.bbl, $n files read by the build"
rm -f "$OUT/arxiv.zip"
(cd "$STAGE/src" && zip -qr -X "$ROOT/$OUT/arxiv.zip" .)

# 3. The zip must compile on its own (as arXiv does: pdflatex, no bibtex) with the same page count.
mkdir -p "$STAGE/check" && (cd "$STAGE/check" && unzip -q "$ROOT/$OUT/arxiv.zip")
for i in 1 2 3; do
  (cd "$STAGE/check" && pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null 2>&1) || {
    grep -m6 -E '^! ' "$STAGE/check/main.log" >&2 || true; die "arxiv.zip does not compile (pass $i)"; }
done
want="$(pdfinfo ".github/build/$STEM/$STEM.pdf" 2>/dev/null | awk '/^Pages:/{print $2}')"
got="$(pdfinfo "$STAGE/check/main.pdf" 2>/dev/null | awk '/^Pages:/{print $2}')"
undef="$(grep -c -E 'Reference .* undefined|Citation .* undefined' "$STAGE/check/main.log" || true)"
[ "$want" = "$got" ] || die "arxiv.zip gives $got pages, the build gave $want"
[ "${undef:-0}" = 0 ] || warn "arxiv.zip: $undef undefined references/citations"
log "arxiv.zip compiles: $got pages, $undef undefined refs, $(du -k "$OUT/arxiv.zip" | cut -f1) kB"

# 4. PDFs, manifest, tag.
BUILT="versions/*.tex"; ls versions/*.tex >/dev/null 2>&1 || BUILT=main.tex   # what build.sh built
for f in $BUILT; do
  if [ -f ".github/pdf/$(basename "$f" .tex).pdf" ]; then cp ".github/pdf/$(basename "$f" .tex).pdf" "$OUT/"; fi
done
sha() { if command -v shasum >/dev/null; then shasum -a 256 "$@"; else sha256sum "$@"; fi; }
{
  echo "release $TAG  $(date '+%Y-%m-%d %H:%M')"
  [ "$INGIT" = 1 ] && echo "commit $(git rev-parse HEAD)"
  echo "arxiv entry $ENTRY"
  (cd "$OUT" && sha ./*.pdf arxiv.zip)
} > "$OUT/MANIFEST.txt"
if [ "$DOTAG" = 1 ]; then
  git tag -a "$TAG" -m "Release $TAG ($ENTRY)"; log "tagged $TAG at $(git rev-parse --short HEAD)"
  if [ "$PUSH" = 1 ] && git remote get-url origin >/dev/null 2>&1; then git push -q origin "$TAG"; log "pushed tag to origin"; fi
fi
log "done: $OUT/ ($(ls "$OUT" | tr '\n' ' '))"
