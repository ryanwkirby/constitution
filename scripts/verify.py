#!/usr/bin/env python3
"""Assert the generated history is what the sourced data says it is.

A generator that is merely self-consistent proves nothing: it would happily
produce a plausible fabrication. These checks tie every commit back to a dated,
cited record, and fail loudly when they cannot.

Usage:  scripts/verify.py [path-to-generated-repo]
"""
import calendar
import datetime
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OFFSET_YEARS = 1000
TZ_SECONDS = -5 * 3600

failures = []


def check(ok, label, detail=""):
    if ok:
        print(f"  ok    {label}")
    else:
        print(f"  FAIL  {label}{(': ' + detail) if detail else ''}")
        failures.append(label)


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"git {' '.join(args)}: {r.stderr}")
    return r.stdout


def expected_epoch(datestr):
    d = datetime.date.fromisoformat(datestr)
    shifted = datetime.datetime(d.year + OFFSET_YEARS, d.month, d.day, 12, 0, 0)
    return calendar.timegm(shifted.timetuple()) - TZ_SECONDS


def main():
    repo = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".build" / "repo"
    if not (repo / ".git").exists():
        raise SystemExit(f"no generated repo at {repo}; run scripts/build_history.py first")

    amendments = json.loads((ROOT / "data" / "amendments.json").read_text())
    edits = json.loads((ROOT / "data" / "edits.json").read_text())
    unratified = json.loads((ROOT / "data" / "unratified.json").read_text())

    print("\nsources cited")
    missing = [a["number"] for a in amendments
               if not a["date_source"].startswith("http")
               or not a["author"]["source"].startswith("http")
               or any(not c["source"].startswith("http") for c in a["co_authors"])]
    check(not missing, "every date and name in data/amendments.json carries a source URL",
          f"amendments {missing}")
    check(all(u["source"].startswith("http") for u in unratified),
          "every unratified amendment carries a source URL")

    print("\ngit dates are exactly the real date plus 1000 years")
    log = git(repo, "log", "--all", "--format=%H%x1f%at%x1f%ct%x1f%B%x1e")
    bad_dates, checked = [], 0
    for entry in log.split("\x1e"):
        if not entry.strip():
            continue
        sha, at, ct, body = entry.strip().split("\x1f", 3)
        def trailer(name):
            m = re.search(rf"^{name}:\s*(\d{{4}}-\d{{2}}-\d{{2}})\s*$", body, re.M)
            return m.group(1) if m else None
        prop, rat = trailer("Proposed-Date"), trailer("Ratified-Date")
        signed, real = trailer("Signed-Date"), trailer("Real-Date")
        want_a = prop or signed or real
        want_c = rat or signed or real or prop
        if not want_a:
            continue
        checked += 1
        if int(at) != expected_epoch(want_a):
            bad_dates.append(f"{sha[:8]} author {at} != {want_a}+{OFFSET_YEARS}y")
        if int(ct) != expected_epoch(want_c):
            bad_dates.append(f"{sha[:8]} committer {ct} != {want_c}+{OFFSET_YEARS}y")
    check(not bad_dates, f"all {checked} dated commits match their trailers",
          "; ".join(bad_dates[:3]))

    print("\nchronology")
    order = git(repo, "log", "--first-parent", "--format=%ct%x1f%s", "main").strip().split("\n")
    times = [int(l.split("\x1f")[0]) for l in order]
    check(times == sorted(times, reverse=True),
          "main's first-parent commit dates are monotonic")
    ratified = sorted(amendments, key=lambda a: a["ratified"])
    check(all(a["proposed"] <= a["ratified"] for a in amendments),
          "every amendment was proposed before it was ratified")

    print("\nthe text")
    head_const = {p.name: git(repo, "show", f"main:constitution/{p.name}")
                  for p in sorted((ROOT / "sources" / "constitution").glob("*.md"))}
    survived = []
    for e in edits:
        if not e["file"].startswith("constitution/"):
            continue
        name = e["file"].split("/", 1)[1]
        needle = " ".join(e["strike"].split())
        haystack = " ".join(head_const[name].split())
        if needle in haystack:
            survived.append(f"Amdt {e['amendment']}: {needle[:50]}")
    check(not survived, "no superseded passage survives in constitution/ at HEAD",
          "; ".join(survived[:3]))

    # The strong check: replay the declared edits onto the 1787 baseline and
    # require the result to equal HEAD byte for byte. A count-based heuristic
    # cannot catch a repair pass that quietly rewrites untouched text, because
    # such damage *reduces* the suspicious-pattern count. This does.
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_history import splice
    mismatched = []
    for name, head_text in head_const.items():
        text = git(repo, "show", f"signed-1787:constitution/{name}")
        for e in sorted((e for e in edits if e["file"] == f"constitution/{name}"),
                        key=lambda e: e["amendment"]):
            text = splice(text, e["strike"], e.get("insert"), e.get("count", 1))
        if text != head_text:
            mismatched.append(name)
    check(not mismatched,
          "HEAD is exactly the 1787 text with the declared edits applied, and nothing else",
          f"differs: {mismatched}")

    # Compare against the 1787 baseline rather than an absolute rule: Articles V
    # and VI legitimately have lines ending in a semicolon, because ventilation
    # split their long clauses there. Only *new* occurrences mean a deletion
    # stranded something.
    # Same replay for the amendment texts. The 26th edits Amendment XIV, so
    # amendments/ is not merely copied from sources/.
    tree_files = set(git(repo, "ls-tree", "-r", "--name-only", "main").split("\n"))
    amd_mismatch = []
    for src in sorted((ROOT / "sources" / "amendments").glob("*.md")):
        path = f"amendments/{src.name}"
        if path not in tree_files:
            continue
        text = src.read_text(encoding="utf-8")
        for e in sorted((e for e in edits if e["file"] == path),
                        key=lambda e: e["amendment"]):
            text = splice(text, e["strike"], e.get("insert"), e.get("count", 1))
        if text != git(repo, "show", f"main:{path}"):
            amd_mismatch.append(src.name)
    check(not amd_mismatch,
          "every amendment at HEAD is its source text with the declared edits applied",
          f"differs: {amd_mismatch}")

    # A substitution can introduce a duplicated word at its seam
    # ("shall be on noon on the 3d day"), which no punctuation rule catches.
    dupes = []
    for name, text in head_const.items():
        base = git(repo, "show", f"signed-1787:constitution/{name}")
        pat = r"\b(\w+)\s+\1\b"
        was = len(re.findall(pat, base, re.I))
        now = len(re.findall(pat, text, re.I))
        if now > was:
            dupes.append(f"{name} ({was} -> {now})")
    check(not dupes, "no edit introduced a duplicated word at its seam",
          "; ".join(dupes))

    stranded = []
    for name, text in head_const.items():
        base = git(repo, "show", f"signed-1787:constitution/{name}")
        for pat, why in [(r"[;,]\u2014\s*[;,]\u2014", "doubled separator"),
                         (r"[ \t]{2,}", "doubled space"),
                         (r"[,;]\s*$", "line ends in comma or semicolon"),
                         (r"[ \t]+[;,.]", "space before punctuation")]:
            now = len(re.findall(pat, text, re.M))
            was = len(re.findall(pat, base, re.M))
            if now > was:
                stranded.append(f"{name}: {why} ({was} -> {now})")
    check(not stranded, "no deletion stranded punctuation that the 1787 text lacked",
          "; ".join(stranded[:3]))

    print("\nstructure")
    branches = git(repo, "branch", "--no-merged", "main").split()
    expect = {f"proposed/{u['slug']}" for u in unratified}
    check(set(branches) == expect,
          f"exactly the {len(expect)} never-ratified amendments are unmerged",
          f"got {sorted(set(branches) ^ expect)}")
    tags = set(git(repo, "tag").split())
    want_tags = {f"amendment-{a['number']:02d}" for a in amendments}
    check(want_tags <= tags, "every ratified amendment is tagged",
          f"missing {sorted(want_tags - tags)}")
    # Exact path membership: sources/amendments/amendment-18.md legitimately
    # remains as source data, so a substring test would give a false positive.
    tree = git(repo, "ls-tree", "-r", "--name-only", "main").split("\n")
    check("amendments/amendment-18.md" not in tree,
          "the operative Eighteenth Amendment is absent at HEAD, having been repealed")
    check("amendment-18" in tags,
          "the Eighteenth Amendment is still reachable by tag")

    print()
    if failures:
        print(f"{len(failures)} check(s) failed\n")
        return 1
    print("all checks passed\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
