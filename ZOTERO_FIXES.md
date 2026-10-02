# Zotero fixes for `references.bib

`references.bib` is auto-exported by Better BibTeX from the Zotero collection
**"MSc Thesis"**, so any hand-edit to the `.bib` is overwritten at the next
export. **Apply the fixes below in Zotero, then re-export before final
submission.** No change was made to `references.bib` in this pass.

Line numbers refer to the `references.bib` present at the time of writing.

---

## D — Bibliography metadata

| # | Zotero item (citekey) | Field | Change to |
|---|---|---|---|
| D1 | Moat et al. 2026 — RAPID dataset (`moat2026`) | author | Store as separate creators, not one literal: `Moat, Ben I.; Smeed, David A.; Rayner, Darren; Johns, William E.; Smith, Ryan H.; Volkov, Denis L.; Elipot, Shane; Petit, Tillys; Kajtar, Jules B.; Baringer, Molly O.; Collins, Julie`. Prints "Ben I Moat et al." now → should print **"Moat et al., 2026"**. Also clean the `type`/`format`/`note` junk ("Documents,Network Common Data Form…") and write the latitude as **26°N**. |
| D2 | IPCC 2023 (`ipcc2021` / IPCC key) | author, date | `author = {{Intergovernmental Panel on Climate Change (IPCC)}}` (double braces so it is one corporate author). Date = **year only** (2023). |
| D3 | Bertin 1983 (`bertin1983`) | author, translator | Bertin is listed twice and **Berg** appears as an author. Make **Bertin** the sole author; move **Berg** to `translator`. Verify publisher/edition (Univ. of Wisconsin Press, 1983). In-text → **"Bertin (1983)"**. |
| D4 | Lakoff 1999 (`lakoff1999`) | author, publisher, title | Add **Mark Johnson** as 2nd author; publisher **Basic Books**; sentence-case title *Philosophy in the flesh: The embodied mind and its challenge to Western thought*. In-text → **"Lakoff & Johnson, 1999"**. |
| D5 | Tversky 2002 & 2019 (`tversky2002`, `tversky2019`) | author given name | Same person stored as "Tversky, B." (2002) and "Tversky, B. G." (2019). Use the **same given-name form** in both so biblatex `uniquename` stops printing "B. G. Tversky". In-text → **"Tversky (2019)"** and **"Tversky et al. (2002)"**. |
| D6 | *Transforming our world…* (title-as-author, n.d.) | author, date, number | author `{United Nations}`; year **2015**; **A/RES/70/1**. |
| D7 | *Conducting Educational Design Research* (title-as-author, n.d.) | author, date, edition, publisher | **McKenney, S., & Reeves, T. C. (2019)**, 2nd ed., Routledge. |
| D8 | *Global Warming's Six Americas, September 2021* (title-as-author) | author, date, publisher | **Leiserowitz, A., Roser-Renouf, C., Marlon, J., & Maibach, E. (2021)**, Yale Program on Climate Change Communication. `% verify the exact author list on the report page.` |
| D9 | *Climate Visuals for COP22 and beyond* (currently author "Creative, V.") | author, date | author `{Climate Outreach}`; year **2016**. `% verify.` |
| D10 | *PrintMag (2017)* | author, date, title, source | **Lupi, G. (2017, January 30). Data humanism: The revolutionary future of data visualization. Print Magazine.** |
| D11 | *The Sonification Handbook \| edited by…* (`hermann2011`) | author→editor, publisher | **Hermann, T., Hunt, A., & Neuhoff, J. G. (Eds.). (2011). The sonification handbook. Logos Verlag.** Also remove the **duplicate `hermann2011`** (see D-dupes). |
| D12 | Hevner et al. 2004 (`hevner2004`) | title | Remove the stray "1" in "Research1". |
| D13 | Stoknes 2015 (`stoknes2015`) | title, url, type | Title truncated ("Actio") and links to ResearchGate. It is a **book**: *What we think about when we try not to think about global warming: Toward a new psychology of climate action*, Chelsea Green Publishing. |
| D14 | Caesar et al. 2018 (`caesar2018`) | url→doi | Replace repository URL with DOI **10.1038/s41586-018-0006-5**. |
| D15 | Dakos et al. 2012 (`dakos2012`) | editor | Remove editor **"B. Yener"** (the PLoS academic editor). |
| D16 | Camps-Valls et al. 2021 (`camps2019`?) | date | Use the **year only**, not "September 27". |
| D17 | Name particles (APA lowercase) | author | Lowercase the particle: **van der Linden**, **van den Broek** (in Fischer et al.), **van Merriënboer** (in Sweller et al.), **van Nes** (in Dakos; Scheffer), **del Rio** (in Iten et al.). |
| D18 | Invalid ISBNs (biber warnings) | ISBN | `camps2019` and `marriott2018` have two space-separated ISBNs, flagged invalid by biber. Keep one valid ISBN each (or clear the field). |

### D-dupes — duplicate citekeys (biber skips the 2nd; fix in Zotero)

Two Zotero items share each of these citekeys, so Better BibTeX exports the key
twice and **biber keeps only the first**. In Zotero, merge the duplicate items
(or give each a distinct citation key), then re-export.

| citekey | duplicate `@entry` lines in references.bib |
|---|---|
| `braunclarke2006` | 220, 236 |
| `hermann2011` | 720, 728 |
| `munzner2014` | 1212, 1224, **1238** (three copies) |
| `scheffer2009` | 1470, 1485 |
| `sonnewald2021` | 1598, 1615 |
| `ware2021` | 1875, 1888 |

---

## C — Wrong source attached to a claim (Enrico chooses the replacement)

These render fine (no undefined refs); the problem is the *source* is wrong.
A consolidated `% TODO(ENRICO)` block was added at the top of `chapters/03_literature.tex`.

| # | citekey | Where cited now | Problem | Candidate / action |
|---|---|---|---|---|
| C1 | `moere2010` | `03_literature.tex` (§3.4) | Entry is a junk Zotero capture titled **"[Cover Art]"** (IEEE IV 2009, DOI 10.1109/IV.2009.114), used for the data-physicalisation recall claim. | Check **Stusak, Schwarz & Butz (2015), "Evaluating the Memorability of Physical Visualizations", CHI 2015.** |
| C2 | *(Lang 2014)* | **not cited** | Lang (2014, Climatic Change 125) is **no longer cited** in the active sources (no `lang…` key found). | Nothing to do, unless you intend to add it. The uncertainty-band / ensemble-spread claim (§3.3, §7.3.1) is already carried by Harold et al. (2016) and Fischer et al. (2020). |
| C3 | `kause2020`, `kause2021` | `01_introduction.tex`, `03_literature.tex`, `10_discussion.tex` | The **in-text "kause2021"** is actually **Kause et al. 2019** (ERL 14, 114005, food carbon footprints); the entry labelled **"kause2020"** was in fact published **2021**. | Confirm the right paper for each claim (preference-vs-comprehension; icon arrays). Likely target: **Kause et al. (2020), Visualizations of projected rainfall change in the United Kingdom, Sustainability 12, 2955.** |
| C4 | `cabrera2023` | `03_literature.tex` (§3.5) | About describing **AI behaviour to users**, cited for **public climate communication**. | Verify or replace. |
| C5 | `sacha2018` | `03_literature.tex`, `07_translation.tex` | Cited for **latent-space visual analytics** (§3.5, §7.1, §7.3.2) — **this is correct, keep it.** No `sacha2017a/2017b` duplicate exists (already a single key). | For the **effectiveness rule (P0)** the correct source is **Mackinlay (1986)** and/or **Munzner (2014)**, not Sacha — but in the current sources P0 already cites `bertin1983, clevelandmcgill1984, munzner2014`, so no change is needed there. Verify. |
