# What is fact and what is editorial

Most of this repository is sourced record. Some of it is an editorial construct,
and the two should not be confused.

## Fact

- **The text.** Extracted from the National Archives transcripts, original
  orthography intact — *defence*, *chuse*, *Article. I.* Not retyped.
- **The dates.** Parsed from the Archives' own "Passed by Congress … Ratified …"
  lines, preserved verbatim in `data/amendments.json`.
- **What each amendment superseded.** The Archives transcript links every
  superseded passage to the amendment that superseded it. Those links, not an
  editorial judgment, decide the contents of `data/edits.json`.
- **Authorship**, to the extent any source establishes it, with a citation per
  name and the disputes recorded in [authorship.md](authorship.md).

## Editorial

- **The integrated text is a construct.** The real parchment is unaltered; the
  National Archives appends amendments and never merges them into the articles.
  Here, an amendment strikes the text it superseded, so that `git blame` can
  answer "what changed this clause". `git show signed-1787:` returns the 1787
  document intact.
- **Strike versus replace.** Where an amendment supplies directly substitutable
  words — the 17th's "elected by the people" for "chosen by the Legislature" —
  the text is replaced. Where it does not, the passage is struck and the new
  operative text lives in its amendment file. Neither is how a court reads the
  document.
- **Punctuation repair.** Striking a clause out of a list strands its separators.
  `tidy()` in `build_history.py` repairs them, and `verify.py` asserts no repaired
  file contains a punctuation pattern the 1787 text lacked. The repairs are
  cosmetic but they *are* changes to the text.
- **Repeal as deletion.** The 18th Amendment is absent from `amendments/` at HEAD
  because the 21st repealed it, recorded as a literal `git revert`. Printed
  editions keep the 18th with a note. Its text remains permanently reachable at
  the `amendment-18` tag.
- **Committer identity.** Merges are committed by `The several States`. Real
  amendments were certified by a named officer — the Secretary of State, later
  the Administrator of General Services, later the Archivist. Those names are not
  in the dataset, so the ratifying body stands in rather than a guess.
- **The `-0500` timezone** on every commit, and noon as the hour. Neither is a
  historical claim.
- **Day of week.** The +1000 year offset preserves month and day but not weekday:
  17 September 1787 was a Monday, and 2787-09-17 is a Thursday.

## Deliberately absent

Ratifying-state detail — which state was decisive, and the count — is not in the
dataset. It is in the GPO *Constitution Annotated* ratification tables and could
be added, but guessing it from memory would put unsourced facts in a repository
whose whole claim is that it does not contain any.

## Rebuilding

`main` is generated output, not a working branch. `scripts/build_history.py`
rebuilds it from `data/` and `sources/`, and the result is force-pushed; commit
hashes change on every rebuild. Development happens on `workshop`.
