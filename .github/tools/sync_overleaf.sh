#!/usr/bin/env bash
# sync_overleaf.sh - merge the co-authors' Overleaf edits into your branch and push the result. It never force-pushes.
# Usage: bash .github/tools/sync_overleaf.sh [--no-push] [--no-github] [--allow-unrelated] [--remote overleaf]
#   1. Stops if tracked files have uncommitted changes (commit or stash them first).
#   2. Fetches Overleaf and saves its master on a branch overleaf-YYYY-MM-DD-HHMM.
#   3. Merges that branch into yours. On a conflict it stops and prints the next commands.
#   4. Pushes to Overleaf (master), then to origin if there is one.
#   --no-push           merge only, push nothing
#   --no-github         push to Overleaf only
#   --remote <name>     the Overleaf remote (default overleaf)
#   --allow-unrelated   for the first sync of a repository that did not start from the Overleaf project

set -euo pipefail
PK_NAME=sync
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

REMOTE=overleaf; PUSH=1; GITHUB=1; UNRELATED=()
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) pk_usage; exit 0 ;;
    --no-push) PUSH=0 ;;
    --no-github) GITHUB=0 ;;
    --allow-unrelated) UNRELATED=(--allow-unrelated-histories) ;;
    --remote) REMOTE="${2:?--remote needs a name}"; shift ;;
    *) die "unknown argument $1 (see --help)" ;;
  esac
  shift
done

git rev-parse --git-dir >/dev/null 2>&1 || die "not a git repository (run bash .github/tools/setup_git.sh)"
cd "$(git rev-parse --show-toplevel)"
git remote get-url "$REMOTE" >/dev/null 2>&1 || die "no remote '$REMOTE' (bash .github/tools/setup_git.sh --overleaf <url>)"
[ -e "$(git rev-parse --git-path MERGE_HEAD)" ] && die "a merge is in progress: finish it (git add <files>; git commit --no-edit) or git merge --abort"
BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null)" || die "detached HEAD: git switch main first"
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  git status --short --untracked-files=no >&2
  die "uncommitted changes (above). Commit them (git add -A && git commit -m \"...\") or stash them (git stash), then rerun."
fi

log "git fetch $REMOTE"
git fetch -q "$REMOTE"
if ! git rev-parse -q --verify "refs/remotes/$REMOTE/master" >/dev/null; then
  log "$REMOTE has no master yet: nothing to merge"
else
  STAMP="$(date +%Y-%m-%d-%H%M)"; OB="overleaf-$STAMP"; n=2
  while git show-ref -q --verify "refs/heads/$OB"; do OB="overleaf-$STAMP-$n"; n=$((n + 1)); done
  if git merge-base --is-ancestor "$REMOTE/master" HEAD; then
    log "no new Overleaf edits ($REMOTE/master is already in $BRANCH)"
  else
    git branch --no-track "$OB" "$REMOTE/master"
    log "branch $OB = $REMOTE/master ($(git log -1 --format='%h %an: %s' "$OB"))"
    MSG="Merge Overleaf edits of $(date '+%Y-%m-%d %H:%M') ($OB into $BRANCH)"
    if ! out="$(git merge --no-ff "${UNRELATED[@]+"${UNRELATED[@]}"}" -m "$MSG" "$OB" 2>&1)"; then
      if [ -z "$(git diff --name-only --diff-filter=U)" ]; then
        printf '%s\n' "$out" >&2
        git merge --abort 2>/dev/null || true; git branch -D "$OB" >/dev/null 2>&1 || true
        case "$out" in *unrelated*) die "histories are unrelated; if this is the first sync, rerun with --allow-unrelated" ;; esac
        die "merge of $OB failed (message above); nothing was changed"
      fi
      {
        echo
        echo "[sync] CONFLICT: the same lines were changed on Overleaf and here. Files:"
        git diff --name-only --diff-filter=U | sed 's/^/    /'
        echo "[sync] Next commands (for each file, use one of the first three):"
        echo "    \$EDITOR <file>                 # keep the right text; delete the <<<<<<<, |||||||, ======= and >>>>>>> lines and the text you drop"
        echo "    git checkout --theirs <file>    # or take Overleaf's version of the file"
        echo "    git checkout --ours <file>      # or keep your version of the file"
        echo "    git add <file>                  # for every file above"
        echo "    git commit --no-edit            # finishes the merge"
        echo "    bash .github/tools/sync_overleaf.sh      # pushes the result to Overleaf and GitHub"
        echo "[sync] To cancel the merge: git merge --abort   (branch $OB keeps the Overleaf edits)"
      } >&2
      exit 2
    fi
    log "merged: $MSG"
    git branch -d "$OB" >/dev/null   # merged; the merge commit message keeps the name
  fi
fi

if [ "$PUSH" = 1 ]; then
  log "git push $REMOTE HEAD:master"
  git push -q "$REMOTE" HEAD:master || die "push to $REMOTE rejected (probably a new edit on Overleaf): rerun bash .github/tools/sync_overleaf.sh"
  if [ "$GITHUB" = 1 ] && git remote get-url origin >/dev/null 2>&1; then
    log "git push origin HEAD:$BRANCH"
    git push -q origin "HEAD:$BRANCH" || die "push to origin rejected: git pull origin $BRANCH, then rerun"
  fi
fi
# Delete the dated branches of earlier conflicts once they are merged (git branch -d only, never -D).
git for-each-ref --format='%(refname:short)' --merged HEAD 'refs/heads/overleaf-*' | while IFS= read -r b; do
  git branch -d "$b" >/dev/null 2>&1 || true; done
log "in sync: $(git log -1 --format='%h %s')"
