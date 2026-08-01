from pathlib import Path
import re


# =========================
# Paths
# =========================

ROOT = Path(__file__).resolve().parent.parent

CHAPTERS = ROOT / "chapters"

OUTPUT = ROOT / "statistics" / "thesis_statistics.tex"


# =========================
# Requirements
# =========================

TARGET_MIN = 15000
TARGET_MAX = 18000

ACCEPTABLE_MIN = 13500
ACCEPTABLE_MAX = 19800

PLACEHOLDER_THRESHOLD = 50


# =========================
# Chapter names
# =========================

CHAPTER_NAMES = {
    "01_introduction": "Introduction",
    "02_research_questions": "Research Questions",
    "03_literature": "Literature Review",
    "04_background": "Background",
    "05_methodology": "Methodology",
    "06_data_pipeline": "Data Pipeline",
    "07_translation": "Translation",
    "08_evaluation": "Evaluation",
    "09_results": "Results",
    "10_discussion": "Discussion",
    "11_conclusion": "Conclusion",
    "12_reflection": "Reflection",
}


# =========================
# Utilities
# =========================

def count_words(text):

    words = re.findall(
        r"\b[a-zA-Z]+\b",
        text
    )

    return len(words)



def count_occurrences(text, pattern):

    return len(
        re.findall(pattern, text)
    )



def clean_latex(text):

    # Remove comments
    text = re.sub(
        r"%.*",
        "",
        text
    )

    # Remove commands
    text = re.sub(
        r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?",
        "",
        text
    )

    # Remove math
    text = re.sub(
        r"\$.*?\$",
        "",
        text
    )

    return text



# =========================
# Analyse chapters
# =========================

chapters_data = []

total_words = 0
total_pages = 0
total_citations = 0
total_figures = 0
total_tables = 0
total_footnotes = 0


for chapter_file in sorted(CHAPTERS.glob("*.tex")):

    chapter_id = chapter_file.stem

    if chapter_id not in CHAPTER_NAMES:
        continue


    raw = chapter_file.read_text(
        encoding="utf-8"
    )

    cleaned = clean_latex(raw)

    words = count_words(cleaned)


    # Placeholder exclusion
    if words < PLACEHOLDER_THRESHOLD:

        pages = "-"
        included = False

    else:

        included = True

        # Approximation:
        # around 350 words/page
        pages = round(words / 350)

        if pages == 0:
            pages = 1



    citations = count_occurrences(
        raw,
        r"\\cite[a-zA-Z]*\{"
    )

    figures = count_occurrences(
        raw,
        r"\\begin\{figure\}"
    )

    tables = count_occurrences(
        raw,
        r"\\begin\{table\}"
    )

    footnotes = count_occurrences(
        raw,
        r"\\footnote\{"
    )


    chapters_data.append(
        {
            "name": CHAPTER_NAMES[chapter_id],
            "pages": pages,
            "words": words,
            "citations": citations,
            "figures": figures,
            "tables": tables,
            "footnotes": footnotes,
        }
    )


    if included:

        total_words += words

        total_pages += pages

        total_citations += citations
        total_figures += figures
        total_tables += tables
        total_footnotes += footnotes



# =========================
# Requirements check
# =========================

if TARGET_MIN <= total_words <= TARGET_MAX:

    status = "MET"

    message = (
        "The thesis meets the expected word count target."
    )


elif ACCEPTABLE_MIN <= total_words <= ACCEPTABLE_MAX:

    status = "PARTIALLY MET"

    message = (
        f"The thesis satisfies the minimum acceptable word count "
        f"range ({total_words:,} words), but additional written "
        "content is recommended to reach the expected target "
        "length of approximately 15,000--18,000 words."
    )


else:

    status = "NOT MET"

    message = (
        "The thesis does not meet the acceptable word count range."
    )



# =========================
# Generate LaTeX
# =========================

with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:


    f.write(
r"""\documentclass[11pt,a4paper]{article}

\usepackage[a4paper,margin=2cm]{geometry}
\usepackage{booktabs}

\begin{document}

\section*{Thesis Statistics}

\begin{tabular}{lrrrrrr}
\toprule
Chapter & Pages & Words & Citations & Figures & Tables & Footnotes\\
\midrule
"""
    )


    for c in chapters_data:

        f.write(
            f"{c['name']} & "
            f"{c['pages']} & "
            f"{c['words']} & "
            f"{c['citations']} & "
            f"{c['figures']} & "
            f"{c['tables']} & "
            f"{c['footnotes']} \\\\\n"
        )


    f.write(
f"""
\\midrule

TOTAL & {total_pages} & {total_words} &
{total_citations} & {total_figures} &
{total_tables} & {total_footnotes}
\\\\

\\bottomrule
\\end{{tabular}}


\\vspace{{1cm}}

\\section*{{Requirements Check}}

\\begin{{itemize}}
\\item Expected length: approximately 50 pages
\\item Expected word count: 15,000--18,000 words
\\item Acceptable word range: 13,500--19,800 words
\\end{{itemize}}


\\vspace{{0.5cm}}

\\noindent
\\textbf{{STATUS: {status}}}


\\vspace{{0.2cm}}

\\noindent
{message}


\\vspace{{0.3cm}}

\\noindent
Placeholder chapters containing fewer than 50 words are excluded
from the page count calculation.


\\end{{document}}
"""
    )


print(
    f"Statistics generated: {OUTPUT}"
)

print(
    f"Total words: {total_words}"
)

print(
    f"Status: {status}"
)