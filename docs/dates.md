# Dates

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

| # | Amendment | Proposed | Ratified | Gap | Git timestamp |
| --- | --- | --- | --- | --- | --- |
| 1 | Freedom of religion, speech, press, assembly and petition | 1789-09-25 | 1791-12-15 | 2 yrs | 2791-12-15 |
| 2 | Right to keep and bear arms | 1789-09-25 | 1791-12-15 | 2 yrs | 2791-12-15 |
| 3 | Quartering of soldiers | 1789-09-25 | 1791-12-15 | 2 yrs | 2791-12-15 |
| 4 | Searches and seizures | 1789-09-25 | 1791-12-15 | 2 yrs | 2791-12-15 |
| 5 | Grand jury, double jeopardy, self-incrimination, due process | 1789-09-25 | 1791-12-15 | 2 yrs | 2791-12-15 |
| 6 | Rights of the accused in criminal prosecutions | 1789-09-25 | 1791-12-15 | 2 yrs | 2791-12-15 |
| 7 | Jury trial in civil cases | 1789-09-25 | 1791-12-15 | 2 yrs | 2791-12-15 |
| 8 | Excessive bail, cruel and unusual punishment | 1789-09-25 | 1791-12-15 | 2 yrs | 2791-12-15 |
| 9 | Rights retained by the people | 1789-09-25 | 1791-12-15 | 2 yrs | 2791-12-15 |
| 10 | Powers reserved to the States | 1789-09-25 | 1791-12-15 | 2 yrs | 2791-12-15 |
| 11 | Suits against the States | 1794-03-04 | 1795-02-07 | 0 yrs | 2795-02-07 |
| 12 | Election of President and Vice President | 1803-12-09 | 1804-06-15 | 0 yrs | 2804-06-15 |
| 13 | Abolition of slavery | 1865-01-31 | 1865-12-06 | 0 yrs | 2865-12-06 |
| 14 | Citizenship, due process and equal protection | 1866-06-13 | 1868-07-09 | 2 yrs | 2868-07-09 |
| 15 | Right to vote regardless of race | 1869-02-26 | 1870-02-03 | 0 yrs | 2870-02-03 |
| 16 | Federal income tax | 1909-07-02 | 1913-02-03 | 3 yrs | 2913-02-03 |
| 17 | Direct election of Senators | 1912-05-13 | 1913-04-08 | 0 yrs | 2913-04-08 |
| 18 | Prohibition of intoxicating liquors | 1917-12-18 | 1919-01-16 | 1 yr | 2919-01-16 |
| 19 | Woman suffrage | 1919-06-04 | 1920-08-18 | 1 yr | 2920-08-18 |
| 20 | Terms of office; the 'Lame Duck' amendment | 1932-03-02 | 1933-01-23 | 0 yrs | 2933-01-23 |
| 21 | Repeal of Prohibition | 1933-02-20 | 1933-12-05 | 0 yrs | 2933-12-05 |
| 22 | Presidential term limits | 1947-03-21 | 1951-02-27 | 3 yrs | 2951-02-27 |
| 23 | Presidential electors for the District of Columbia | 1960-06-16 | 1961-03-29 | 0 yrs | 2961-03-29 |
| 24 | Abolition of the poll tax | 1962-08-27 | 1964-01-23 | 1 yr | 2964-01-23 |
| 25 | Presidential succession and disability | 1965-07-06 | 1967-02-10 | 1 yr | 2967-02-10 |
| 26 | Voting age of eighteen | 1971-03-23 | 1971-07-01 | 0 yrs | 2971-07-01 |
| 27 | Congressional compensation | 1789-09-25 | 1992-05-07 | 202 yrs | 2992-05-07 |
