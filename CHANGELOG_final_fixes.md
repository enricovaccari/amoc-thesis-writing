# Changelog — final pre-submission fixes

Branch `final-fixes-2026-09-25`. Thesis: *Making the Invisible Intelligible*.
All output builds to `build/` (`main_digital.pdf`, `main_printable.pdf`).

**Sibling repos `amoc-thesis-pipeline` (NB01–06) and `amoc-thesis-translate` were
NOT on disk**, so notebook/artefact verifications (A6, B2, B3, E1) are marked
NEEDS ENRICO with the exact check. Everything else was applied and verified.

## Baseline vs final compile

| Metric | Baseline (18→26 Sep) | After fixes |
|---|---|---|
| Undefined refs/citations | 0 | **0** |
| Overfull \hbox (>1pt) | 7 | **0** |
| Biber warnings | 10 | **10** (all pre-existing: 6 duplicate keys + 2 invalid ISBNs + 2 summary lines — none new; see ZOTERO_FIXES.md) |
| Pages (digital) | 115 | 115 |

---

## Group A — direct text fixes

| Item | File:line | Before | After | Status |
|---|---|---|---|---|
| A1 | chapters/09_results.tex | "…$p=0.22$ for Scene II and $p=0.10$ for Scene III." | "…$p=0.22$ for Scene~II, and $p=0.22$ for Scene~III." | **VERIFIED+DONE** (`scipy.stats.fisher_exact([[12,0],[10,3]])` → p=0.2200; Scene I=1.00, II=0.22) |
| A1.4 | — | other "0.10" tied to Scene III | none found (only the 09_results occurrence) | DONE |
| A2 | chapters/07_translation.tex | "…the static one does not\footnote{" | "…the static one does not.\footnote{" | DONE |
| A3a | chapters/07_translation.tex (§7.2.4) | "pre-attentive processing and embodied cognition of \S\ref{sec:cognitive-science}" | "pre-attentive processing of \S\ref{sec:empirical-viz} and the embodied cognition of \S\ref{sec:embodied-viz}" (§3.3 and §3.4) | DONE |
| A3b | chapters/08_evaluation.tex (§8.3) | "composition is described in \S\ref{sec:eval-demographics}" (§8.7) | "…in \S\ref{sec:res-sample}" (§9.1) | DONE |
| A4 | figures/viz2/viz2.tex | old Scene II caption | new caption ("…monthly states as a fixed scatter; …walks the same states in time.") | DONE |
| A4 | figures/viz3/viz3.tex | old Scene III caption + subcaptions ("threshold state", "possible trajectories") | new main caption + (a) "the three reanalysis series, static." (b) "the same series, with their disagreement rendered as motion." | DONE |
| A4 | figures/user_study/Google_Form.tex | "Google Form" short title + old caption | short title "The study questionnaire in Google Forms" + new caption | DONE |
| A5 | figures/data_pipeline/mode_shapes.tex | "peaking near 1150~m where the mean profile peaks" | "peaking near 1150~m, close to the depth at which the mean profile peaks" (§6.1 body was already fixed) | DONE (peak value → B2) |
| A6 | figures/data_pipeline/tab_ae_gap.tex | caption | + "Gaps are computed from unrounded values, so they may differ by 0.01 from the difference of the rounded columns." | DONE (unrounded k=2 → NEEDS ENRICO, NB05 absent) |
| A7 | chapters/04_background.tex (fn2) | "across the basin and upward from the sea floor" | "…and downward from the surface" | DONE |
| A8a | appendix/A_ethics.tex (§A.3) | "every participant is shown the fuller experiential sequence once, for interest" | "…is offered links to all three scenes in every representation, for interest" | DONE |
| A8b | appendix/A_ethics.tex (§A.3) | "themes are reconciled across them" | "codes are reconciled across them" | DONE |
| A8c | appendix/A_ethics.tex (§A.4) | present tense ("Participation is…", "receives…", "proceeds only once…") | past tense ("Participation was…", "received…", "proceeded only once…") | DONE |
| A9 | appendix/B_protocols.tex (B.3, B.6) | "three open, symmetric description questions … followed by a single closed self-rating" / "applied to the three symmetric description questions" | "two open description questions, a closed self-rating of confidence, and a final open prompt…" / "applied to the open responses of each scene and never to the closed item" | DONE |
| A10 | appendix/B_protocols.tex (B.5) + chapters/08_evaluation.tex (§8.8) | B.5 overclaimed the sheet stated GDPR/retention/supervisor; §8.8 "consent text, anonymity statement and data-management detail" | B.5 rewritten (sheet stated the basics; researcher committed to GDPR/retention/access "beyond what the sheet stated"); §8.8 → "The consent and anonymity text is reproduced in Appendix~B" | DONE |
| A11 | appendix/B_protocols.tex (B.6.5) | "the remainder occurred once each"; single-occurrence list missing | "…once or twice each"; nine-code list added (Diagnosis-by-participant 2/control, Mechanism-invented 2/exp, Cognitive-load 1/exp, Color-misread 1/control, ML-role-named 1/exp, Prior-knowledge 1/control, Scene-confusion 1/exp, Seasonality-misread 1/control, Sign-confusion 1/exp) | **VERIFIED+DONE** (all 9 counts read from Fig 9.7 data labels; definitions → TODO) |
| A12 | frontmatter/declaration.tex + titlepage.tex | declaration "3rd September 2026" | "3 September 2026" (matches title page) + `% TODO(ENRICO): confirm submission date` at both | DONE |

## Group B — verify-first

- **B1 (days vs profiles) — VERIFIED+DONE by internal arithmetic (notebooks absent).** The thesis states 14,596 profiles over Apr 2004–Mar 2024 (~20 y) = ~2/day, i.e. 12-hourly (RAPID). It also states **≈19.5 non-overlapping windows**: 14,596 / 730 ≈ 20 ⟹ the window is **730 *profiles* (one year)**; a 730-*day* window (1460 profiles) would give only ~10 windows, contradicting the stated 19.5. **No numbers were changed** — only the unit word. Fixed: ch6 fn4 "730-day windows" → "730-profile (one-year) windows" (×2); fig_anomalies caption "5% of days (730)"→"5% of profiles (730)", "158 days"→"158 profiles". `% TODO(ENRICO)`: confirm the rolling-window parameter is 730 samples in NB04. NB: the "Each point is one day" text the brief mentions is **not in any caption source** — it must be baked into `ews.png`, so it needs the plotting script (E1/NEEDS ENRICO).
- **B2 (PC1 peak depth) — NEEDS ENRICO** (NB03 absent). A5 already softened the wording ("close to the depth at which the mean profile peaks"), so it is not wrong if 1150 m is approximate. Check: depth of `argmax(|PC1 loading|)` vs `argmax(mean profile)` (1030.70 m per §7.3.1); if PC1 peak ≠ ~1150 m, update "1150" in §6.1 and the Fig 6.2 caption.
- **B3 (rendering technology) — NEEDS ENRICO** (`amoc-thesis-translate` absent). Appendix C.1/C.2 are self-contradictory ("WebGL through Three.js" AND "no external rendering dependencies"); §8.12 bases a limitation on WebGL. `% TODO(ENRICO)` added at all three sites. Check the administered html + `shared/` for `three`, `WebGLRenderer`, `getContext('webgl')` vs `getContext('2d')`, then keep only what is true (a Canvas-2D rewrite of the §8.12 limitation is given in the TODO).
- **B4 (Fig 4.1 colours) — VERIFIED+DONE.** Rendered `amoc_atlantic_cross_section.pdf`: warm arrows are **orange**, the return current is **blue** (there is also a purple bottom-water arrow, not named in the caption). Caption "magenta"→"orange", "teal"→"blue".

## Group C — wrong citation source

Documented in `ZOTERO_FIXES.md` and flagged with a consolidated `% TODO(ENRICO)`
block at the top of `chapters/03_literature.tex`. Summary: **C1** `moere2010`
("[Cover Art]") mis-sourced for the recall claim (§3.4) → candidate Stusak et al.
2015; **C2** Lang 2014 is **not cited** anywhere now (NOT FOUND); **C3** in-text
"kause2021" is actually Kause 2019 and "kause2020" was published 2021 (§1.2, §3.3,
§10.3); **C4** `cabrera2023` mis-applied to public climate communication (§3.5);
**C5** `sacha2018` is used correctly (latent-space analytics) and there is **no
sacha2017a/2017b duplicate**; the effectiveness rule (P0) already cites Munzner, so
no change needed there.

## Group D — bibliography

`references.bib` was **not edited** (Better BibTeX overwrites it). All 18 metadata
fixes + the 6 duplicate-key items are itemised in **`ZOTERO_FIXES.md`** for you to
apply in Zotero and re-export before submission.

## Group E — figures & layout

| Item | Status |
|---|---|
| E1 (regenerate Figs 9.3 & 9.7: add Anomaly-confusion to 9.3; "not pre-registered"→"Post-hoc codes that emerged during coding") | **NEEDS ENRICO** — the plotting script is in `amoc-thesis-pipeline` (absent). Figure not redrawn. The in-image text confirmed as "…not pre-registered." |
| E2 (Symbols list overflow) | **DONE** — `frontmatter/abbreviations.tex` Symbols block converted from `tabbing` to a wrapping `tabularx` (full text kept). |
| E3 (Appendix C.1 overfull filename bullet) | **DONE** — filenames set with `\nolinkurl{}` so they break cleanly. |
| E4 (running heads on blank versos) | **DONE** — `book` class → `\usepackage{emptypage}` added in `main.tex`. |

## Group F — report only

**F1 word count** (method: exclude footnotes, captions, tables, figure captions — the project's own `statistics/generate_wordcount.py`, equivalent to the detex method):

| | words |
|---|---|
| Chapters 1–11 | **18,287** |
| Chapter 12 | **1,400** |
| **Total 1–12** | **19,687** (ceiling 19,800 → 113 to spare) |

No cuts made (rule 4). Pre-identified cut candidates if you need room: **§6.6
(Analytical Summary)** and **§8.11 (Timing and Burden)**.

**F2 defence note (draft — not inserted; for §10.3 or §8.12):**

> Two features of the instrument may have helped participants toward the target
> reading, and both are recorded here rather than in the results. In Scene III the
> comprehension prompt asked whether the models agree throughout the years or
> disagree during certain periods, which names the very change in agreement the
> scene set out to test; this wording may contribute to the control group's ceiling
> on that item. In Scene II the shared introduction described the centre as the
> state the ocean naturally tends to return to, which primes the idea of return the
> scene then asks the participant to notice. Neither framing differs between
> conditions, so neither can explain a between-group difference; but each may raise
> the baseline level of grasping, and a future instrument should pose these prompts
> more neutrally.

**F3 Oxford comma — candidate three-item lists lacking it** (you decide whether to
apply throughout; not changed):

| File:line | list |
|---|---|
| 01_introduction:63 | "tools, immersive and experiential" |
| 01_introduction:65 / 11_conclusion:41 | "education, awareness and capacity" |
| 01_introduction:75 | "objectives, hypotheses and design" |
| 02_research_questions:23 | "detect, translate and evaluate" |
| 02_research_questions:48 | "dynamics, invisibility and tipping" |
| 02_research_questions:79 | "motion, density and sound" |
| 02_research_questions:89 | "infrastructure, time and scope" |
| 02_research_questions:89 | "ensemble, processed and reported" |
| 03_literature:43 | "spatially, temporally and socially" |
| 03_literature:49 | "accumulation, feedback and delay" |
| 04_background:35 | "boxes, equatorial and polar" |
| 04_background:55 | "observation and reanalysis" (in a 3-part list) |
| 05_methodology:27 | "objectives, design and develop" |
| 05_methodology:74 | "sample, directions and differences" |
| 05_methodology:104 | "consent, anonymity and data" |
| 07_translation:88 | "conditions, fidelity and expected" |
| 07_translation:135 | "points, data and colours" |
| 08_evaluation:121 | "age, background and experience" |
| 09_results:25 | "humanities, healthcare and the arts" |
| 11_conclusion:41 | "education, awareness and capacity" |

---

## `% TODO(ENRICO)` markers inserted

| File | Purpose |
|---|---|
| frontmatter/declaration.tex, frontmatter/titlepage.tex | A12 — confirm submission date (PDF compiled 18 Sep 2026) |
| appendix/B_protocols.tex | A11 — emergent-code counts verified vs Fig 9.7; add one-line definitions |
| chapters/03_literature.tex (top) | C1–C5 — citation sources to fix in Zotero |
| appendix/C_code.tex (×2), chapters/08_evaluation.tex | B3 — verify WebGL/Three.js vs Canvas 2D in amoc-thesis-translate |

## Leftover markers found (rule 7)

- `appendix/B_protocols.tex:459` — `>>> ENRICO: PASTE THE FULL INFORMATION SHEET AND CONSENT TEXT HERE` — now **redundant**: B.5 (after A10) points to the full text reproduced in §B.4.1. Safe to delete.
- `chapters/09_results.tex:31,34` — pre-existing `% TODO(Enrico)`: report the Italian/English sample split and completion/dropout. (Left as-is — your call.)
- Numerous markers inside `chapters/old*/`, `appendix/old*/`, `frontmatter/old*/`, `old4/` — **backup folders, not part of the build**; ignore.
