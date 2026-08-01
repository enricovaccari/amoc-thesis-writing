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

BIB_FILE = ROOT / "references.bib"

APPENDIX_DIR = ROOT / "appendix"


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
        ROOT / "chapters" / filename,
        ROOT / "appendix" / filename,
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


# ============================================================
# THESIS STRUCTURE: PARTS, CHAPTERS, APPENDICES
# ============================================================
#
# The grouping of chapters into parts is read directly from
# main.tex, by tracking which \part{...} each \input precedes.
# This is exactly how LaTeX itself assigns chapters to parts,
# so the statistics can never drift from the compiled thesis
# even if chapters are reordered.

def extract_structure(main_text):
    """
    Returns:
        parts      -> list of (part_title, [chapter_keys]) in order
        appendices -> list of appendix keys (e.g. 'A_ethics')
    """

    # --- main matter region: \mainmatter ... \appendix (or \backmatter) ---
    main_region = _slice(main_text, r'\\mainmatter', r'\\appendix')
    if not main_region:
        main_region = _slice(main_text, r'\\mainmatter', r'\\backmatter')
    if not main_region:
        main_region = main_text

    parts = []
    current_title = None
    current_chapters = None

    # Chapters that appear before the first \part are collected
    # under a provisional bucket and merged into the first real
    # part, matching this thesis where ch.5--6 precede \part{TRANSLATE}
    # yet belong to Part I.
    pre_part_chapters = []

    for line in main_region.splitlines():

        pm = re.search(r'\\part\{([^}]+)\}', line)
        if pm:
            current_title = pm.group(1).strip()
            current_chapters = []
            parts.append((current_title, current_chapters))
            continue

        cm = re.search(r'\\input\{chapters/([^}]+)\}', line)
        if cm:
            key = cm.group(1)
            if current_chapters is None:
                pre_part_chapters.append(key)
            else:
                current_chapters.append(key)

    # Merge any pre-part chapters into the first part.
    if pre_part_chapters and parts:
        parts[0][1][:0] = pre_part_chapters
    elif pre_part_chapters and not parts:
        parts.append(("", pre_part_chapters))

    # --- appendix region: \appendix ... \backmatter (or end) ---
    app_region = _slice(main_text, r'\\appendix', r'\\backmatter')
    if not app_region:
        app_region = _slice(main_text, r'\\appendix', None)

    appendices = re.findall(
        r'\\input\{appendix/([^}]+)\}',
        app_region or ""
    )

    return parts, appendices


def _slice(text, start_pat, end_pat):
    """Return the substring between two regex markers, or ''."""

    s = re.search(start_pat, text)
    if not s:
        return ""

    start = s.end()

    if end_pat is None:
        return text[start:]

    e = re.search(end_pat, text[start:])
    if not e:
        return text[start:]

    return text[start:start + e.start()]


# ============================================================
# CHAPTER / APPENDIX DISPLAY NAMES (from the TOC)
# ============================================================
#
# We want the REAL rendered titles, not the file keys. The .toc
# holds titles exactly as LaTeX typeset them, so it never drifts.
# We map them positionally: chapter entries in document order,
# appendix entries in document order. If the TOC is unavailable
# (e.g. first compile), we fall back to a formatted key.

def extract_toc_titles():
    """
    Returns (chapter_titles, appendix_titles), each a list of
    strings in document order, harvested from main.toc.
    """

    toc = read_file(TOC_FILE)
    if not toc:
        return [], []

    # \contentsline{chapter}{\numberline {3}Literature Review}{15}...
    # Appendices use the same 'chapter' level but a letter number.
    pattern = re.compile(
        r'\\contentsline\s*\{chapter\}'
        r'\{\\numberline\s*\{([^}]+)\}\s*(.*?)\}'
        r'\{[^}]*\}'
    )

    chapter_titles = []
    appendix_titles = []

    for number, title in pattern.findall(toc):
        title = _clean_toc_title(title)
        # Numbered chapters have digit labels; appendices have
        # letter labels (A, B, C).
        if number.strip().isdigit():
            chapter_titles.append(title)
        else:
            appendix_titles.append(title)

    return chapter_titles, appendix_titles


def _clean_toc_title(title):
    """
    Tidy a harvested TOC title WITHOUT breaking its LaTeX.

    Titles in the .toc are already valid LaTeX exactly as the
    thesis typeset them: '&' appears as '\&', inline maths as
    '\(\Psi\)', and so on. They are therefore safe to drop into
    the stats table verbatim. We only strip a couple of things
    that are pure TOC scaffolding and never meant to render:
    a stray leading \numberline, hyperlink wrappers, and any
    protecting \relax / \nobreakspace noise, then collapse
    whitespace. Crucially we do NOT escape these titles again
    (see the note in the title-selection code): re-escaping an
    already-escaped '\&' is what put a stray backslash in the PDF.
    """

    # Remove hyperref anchors like \numberline{..} residue and
    # \hbox/\relax scaffolding, but keep real content commands.
    title = re.sub(r'\\numberline\s*\{[^}]*\}', '', title)
    title = re.sub(r'\\(?:relax|nobreakspace|protect)\b\s*', '', title)

    # Collapse whitespace. Leave \&, \%, \(\Psi\) etc. intact.
    title = re.sub(r'\s+', ' ', title).strip()

    return title


def prettify_key(key):
    """Fallback display name from a file key: '03_literature' -> 'Literature'."""

    name = re.sub(r'^\d+_', '', key)
    name = re.sub(r'^[A-Z]_', '', name)   # appendix keys like 'A_ethics'
    return name.replace("_", " ").title()


# ============================================================
# PDF PAGE COUNT
# ============================================================

def count_pages():

    if not PDF_FILE.exists():
        return 0

    reader = PdfReader(str(PDF_FILE))

    return len(reader.pages)


def extract_all_chapter_pages():
    """
    Page spans for every numbered 'chapter'-level TOC entry,
    split by the entry's LABEL rather than by position.

    Two subtleties this handles:

    1. Appendices are chapter-level entries whose \numberline
       label is a LETTER (A, B, C); real chapters carry a DIGIT.
       Splitting by label keeps them correctly separated even
       when the thesis has placeholder chapters.

    2. The span of an entry is (next entry's start page - 1).
       The entry that FOLLOWS the last appendix is often an
       UNNUMBERED chapter-level entry such as "References" or
       "Bibliography" (no \numberline). If we ignore those, the
       last appendix has no closing boundary and stretches all
       the way to the end of the PDF, hugely inflating its page
       count. So we collect unnumbered chapter entries too and
       use them purely as closing boundaries — we never emit a
       span for them.

    Front-matter entries (Abstract, Acknowledgements, ...) sit on
    roman-numeral pages; their {page} field is not arabic, so the
    arabic-only page pattern skips them and they cannot corrupt
    the spans.

    Returns (chapter_spans, appendix_spans): two lists of integer
    page counts, in document order.
    """

    if not TOC_FILE.exists():
        return [], []

    toc = read_file(TOC_FILE)

    total = count_pages()

    # Scan every chapter-level entry that sits on an ARABIC page.
    # Group 1 = the inner title blob, group 2 = the start page.
    # An entry is a measurable 'body' entry if its inner blob
    # begins with \numberline; otherwise it is a 'boundary'
    # (References, Bibliography, ...) used only to close spans.
    points = []

    for m in re.finditer(
        r'\\contentsline\s*\{chapter\}\{(.*?)\}\{(\d+)\}',
        toc
    ):
        inner, page = m.group(1), int(m.group(2))

        nm = re.match(r'\\numberline\s*\{([^}]+)\}', inner)
        if nm:
            points.append(("body", nm.group(1).strip(), page))
        else:
            points.append(("boundary", None, page))

    chapter_spans = []
    appendix_spans = []

    for i, (kind, label, start) in enumerate(points):

        if kind != "body":
            continue  # boundaries are used below, never emitted

        # Closing page = (start of the next point) - 1, where the
        # next point may be another body entry OR a boundary such
        # as References. If none follows, close at end of PDF.
        if i < len(points) - 1:
            end = points[i + 1][2] - 1
        else:
            end = total

        span = end - start + 1
        if span < 0:
            span = 0

        if label.isdigit():
            chapter_spans.append(span)
        else:
            appendix_spans.append(span)

    return chapter_spans, appendix_spans


# ============================================================
# BIBLIOGRAPHY
# ============================================================

def count_bib_entries():
    """
    Count bibliographic entries in references.bib by counting
    top-level @type{key,...} declarations, ignoring @comment,
    @string and @preamble which are not references.
    """

    text = read_file(BIB_FILE)
    if not text:
        return 0

    entries = re.findall(r'^\s*@(\w+)\s*\{', text, flags=re.MULTILINE)

    ignored = {"comment", "string", "preamble"}

    return len([e for e in entries if e.lower() not in ignored])


# ============================================================
# ANALYSE A SINGLE .tex UNIT (chapter or appendix)
# ============================================================

def analyse_unit(path):

    expanded = expand_inputs(read_file(path), path.parent)

    words = count_words(expanded)

    return {
        "words": words,
        "citations": count_citations(expanded),
        "figures": count_figures(expanded),
        "tables": count_env(expanded, "table"),
        "footnotes": count_footnotes(expanded),
        "placeholder": words < PLACEHOLDER_THRESHOLD,
    }


# ============================================================
# REQUIREMENTS CHECK (three states) — MAIN THESIS ONLY
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
        + r"words (acceptable range: 13,500--19,800 words). "
        + r"Appendices and bibliography are excluded from this check."
    )

    return label, status


# ============================================================
# LATEX HELPERS
# ============================================================

def esc(text):
    """
    Escape LaTeX-special characters in a title, idempotently.

    Titles harvested from the .toc are already valid LaTeX: a
    literal ampersand is already written as '\&', inline maths as
    '\(\Psi\)'. Blindly turning every '&' into '\&' and every '\'
    into '\textbackslash' would double-escape them and print a
    stray backslash. So we only escape a special character when it
    is *not* already backslash-protected, and we leave existing
    control sequences (\&, \%, \(...\), \Psi, ...) untouched.

    Fallback names built from file keys are plain text with no
    backslashes, so they are escaped normally by the same rules.
    """

    # Escape a special char only if not already preceded by '\'.
    # (?<!\\) is a negative lookbehind for a backslash.
    for ch in "&%$#_":
        text = re.sub(r'(?<!\\)' + re.escape(ch), '\\' + ch, text)

    # Braces: only escape unescaped ones.
    text = re.sub(r'(?<!\\)\{', r'\{', text)
    text = re.sub(r'(?<!\\)\}', r'\}', text)

    # A lone backslash that is NOT the start of a LaTeX command or
    # an escaped special char becomes \textbackslash. A backslash
    # followed by a letter (\Psi) or by a special char (\&) is
    # legitimate and left alone.
    text = re.sub(r'\\(?![a-zA-Z]|[&%$#_{}()\[\]])', r'\\textbackslash ', text)

    return text


def data_row(name, pages_cell, r, suffix=""):
    """
    One tabular row from a stats dict r plus a pages cell.
    `suffix` is appended after escaping, so LaTeX markers such as
    the appendix asterisk are not themselves escaped.
    """

    return (
        f"{esc(name)}{suffix} & {pages_cell} & {r['words']} & "
        f"{r['citations']} & {r['figures']} & "
        f"{r['tables']} & {r['footnotes']} \\\\\n"
    )


def subtotal_row(label, acc):

    return (
        f"\\textit{{{esc(label)}}} & \\textit{{{acc['pages']}}} & "
        f"\\textit{{{acc['words']}}} & \\textit{{{acc['citations']}}} & "
        f"\\textit{{{acc['figures']}}} & \\textit{{{acc['tables']}}} & "
        f"\\textit{{{acc['footnotes']}}} \\\\\n"
    )


# ============================================================
# CREATE LATEX REPORT
# ============================================================

def generate_tex(parts_results, appendix_results, bib_count):

    grand = defaultdict(int)
    body = ""

    # ---- Parts, each with its own subtotal ----
    for part_idx, (part_title, chapters) in enumerate(parts_results, start=1):

        sub = defaultdict(int)

        body += (
            f"\\multicolumn{{7}}{{l}}{{\\textbf{{Part {_roman(part_idx)} --- "
            f"{esc(part_title)}}}}} \\\\\n\\midrule\n"
        )

        for ch in chapters:

            if ch["placeholder"]:
                pages_cell = "-"
            else:
                pages_cell = ch["pages"]
                for k in ("pages", "words", "citations",
                          "figures", "tables", "footnotes"):
                    sub[k] += ch[k]
                    grand[k] += ch[k]

            body += data_row(ch["name"], pages_cell, ch)

        body += "\\midrule\n"
        body += subtotal_row(f"Subtotal --- Part {_roman(part_idx)}", sub)
        body += "\\midrule\n"

    # ---- Grand total (main thesis only) ----
    body += (
        f"\\textbf{{TOTAL (main thesis)}} & \\textbf{{{grand['pages']}}} & "
        f"\\textbf{{{grand['words']}}} & \\textbf{{{grand['citations']}}} & "
        f"\\textbf{{{grand['figures']}}} & \\textbf{{{grand['tables']}}} & "
        f"\\textbf{{{grand['footnotes']}}} \\\\\n"
    )

    # ---- Appendix section ----
    app_body = ""
    app_acc = defaultdict(int)

    for ap in appendix_results:
        pages_cell = ap["pages"] if not ap["placeholder"] else "-"
        app_body += data_row(ap["name"], pages_cell, ap, suffix=r"$^{*}$")
        for k in ("pages", "words", "citations",
                  "figures", "tables", "footnotes"):
            app_acc[k] += ap[k]

    if appendix_results:
        app_body += "\\midrule\n"
        app_body += subtotal_row("Subtotal --- Appendices", app_acc)

    # ---- Requirements: MAIN THESIS ONLY ----
    label, status = evaluate_requirements(grand["words"], grand["pages"])

    # ---- Assemble document ----
    appendix_section = ""
    if appendix_results:
        appendix_section = rf"""
\section*{{Appendix Statistics}}

\begin{{tabularx}}{{\textwidth}}{{Xrrrrrr}}
\toprule
Appendix & Pages & Words & Citations & Figures & Tables & Footnotes \\
\midrule
{app_body}\bottomrule
\end{{tabularx}}

\vspace{{0.3cm}}

\noindent
\textit{{$^{{*}}$ Appendices are reported for reference only and are
excluded from the main thesis length calculation.}}
"""

    bibliography_section = rf"""
\section*{{Bibliography}}

\noindent
Total references in \texttt{{references.bib}}: \textbf{{{bib_count}}}.

\vspace{{0.2cm}}

\noindent
\textit{{The bibliography is reported separately and does not count
towards the thesis word or page totals.}}
"""

    tex = rf"""
\documentclass[11pt,a4paper]{{article}}

\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage[a4paper,margin=2.5cm]{{geometry}}
\usepackage{{booktabs}}
\usepackage{{tabularx}}

% Only the first (title) column flexes and wraps; the six numeric
% columns keep their natural narrow width, right-aligned. This
% makes the table fill \textwidth exactly and long chapter titles
% wrap onto a second line instead of overflowing the page.
\begin{{document}}


\section*{{Thesis Statistics}}

\begin{{tabularx}}{{\textwidth}}{{Xrrrrrr}}
\toprule
Chapter & Pages & Words & Citations & Figures & Tables & Footnotes \\
\midrule
{body}\bottomrule
\end{{tabularx}}


\vspace{{1cm}}

\noindent
{status}


\vspace{{0.4cm}}

\noindent
\textit{{Placeholder chapters (fewer than {PLACEHOLDER_THRESHOLD}
words) are shown with a dash and excluded from all totals.}}

{appendix_section}

{bibliography_section}

\end{{document}}
"""

    OUTPUT_TEX.write_text(tex, encoding="utf8")

    return label, grand["words"], grand["pages"]


def _roman(n):
    return {1: "I", 2: "II", 3: "III", 4: "IV",
            5: "V", 6: "VI"}.get(n, str(n))


# ============================================================
# MAIN
# ============================================================

def main():

    print("Reading thesis...")

    main_text = read_file(MAIN)

    parts, appendices = extract_structure(main_text)

    toc_chapter_titles, toc_appendix_titles = extract_toc_titles()

    # Page spans are already split by TOC label: chapters carry
    # digit labels, appendices carry letter labels. This stays
    # aligned even when the thesis has placeholder chapters.
    chapter_pages, appendix_pages = extract_all_chapter_pages()

    # ---- analyse chapters, grouped by part ----
    parts_results = []
    chapter_index = 0

    for part_title, chapter_keys in parts:

        chapter_dicts = []

        for key in chapter_keys:

            path = ROOT / "chapters" / (key + ".tex")
            print("Analysing:", key)

            stats = analyse_unit(path)

            # Prefer the real TOC title; fall back to the key.
            if chapter_index < len(toc_chapter_titles):
                display = toc_chapter_titles[chapter_index]
            else:
                display = prettify_key(key)

            if chapter_index < len(chapter_pages):
                stats["pages"] = chapter_pages[chapter_index]
            else:
                stats["pages"] = 0

            stats["name"] = display
            chapter_dicts.append(stats)
            chapter_index += 1

        parts_results.append((part_title, chapter_dicts))

    # ---- analyse appendices ----
    appendix_results = []

    for i, key in enumerate(appendices):

        path = APPENDIX_DIR / (key + ".tex")
        print("Analysing appendix:", key)

        stats = analyse_unit(path)

        if i < len(toc_appendix_titles):
            display = toc_appendix_titles[i]
        else:
            display = prettify_key(key)

        if i < len(appendix_pages):
            stats["pages"] = appendix_pages[i]
        else:
            stats["pages"] = 0

        stats["name"] = display
        appendix_results.append(stats)

    # ---- bibliography ----
    bib_count = count_bib_entries()

    # ---- generate + compile ----
    label, total_words, total_pages = generate_tex(
        parts_results, appendix_results, bib_count
    )

    print("Generated:", OUTPUT_TEX)
    print(f"Total words (main thesis, excl. placeholders): {total_words:,}")
    print(f"Total pages (main thesis, excl. placeholders): {total_pages}")
    print(f"Appendices: {len(appendix_results)}")
    print(f"Bibliography entries: {bib_count}")
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


if __name__ == "__main__":
    main()