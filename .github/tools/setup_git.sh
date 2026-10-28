#!/usr/bin/env bash
# setup_git.sh - make the paper folder a git repository with Overleaf and, optionally, GitHub as remotes.
# Usage: bash .github/tools/setup_git.sh [--overleaf URL] [--github URL] [--push]
#   URLs look like https://git@git.overleaf.com/<project-id> and git@github.com:<user>/<repo>.git
#   It runs git init -b main if needed and renames a cloned Overleaf remote `origin` to `overleaf` and the
#   branch master to main. It adds or updates the remotes `overleaf` and `origin` (GitHub), adds patterns for
#   build files in the top folder to .git/info/exclude (this clone only) and installs the pre-commit check.
#   Running it again is safe.
#   --push   make a first commit if there is none, and push main to both remotes (Overleaf: master)

set -euo pipefail
PK_NAME=setup_git
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

OVERLEAF=""; GITHUB=""; PUSH=0
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) pk_usage; exit 0 ;;
    --overleaf) OVERLEAF="${2:?--overleaf needs a URL}"; shift ;;
    --github) GITHUB="${2:?--github needs a URL}"; shift ;;
    --push) PUSH=1 ;;
    *) die "unknown argument $1 (see --help)" ;;
  esac
  shift
done

ROOT="$(pk_find_root)"
cd "$ROOT"
command -v git >/dev/null || die "git not found"

# 1. Repository and branch main.
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  git init -q -b main 2>/dev/null || { git init -q && git symbolic-ref HEAD refs/heads/main; }
  log "git init (branch main) in $ROOT"
fi
TOP="$(git rev-parse --show-toplevel)"

# 2. A clone of the Overleaf project has origin = Overleaf and branch master: rename both.
if git remote get-url origin >/dev/null 2>&1 && git remote get-url origin | grep -q 'git\.overleaf\.com'; then
  if git remote get-url overleaf >/dev/null 2>&1; then die "both origin and overleaf point to Overleaf; remove one"; fi
  git remote rename origin overleaf; log "renamed remote origin -> overleaf"
fi
if [ "$(git symbolic-ref --short HEAD 2>/dev/null || true)" = master ] && ! git show-ref -q --verify refs/heads/main; then
  git branch -m master main; log "renamed local branch master -> main (Overleaf keeps master)"
fi

# 3. Remotes (add or update).
set_remote() {
  if git remote get-url "$1" >/dev/null 2>&1; then git remote set-url "$1" "$2"; log "remote $1 updated: $2"
  else git remote add "$1" "$2"; log "remote $1 added: $2"; fi
}
[ -z "$OVERLEAF" ] || set_remote overleaf "$OVERLEAF"
[ -z "$GITHUB" ] || set_remote origin "$GITHUB"
git config pull.rebase false          # git pull merges and never rewrites shared history
git config merge.conflictstyle diff3  # conflicts show the common ancestor too

# 4. Builds write to .github/ (see .github/.gitignore). An editor that runs pdflatex in the top folder, or
#    Finder, can still leave files there. Ignore them in .git/info/exclude: it applies to this clone only
#    and adds no file to the top folder.
EXCLUDE="$(git rev-parse --git-path info/exclude)"
NEED="/*.aux /*.log /*.out /*.fls /*.fdb_latexmk /*.synctex.gz /*.afg /*.bbl /*.blg /*.pdf /*.spl comment.cut __pycache__/ .DS_Store"
mkdir -p "$(dirname "$EXCLUDE")"; touch "$EXCLUDE"
added=""
set -f   # the patterns are not file names here
for pat in $NEED; do
  grep -qxF -- "$pat" "$EXCLUDE" || { printf '%s\n' "$pat" >> "$EXCLUDE"; added="$added $pat"; }
done
set +f
[ -z "$added" ] && log "$EXCLUDE ok" || log "$EXCLUDE: added$added"

# 5. Pre-commit hook: a stub that runs .github/tools/hooks/pre-commit from the working tree.
HOOK_SRC="$PK_TOOLS/hooks/pre-commit"
[ -f "$HOOK_SRC" ] || die "missing $HOOK_SRC"
case "$HOOK_SRC" in
  "$TOP"/*) TARGET="\"\$(git rev-parse --show-toplevel)/${HOOK_SRC#"$TOP"/}\"" ;;
  *) TARGET="\"$HOOK_SRC\""; warn "hook lives outside the repo ($HOOK_SRC); copy the .github folder of the template into the paper" ;;
esac
HOOKS_DIR="$(git rev-parse --git-dir)/hooks"
if [ -n "$(git config --get core.hooksPath || true)" ]; then
  warn "core.hooksPath is set ($(git config --get core.hooksPath)): git ignores .git/hooks; add .github/tools/hooks/pre-commit there yourself"
else
  mkdir -p "$HOOKS_DIR"
  printf '#!/bin/sh\n# installed by .github/tools/setup_git.sh\nexec %s "$@"\n' "$TARGET" > "$HOOKS_DIR/pre-commit"
  chmod +x "$HOOKS_DIR/pre-commit" "$HOOK_SRC"
  log "pre-commit hook installed"
fi

# 6. Optional first push.
if [ "$PUSH" = 1 ]; then
  if ! git rev-parse -q --verify HEAD >/dev/null; then
    git add -A && git commit -q -m "Initial commit (paperkit)" && log "first commit"
  fi
  if git remote get-url overleaf >/dev/null 2>&1; then
    git push overleaf HEAD:master && log "pushed to overleaf (master)"
  fi
  if git remote get-url origin >/dev/null 2>&1; then
    git push -u origin HEAD:main && log "pushed to origin (main)"
  fi
fi

log "done. Remotes:"; git remote -v | sed 's/^/    /'
case "$(git remote get-url overleaf 2>/dev/null || true)" in
  *git.overleaf.com*) log "Overleaf asks for user 'git' and an Overleaf git token as the password. To save it so git does not ask again:"
    log "    git config --global credential.helper osxkeychain   # Linux: store or libsecret" ;;
esac
