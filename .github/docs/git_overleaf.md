# Git and Overleaf

Every Overleaf project has a git URL. With it, your laptop pulls from and pushes to Overleaf directly. The link is optional; `make -f .github/Makefile live` uses it when the remote `overleaf` exists.
Most papers sync through GitHub instead: [workflow.md](workflow.md).
Use this link or Overleaf's GitHub Sync. Using both adds extra merge commits.

```
 Overleaf (master)  <-- sync_overleaf.sh -->  laptop (main)  -- push -->  GitHub (main), a backup
```

## Without a paid plan

Git access to Overleaf needs a paid or institutional plan. Without one, download `template-for-overleaf.zip` from [the template's Releases page](https://github.com/omidmirza/paper-template/releases/latest), and on Overleaf choose New Project > Upload Project. After each laptop build, upload the changed files of `figures/auto/` to the same folder on Overleaf.

## Set up

1. On Overleaf: Account Settings, Git integration, create a token. The token is your git password. Copy it.
2. Store the token on your computer. Git asks for it once: user `git`, password the token.
   ```bash
   git config --global credential.helper osxkeychain      # macOS
   git config --global credential.helper libsecret        # Linux desktop
   ```
3. Copy the project URL from Overleaf: Menu, Sync, Git. Then:
   ```bash
   git clone https://git@git.overleaf.com/<project-id> my-paper && cd my-paper
   bash .github/tools/setup_git.sh --github git@github.com:<user>/<repo>.git     # GitHub is optional
   ```
   Running `setup_git.sh` again does no harm. If you already have a local copy, run
   `bash .github/tools/setup_git.sh --overleaf <url>`, then once
   `bash .github/tools/sync_overleaf.sh --allow-unrelated`, and resolve any conflicts (see Conflicts below).
4. For the figures, run `python3 -m venv .github/.venv` and `.github/.venv/bin/pip install -r .github/python/requirements.txt`,
   or set `PAPERKIT_PYTHON` to a Python that has these packages.

## Every day

```bash
bash .github/tools/sync_overleaf.sh     # get the co-authors' edits
make -f .github/Makefile                # after your edits: build and redraw the figures
git add -A && git commit -m "Results: shorter discussion"
bash .github/tools/sync_overleaf.sh     # send your commits to Overleaf and GitHub
```

Commit first. The script stops if tracked files have uncommitted changes.
It merges Overleaf's edits through a branch `overleaf-YYYY-MM-DD-HHMM`, which stays only if there is a conflict. It never force-pushes.
Options: `--no-push`, `--no-github`.

## Live mode

| Command | Effect |
|---|---|
| `make -f .github/Makefile watch` | rebuilds on every save and commits new figures; nothing leaves the laptop |
| `make -f .github/Makefile live` | as `watch`, and also pulls before each build and pushes the new figures and changed `.tex` files (to `overleaf` if that remote exists, else to `origin`) |

Stop either with Ctrl-C. With the Overleaf link, `live` runs on `main` only.
If a pull fails or a merge has conflicts, it prints one line and waits until you commit.

## Conflicts

The script stops and lists the files. For each file:

```bash
$EDITOR sections/results.tex        # keep the right text; delete the <<<<<<<, |||||||, ======= and >>>>>>> lines and the text you drop
#   or take one side:  git checkout --theirs <file>  (Overleaf)  |  git checkout --ours <file>  (yours)
git add sections/results.tex
git commit --no-edit                # finishes the merge
bash .github/tools/sync_overleaf.sh     # pushes the result
```

To cancel the merge: `git merge --abort`. The Overleaf edits stay on the dated branch.
For fewer conflicts, write one sentence per line and tell the others which section you edit.

## What to commit

| Commit | Never commit |
|---|---|
| `.tex` and `.bib` files, `figures/src/*.py`, `figures/data/` | `.github/build/`, `.github/pdf/`, `.github/releases/` |
| `figures/auto/*.pdf` and `*.json` (Overleaf cannot draw figures) | `*.aux *.log *.fls *.fdb_latexmk *.synctex.gz *.afg *.bbl` |
| `refs/extended_labels.tex` | tokens, `.env`, files over 50 MB |

`setup_git.sh` installs a check that runs before each commit. It refuses build files, conflict markers,
files over 50 MB and figures that break the rules. To skip it once: `git commit --no-verify`.
