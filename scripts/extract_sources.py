#!/usr/bin/env python3
"""Build sources/ from National Archives transcripts.

Text provenance lives here so it is reproducible rather than hand-typed. The
Archives transcripts preserve original orthography ("defence", "chuse",
"Article. I.") and mark every superseded passage with a link to the amendment
that superseded it -- we harvest both.

Usage:  scripts/extract_sources.py [cache-dir]

Downloads the transcripts if the cache is empty, so a clean checkout can
regenerate sources/ from scratch.
"""
import html
import json
import pathlib
import re
import sys
import urllib.request

PAGES = {
    "const.html": "https://www.archives.gov/founding-docs/constitution-transcript",
    "bor.html": "https://www.archives.gov/founding-docs/bill-of-rights-transcript",
    "amd.html": "https://www.archives.gov/founding-docs/amendments-11-27",
}

ROMAN = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
    "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
    "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20, "XXI": 21,
    "XXII": 22, "XXIII": 23, "XXIV": 24, "XXV": 25, "XXVI": 26, "XXVII": 27,
}

ROOT = pathlib.Path(__file__).resolve().parent.parent


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def ventilate(para):
    """One sentence per line ("semantic line breaks").

    Legal prose is sentence-structured, so an amendment that rewrites one
    sentence touches exactly one line. Wrapping at a column count instead would
    reflow the remainder of the paragraph and make `git blame` attribute
    untouched text to the amending commit -- i.e. lie.
    """
    parts = re.split(r"(?<=[.?!])\s+(?=[A-Z\"'])", para)
    out = []
    for p in parts:
        # Enumerated-powers clauses are single sentences hundreds of words long;
        # semicolons are their real structural boundary.
        if len(p) > 220 and "; " in p:
            chunks = p.split("; ")
            out.extend(c + ";" for c in chunks[:-1])
            out.append(chunks[-1])
        else:
            out.append(p)
    return [o.strip() for o in out if o.strip()]


def parse_constitution(raw):
    body = raw[raw.find("We the People"):raw.find("Attest")]

    superseded = []
    for m in re.finditer(r'<a href="[^"]*#toc-amendment-([ivx]+)"[^>]*>(.*?)</a>', body, re.S | re.I):
        superseded.append({
            "amendment": ROMAN[m.group(1).upper()],
            "text": strip_tags(m.group(2)),
        })

    articles, cur_art, cur_sec = {}, None, None
    token = re.compile(r"<h[23][^>]*>(.*?)</h[23]>|<p[^>]*>(.*?)</p>", re.S | re.I)
    for m in token.finditer(body):
        head, para = m.group(1), m.group(2)
        if head is not None:
            t = strip_tags(head)
            a = re.match(r"Article\.?\s+([IVX]+)\.?$", t, re.I)
            s = re.match(r"Section\.?\s+(\d+)\.?$", t, re.I)
            if a:
                cur_art = ROMAN[a.group(1).upper()]
                articles.setdefault(cur_art, [])
                cur_sec = None
            elif s and cur_art:
                cur_sec = int(s.group(1))
                articles[cur_art].append(("section", cur_sec))
        elif para is not None and cur_art:
            t = strip_tags(para)
            if t:
                articles[cur_art].append(("para", t))
    return articles, superseded


def parse_amendments(raw, numbers):
    """Pull each amendment's text, sections, and 'Passed by Congress' line.

    The two Archives pages differ: the Bill of Rights uses plain
    "<h3>Amendment I</h3>", amendments 11-27 use
    "<h2><a id="xiii"></a>AMENDMENT XIII</h2>" with "Section N." subheadings.
    Normalise both by matching on heading *text* rather than markup.
    """
    heading = re.compile(r"<h[1-4][^>]*>(.*?)</h[1-4]>|<p[^>]*>(.*?)</p>", re.S | re.I)
    amd_re = re.compile(r"^AMENDMENT\s+([IVX]+)\.?$", re.I)
    sec_re = re.compile(r"^Section\.?\s+(\d+)\.?$", re.I)

    out, cur = {}, None
    for m in heading.finditer(raw):
        head, para = m.group(1), m.group(2)
        if head is not None:
            t = strip_tags(head)
            a = amd_re.match(t)
            if a:
                num = ROMAN[a.group(1).upper()]
                cur = num if num in numbers else None
                if cur:
                    out[cur] = {"blocks": [], "dates_line": None}
                continue
            s = sec_re.match(t)
            if s and cur:
                out[cur]["blocks"].append(("section", int(s.group(1))))
        elif para is not None and cur:
            t = strip_tags(para)
            if not t:
                continue
            if re.search(r"(Passed by Congress|Originally proposed)", t):
                out[cur]["dates_line"] = t
            elif t.startswith("Note:"):
                # Archives editorial apparatus, not amendment text -- but it is
                # the Archives' own statement of what this amendment modified,
                # so keep it as metadata.
                out[cur].setdefault("notes", []).append(t[len("Note:"):].strip())
            else:
                out[cur]["blocks"].append(("para", t))
    return out


def fetch(cache):
    cache.mkdir(parents=True, exist_ok=True)
    for name, url in PAGES.items():
        dest = cache / name
        if dest.exists() and dest.stat().st_size > 1000:
            continue
        print(f"fetching {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            dest.write_bytes(r.read())


def main():
    cache = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / ".build" / "cache")
    fetch(cache)
    const_raw = (cache / "const.html").read_text(encoding="utf-8", errors="replace")
    bor_raw = (cache / "bor.html").read_text(encoding="utf-8", errors="replace")
    amd_raw = (cache / "amd.html").read_text(encoding="utf-8", errors="replace")

    articles, superseded = parse_constitution(const_raw)
    cdir = ROOT / "sources" / "constitution"
    cdir.mkdir(parents=True, exist_ok=True)

    pre = strip_tags(re.search(r"(We the People.*?)</p>", const_raw, re.S).group(1))
    (cdir / "00-preamble.md").write_text(
        "# Preamble\n\n" + "\n".join(ventilate(pre)) + "\n", encoding="utf-8")

    numerals = {v: k for k, v in ROMAN.items()}
    for num in sorted(articles):
        lines = [f"# Article {numerals[num]}", ""]
        for kind, val in articles[num]:
            if kind == "section":
                lines += [f"## Section {val}", ""]
            else:
                lines += ventilate(val) + [""]
        (cdir / f"article-{num:02d}.md").write_text(
            "\n".join(lines).rstrip() + "\n", encoding="utf-8")

    bor = parse_amendments(bor_raw, set(range(1, 11)))
    rest = parse_amendments(amd_raw, set(range(11, 28)))
    adir = ROOT / "sources" / "amendments"
    adir.mkdir(parents=True, exist_ok=True)
    allamd = {**bor, **rest}
    for num, data in sorted(allamd.items()):
        lines = [f"# Amendment {numerals[num]}", ""]
        for kind, val in data["blocks"]:
            if kind == "section":
                lines += [f"## Section {val}", ""]
            else:
                lines += ventilate(val) + [""]
        (adir / f"amendment-{num:02d}.md").write_text(
            "\n".join(lines).rstrip() + "\n", encoding="utf-8")

    # The Bill of Rights page states its ratification date in prose rather than
    # in a "Passed by Congress ... Ratified ..." line. Capture that sentence so
    # amendments 1-10 are sourced verbatim like every other amendment.
    bor_text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", bor_raw)))
    m = re.search(r"[^.]*ratified by three-fourths of the state legislatures on "
                  r"December 15, 1791\.", bor_text)
    bor_line = m.group(0).strip() if m else None
    if not bor_line:
        raise SystemExit("could not find the Bill of Rights ratification sentence")

    (ROOT / "sources" / "archives-metadata.json").write_text(json.dumps({
        "superseded": superseded,
        "bill_of_rights_line": bor_line,
        "date_lines": {str(n): d["dates_line"] for n, d in sorted(allamd.items())},
        "notes": {str(n): d.get("notes", []) for n, d in sorted(allamd.items())
                  if d.get("notes")},
        "sources": {
            "constitution": "https://www.archives.gov/founding-docs/constitution-transcript",
            "bill_of_rights": "https://www.archives.gov/founding-docs/bill-of-rights-transcript",
            "amendments_11_27": "https://www.archives.gov/founding-docs/amendments-11-27",
        },
    }, indent=2) + "\n", encoding="utf-8")

    print(f"articles: {len(articles)}  amendments: {len(allamd)}  "
          f"superseded passages: {len(superseded)}")


if __name__ == "__main__":
    main()
