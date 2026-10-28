#!/usr/bin/env bash
# build.sh - build every version of the paper, with each figure drawn at its final size.
# Usage: bash .github/tools/build.sh [--no-figures] [entry.tex ...]
#   Without entries it builds every file in versions/ (or main.tex if there is none).
#   It runs latexmk on each entry (output in .github/build/<name>/), then `python -m autofig make`, then
#   latexmk again on each entry if a figure changed. Each PDF is copied to .github/pdf/<name>.pdf, and a
#   table of all versions is printed at the end.
#   The arXiv version is built first. The labels of its .aux file are copied to refs/extended_labels.tex,
#   so the other versions can refer to its appendix.
#   For a page limit, put a line `% page limit: 6` in the entry file; the table says OVER when the PDF is longer.
#   On GitHub Actions the table also goes to the job summary.
#   Environment: PAPERKIT_PYTHON (a Python with matplotlib), PAPERKIT_EXTENDED (the name of the entry
#   whose labels the others cite; default: the first entry with "extended", else with "arxiv", in its name).

set -euo pipefail
PK_NAME=build
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

FIGS=1
ENTRIES=()
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) pk_usage; exit 0 ;;
    --no-figures) FIGS=0 ;;
    -*) die "unknown option $1 (see --help)" ;;
    *) ENTRIES+=("$1") ;;
  esac
  shift
done

ROOT="$(pk_find_root)"
# Entries given on the command line: make them relative to the root (spaces in paths break pdflatex).
if [ ${#ENTRIES[@]} -gt 0 ]; then
  for i in "${!ENTRIES[@]}"; do
    e="${ENTRIES[$i]}"
    [ -f "$e" ] || [ -f "$ROOT/$e" ] || die "entry not found: $e"
    [ -f "$e" ] || e="$ROOT/$e"
    abs="$(cd "$(dirname "$e")" && pwd)/$(basename "$e")"
    [ "${abs#"$ROOT"/}" != "$abs" ] || die "entry $e is not inside the paper root $ROOT"
    ENTRIES[$i]="${abs#"$ROOT"/}"
  done
fi
cd "$ROOT"
export TEXINPUTS="./.github//:${TEXINPUTS:-}"   # packages, classes, layout.tex (latexmkrc adds it too, for Overleaf)
command -v latexmk >/dev/null || die "latexmk not found (install TeX Live)"
pk_find_python "$ROOT"

# Entries relative to the root; default = versions/*.tex (sorted), else main.tex.
if [ ${#ENTRIES[@]} -eq 0 ]; then
  for f in versions/*.tex; do [ -f "$f" ] && ENTRIES+=("$f"); done
  [ ${#ENTRIES[@]} -gt 0 ] || ENTRIES=(main.tex)
fi

# Long (arXiv) entry first: its .aux feeds refs/extended_labels.tex for the other versions.
EXT="${PAPERKIT_EXTENDED:-}"
if [ -z "$EXT" ]; then
  for pat in '*extended*' '*arxiv*'; do
    for e in "${ENTRIES[@]}"; do case "$(basename "$e" .tex)" in $pat) EXT="$(basename "$e" .tex)"; break 2 ;; esac; done
  done
fi
ORDER=()
for e in "${ENTRIES[@]}"; do [ "$(basename "$e" .tex)" = "$EXT" ] && ORDER+=("$e"); done
for e in "${ENTRIES[@]}"; do [ "$(basename "$e" .tex)" = "$EXT" ] || ORDER+=("$e"); done

LATEXMK=(latexmk -pdf -interaction=nonstopmode -file-line-error -halt-on-error)
FAILED=()

compile() {  # compile <entry> [extra latexmk args]; never exits the script on a TeX error
  local e="$1"; shift
  local stem; stem="$(basename "$e" .tex)"
  mkdir -p ".github/build/$stem"
  if "${LATEXMK[@]}" "$@" -outdir=".github/build/$stem" "$e" >".github/build/$stem/latexmk.out" 2>&1; then
    return 0
  fi
  warn "$e failed; first errors from .github/build/$stem/$stem.log:"
  grep -m6 -E '^(! |.*:[0-9]+: )' ".github/build/$stem/$stem.log" >&2 2>/dev/null || tail -n 15 ".github/build/$stem/latexmk.out" >&2
  return 1
}

# Copy only the \newlabel lines (all that layout.tex reads), so the file changes only when a label of the
# arXiv version changes, not with every edit mark or page count. It is a .tex file because Overleaf drops
# *.aux files. Called only after a successful compile; an .aux without labels leaves the file as it is.
LABELS=refs/extended_labels.tex
copy_ext_aux() {
  if [ -n "$EXT" ] && [ -f ".github/build/$EXT/$EXT.aux" ]; then
    mkdir -p refs
    { echo '\relax'; grep '^\\newlabel' ".github/build/$EXT/$EXT.aux" || true; } > "$LABELS.new"
    grep -q '^\\newlabel' "$LABELS.new" || { rm -f "$LABELS.new"; return 0; }
    if cmp -s "$LABELS.new" "$LABELS" 2>/dev/null; then
      rm -f "$LABELS.new"
    else
      mv "$LABELS.new" "$LABELS"; log "$LABELS updated from $EXT"
    fi
  fi
}

# Pass 1: compile everything (writes .github/build/<stem>/<stem>.afg figure requests).
for e in "${ORDER[@]}"; do
  log "latexmk $e"
  if compile "$e"; then [ "$(basename "$e" .tex)" != "$EXT" ] || copy_ext_aux; else FAILED+=("$e"); fi
done

# Figures: make every requested variant, then recompile entries if any figure changed.
if [ "$FIGS" = 1 ] && [ ${#FAILED[@]} -ge ${#ORDER[@]} ]; then
  log "figure step skipped: every entry failed"
elif [ "$FIGS" = 1 ]; then
  if pk_autofig_ok; then
    before="$(pk_fingerprint figures/auto)"
    log "python -m autofig make"
    pk_autofig make --builds .github/build || die "autofig make failed (see messages above)"
    if [ "$(pk_fingerprint figures/auto)" != "$before" ]; then
      log "figures changed: recompiling"
      for e in "${ORDER[@]}"; do
        if compile "$e" -g; then [ "$(basename "$e" .tex)" != "$EXT" ] || copy_ext_aux
        else case " ${FAILED[*]-} " in *" $e "*) ;; *) FAILED+=("$e") ;; esac; fi
      done
    else
      log "figures up to date"
    fi
  fi
else
  log "figure step skipped (--no-figures)"
fi

# Copy PDFs and print a summary table (and a Markdown one for the GitHub job summary).
mkdir -p .github/pdf
SUMMARY="${GITHUB_STEP_SUMMARY:-}"
if [ -n "$SUMMARY" ]; then
  printf '| version | status | pages | page limit | undefined references |\n|---|---|---|---|---|\n' >> "$SUMMARY"
fi
printf '\n%-32s %-6s %6s %6s %6s  %s\n' entry status pages limit undef pdf
for e in "${ORDER[@]}"; do
  stem="$(basename "$e" .tex)"; st=ok; pages=-; undef=-
  limit="$(grep -m1 -i -E '^%+ *page limit: *[0-9]+' "$e" 2>/dev/null | grep -o -E '[0-9]+' | head -n 1 || true)"
  case " ${FAILED[*]-} " in *" $e "*) st=FAIL ;; esac
  [ "$st" = ok ] || rm -f ".github/pdf/$stem.pdf"   # never leave an old PDF next to FAIL
  if [ "$st" = ok ] && [ -f ".github/build/$stem/$stem.pdf" ]; then
    cp ".github/build/$stem/$stem.pdf" ".github/pdf/$stem.pdf"
    pages="$( (pdfinfo ".github/pdf/$stem.pdf" 2>/dev/null || true) | awk '/^Pages:/{print $2}')"
    undef="$(grep -c -E 'Reference .* undefined|Citation .* undefined' ".github/build/$stem/$stem.log" || true)"
    [ "${undef:-0}" -gt 0 ] && st=WARN
    if [ -n "$limit" ] && [ -n "$pages" ] && [ "$pages" -gt "$limit" ]; then st=OVER; fi
  fi
  printf '%-32s %-6s %6s %6s %6s  %s\n' "$stem" "$st" "${pages:--}" "${limit:--}" "$undef" \
    "$( [ -f ".github/pdf/$stem.pdf" ] && echo ".github/pdf/$stem.pdf" || echo -)"
  [ -z "$SUMMARY" ] || printf '| %s | %s | %s | %s | %s |\n' "$stem" "$st" "${pages:--}" "${limit:--}" "$undef" >> "$SUMMARY"
done
[ ${#FAILED[@]} -eq 0 ] || die "${#FAILED[@]} entr$( [ ${#FAILED[@]} -eq 1 ] && echo y || echo ies) failed: ${FAILED[*]}"
