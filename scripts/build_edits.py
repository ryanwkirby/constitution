#!/usr/bin/env python3
"""Derive data/edits.json -- what each amendment did to the text.

The National Archives transcript links every superseded passage to the amendment
that superseded it. Those links are the authority for *what* was struck. This
script locates each passage in sources/ and records the exact matched substring.

Replacement wording (`insert`) is entered by hand from the amendment's own text,
and only where the amendment supplies directly substitutable words. Where it does
not, the strike is a pure deletion and the new operative text lives in the
amendment file -- which is how the document actually works.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Amendment -> replacement wording, drawn from that amendment's own text.
# Keyed by the first 40 chars of the struck passage, since some amendments strike
# more than one passage and only some strikes have a substitute.
INSERTS = {
    "chosen by the Legislature": "elected by the people",
    # The surrounding text already reads "such Meeting shall be on ...", so the
    # substitute drops the 20th's own leading "noon on" to avoid "be on noon on".
    "the first Monday in December": "the 3d day of January",
    "Representatives and direct Taxes shall be": (
        "Representatives shall be apportioned among the several States according to "
        "their respective numbers, counting the whole number of persons in each State, "
        "excluding Indians not taxed."),
}

# Changes the Archives records in prose rather than as inline links: amendments
# that amended *amendments*, and the amendment that added and then lost an article.
EXTRA = [
    {"amendment": 26, "file": "amendments/amendment-14.md",
     "strike": "twenty-one years", "insert": "eighteen years", "count": 2,
     "note": ("Section 1 of the 26th modified Section 2 of the 14th. Section 2 "
              "states the age qualification twice; the 26th lowered both."),
     "source": "https://www.archives.gov/founding-docs/amendments-11-27"},
]


def flexible(needle):
    """Match a passage across the semantic line breaks ventilation introduced."""
    return re.compile(r"\s+".join(re.escape(w) for w in needle.split()))


def main():
    meta = json.loads((ROOT / "sources" / "archives-metadata.json").read_text())
    files = sorted((ROOT / "sources" / "constitution").glob("*.md"))
    edits, unmatched = [], []

    for s in meta["superseded"]:
        pat = flexible(s["text"])
        hits = [(f, m) for f in files for m in [pat.search(f.read_text(encoding="utf-8"))] if m]
        if len(hits) != 1:
            unmatched.append((s["amendment"], s["text"][:60], len(hits)))
            continue
        f, m = hits[0]
        matched = m.group(0)
        insert = None
        for key, val in INSERTS.items():
            if s["text"].startswith(key):
                insert = val
                break
        edits.append({
            "amendment": s["amendment"],
            "file": f"constitution/{f.name}",
            "strike": matched,
            "insert": insert,
            "source": meta["sources"]["constitution"],
        })

    for e in EXTRA:
        path = ROOT / "sources" / e["file"].replace("amendments/", "amendments/")
        text = path.read_text(encoding="utf-8")
        expected = e.get("count", 1)
        if text.count(e["strike"]) != expected:
            unmatched.append((e["amendment"], e["strike"], text.count(e["strike"])))
            continue
        edits.append(e)

    edits.sort(key=lambda e: (e["amendment"], e["file"]))
    (ROOT / "data" / "edits.json").write_text(
        json.dumps(edits, indent=2) + "\n", encoding="utf-8")

    print(f"{len(edits)} edits across {len(set(e['amendment'] for e in edits))} amendments")
    for e in edits:
        kind = "replace" if e.get("insert") else "delete "
        n = f" x{e['count']}" if e.get("count", 1) > 1 else ""
        print(f"  Amdt {e['amendment']:>2}  {kind}  {e['file']:<32} {e['strike'][:48]!r}{n}")
    if unmatched:
        print("\nUNMATCHED (must be zero):")
        for a, t, n in unmatched:
            print(f"  Amdt {a}: {n} matches for {t!r}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
