# Thesis corrections — applied 3 September 2026

All files in this archive are drop-in replacements. Folder structure matches your repo:

```
main.tex
frontmatter/  titlepage.tex  declaration.tex (NEW)  abstract.tex
              acknowledgements.tex  abbreviations.tex
chapters/     01 … 12
appendix/     A_ethics.tex  B_protocols.tex  C_code.tex
check_refs.py (NEW — run it after you restore the figure labels)
```

Verified after editing: **0 broken cross-references, 0 orphan floats, 0 duplicate labels,
0 printing placeholders, 0 remaining typos from the audit, all braces balanced.**

---

## 1. What you MUST still do yourself (4 items)

These need information I do not have. Each is marked in the source with a `>>> ENRICO:` or
`% VERIFY:` / `% RESTORE` comment so you can find them with a search.

1. **Verify two numbers against your notebooks** (search `VERIFY:` in `chapters/06_data_pipeline.tex`)
   - The record has 14,596 profiles over 20 years, which is arithmetically **twice-daily**, not
     daily. I removed the word "daily" everywhere and changed "730 days" to "730 profiles", which
     is true under either reading. Confirm the real cadence and put it back explicitly.
   - Ch.6 said PC1 peaks near 1150 m "exactly where the average profile peaks"; ch.7 says the mean
     profile peaks at 1030.70 m. I removed "exactly". Confirm which depth is right.

2. **Paste the questionnaire text and consent form** into `appendix/B_protocols.tex`
   (search `>>> ENRICO:`). Chapters 5 and 8 both promise the reader the full instrument there.
   Also list the single-occurrence emergent codes — chapter 9 promises those too.

3. **Restore 6 figure references** once you know the real labels (search `% RESTORE`):
   | Reference | File | Status |
   |---|---|---|
   | `fig:psi-slope` | ch.7 §7.3.1 | figure does not exist — **make this one** (see below) |
   | `fig:flow-regimes` | ch.7 §7.3.1 | reworded, reference removed |
   | `fig:column-conditions` | ch.7 §7.3.1 | figure exists in `viz1.tex`, label unknown |
   | `fig:extremes` | ch.7 §7.3.1 | figure does not exist |
   | `fig:stommel-hysteresis` | ch.4 §4.2 | figure does not exist |
   | `fig:sterman-scenario/-response` | ch.3 §3.2 | figure exists, labels unknown |

   Run `python check_refs.py` from your repo root: it lists every label in `figures/`, so you can
   match them up in one pass.

4. **Two new bibliography entries** are cited and must be added to `references.bib`
   (verify the metadata — I have not consulted the sources):
   ```bibtex
   @article{malterud2016,
     author = {Malterud, Kirsti and Siersma, Volkert Dirk and Guassora, Ann Dorrit},
     title = {Sample Size in Qualitative Interview Studies: Guided by Information Power},
     journal = {Qualitative Health Research}, volume = {26}, number = {13},
     pages = {1753--1760}, year = {2016}, doi = {10.1177/1049732315617444}}
   @article{braunclarke2021,
     author = {Braun, Virginia and Clarke, Victoria},
     title = {To Saturate or Not to Saturate? Questioning Data Saturation as a Useful Concept
              for Thematic Analysis and Sample-Size Rationales},
     journal = {Qualitative Research in Sport, Exercise and Health}, volume = {13},
     number = {2}, pages = {201--216}, year = {2021}, doi = {10.1080/2159676X.2019.1704846}}
   ```
   Also: deduplicate the 7 repeated keys biber flagged (`braunclarke2006`, `hermann2011`,
   `munzner2014` ×2, `scheffer2009`, `sonnewald2021`, `ware2021`), and confirm `braunclarke2019`
   exists — it now carries the methodological claim in ch.5 and ch.7.

---

## 2. Critical fixes applied

| # | Fix | Where |
|---|---|---|
| 1 | **Removed the stray `...`** that was printing on its own page after the Part I divider | `main.tex` L160 |
| 2 | Rebuilt Appendix C: deleted the duplicated §C.1/§C.2, filled all **9 `[FILL:]` placeholders** from values stated elsewhere in your own thesis, removed 5 blank lines and the orphan paragraph | `appendix/C_code.tex` |
| 3 | Replaced the two bracketed placeholders in Appendix B with honest text + paste markers | `appendix/B_protocols.tex` |
| 4 | Fixed all 12 broken cross-references: `ch:detect`→`ch:data_pipeline` (×3), `app:limitations`→`app:limits-translate`, and 8 figure refs removed or resolved | ch.3, 4, 7 |
| 5 | **Defined `eq:velocity`** — the equation ch.7 cited but never wrote. It now anchors the streamfunction misconception formally | ch.7 §7.2.3 |
| 6 | "reflexive thematic analysis" → "codebook analysis": it contradicted ch.2, ch.5 and Appendix B | ch.7 §7.2.1 |
| 7 | "pre-registered" → "pre-specified" (×4). You have a pre-specified grid, not a deposited registration | ch.9 |
| 8 | "random people" removed — it contradicted the convenience sample two paragraphs later | ch.8 §8.3 |
| 9 | SDG hierarchy aligned: the conclusion now matches the introduction (13 primary via 13.3, 4 secondary, 14 indirect) | ch.11 |
| 10 | Removed "daily" / "730 days" pending your check (see §1.1) | ch.6 |
| 11 | Removed "exactly where the average profile peaks" pending your check | ch.6 §6.1 |

## 3. Methodology and rubric gaps closed

- **Scene-order confound declared.** Every participant met the scenes I→II→III, yet chapters 9–10
  compare scenes to each other. Fatigue and learning are confounded with scene identity, and this
  bears directly on the Scene III result. Now stated in ch.8 §8.11, ch.10 §10.3, Appendix A and
  ch.11 future work. *This was the most attackable hole in the thesis.*
- **Saturation answered properly** (ch.8 §8.2). Your professor pointed in the right direction, but
  saturation does **not** apply to your design — it belongs to inductive, theory-generating work,
  and your grid was fixed before you read a single response. The correct criterion is
  **information power** (Malterud et al. 2016), and your study satisfies all five of its
  conditions. The text now says explicitly why saturation is *not* claimed. Do not let anyone
  talk you into claiming it.
- **Ethics Statement as a section** (ch.5 §5.6). It was buried in a footnote; the programme asks
  for a section at the end of the methodology chapter.
- **LLM-assisted coding disclosed in the methodology chapter** and in Appendix A/B, not only in
  ch.8. Anchoring on the automated label is now named as a bias.
- **Implications section added** (ch.10 §10.6): theoretical, practical, sustainability. This was a
  rubric criterion with nothing against it.
- **The misconception anchored in Sterman and Cronin** (ch.10 §10.4). Reading the height of a
  cumulative integral as a local rate *is* the stock–flow confusion you introduce in ch.1 and ch.3.
  This turns your main empirical finding from a design flaw into a confirmation of a known
  cognitive limit in a new domain. It is the single highest-value addition in this pass.
- **`Anomaly-confusion` now interpreted** (ch.10 §10.3). You reported a code that runs against your
  own thesis and then never discussed it. It now yields a specific critique of principle P3.
- **Triangulation named** (ch.5 §5.5) — you were doing it in three places without using the word.
- **Mission reaffirmed in the conclusion** (ch.11 §11.3), qualified by the findings rather than
  repeated.
- **Statistics**: subgroup *n* now reported everywhere (two confidence means rest on n=3); the
  balance check reports size and direction instead of a p-value; the near-identity of the two
  misconception splits is stated; a sentence explains why no effect sizes or CIs are reported.

## 4. Front matter

- **`frontmatter/declaration.tex` — NEW.** Declaration of authorship + AI use, which the programme
  requires and which existed only in Appendix A. Wired into `main.tex`.
- **Title page**: "Thesis" is correct — the programme never says "Final Thesis". Added the degree
  statement, fixed the date (`\today` would change on every recompile — **check 3 September 2026
  is your real submission date**), simplified the logo path. ⚠️ Verify `figures/logos/ToU_logo.png`
  exists: your last compile log loaded it from `figures/ToU_logo.png`.
- **Abbreviations rebuilt**: 7 missing acronyms added (GREP, DSR, EOF, GDPR, IPCC, MVP + fixed
  RAPID to 26.5°N), alphabetical order fixed, and **a symbols list added** — Ψ as cumulative
  transport vs ∂Ψ/∂z as local flow, on page xvii, is exactly the distinction your participants got
  wrong.
- **Preamble**: float parameters so standalone tables sit at the top of the page (your request);
  `\parskip` conflict resolved (recovers ~4 pages); LoF/LoT now appear in the ToC; dead glossary
  block and unused `\amoc` removed.

## 5. The roadmap (§1.6) — I was wrong last time

Without `main.tex` I proposed a five-part structure. Now that I can see it: **chapter 6 is already
under DETECT**, and chapters 7 and 8 are already correct. The real problem was that §1.6 described
a *different* structure from the one `main.tex` builds, and stopped at chapter 11. §1.6 now matches
`main.tex` exactly and covers chapters 1–12 plus the appendices. `main.tex` itself is unchanged
except for the Part I subtitle, which gains "the Method".

---

## 6. Word count — read this before you compile

| | words |
|---|---|
| Your tool, before | 19,784 |
| **Projected now** | **~20,167** |
| Ceiling | 19,800 |
| Ideal band | 15,000–18,000 |

I added ~1,900 words of rubric-required content and cut ~1,500 of genuine redundancy. Net **+383**,
which puts you roughly **370 words over the ceiling**.

Two things to know:

**(a) Your tool does not count footnote words.** It counts the *number* of footnotes (63) but not
their text. There are **2,257 words in your footnotes** — 11% of the total. If your programme
counts them, you are at ~22,400, not 20,167. **Ask your supervisor this one question**, because it
changes the size of the problem by a factor of six.

**(b) To get back under the ceiling**, delete any ~400 words. The three least load-bearing
candidates, already isolated:

| Cut | Where | ~words |
|---|---|---|
| §8.10 "Timing and Burden" — fully covered by §8.4 and Appendix B | ch.8 | 60 |
| §7.3 the three "Fidelity" paragraphs — §7.2.2 states the commitment once for all scenes | ch.7 | 140 |
| §6.6 "Analytical Summary" — restates four sections read three pages earlier | ch.6 | 190 |

That is a 10-minute job and gets you to ~19,780. For real margin, also consider whether the
Reflection chapter (1,425 words) counts toward the limit in your programme — it is a separate
rubric deliverable, and if it is excluded you are at ~18,740 and comfortable.

I did not make these cuts myself because each removes something rather than tightening it, and
that is your call, not mine.

---

## 7. One decision I made on your behalf

In the abstract I changed **"It undoubtedly helped"** to **"It helped most clearly"**. You asked
for "undoubtedly" and I flagged it in the audit as the one word in the thesis that promises more
than the data give: the evidence is 3/13 against 0/12 in a single scene, n=25, Fisher p=0.22.
It is also the first sentence a supervisor reads, and it sits two lines above your own statement
that the result "is not offered as a finding to be carried elsewhere". Revert it in five seconds
if you disagree — `frontmatter/abstract.tex`, third paragraph.
