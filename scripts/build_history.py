#!/usr/bin/env python3
"""Generate the constitutional git history into .build/repo.

Article V has two stages -- Congress proposes, the states ratify -- and git has
two of everything: two identities per commit, two dates, and branches that merge.
So an amendment is a branch created on the day it was proposed and merged on the
day it was ratified. The 27th sits unmerged for 202 years because that is what
happened.

  branch commit   author    = principal sponsor,      date = proposal
  merge commit    author    = principal sponsor,      date = proposal
                  committer = "The several States",   date = ratification

Every git timestamp is the real date plus exactly 1000 years, because git's date
parser rejects any year outside 1970-2099. Real dates are in the trailers.
"""
import calendar
import datetime
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / ".build" / "repo"

OFFSET_YEARS = 1000
TZ_SECONDS = -5 * 3600          # Washington standard time
TZ = "-0500"

ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI",
         "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI",
         "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII"]

STATES = ("The several States", "states@us.congress.historic.invalid")
SIGNED = "1787-09-17"
EFFECTIVE = "1789-03-04"
ARCHIVES = "https://www.archives.gov/founding-docs"


def git_epoch(datestr):
    """Real date -> git timestamp, shifted by exactly OFFSET_YEARS.

    Computed per-date rather than as a fixed second count so leap years stay
    correct. Anchored at noon so the UTC rendering never rolls to another day.
    """
    d = datetime.date.fromisoformat(datestr)
    shifted = datetime.datetime(d.year + OFFSET_YEARS, d.month, d.day, 12, 0, 0)
    return calendar.timegm(shifted.timetuple()) - TZ_SECONDS


def full_years(start, end):
    """Whole years elapsed, accounting for month and day.

    1789-09-25 to 1992-05-07 is 202 years, not the 203 that subtracting the
    year numbers would give.
    """
    a = datetime.date.fromisoformat(start)
    b = datetime.date.fromisoformat(end)
    return b.year - a.year - ((b.month, b.day) < (a.month, a.day))


def stamp(datestr):
    return f"@{git_epoch(datestr)} {TZ}"


def email(name):
    slug = "".join(c.lower() if c.isalnum() else "." for c in name)
    while ".." in slug:
        slug = slug.replace("..", ".")
    return f"{slug.strip('.')}@us.congress.historic.invalid"


def git(*args, env=None, check=True):
    e = dict(**{k: v for k, v in __import__("os").environ.items()})
    e.setdefault("GIT_CONFIG_GLOBAL", "/dev/null")
    if env:
        e.update(env)
    r = subprocess.run(["git", "-C", str(BUILD), *args], env=e,
                       capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(f"git {' '.join(args)} failed:\n{r.stdout}\n{r.stderr}")
    return r.stdout.strip()


def commit(message, author, adate, committer=None, cdate=None):
    an, ae = author
    cn, ce = committer or author
    git("commit", "-q", "--allow-empty", "-m", message, env={
        "GIT_AUTHOR_NAME": an, "GIT_AUTHOR_EMAIL": ae, "GIT_AUTHOR_DATE": stamp(adate),
        "GIT_COMMITTER_NAME": cn, "GIT_COMMITTER_EMAIL": ce,
        "GIT_COMMITTER_DATE": stamp(cdate or adate)})


def merge(branch, message, author, adate, committer, cdate):
    an, ae = author
    cn, ce = committer
    git("merge", "-q", "--no-ff", branch, "-m", message, env={
        "GIT_AUTHOR_NAME": an, "GIT_AUTHOR_EMAIL": ae, "GIT_AUTHOR_DATE": stamp(adate),
        "GIT_COMMITTER_NAME": cn, "GIT_COMMITTER_EMAIL": ce,
        "GIT_COMMITTER_DATE": stamp(cdate)})


def tag(name, message, datestr, tagger=STATES):
    tn, te = tagger
    git("tag", "-a", name, "-m", message, env={
        "GIT_COMMITTER_NAME": tn, "GIT_COMMITTER_EMAIL": te,
        "GIT_TAGGER_NAME": tn, "GIT_TAGGER_EMAIL": te,
        "GIT_COMMITTER_DATE": stamp(datestr), "GIT_TAGGER_DATE": stamp(datestr)})


def splice(text, strike, insert, count):
    """Replace a passage, repairing only the junction the removal creates.

    An earlier version ran a punctuation pass over the whole file and quietly
    rewrote text no amendment had touched -- turning a legitimate ventilated
    "...without due process of law;" into "...law." several clauses away from
    any edit. Repairs are therefore made only at the splice point, and
    verify.py reproduces HEAD from the 1787 baseline to prove nothing else moved.
    """
    for _ in range(count):
        i = text.index(strike)
        before, after = text[:i], text[i + len(strike):]
        if insert:
            text = before + insert + after
            continue
        # A deletion strands the separators that attached the clause to its list.
        m = re.search(r"([;,]\u2014|[;,])[ \t]*$", before)
        if m:
            sep = m.group(1)
            nxt = re.match(r"[ \t]*([;,]\u2014|[;,])", after)
            if nxt:
                # Two separators now adjacent: keep the first, drop the second.
                after = after[nxt.end():]
            elif re.match(r"[ \t]*(\n|$)", after):
                # The sentence was truncated: close it.
                before = before[:m.start()] + "."
        text = before + after
    # Collapse whitespace the removal doubled up, at the junction only.
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def apply_edits(edits):
    """Strike superseded text; insert the replacement where one exists."""
    for e in edits:
        path = BUILD / e["file"]
        text = path.read_text(encoding="utf-8")
        expected = e.get("count", 1)
        found = len(text.split(e["strike"])) - 1
        if found != expected:
            raise SystemExit(
                f"anchor for amendment {e['amendment']} matched {found} times, "
                f"expected {expected}: {e['strike'][:60]!r}")
        path.write_text(splice(text, e["strike"], e.get("insert"), expected),
                        encoding="utf-8")


def trailers(a, kind):
    lines = [f"Proposed-Date: {a['proposed']}"]
    if kind == "ratify":
        lines.append(f"Ratified-Date: {a['ratified']}")
    lines.append(f"Git-Date-Offset: +{OFFSET_YEARS} years")
    lines.append(f"Source: {a['date_source']}")
    for c in a["co_authors"]:
        lines.append(f"Co-Authored-By: {c['name']} <{email(c['name'])}>")
    return "\n".join(lines)


def main():
    amendments = json.loads((ROOT / "data" / "amendments.json").read_text())
    all_edits = json.loads((ROOT / "data" / "edits.json").read_text())
    unratified = json.loads((ROOT / "data" / "unratified.json").read_text())
    by_num = {a["number"]: a for a in amendments}
    edits_for = lambda n: [e for e in all_edits if e["amendment"] == n]

    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    git("init", "-q", "-b", "main")
    git("config", "user.name", STATES[0])
    git("config", "user.email", STATES[1])

    # ---- 1787: the Constitution as signed -------------------------------
    shutil.copytree(ROOT / "sources" / "constitution", BUILD / "constitution")
    git("add", "-A")
    commit(
        "The Constitution of the United States, as signed in Convention\n\n"
        "Done in Convention by the Unanimous Consent of the States present the\n"
        "Seventeenth Day of September in the Year of our Lord one thousand seven\n"
        "hundred and Eighty seven.\n\n"
        f"Signed-Date: {SIGNED}\n"
        f"Git-Date-Offset: +{OFFSET_YEARS} years\n"
        f"Source: {ARCHIVES}/constitution-transcript",
        ("Constitutional Convention", "convention@us.congress.historic.invalid"),
        SIGNED)
    tag("signed-1787", "The Constitution as signed, 17 September 1787", SIGNED,
        tagger=("Constitutional Convention", "convention@us.congress.historic.invalid"))
    tag("effective-1789", "In effect, 4 March 1789, the ninth State having ratified",
        EFFECTIVE)

    # ---- group amendments by the joint resolution that proposed them ----
    # The 1789 resolution proposed twelve articles. Ten became the Bill of
    # Rights, one became the 27th Amendment 202 years later, one is pending still.
    groups = [{"slug": "bill-of-rights", "label": "Bill of Rights",
               "numbers": list(range(1, 11)), "proposed": "1789-09-25",
               "ratified": "1791-12-15"}]
    groups += [{"slug": f"{n:02d}-{by_num[n]['title'].split(';')[0].lower().replace(' ', '-').replace(',', '')[:40]}",
                "label": f"Amendment {ROMAN[n]}", "numbers": [n],
                "proposed": by_num[n]["proposed"], "ratified": by_num[n]["ratified"]}
               for n in range(11, 28)]

    order_prop = sorted(groups, key=lambda g: (g["proposed"], g["numbers"][0]))
    order_rat = sorted(groups, key=lambda g: (g["ratified"], g["numbers"][0]))

    merged, created, sha = set(), {}, {}

    # The Twenty-first Amendment repealed the Eighteenth. That is a revert.
    REPEALS = {21: 18}

    def main_as_of(datestr):
        """Rewind to main as it stood when Congress proposed -- historically
        correct (Congress proposed against the text as it then was) and the
        reason these merges do not conflict."""
        eligible = [g for g in order_rat if g["ratified"] <= datestr and g["slug"] in merged]
        return "main" if eligible else git("rev-list", "--max-parents=0", "main")

    # Interleave proposals and ratifications in true chronological order.
    events = ([("propose", g, g["proposed"]) for g in groups]
              + [("ratify", g, g["ratified"]) for g in groups])
    events.sort(key=lambda e: (e[2], 0 if e[0] == "propose" else 1, e[1]["numbers"][0]))

    for kind, g, when in events:
        branch = f"proposed/{g['slug']}"
        if kind == "propose":
            git("checkout", "-q", "-b", branch, main_as_of(when))
            created[g["slug"]] = branch
            for n in g["numbers"]:
                a = by_num[n]
                if n in REPEALS:
                    git("revert", "--no-commit", sha[REPEALS[n]])
                (BUILD / "amendments").mkdir(exist_ok=True)
                shutil.copy(ROOT / "sources" / "amendments" / f"amendment-{n:02d}.md",
                            BUILD / "amendments" / f"amendment-{n:02d}.md")
                apply_edits(edits_for(n))
                git("add", "-A")
                commit(
                    f"Propose Amendment {ROMAN[n]} — {a['title']}\n\n"
                    + (f"{a['archives_note'][0]}\n\n" if a["archives_note"] else "")
                    + f"{a['author']['name']}: {a['author']['role']}\n\n"
                    + trailers(a, "propose")
                    + ("\n\nThis reverts Amendment XVIII, which it repeals."
                       if n in REPEALS else ""),
                    (a["author"]["name"], email(a["author"]["name"])), a["proposed"])
                sha[n] = git("rev-parse", "HEAD")
        else:
            git("checkout", "-q", "main")
            lead = by_num[g["numbers"][0]]
            nums = ", ".join(ROMAN[n] for n in g["numbers"])
            title = (f"Ratify the Bill of Rights — Amendments {ROMAN[g['numbers'][0]]}–{ROMAN[g['numbers'][-1]]}"
                     if len(g["numbers"]) > 1 else
                     f"Ratify Amendment {nums} — {lead['title']}")
            gap = full_years(g["proposed"], g["ratified"])
            body = (f"Ratified by three fourths of the several States.\n\n"
                    + (f"Proposed {g['proposed']}, ratified {g['ratified']} — {gap} years.\n\n"
                       if gap >= 5 else "")
                    + f"Proposed-Date: {g['proposed']}\nRatified-Date: {g['ratified']}\n"
                    + f"Git-Date-Offset: +{OFFSET_YEARS} years\nSource: {lead['date_source']}")
            merge(created[g["slug"]], f"{title}\n\n{body}",
                  (lead["author"]["name"], email(lead["author"]["name"])),
                  g["proposed"], STATES, g["ratified"])
            merged.add(g["slug"])
            for n in g["numbers"]:
                tag(f"amendment-{n:02d}",
                    f"Amendment {ROMAN[n]} — {by_num[n]['title']}\n"
                    f"Proposed {g['proposed']}, ratified {g['ratified']}.",
                    g["ratified"])
            if len(g["numbers"]) > 1:
                tag("bill-of-rights-1791",
                    "The Bill of Rights, ratified 15 December 1791", g["ratified"])

    # ---- the never-ratified: branches that were never merged ------------
    git("checkout", "-q", "main")
    for u in unratified:
        git("checkout", "-q", "-b", f"proposed/{u['slug']}", main_as_of(u["proposed"]))
        (BUILD / "amendments").mkdir(exist_ok=True)
        (BUILD / "amendments" / f"proposed-{u['slug']}.md").write_text(
            f"# {u['title']}\n\n{u['text']}\n", encoding="utf-8")
        git("add", "-A")
        commit(f"Propose: {u['title']}\n\n{u['status']}\n\n"
               f"Proposed-Date: {u['proposed']}\n"
               f"Git-Date-Offset: +{OFFSET_YEARS} years\nSource: {u['source']}",
               (u["author"], email(u["author"])), u["proposed"])

    # ---- the modern era: tooling, dated so it sorts last ----------------
    git("checkout", "-q", "main")
    today = datetime.date.today().isoformat()
    for item in ["README.md", "docs", "data", "scripts", "sources", ".github", ".gitignore"]:
        src = ROOT / item
        if not src.exists():
            continue
        dst = BUILD / item
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy(src, dst)
    git("add", "-A")
    commit(
        "Add the apparatus: sources, dataset, generator and documentation\n\n"
        "Everything before this commit is the Constitution and nothing else, so\n"
        "`git checkout amendment-13` yields the document as it stood in 1865\n"
        "rather than a repository that happens to contain it.\n\n"
        "Dated with the same +1000 year offset as every other commit, so it sorts\n"
        "after 1992 rather than before 1787.\n\n"
        f"Real-Date: {today}\nGit-Date-Offset: +{OFFSET_YEARS} years",
        ("Ryan Kirby", "github@ryankirby.net"), today)

    print(f"built {BUILD}")
    print(git("log", "--oneline", "--graph", "main", "--", ) [:0] or "", end="")
    print(subprocess.run(["git", "-C", str(BUILD), "log", "--graph", "--oneline",
                          "-14", "main"], capture_output=True, text=True).stdout)


if __name__ == "__main__":
    main()
