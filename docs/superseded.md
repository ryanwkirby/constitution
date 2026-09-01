# What each amendment changed

The National Archives transcript links every superseded passage to the
amendment that superseded it. Those links are the authority for this table;
`scripts/build_edits.py` locates each passage in the text and records the
exact substring, and `scripts/verify.py` asserts that no passage listed here
survives in `constitution/` at HEAD.

| Amendment | File | Struck | Replaced with |
| --- | --- | --- | --- |
| XI | `constitution/article-03.md` | between a State and Citizens of another State | *(deleted)* |
| XII | `constitution/article-02.md` | The Electors shall meet in their respective States, and vote by Ballot… | *(deleted)* |
| XIII | `constitution/article-04.md` | No Person held to Service or Labour in one State, under the Laws there… | *(deleted)* |
| XIV | `constitution/article-01.md` | Representatives and direct Taxes shall be apportioned among the severa… | Representatives shall be apportioned among the sev… |
| XVI | `constitution/article-01.md` | unless in Proportion to the Census or enumeration herein before direct… | *(deleted)* |
| XVII | `constitution/article-01.md` | chosen by the Legislature | elected by the people |
| XVII | `constitution/article-01.md` | and if Vacancies happen by Resignation, or otherwise, during the Reces… | *(deleted)* |
| XX | `constitution/article-01.md` | the first Monday in December | the 3d day of January |
| XXV | `constitution/article-02.md` | In Case of the Removal of the President from Office, or of his Death, … | *(deleted)* |
| XXVI | `amendments/amendment-14.md` | twenty-one years ×2 | eighteen years |

## Not in the table

- **Amendment XVIII** added no text to the original articles; it stood on
  its own and was repealed entire by **Amendment XXI**, which the history
  records as a literal `git revert`. Its text is gone from `amendments/` at
  HEAD and permanently reachable at the `amendment-18` tag.
- **Amendment XXVI** amended *Amendment XIV*, not the original text — the
  one case where an amendment edits another amendment's file.
- **Amendment XX** superseded part of Amendment XII as well as Article I;
  the Archives records that in prose rather than inline markup, so it is
  noted here rather than applied as an edit.
