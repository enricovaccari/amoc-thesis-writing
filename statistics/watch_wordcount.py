from pathlib import Path
import re


# =========================
# Paths
# =========================

ROOT = Path(__file__).resolve().parent.parent

MAIN = ROOT / "main.tex"

CHAPTERS = ROOT / "chapters"

APPENDIX_DIR = ROOT / "appendix"

BIB_FILE = ROOT / "references.bib"

TOC_FILE = ROOT / "main.toc"

OUTPUT = ROOT / "statistics" / "thesis_statistics.tex"


# =========================
# Requirements
# =========================

TARGET_MIN = 15000
TARGET_MAX = 18000

ACCEPTABLE_MIN = 13500
ACCEPTABLE_MAX = 19800

PLACEHOLDER_THRESHOLD = 50

# Words-per-page approximation used by the live watcher. The
# watcher is meant to run instantly on every save, so it does
# NOT read the compiled PDF; it estimates pages from words.
WORDS_PER_PAGE = 350


# =========================
# Fallback chapter names
# =========================
# Only used when a real title cannot be read from the TOC
# (e.g. before the first compile).

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

def read_file(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def count_words(text):
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    return len(words)


def count_occurrences(text, pattern):
    return len(re.findall(pattern, text))


def clean_latex(text):

    # Remove comments
    text = re.sub(r"%.*", "", text)

    # Remove commands
    text = re.sub(
        r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?",
        "",
        text
    )

    # Remove math
    text = re.sub(r"\$.*?\$", "", text)

    return text


def esc(text):
    """
    Escape LaTeX-special characters in a title, idempotently.

    Titles harvested from the .toc are already valid LaTeX: a
    literal ampersand is already written as '\&', inline maths as
    '\(\Psi\)'. Blindly turning every '&' into '\&' and every '\'
    into '\textbackslash' would double-escape them and print a
    stray backslash. So we only escape a special character when it
    is NOT already backslash-protected, and we leave existing
    control sequences (\&, \%, \(...\), \Psi, ...) untouched.
    """

    # Escape a special char only if not already preceded by '\'.
    for ch in "&%$#_":
        text = re.sub(r'(?<!\\)' + re.escape(ch), '\\' + ch, text)

    # Braces: only escape unescaped ones.
    text = re.sub(r'(?<!\\)\{', r'\{', text)
    text = re.sub(r'(?<!\\)\}', r'\}', text)

    # A lone backslash that is NOT the start of a LaTeX command or
    # an escaped special char becomes \textbackslash. A backslash
    # before a letter (\Psi) or a special char (\&) is legitimate.
    text = re.sub(r'\\(?![a-zA-Z]|[&%$#_{}()\[\]])', r'\\textbackslash ', text)

    return text


def prettify_key(key):
    name = re.sub(r"^\d+_", "", key)
    name = re.sub(r"^[A-Z]_", "", name)
    return name.replace("_", " ").title()


def roman(n):
    return {1: "I", 2: "II", 3: "III", 4: "IV",
            5: "V", 6: "VI"}.get(n, str(n))


# =========================
# Thesis structure (parts, appendices) from main.tex
# =========================
# Chapters are grouped into parts exactly as LaTeX groups them:
# by which \part{...} each \input precedes. Chapters appearing
# before the first \part belong to the first part.

def slice_between(text, start_pat, end_pat):
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


def extract_structure(main_text):

    region = slice_between(main_text, r"\\mainmatter", r"\\appendix")
    if not region:
        region = slice_between(main_text, r"\\mainmatter", r"\\backmatter")
    if not region:
        region = main_text

    parts = []
    current_chapters = None
    pre_part = []

    for line in region.splitlines():

        pm = re.search(r"\\part\{([^}]+)\}", line)
        if pm:
            current_chapters = []
            parts.append((pm.group(1).strip(), current_chapters))
            continue

        cm = re.search(r"\\input\{chapters/([^}]+)\}", line)
        if cm:
            key = cm.group(1)
            if current_chapters is None:
                pre_part.append(key)
            else:
                current_chapters.append(key)

    if pre_part and parts:
        parts[0][1][:0] = pre_part
    elif pre_part:
        parts.append(("", pre_part))

    app_region = slice_between(main_text, r"\\appendix", r"\\backmatter")
    if not app_region:
        app_region = slice_between(main_text, r"\\appendix", None)

    appendices = re.findall(r"\\input\{appendix/([^}]+)\}", app_region or "")

    return parts, appendices


# =========================
# Real titles from the TOC (optional)
# =========================

def extract_toc_titles():

    toc = read_file(TOC_FILE)
    if not toc:
        return [], []

    pattern = re.compile(
        r"\\contentsline\s*\{chapter\}"
        r"\{\\numberline\s*\{([^}]+)\}\s*(.*?)\}"
        r"\{[^}]*\}"
    )

    chapters, appendices = [], []

    for number, title in pattern.findall(toc):
        # Titles in the .toc are already valid LaTeX exactly as the
        # thesis typeset them ('\&', inline maths '\(\Psi\)', ...),
        # so they are safe to use verbatim. We only strip pure TOC
        # scaffolding and collapse whitespace; we do NOT remove
        # commands or braces (that would break maths) and we do NOT
        # escape here (esc() does that once, idempotently).
        title = re.sub(r"\\numberline\s*\{[^}]*\}", "", title)
        title = re.sub(r"\\(?:relax|nobreakspace|protect)\b\s*", "", title)
        title = re.sub(r"\s+", " ", title).strip()

        if number.strip().isdigit():
            chapters.append(title)
        else:
            appendices.append(title)

    return chapters, appendices


# =========================
# Bibliography
# =========================

def count_bib_entries():
    text = read_file(BIB_FILE)
    if not text:
        return 0
    entries = re.findall(r"^\s*@(\w+)\s*\{", text, flags=re.MULTILINE)
    ignored = {"comment", "string", "preamble"}
    return len([e for e in entries if e.lower() not in ignored])


# =========================
# Analyse one .tex unit
# =========================

def analyse_unit(key, folder):

    path = folder / (key + ".tex")
    raw = read_file(path)
    cleaned = clean_latex(raw)
    words = count_words(cleaned)

    placeholder = words < PLACEHOLDER_THRESHOLD

    if placeholder:
        pages = "-"
    else:
        pages = max(1, round(words / WORDS_PER_PAGE))

    return {
        "words": words,
        "pages": pages,
        "citations": count_occurrences(raw, r"\\cite[a-zA-Z]*\{"),
        "figures": count_occurrences(raw, r"\\begin\{figure\}"),
        "tables": count_occurrences(raw, r"\\begin\{table\}"),
        "footnotes": count_occurrences(raw, r"\\footnote\{"),
        "placeholder": placeholder,
    }


# =========================
# Analyse thesis
# =========================

main_text = read_file(MAIN)
parts, appendices = extract_structure(main_text)
toc_chapters, toc_appendices = extract_toc_titles()

parts_results = []
grand = {k: 0 for k in
         ("words", "pages", "citations", "figures", "tables", "footnotes")}

chapter_index = 0

for part_title, chapter_keys in parts:

    sub = {k: 0 for k in grand}
    chapter_dicts = []

    for key in chapter_keys:

        stats = analyse_unit(key, CHAPTERS)

        if chapter_index < len(toc_chapters):
            display = toc_chapters[chapter_index]
        else:
            display = CHAPTER_NAMES.get(key, prettify_key(key))

        stats["name"] = display
        chapter_dicts.append(stats)

        if not stats["placeholder"]:
            for k in grand:
                sub[k] += stats[k]
                grand[k] += stats[k]

        chapter_index += 1

    parts_results.append((part_title, chapter_dicts, sub))


# appendices
appendix_results = []
app_acc = {k: 0 for k in grand}

for i, key in enumerate(appendices):

    stats = analyse_unit(key, APPENDIX_DIR)

    if i < len(toc_appendices):
        display = toc_appendices[i]
    else:
        display = prettify_key(key)

    stats["name"] = display
    appendix_results.append(stats)

    if not stats["placeholder"]:
        for k in app_acc:
            app_acc[k] += stats[k]


bib_count = count_bib_entries()

total_words = grand["words"]
total_pages = grand["pages"]


# =========================
# Requirements check (main thesis only)
# =========================

if TARGET_MIN <= total_words <= TARGET_MAX:
    status = "MET"
    message = "The thesis meets the expected word count target."

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
    message = "The thesis does not meet the acceptable word count range."


# =========================
# Build LaTeX rows
# =========================

def data_row(name, r, suffix=""):
    return (
        f"{esc(name)}{suffix} & {r['pages']} & {r['words']} & "
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


body = ""

for idx, (part_title, chapter_dicts, sub) in enumerate(parts_results, start=1):

    body += (
        f"\\multicolumn{{7}}{{l}}{{\\textbf{{Part {roman(idx)} --- "
        f"{esc(part_title)}}}}} \\\\\n\\midrule\n"
    )

    for c in chapter_dicts:
        body += data_row(c["name"], c)

    body += "\\midrule\n"
    body += subtotal_row(f"Subtotal --- Part {roman(idx)}", sub)
    body += "\\midrule\n"

body += (
    f"\\textbf{{TOTAL (main thesis)}} & \\textbf{{{grand['pages']}}} & "
    f"\\textbf{{{grand['words']}}} & \\textbf{{{grand['citations']}}} & "
    f"\\textbf{{{grand['figures']}}} & \\textbf{{{grand['tables']}}} & "
    f"\\textbf{{{grand['footnotes']}}} \\\\\n"
)


# appendix section
appendix_section = ""
if appendix_results:

    app_body = ""
    for ap in appendix_results:
        app_body += data_row(ap["name"], ap, suffix=r"$^{*}$")

    app_body += "\\midrule\n"
    app_body += subtotal_row("Subtotal --- Appendices", app_acc)

    appendix_section = (
        "\\section*{Appendix Statistics}\n\n"
        "\\begin{tabularx}{\\textwidth}{Xrrrrrr}\n\\toprule\n"
        "Appendix & Pages & Words & Citations & Figures & Tables & Footnotes \\\\\n"
        "\\midrule\n"
        f"{app_body}"
        "\\bottomrule\n\\end{tabularx}\n\n"
        "\\vspace{0.3cm}\n\n\\noindent\n"
        "\\textit{$^{*}$ Appendices are reported for reference only and are "
        "excluded from the main thesis length calculation.}\n\n\\vspace{0.5cm}\n\n"
    )


# bibliography section
bibliography_section = (
    "\\section*{Bibliography}\n\n\\noindent\n"
    f"Total references in \\texttt{{references.bib}}: \\textbf{{{bib_count}}}.\n\n"
    "\\vspace{0.2cm}\n\n\\noindent\n"
    "\\textit{The bibliography is reported separately and does not count "
    "towards the thesis word or page totals.}\n\n\\vspace{0.5cm}\n\n"
)


# =========================
# Write LaTeX
# =========================

with open(OUTPUT, "w", encoding="utf-8") as f:

    f.write(
        "\\documentclass[11pt,a4paper]{article}\n\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage[T1]{fontenc}\n"
        "\\usepackage[a4paper,margin=2.5cm]{geometry}\n"
        "\\usepackage{booktabs}\n"
        "\\usepackage{tabularx}\n\n"
        "\\begin{document}\n\n"
        "\\section*{Thesis Statistics}\n\n"
        # Only the title column flexes/wraps; number columns stay
        # narrow and right-aligned, so the table fits \textwidth
        # and long chapter titles wrap instead of overflowing.
        "\\begin{tabularx}{\\textwidth}{Xrrrrrr}\n\\toprule\n"
        "Chapter & Pages & Words & Citations & Figures & Tables & Footnotes\\\\\n"
        "\\midrule\n"
    )

    f.write(body)

    f.write("\\bottomrule\n\\end{tabularx}\n\n\\vspace{1cm}\n\n")

    f.write(appendix_section)
    f.write(bibliography_section)

    f.write(
        "\\section*{Requirements Check}\n\n"
        "\\begin{itemize}\n"
        "\\item Expected length: approximately 50 pages\n"
        "\\item Expected word count: 15,000--18,000 words\n"
        "\\item Acceptable word range: 13,500--19,800 words\n"
        "\\item Status is computed on the main thesis only "
        "(appendices and bibliography excluded)\n"
        "\\end{itemize}\n\n"
        "\\vspace{0.5cm}\n\n\\noindent\n"
        f"\\textbf{{STATUS: {status}}}\n\n"
        "\\vspace{0.2cm}\n\n\\noindent\n"
        f"{message}\n\n"
        "\\vspace{0.3cm}\n\n\\noindent\n"
        "Placeholder chapters containing fewer than 50 words are excluded "
        "from the totals. Page counts here are an estimate of about "
        f"{WORDS_PER_PAGE} words per page, for live monitoring; the compiled "
        "figures in \\texttt{thesis\\_stats.pdf} are authoritative.\n\n"
        "\\end{document}\n"
    )


print(f"Statistics generated: {OUTPUT}")
print(f"Total words (main thesis): {total_words:,}")
print(f"Appendices: {len(appendix_results)} | Bibliography entries: {bib_count}")
print(f"Status: {status}")