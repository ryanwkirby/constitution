# Who wrote it

Git gives every commit two identities and a list of trailers, which is more
attribution than most version control offers and still less than a constitutional
amendment deserves. The convention here:

- **`Author`** — the principal drafter or sponsor. One person.
- **`Co-Authored-By`** — everyone else with a documented claim.
- **`Committer` on a merge** — `The several States`, because ratification is
  something the states do, not a person.

Every name in `data/amendments.json` carries a `source` URL establishing the role
it claims. Emails use the RFC 2606 reserved `.invalid` TLD
(`james.madison@us.congress.historic.invalid`) so they can never route and GitHub
can never bind a living person's account to a fabricated commit.

## Where a single author is a fiction

Naming one author is often a simplification, and in a few cases it is a genuine
dispute. Those are recorded rather than quietly resolved.

**Amendment XIII** — three plausible answers. John B. Henderson introduced the
joint resolution in January 1864 and is the Author here. Lyman Trumbull, chairing
Senate Judiciary, reported it back with the amendments that produced the final
text. James Ashley had proposed an abolition amendment a month earlier and led it
through the House. Trumbull has the strongest claim on the *words*; Henderson on
the *resolution*. Both are on the commit.

**Amendment XIV** — John Bingham is the Author, as principal author of Section 1
and the amendment's principal framer. Thaddeus Stevens introduced the Joint
Committee's proposal to the House and is the reason it reached the floor at all.
Sections 2 through 4 are substantially committee work with no single hand.

**Amendment XIX** — the hardest case. The text is Aaron Sargent's, introduced in
1878 and known ever after as the Susan B. Anthony Amendment. It passed 41 years
later, in 1919, under James Mann. The Author here is Sargent, because the words
ratified in 1920 are the words he introduced in 1878 — but the *commit is dated
1919*, when Sargent had been dead for thirty-two years. The date is the proposal
date, which is a fact; the authorship is the drafting, which is also a fact; that
they sit oddly together is a property of the amendment, not of the record.

**Amendment XXVI** — sources conflict outright. Jennings Randolph introduced a
voting-age amendment repeatedly from 1942 and is usually called its chief sponsor;
Birch Bayh chaired the subcommittee that drove the 1971 passage and is sometimes
credited as author of both the 25th and the 26th. Randolph is the Author here on
the strength of the four-decade sponsorship, with Bayh as co-author. Reasonable
people disagree.

**Amendment XXVII** — James Madison drafted it in 1789 as part of the same package
as the Bill of Rights. It was ratified in 1992 because Gregory Watson, an
undergraduate who received a C on a paper arguing it was still live, spent ten
years lobbying state legislatures. Madison is the Author; Watson is a co-author,
and the only person in this repository who is credited for a ratification rather
than a text.

**Amendments I–X** are all attributed to Madison, who introduced them on 8 June
1789. This flattens real committee work in both chambers, and the ten are recorded
as ten commits on one branch because they were one joint resolution — the same
resolution that carried what became the 27th Amendment and the still-pending
Congressional Apportionment Amendment.

**The Constitution itself** is committed by the `Constitutional Convention` rather
than a person. Gouverneur Morris has the best claim to the final wording through
the Committee of Style, and Madison to the design, but attributing the 1787 text
to one signer would assert more than the record supports.
