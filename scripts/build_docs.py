#!/usr/bin/env python3
"""Generate the data-driven docs so they cannot drift from data/.

docs/authorship.md and docs/method.md are prose and are maintained by hand.
"""
import datetime
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI",
         "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI",
         "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII"]


def full_years(a, b):
    a, b = datetime.date.fromisoformat(a), datetime.date.fromisoformat(b)
    return b.year - a.year - ((b.month, b.day) < (a.month, a.day))


def main():
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    amendments = json.loads((ROOT / "data" / "amendments.json").read_text())
    edits = json.loads((ROOT / "data" / "edits.json").read_text())
    unratified = json.loads((ROOT / "data" / "unratified.json").read_text())
    by_num = {a["number"]: a for a in amendments}

    # ---- dates -------------------------------------------------------
    rows = ["| # | Amendment | Proposed | Ratified | Gap | Git timestamp |",
            "| --- | --- | --- | --- | --- | --- |"]
    for a in amendments:
        gap = full_years(a["proposed"], a["ratified"])
        rows.append(
            f"| {a['number']} | {a['title']} | {a['proposed']} | {a['ratified']} | "
            f"{gap} yr{'s' if gap != 1 else ''} | {int(a['ratified'][:4]) + 1000}"
            f"{a['ratified'][4:]} |")
    (docs / "dates.md").write_text(f"""# Dates

Every date here comes from the National Archives' own
"Passed by Congress … Ratified …" line for each amendment, parsed rather than
retyped. The Archives wording is preserved verbatim in
`data/amendments.json` as `archives_date_line`.

## The +1000 year offset

Git cannot store these dates. Its date parser (`date.c`, `tm_to_time_t`) accepts
only years 1970–2099, so `--date="1787-09-17"` is rejected outright. The raw
`@<seconds>` form bypasses that parser, but a pre-1970 value is parsed as
*unsigned* and wraps to nonsense — so dates in the past are not merely awkward,
they are unrepresentable.

Dates in the future are ordinary positive integers. So every git timestamp in
this repository is **the real date plus exactly 1000 years**, at noon, `-0500`:

    1787-09-17  ->  2787-09-17
    1992-05-07  ->  2992-05-07

One constant, applied to every commit without exception. Month, day and ordering
are exact, and subtracting 1000 recovers the truth. The offset is computed per
date rather than as a fixed number of seconds, so leap years stay correct, and
noon is the anchor so the UTC rendering never rolls onto an adjacent day.

The real dates are never faked. They travel in every commit's trailers
(`Proposed-Date`, `Ratified-Date`, `Git-Date-Offset`), `scripts/timeline` prints
the true chronology, and `scripts/verify.py` asserts that every commit's
timestamp is exactly its trailer date plus 1000 years.

This is the one place this repository knowingly writes something untrue, and it
does so uniformly, reversibly, and with the truth alongside it.

## The record

{chr(10).join(rows)}
""", encoding="utf-8")

    # ---- superseded --------------------------------------------------
    lines = ["# What each amendment changed", "",
             "The National Archives transcript links every superseded passage to the",
             "amendment that superseded it. Those links are the authority for this table;",
             "`scripts/build_edits.py` locates each passage in the text and records the",
             "exact substring, and `scripts/verify.py` asserts that no passage listed here",
             "survives in `constitution/` at HEAD.", "",
             "| Amendment | File | Struck | Replaced with |",
             "| --- | --- | --- | --- |"]
    for e in sorted(edits, key=lambda e: e["amendment"]):
        struck = e["strike"].replace("\n", " ")
        struck = (struck[:70] + "…") if len(struck) > 70 else struck
        ins = e.get("insert")
        ins = ((ins[:50] + "…") if ins and len(ins) > 50 else ins) or "*(deleted)*"
        n = f" ×{e['count']}" if e.get("count", 1) > 1 else ""
        lines.append(f"| {ROMAN[e['amendment']]} | `{e['file']}` | {struck}{n} | {ins} |")
    lines += ["", "## Not in the table", "",
              "- **Amendment XVIII** added no text to the original articles; it stood on",
              "  its own and was repealed entire by **Amendment XXI**, which the history",
              "  records as a literal `git revert`. Its text is gone from `amendments/` at",
              "  HEAD and permanently reachable at the `amendment-18` tag.",
              "- **Amendment XXVI** amended *Amendment XIV*, not the original text — the",
              "  one case where an amendment edits another amendment's file.",
              "- **Amendment XX** superseded part of Amendment XII as well as Article I;",
              "  the Archives records that in prose rather than inline markup, so it is",
              "  noted here rather than applied as an edit."]
    (docs / "superseded.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- unratified --------------------------------------------------
    lines = ["# The six that never made it", "",
             "Each is a branch that was never merged, and an open pull request.", ""]
    for u in unratified:
        lines += [f"## {u['title']}", "",
                  f"- **Proposed** {u['proposed']} by {u['author']}",
                  f"- **Branch** `proposed/{u['slug']}`",
                  f"- **Source** {u['source']}", "", u["status"], "",
                  "> " + u["text"].replace("\n\n", "\n> \n> "), ""]
    (docs / "unratified.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("wrote docs/dates.md, docs/superseded.md, docs/unratified.md")


if __name__ == "__main__":
    main()
