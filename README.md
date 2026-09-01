# The Constitution of the United States

The U.S. Constitution as a git repository. Each amendment is a **branch**, created
on the day Congress proposed it and merged on the day the states ratified it — so
the document's history is the repository's history.

Run `git blame` on any clause and you get the amendment that last changed it, who
wrote it, and when.

```console
$ git blame constitution/article-01.md
Joseph L. Bristow  1913  ...composed of two Senators from each State, elected by the people thereof...

$ git log --format='%an proposed %ad · ratified %cd' -1 amendment-27
James Madison proposed 1789-09-25 · ratified 1992-05-07

$ git branch --no-merged main
proposed/corwin  proposed/era  proposed/child-labor  ...
```

Inspired by [JesseKPhillips/USA-Constitution](https://github.com/JesseKPhillips/USA-Constitution),
which had the original idea of letting `git log -p` show what an amendment actually
did to the text. This is a rebuild of that idea on a sourced dataset.

### What this one does

- **Real dates, from the National Archives.** Proposal, ratification and the
  Archives' own wording travel in every commit's trailers. Git cannot store a year
  before 1970, so the timestamps carry a uniform, documented **+1000 years**;
  `scripts/timeline` prints the true chronology. Nothing is approximated — see
  [docs/dates.md](docs/dates.md).
- **Researched authorship.** One `Author` per amendment with a cited role,
  co-sponsors as `Co-Authored-By`. Where credit is genuinely contested — the 13th,
  the 19th, the 26th — the dispute is recorded rather than resolved:
  [docs/authorship.md](docs/authorship.md).
- **Article V as branch → merge.** Proposal and ratification are separate events,
  which is why the 27th sits unmerged for 202 years, the 21st is a literal revert
  of the 18th, and the six never-ratified amendments are still-open pull requests.
- **Reproducible.** `build_history.py` regenerates the whole history from `data/`
  and `sources/`; `verify.py` ties every commit back to a cited date and fails if
  it cannot. A generator that is merely self-consistent proves nothing.

```console
scripts/extract_sources.py   # fetch the Archives transcripts -> sources/
scripts/build_history.py     # sources/ + data/ -> the git history
scripts/verify.py            # assert it matches the sourced record
```

### Sources

- [National Archives founding documents](https://www.archives.gov/founding-docs) —
  verbatim text, per-amendment proposal and ratification dates, and the inline
  markup identifying every superseded passage.
- [GPO *Constitution Annotated*](https://www.govinfo.gov/content/pkg/GPO-CONAN-REV-2014/pdf/GPO-CONAN-REV-2014-7.pdf)
  on govinfo — ratification tables.
- [Senate](https://www.senate.gov/artandhistory/) and
  [House](https://history.house.gov/) historical offices — sponsorship and
  floor history. Every date and name in `data/` carries its own source URL.

The integrated text is an editorial construct: the real parchment is unaltered and
amendments are appended, never merged in. [docs/method.md](docs/method.md) says what
is fact and what is editorial.
