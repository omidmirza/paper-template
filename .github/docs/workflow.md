# Workflow

There are three copies of the paper: on Overleaf, on GitHub and on your laptop. Changes usually go through GitHub; [git_overleaf.md](git_overleaf.md) links the laptop to Overleaf directly.

| Who | Edits on | Syncs with |
|---|---|---|
| co-authors | Overleaf | Menu > GitHub on Overleaf: "Push Overleaf changes to GitHub" and "Pull GitHub changes into Overleaf" |
| you | your laptop | `git pull`, `make -f .github/Makefile`, `git push` |

Reviewers comment on pull requests on GitHub.

Overleaf's GitHub Sync needs a paid or institutional plan, such as the ETH plan.
[team.md](team.md) covers working with several co-authors.

## Start

- With GitHub Sync: on GitHub, press "Use this template". On Overleaf: New Project, Import from GitHub.
- Without it: download `template-for-overleaf.zip` from [the template's Releases page](https://github.com/omidmirza/paper-template/releases/latest). On Overleaf: New Project, Upload Project.

Then fill in `setup.tex` and press Recompile. `main.tex` builds the review copy.
To build one version, open its file in `versions/` and press Recompile.

On a laptop, run make from the top folder. `make -f .github/Makefile help` lists the targets.
PDFs go to `.github/pdf/`, all other build files to `.github/build/`. Git ignores both.
`latexmk -pdf versions/<name>.tex` also builds into `.github/build/<name>/`, without redrawing the figures.

## Every day

```bash
git pull                        # get the co-authors' Overleaf edits
make -f .github/Makefile data   # new results into figures/data/
make -f .github/Makefile        # redraw figures, build every PDF
git add -A && git commit -m "Results: new runs" && git push
```

Then press "Pull GitHub changes into Overleaf".
Always commit `figures/auto/`, since Overleaf cannot run Python.

## More commands

| Command | Effect |
|---|---|
| `make -f .github/Makefile live` | pulls, rebuilds on every save, redraws figures whose size changed, and commits and pushes them with the changed `.tex` files |
| `make -f .github/Makefile release TAG=v1-arxiv` | builds all PDFs and a checked arXiv zip, and tags the commit `v1-arxiv` |
| `make -f .github/Makefile diff OLD=v1-conference ENTRY=versions/conference.tex` | builds the conference PDF with the changes since that tag marked (without ENTRY: the arXiv version) |

With a direct git link ([git_overleaf.md](git_overleaf.md)), `live` pulls Overleaf edits itself; through GitHub they arrive only after someone presses "Push Overleaf changes to GitHub".
Use either Overleaf's GitHub Sync or the direct git link. Both together work, but add extra merge commits.

GitHub builds every PDF on each push (`.github/workflows/build.yml`).
To type less, put `alias pmake='make -f .github/Makefile'` in your shell profile.
