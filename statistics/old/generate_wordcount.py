from pathlib import Path
import re
import subprocess
from collections import defaultdict
from pypdf import PdfReader


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

MAIN = ROOT / "main.tex"

STAT_DIR = ROOT / "statistics"

OUTPUT_TEX = STAT_DIR / "thesis_stats.tex"

PDF_FILE = ROOT / "main.pdf"

TOC_FILE = ROOT / "main.toc"


# ============================================================
# REQUIREMENTS
# ============================================================

TARGET_MIN = 15000
TARGET_MAX = 18000

ACCEPTABLE_MIN = 13500
ACCEPTABLE_MAX = 19800

PAGES_MIN = 45
PAGES_MAX = 55

# A chapter below this word count is treated as an empty
# placeholder and excluded from the totals.
PLACEHOLDER_THRESHOLD = 50


# ============================================================
# READ FILES
# ============================================================

def read_file(path):

    if not path.exists():
        return ""

    return path.read_text(
        encoding="utf-8",
        errors="ignore"
    )


def resolve_tex_file(filename, current_dir):

    if not filename.endswith(".tex"):
        filename += ".tex"

    candidates = [
        current_dir / filename,
        ROOT / filename,
        ROOT / "chapters" / filename
    ]

    for c in candidates:
        if c.exists():
            return c

    return None


def expand_inputs(text, current_dir, visited=None):

    if visited is None:
        visited = set()

    pattern = r'\\(?:input|include)\{([^}]+)\}'

    def replace(match):

        target = resolve_tex_file(
            match.group(1),
            current_dir
        )

        if target is None:
            return ""

        if target in visited:
            return ""

        visited.add(target)

        return expand_inputs(
            read_file(target),
            target.parent,
            visited
        )

    return re.sub(
        pattern,
        replace,
        text
    )


# ============================================================
# CLEAN TEXT FOR WORD COUNT
# ============================================================

def clean_text(text):

    # remove comments
    text = re.sub(r'(?<!\\)%.*', '', text)

    # remove figures completely
    text = re.sub(
        r'\\begin\{figure\}.*?\\end\{figure\}',
        '', text, flags=re.DOTALL
    )

    # remove tables completely
    text = re.sub(
        r'\\begin\{table\}.*?\\end\{table\}',
        '', text, flags=re.DOTALL
    )

    # remove captions
    text = re.sub(
        r'\\caption\{.*?\}',
        '', text, flags=re.DOTALL
    )

    # remove footnotes from word count
    text = re.sub(
        r'\\footnote\{.*?\}',
        '', text, flags=re.DOTALL
    )

    # remove latex commands
    text = re.sub(
        r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?',
        ' ', text
    )

    text = text.replace("{", " ").replace("}", " ")

    return text


def count_words(text):

    cleaned = clean_text(text)

    words = re.findall(
        r"\b[A-Za-zÀ-ÿ]+\b",
        cleaned
    )

    return len(words)


# ============================================================
# OTHER COUNTERS
# ============================================================

def count_citations(text):

    matches = re.findall(
        r'\\(?:cite|citep|citet|parencite|textcite)\{([^}]*)\}',
        text
    )

    total = 0

    for m in matches:
        total += len(
            [x for x in m.split(",") if x.strip()]
        )

    return total


def count_env(text, env):

    return len(
        re.findall(rf'\\begin\{{{env}\}}', text)
    )


def count_footnotes(text):

    return len(re.findall(r'\\footnote\{', text))


def count_figures(text):

    return len(re.findall(r'\\begin\{figure\}', text))


def extract_chapters(main_text):

    chapters = []

    for x in re.findall(
        r'\\input\{chapters/([^}]+)\}',
        main_text
    ):

        clean_name = re.sub(r'^\d+_', '', x)

        chapters.append(
            (
                clean_name.replace("_", " "),
                ROOT / "chapters" / (x + ".tex")
            )
        )

    return chapters


# ============================================================
# PDF PAGE COUNT
# ============================================================

def count_pages():

    if not PDF_FILE.exists():
        return 0

    reader = PdfReader(str(PDF_FILE))

    return len(reader.pages)


def extract_chapter_pages():

    if not TOC_FILE.exists():
        return []

    toc = read_file(TOC_FILE)

    # Match only real chapter lines. The \numberline group is
    # required, which filters out unnumbered front/back matter
    # and any spurious \contentsline entries that were inflating
    # the page count.
    pattern = re.compile(
        r'\\contentsline\s*\{chapter\}'
        r'\{\\numberline\s*\{[^}]+\}[^}]*\}'
        r'\{(\d+)\}'
    )

    starts = [int(page) for page in pattern.findall(toc)]

    pages = []
    total = count_pages()

    for i, start in enumerate(starts):

        if i < len(starts) - 1:
            end = starts[i + 1] - 1
        else:
            end = total

        span = end - start + 1

        # Guard against malformed TOC entries producing
        # negative or absurd spans.
        if span < 0:
            span = 0

        pages.append(span)

    return pages


# ============================================================
# REQUIREMENTS CHECK (three states)
# ============================================================

def evaluate_requirements(words, pages):

    words_target = TARGET_MIN <= words <= TARGET_MAX
    words_ok = ACCEPTABLE_MIN <= words <= ACCEPTABLE_MAX
    pages_ok = PAGES_MIN <= pages <= PAGES_MAX

    if words_target and pages_ok:
        label = "YES"
        headline = (
            r"\textbf{YES: Your thesis meets the expected "
            r"requirements.}"
        )
        detail = (
            f"Word count ({words:,}) is within the target range, "
            f"and the length ({pages} pages) is within the "
            f"expected range."
        )

    elif words_ok and pages_ok:
        label = "PARTIALLY"
        headline = (
            r"\textbf{PARTIALLY: Your thesis is within the "
            r"acceptable range but not the expected target.}"
        )
        detail = (
            f"Word count ({words:,}) falls inside the acceptable "
            f"range but outside the {TARGET_MIN:,}--{TARGET_MAX:,} "
            f"target; the length is {pages} pages. Additional "
            f"content is recommended to reach the target."
        )

    else:
        label = "NO"
        headline = (
            r"\textbf{NO: Your thesis does not meet the expected "
            r"requirements.}"
        )

        reasons = []
        if not words_ok:
            reasons.append(
                f"word count ({words:,}) is outside the acceptable "
                f"range ({ACCEPTABLE_MIN:,}--{ACCEPTABLE_MAX:,})"
            )
        if not pages_ok:
            reasons.append(
                f"page count ({pages}) is outside the expected "
                f"range ({PAGES_MIN}--{PAGES_MAX})"
            )

        detail = "Reason: " + "; ".join(reasons) + "."

    status = (
        headline
        + r"\\"
        + r"\\"
        + detail
        + r"\\"
        + r"\\"
        + r"Target: approximately 50 pages and 15,000--18,000 "
        + r"words (acceptable range: 13,500--19,800 words)."
    )

    return label, status


# ============================================================
# CREATE LATEX REPORT
# ============================================================

def generate_tex(results, total_pages_pdf):

    totals = defaultdict(int)

    rows = ""

    for r in results:

        # Placeholder rows show a dash and are NOT summed.
        if r["placeholder"]:
            pages_cell = "-"
            words_cell = r["words"]
        else:
            pages_cell = r["pages"]
            words_cell = r["words"]

            for k in (
                "pages", "words", "citations",
                "figures", "tables", "footnotes"
            ):
                v = r[k]
                if isinstance(v, int):
                    totals[k] += v

        rows += f"""
{r['chapter']}
&
{pages_cell}
&
{words_cell}
&
{r['citations']}
&
{r['figures']}
&
{r['tables']}
&
{r['footnotes']}
\\\\
"""

    words = totals["words"]
    total_pages = totals["pages"]

    label, status = evaluate_requirements(words, total_pages)

    tex = rf"""
\documentclass[11pt,a4paper]{{article}}

\usepackage[a4paper,margin=2cm]{{geometry}}
\usepackage{{booktabs}}

\begin{{document}}


\section*{{Thesis Statistics}}


\begin{{tabular}}{{lrrrrrr}}

\toprule

Chapter & Pages & Words & Citations & Figures & Tables & Footnotes \\

\midrule

{rows}

\midrule

TOTAL
&
{total_pages}
&
{totals['words']}
&
{totals['citations']}
&
{totals['figures']}
&
{totals['tables']}
&
{totals['footnotes']}

\\

\bottomrule

\end{{tabular}}


\vspace{{1cm}}

\noindent
{status}


\vspace{{0.4cm}}

\noindent
\textit{{Placeholder chapters (fewer than {PLACEHOLDER_THRESHOLD}
words) are shown with a dash and excluded from all totals.}}


\end{{document}}

"""

    OUTPUT_TEX.write_text(tex, encoding="utf8")

    return label, words, total_pages


# ============================================================
# MAIN
# ============================================================

print("Reading thesis...")

main_text = read_file(MAIN)

chapters = extract_chapters(main_text)

results = []

chapter_pages = extract_chapter_pages()

for name, path in chapters:

    print("Analysing:", name)

    expanded = expand_inputs(
        read_file(path),
        path.parent
    )

    words = count_words(expanded)

    is_placeholder = words < PLACEHOLDER_THRESHOLD

    if len(results) < len(chapter_pages):
        pages = chapter_pages[len(results)]
    else:
        pages = 0

    results.append({
        "chapter": name.replace("_", " "),
        "pages": pages,
        "words": words,
        "citations": count_citations(expanded),
        "figures": count_figures(expanded),
        "tables": count_env(expanded, "table"),
        "footnotes": count_footnotes(expanded),
        "placeholder": is_placeholder,
    })


pdf_pages = count_pages()

label, total_words, total_pages = generate_tex(results, pdf_pages)

print("Generated:", OUTPUT_TEX)
print(f"Total words (excl. placeholders): {total_words:,}")
print(f"Total pages (excl. placeholders): {total_pages}")
print(f"Status: {label}")


subprocess.run(
    [
        "pdflatex",
        "-interaction=batchmode",
        "-output-directory",
        str(STAT_DIR),
        str(OUTPUT_TEX)
    ]
)

print("PDF created:", STAT_DIR / "thesis_stats.pdf")