# Making the Invisible Intelligible — Thesis Project

LaTeX skeleton for Enrico Vaccari's MSc thesis. Sober academic styling, APA 7
bibliography via biblatex + biber, three-part structure (Foundations,
Translation, Evaluation).

## How to use on Overleaf

1. Compress the entire `amoc-thesis-latex/` folder into a `.zip`.
2. On Overleaf: **New Project → Upload Project → select the zip**.
3. Open Menu (top-left in editor) and set:
   - **Compiler**: pdfLaTeX (LuaLaTeX also works; XeLaTeX should too)
   - **Main document**: `main.tex`
4. Click **Recompile**. First compile may take ~60 seconds because biber
   builds the bibliography. From then on it's fast.

If biber fails on first run, click the dropdown next to Recompile and pick
"Clear cached files", then recompile.

## Project layout

```
main.tex                   ← root file; preamble + chapter includes
references.bib             ← BibTeX database (seeded)
.gitignore                 ← LaTeX build artefacts
frontmatter/
    titlepage.tex
    abstract.tex
    acknowledgements.tex
chapters/
    01_introduction.tex    ← §1.1 and §1.2 drafted in full
    02_research_questions.tex
    03_literature.tex
    04_background.tex
    05_methodology.tex
    06_data_pipeline.tex
    07_translation.tex
    08_evaluation.tex
    09_results.tex
    10_discussion.tex
    11_conclusion.tex
appendix/
    A_ethics.tex
    B_protocols.tex
    C_code.tex
figures/                   ← drop figure files here
```

## Connecting to GitHub

Two options:

- **Overleaf Premium (paid)**: native GitHub sync via Menu → GitHub.
- **Free account**: clone the Overleaf project locally via git
  (Menu → Git → Clone with Git), push to GitHub manually. The Overleaf
  remote URL stays as the working copy; GitHub becomes the public mirror.

## Writing conventions

- All chapter files are independent; the master file `main.tex` controls
  inclusion order.
- Citations use `\citep{key}` (parenthetical) or `\citet{key}` (textual).
- Section labels follow `sec:short-name`; chapter labels `ch:short-name`.
- Quotation marks: use `` ``text'' `` (LaTeX quotes), not Unicode quotes.
- Em-dashes: `---` (three hyphens) produce the long dash.
