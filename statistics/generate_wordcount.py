from pathlib import Path
import re
import sys
import subprocess
from collections import defaultdict

# pypdf is OPTIONAL. It is only used to read the total page count
# of the compiled PDF, which in turn only ever serves as the
# closing boundary of the very last chapter-level TOC entry. If it
# is not installed we fall back to the .toc (see count_pages), so
# the script keeps working in a bare LaTeX environment.
try:
    from pypdf import PdfReader
except ModuleNotFoundError:
    try:
        from PyPDF2 import PdfReader  # older distribution, same API
    except ModuleNotFoundError:
        PdfReader = None


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

FRONT_DIR = ROOT / "frontmatter"

# Front-matter units shown above Part I for reference (word/page
# counts) but NEVER added to the main-thesis totals. (file key, title)
FRONT_UNITS = [
    ("abstract", "Abstract"),
    ("acknowledgements", "Acknowledgements"),
]


# ============================================================
# REQUIREMENTS
# ============================================================

TARGET_MIN = 15000
TARGET_MAX = 18000

ACCEPTABLE_MIN = 13500
ACCEPTABLE_MAX = 19800

# The word count is the ONLY determinant of the requirements
# verdict, which is two-state (YES / NO -- no PARTIALLY). The page
# count is reported (see the Page Breakdown section) but never decides
# the verdict.

# A chapter below this word count is treated as an empty
# placeholder and excluded from the totals.
PLACEHOLDER_THRESHOLD = 50

# A compiled PDF page whose extracted text is shorter than this many
# characters is treated as a blank/filler page (an openright verso
# carries only a running header, ~30-70 chars; real content pages run
# to several hundred). Used to report EFFECTIVE (content) pages.
BLANK_PAGE_MAXLEN = 100


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
    r"""
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
    """
    Total page count of the compiled PDF.

    Uses pypdf when it is installed and the PDF exists. Otherwise
    falls back to the highest arabic page number recorded in the
    .toc, which is a close proxy: this value is only ever consumed
    as the closing boundary of the last chapter-level entry, and
    that entry is always followed by 'References' in the TOC, so
    the fallback never actually changes an emitted page span.
    """

    if PdfReader is not None and PDF_FILE.exists():
        return len(PdfReader(str(PDF_FILE)).pages)

    # ---- fallback: last arabic {page} field in the TOC ----
    toc = read_file(TOC_FILE)
    pages = [int(p) for p in re.findall(r'\}\{(\d+)\}\{', toc)]
    return max(pages) if pages else 0


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


def compute_effective_pages():
    r"""
    EFFECTIVE (content) page counts read from the compiled PDF.

    Unlike the TOC-span method above, this excludes the blank/filler
    versos that an openright book inserts, so the numbers reflect the
    pages a reader actually reads. It relies on two PDF features:

    * page labels: the printed number of each physical page ('iii',
      '1', '2', ...). These give an exact printed<->physical map, so
      roman front matter and arabic body never get confused.
    * extracted text length: a page under BLANK_PAGE_MAXLEN chars is a
      blank/filler page (only a running header) and is not counted.

    Every physical page is assigned to the TOC entry whose printed
    start page precedes it (chapters, part dividers, appendices,
    References). Part-divider and appendix pages therefore fall OUTSIDE
    chapters 1--12, which is what lets us split the thesis into
    'chapters 1--12' and 'everything else'.

    Returns a dict, or None when pypdf / the PDF is unavailable (the
    caller then falls back to the TOC spans):
        {
          "chapters":   {1: 4, 2: 5, ...},   # effective pages
          "appendices": {"A": 4, "B": 4, ...},
          "front":      {"abstract": 1, "acknowledgements": 1},
          "total": 113,        # full PDF
          "ch1_12": 62,        # chapters 1-12, blanks excluded
          "rest": 51,          # total - ch1_12
        }
    """

    if PdfReader is None or not PDF_FILE.exists() or not TOC_FILE.exists():
        return None

    try:
        reader = PdfReader(str(PDF_FILE))
        n = len(reader.pages)
        labels = list(reader.page_labels)
        if len(labels) != n:
            return None
        is_blank = [
            len((reader.pages[i].extract_text() or "").strip()) < BLANK_PAGE_MAXLEN
            for i in range(n)
        ]
    except Exception:
        # main.pdf may be mid-recompile (locked / half-written); skip the
        # page breakdown for this pass and recover on the next one.
        return None

    # First physical index carrying each printed label.
    label_to_phys = {}
    for i, lab in enumerate(labels):
        label_to_phys.setdefault(lab, i)

    toc = read_file(TOC_FILE)

    # ---- body boundaries (arabic printed pages) ----
    boundaries = []  # (printed_start, kind, key)
    for m in re.finditer(
        r'\\contentsline\s*\{(chapter|part)\}\{(.*?)\}\{([^}]*)\}', toc
    ):
        lvl, inner, page = m.group(1), m.group(2), m.group(3)
        if not page.strip().isdigit():
            continue  # roman front matter handled separately
        start = int(page)
        if lvl == "part":
            boundaries.append((start, "part", None))
            continue
        nm = re.match(r'\\numberline\s*\{([^}]+)\}', inner)
        if not nm:
            boundaries.append((start, "refs", None))
        elif nm.group(1).strip().isdigit():
            boundaries.append((start, "chapter", int(nm.group(1))))
        else:
            boundaries.append((start, "appendix", nm.group(1).strip()))
    boundaries.sort()

    def bucket_for(printed_arabic):
        chosen = None
        for start, kind, key in boundaries:
            if start <= printed_arabic:
                chosen = (kind, key)
            else:
                break
        return chosen

    chapters, appendices = {}, {}
    for i in range(n):
        lab = labels[i].strip()
        if not lab.isdigit() or is_blank[i]:
            continue
        b = bucket_for(int(lab))
        if not b:
            continue
        kind, key = b
        if kind == "chapter":
            chapters[key] = chapters.get(key, 0) + 1
        elif kind == "appendix":
            appendices[key] = appendices.get(key, 0) + 1

    # ---- front-matter sections (roman printed pages) ----
    front_entries = []  # (key, printed_label)
    for m in re.finditer(
        r'\\contentsline\s*\{chapter\}\{([^{}]*)\}\{([^}]*)\}', toc
    ):
        title, page = m.group(1), m.group(2).strip()
        if page.isdigit():
            continue
        low = title.lower()
        for key, _ in FRONT_UNITS:
            if key.rstrip("s") in low:
                front_entries.append((key, page))
                break

    front_starts = sorted(
        label_to_phys[p] for _, p in front_entries if p in label_to_phys
    )

    front = {}
    for key, page in front_entries:
        start = label_to_phys.get(page)
        if start is None:
            front[key] = 0
            continue
        # stop at the next front section, or the end of the roman run
        nexts = [s for s in front_starts if s > start]
        stop = min(nexts) if nexts else n
        cnt = 0
        j = start
        while j < stop and not is_blank[j]:
            cnt += 1
            j += 1
        front[key] = cnt

    ch1_12 = sum(v for k, v in chapters.items() if 1 <= k <= 12)

    return {
        "chapters": chapters,
        "appendices": appendices,
        "front": front,
        "total": n,
        "ch1_12": ch1_12,
        "rest": n - ch1_12,
    }


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

def evaluate_requirements(words):
    """
    Two-state verdict based on the WORD COUNT ALONE: YES if the count is
    anywhere within the acceptable range, NO otherwise (no PARTIALLY). A
    specification line still says whether it sits in the ideal target band
    or merely in the wider acceptable band. The page count is reported
    separately (Page Breakdown) and never affects the verdict.
    """

    words_target = TARGET_MIN <= words <= TARGET_MAX
    words_ok = ACCEPTABLE_MIN <= words <= ACCEPTABLE_MAX

    if words_ok:
        label = "YES"
        headline = (
            r"\textbf{YES: Your thesis meets the word-count requirement.}"
        )
        if words_target:
            detail = (
                f"Word count ({words:,}) is within the ideal "
                f"{TARGET_MIN:,}--{TARGET_MAX:,} target range."
            )
        else:
            detail = (
                f"Word count ({words:,}) is within the acceptable "
                f"{ACCEPTABLE_MIN:,}--{ACCEPTABLE_MAX:,} range -- outside the "
                f"ideal {TARGET_MIN:,}--{TARGET_MAX:,} target, but acceptable."
            )

    else:
        label = "NO"
        headline = (
            r"\textbf{NO: Your thesis does not meet the word-count "
            r"requirement.}"
        )
        if words < ACCEPTABLE_MIN:
            detail = (
                f"Word count ({words:,}) is below the acceptable "
                f"minimum ({ACCEPTABLE_MIN:,})."
            )
        else:
            detail = (
                f"Word count ({words:,}) is above the acceptable "
                f"maximum ({ACCEPTABLE_MAX:,})."
            )

    status = (
        headline
        + r"\\"
        + r"\\"
        + detail
        + r"\\"
        + r"\\"
        + r"Acceptable range: 13,500--19,800 words (ideal target: "
        + r"15,000--18,000). This verdict is decided by the word count "
        + r"only; the page count is reported below and does not affect it. "
        + r"Front matter, appendices and the bibliography are excluded "
        + r"from the word total."
    )

    return label, status


# ============================================================
# LATEX HELPERS
# ============================================================

def esc(text):
    r"""
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

def page_breakdown_section(page_info):
    """The bottom Page Breakdown block: chapters 1-12 vs everything else."""

    if not page_info:
        return (
            "\\section*{Page Breakdown}\n\n\\noindent\n\\textit{The page "
            "breakdown needs a compiled \\texttt{main.pdf} and pypdf; "
            "neither was available in this run.}\n"
        )

    ch = page_info["ch1_12"]
    rest = page_info["rest"]
    total = page_info["total"]

    return rf"""
\section*{{Page Breakdown}}

\noindent
Page counts read directly from the compiled \texttt{{main.pdf}}. Blank and
filler pages (the empty versos an openright book inserts) are excluded from
the chapters figure and folded into ``everything else''.

\vspace{{0.2cm}}

\begin{{tabularx}}{{\textwidth}}{{Xr}}
\toprule
Section & Pages \\
\midrule
Chapters 1--12 (content only, blank pages excluded) & {ch} \\
Everything else (front matter, part dividers, appendices, bibliography, blank pages) & {rest} \\
\midrule
\textbf{{Total thesis pages}} & \textbf{{{total}}} \\
\bottomrule
\end{{tabularx}}
"""


def generate_tex(front_results, parts_results, appendix_results,
                 bib_count, page_info):

    grand = defaultdict(int)
    body = ""

    # ---- Front matter: shown for reference, EXCLUDED from totals ----
    if front_results:
        body += (
            "\\multicolumn{7}{l}{\\textbf{Front matter "
            "(excluded from totals)}} \\\\\n\\midrule\n"
        )
        for fu in front_results:
            body += data_row(fu["name"], fu["pages"], fu)
        body += "\\midrule\n"

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

    # ---- Requirements: word count only (pages are informational) ----
    label, status = evaluate_requirements(grand["words"])

    # ---- Page breakdown block (chapters 1-12 vs everything else) ----
    page_section = page_breakdown_section(page_info)

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
words) are shown with a dash and excluded from all totals. The Pages
column shows EFFECTIVE content pages (blank/filler pages excluded);
front matter is listed for reference and excluded from every total.}}

{page_section}

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

    # EFFECTIVE pages from the compiled PDF (blank pages excluded).
    # Falls back to TOC spans when pypdf / the PDF is unavailable.
    page_info = compute_effective_pages()
    chapter_spans, appendix_spans = extract_all_chapter_pages()

    # ---- front matter (Abstract, Acknowledgements): reference only ----
    front_results = []
    for key, title in FRONT_UNITS:
        path = FRONT_DIR / (key + ".tex")
        print("Analysing front matter:", key)
        stats = analyse_unit(path)
        if page_info:
            stats["pages"] = page_info["front"].get(key, "-")
        else:
            stats["pages"] = "-"
        stats["name"] = title
        front_results.append(stats)

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

            # Chapters are numbered 1..N in document order.
            number = chapter_index + 1
            if page_info:
                stats["pages"] = page_info["chapters"].get(number, 0)
            elif chapter_index < len(chapter_spans):
                stats["pages"] = chapter_spans[chapter_index]
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

        letter = chr(ord("A") + i)
        if page_info:
            stats["pages"] = page_info["appendices"].get(letter, 0)
        elif i < len(appendix_spans):
            stats["pages"] = appendix_spans[i]
        else:
            stats["pages"] = 0

        stats["name"] = display
        appendix_results.append(stats)

    # ---- bibliography ----
    bib_count = count_bib_entries()

    # ---- generate + compile ----
    label, total_words, total_pages = generate_tex(
        front_results, parts_results, appendix_results, bib_count, page_info
    )

    print("Generated:", OUTPUT_TEX)
    print(f"Total words (main thesis, excl. placeholders): {total_words:,}")
    print(f"Chapters 1-12 effective pages (blanks excluded): {total_pages}")
    if page_info:
        print(f"Everything else: {page_info['rest']} | "
              f"Total thesis pages: {page_info['total']}")
    print(f"Appendices: {len(appendix_results)}")
    print(f"Bibliography entries: {bib_count}")
    print(f"Status (word count only): {label}")

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


def _watch_loop():
    """
    LIVE mode: re-run this script (one full pass, which recompiles
    statistics/thesis_stats.pdf) every time a thesis source file changes.
    Keep statistics/thesis_stats.pdf open in the VS Code PDF viewer and it
    reloads automatically on each save.
    """

    import time

    self_path = str(Path(__file__).resolve())

    def watched():
        files = [MAIN, TOC_FILE, PDF_FILE, BIB_FILE]
        for d in (ROOT / "chapters", APPENDIX_DIR, FRONT_DIR):
            files += sorted(d.glob("*.tex"))
        return files

    def snapshot():
        snap = {}
        for p in watched():
            try:
                snap[str(p)] = p.stat().st_mtime
            except OSError:
                pass
        return snap

    print("Watching thesis sources... regenerating thesis_stats.pdf on every "
          "save (Ctrl+C to stop).")
    last = None
    try:
        while True:
            snap = snapshot()
            if snap != last:
                # Re-run myself as a plain one-shot (no --watch).
                subprocess.run([sys.executable, self_path])
                last = snap
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped watching.")


if __name__ == "__main__":
    if "--watch" in sys.argv:
        _watch_loop()
    else:
        main()