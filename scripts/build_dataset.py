#!/usr/bin/env python3
"""Merge Archives-derived dates with researched authorship into data/amendments.json.

Dates are parsed from the National Archives 'Passed by Congress ... Ratified ...'
lines captured in sources/archives-metadata.json, so they are never retyped by
hand. Authorship is hand-entered here with a source URL per amendment, because
no machine-readable dataset of amendment sponsors exists.
"""
import datetime
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARCHIVES_AMD = "https://www.archives.gov/founding-docs/amendments-11-27"
ARCHIVES_BOR = "https://www.archives.gov/founding-docs/bill-of-rights-transcript"

# Bill of Rights dates are not on the amendments-11-27 page. The Archives Bill of
# Rights transcript states them in prose, and extract_sources.py captures that
# sentence verbatim as `bill_of_rights_line`.
BOR_DATES = {"proposed": "1789-09-25", "ratified": "1791-12-15", "source": ARCHIVES_BOR}

# name, role, one source establishing the attribution
AUTHORS = {
    1: [("James Madison", "Representative (VA); introduced the amendments in the House, 8 June 1789", "https://www.archives.gov/founding-docs/bill-of-rights")],
    11: [("Caleb Strong", "Senator (MA); introduced the resolution", "https://constitutioncenter.org/blog/the-11th-amendment-correcting-the-supreme-court-in-action")],
    12: [("John Dawson", "Representative (VA); offered the House resolution, 17 Oct 1803", "https://constitutioncenter.org/news-debate/special-projects/a-madisonian-constitution-for-all/essay-series/the-constitution-the-presidency-and-partisan-democracy-congress-revises-the-electoral-college-1804"),
         ("DeWitt Clinton", "Senator (NY); offered the parallel Senate resolution four days later", "https://constitutioncenter.org/news-debate/special-projects/a-madisonian-constitution-for-all/essay-series/the-constitution-the-presidency-and-partisan-democracy-congress-revises-the-electoral-college-1804")],
    13: [("John B. Henderson", "Senator (MO); introduced the joint resolution, Jan 1864", "https://www.senate.gov/about/origins-foundations/senate-and-constitution/senate-passes-the-thirteenth-amendment.htm"),
         ("Lyman Trumbull", "Senator (IL); Judiciary chair, reported the resolution with the amendments that became the final text", "https://www.senate.gov/about/origins-foundations/senate-and-constitution/senate-passes-the-thirteenth-amendment.htm"),
         ("James M. Ashley", "Representative (OH); proposed an abolition amendment Dec 1863 and led House passage", "https://history.house.gov/Historical-Highlights/1851-1900/The-13th-Amendment/")],
    14: [("John A. Bingham", "Representative (OH); principal author of Section 1", "https://constitutioncenter.org/blog/it-was-today-congress-approved-the-14th-amendment"),
         ("Thaddeus Stevens", "Representative (PA); introduced the Joint Committee's proposal to the House, 30 Apr 1866", "https://constitutioncenter.org/the-constitution/historic-document-library/detail/thaddeus-stevens-speech-introducing-the-fourteenth-amendment-1866"),
         ("Jacob M. Howard", "Senator (MI); Joint Committee member, floor manager in the Senate", "https://constitutioncenter.org/blog/it-was-today-congress-approved-the-14th-amendment")],
    15: [("George S. Boutwell", "Representative (MA); drafted the version the House passed, 30 Jan 1869", "https://history.house.gov/Historical-Highlights/1851-1900/1869_02_25_15thAmendment/"),
         ("William M. Stewart", "Senator (NV); shepherded the amendment through the Senate", "https://15thamendment.harpweek.com/HubPages/CommentaryPage.asp?Commentary=06Bios16")],
    16: [("Norris Brown", "Senator (NE); sponsored the resolution", "https://history.nebraska.gov/100-years-of-the-federal-income-tax/"),
         ("Nelson W. Aldrich", "Senator (RI); moved the amendment as the compromise that preserved the Payne-Aldrich tariff", "https://constitution.heritage.org/essays/amdt-16/")],
    17: [("Joseph L. Bristow", "Senator (KS); author of the 'Bristow amendment'", "https://www.senate.gov/artandhistory/history/common/generic/SeventeenthAmendment.htm"),
         ("William E. Borah", "Senator (ID); leading proponent", "https://www.senate.gov/artandhistory/history/common/generic/SeventeenthAmendment.htm")],
    18: [("Morris Sheppard", "Senator (TX); introduced the joint resolution, 4 Apr 1917", "https://www.tshaonline.org/handbook/entries/sheppard-john-morris")],
    19: [("Aaron A. Sargent", "Senator (CA); introduced the text in 1878 as the 'Susan B. Anthony Amendment'", "https://history.house.gov/Historical-Highlights/1901-1950/The-19th-Amendment/"),
         ("James R. Mann", "Representative (IL); Woman Suffrage Committee chair, secured House passage 21 May 1919", "https://history.house.gov/Historical-Highlights/1901-1950/The-19th-Amendment/")],
    20: [("George W. Norris", "Senator (NE); Judiciary chair and sponsor of the 'Lame Duck Amendment'", "https://www.annenbergclassroom.org/resource/our-constitution/constitution-amendment-20/")],
    21: [("John J. Blaine", "Senator (WI); drafted and submitted the repeal resolution, 6 Dec 1932", "https://www.congress.gov/crs-product/LSB11067")],
    22: [("Earl C. Michener", "Representative (MI); introduced the term-limit resolution", "https://www.encyclopedia.com/law/legal-and-political-magazines/twenty-second-amendment")],
    23: [("Kenneth B. Keating", "Senator (NY); added the District electoral-vote clause", "https://www.senate.gov/senators/FeaturedBios/Featured_Bio_KeatingKenneth.htm"),
         ("Estes Kefauver", "Senator (TN); author of the resolution that carried the clause", "https://www.encyclopedia.com/law/legal-and-political-magazines/twenty-third-amendment")],
    24: [("Spessard L. Holland", "Senator (FL); proposed the poll-tax amendment", "https://constitution.heritage.org/essays/amdt-24/")],
    25: [("Birch Bayh", "Senator (IN); author, chair of the Subcommittee on Constitutional Amendments", "https://ir.lawnet.fordham.edu/flr/vol86/iss3/7/")],
    26: [("Jennings Randolph", "Senator (WV); chief sponsor, introduced the proposal repeatedly from 1942", "https://www.annenbergclassroom.org/resource/our-constitution/constitution-amendment-26/"),
         ("Birch Bayh", "Senator (IN); drove the 1971 passage as subcommittee chair", "https://ir.lawnet.fordham.edu/flr/vol86/iss3/7/")],
    27: [("James Madison", "Representative (VA); drafted it as part of the 1789 package", "https://www.archives.gov/founding-docs/amendments-11-27"),
         ("Gregory Watson", "University of Texas undergraduate whose 1982-1992 campaign secured ratification", "https://www.archives.gov/founding-docs/amendments-11-27")],
}
for n in range(2, 11):
    AUTHORS[n] = AUTHORS[1]

TITLES = {
    1: "Freedom of religion, speech, press, assembly and petition",
    2: "Right to keep and bear arms", 3: "Quartering of soldiers",
    4: "Searches and seizures", 5: "Grand jury, double jeopardy, self-incrimination, due process",
    6: "Rights of the accused in criminal prosecutions", 7: "Jury trial in civil cases",
    8: "Excessive bail, cruel and unusual punishment", 9: "Rights retained by the people",
    10: "Powers reserved to the States", 11: "Suits against the States",
    12: "Election of President and Vice President", 13: "Abolition of slavery",
    14: "Citizenship, due process and equal protection", 15: "Right to vote regardless of race",
    16: "Federal income tax", 17: "Direct election of Senators",
    18: "Prohibition of intoxicating liquors", 19: "Woman suffrage",
    20: "Terms of office; the 'Lame Duck' amendment", 21: "Repeal of Prohibition",
    22: "Presidential term limits", 23: "Presidential electors for the District of Columbia",
    24: "Abolition of the poll tax", 25: "Presidential succession and disability",
    26: "Voting age of eighteen", 27: "Congressional compensation",
}

MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}
MONTHS.update({"Sept.": 9, "Jan.": 1, "Feb.": 2, "Mar.": 3, "Apr.": 4,
               "Aug.": 8, "Oct.": 10, "Nov.": 11, "Dec.": 12})


def parse_date(text):
    m = re.search(r"([A-Z][a-z]+\.?)\s+(\d{1,2}),\s*(\d{4})", text)
    if not m:
        return None
    mon = MONTHS.get(m.group(1)) or MONTHS.get(m.group(1).rstrip("."))
    return datetime.date(int(m.group(3)), mon, int(m.group(2))).isoformat()


def main():
    meta = json.loads((ROOT / "sources" / "archives-metadata.json").read_text())
    out = []
    for num in range(1, 28):
        line = meta["date_lines"].get(str(num))
        if num <= 10:
            proposed, ratified, dsrc = (
                BOR_DATES["proposed"], BOR_DATES["ratified"], ARCHIVES_BOR)
            dline = meta["bill_of_rights_line"]
        else:
            parts = re.split(r"(?<=\.)\s+(?=Ratified)", line)
            proposed, ratified = parse_date(parts[0]), parse_date(parts[1])
            dsrc, dline = ARCHIVES_AMD, line
        authors = AUTHORS[num]
        out.append({
            "number": num,
            "title": TITLES[num],
            "proposed": proposed,
            "ratified": ratified,
            "date_source": dsrc,
            "archives_date_line": dline,
            "author": {"name": authors[0][0], "role": authors[0][1], "source": authors[0][2]},
            "co_authors": [{"name": n, "role": r, "source": s} for n, r, s in authors[1:]],
            "archives_note": meta["notes"].get(str(num), []),
        })
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "amendments.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(out)} amendments")
    for a in out:
        print(f"  {a['number']:>2}. {a['proposed']} -> {a['ratified']}  {a['author']['name']}")


if __name__ == "__main__":
    main()
