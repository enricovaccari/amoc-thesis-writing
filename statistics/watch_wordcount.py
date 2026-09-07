from pathlib import Path
import re
import sys

# Reuse the authoritative page logic from generate_wordcount so the two
# scripts always agree. Adding this file's own folder to sys.path lets
# the import work regardless of the current working directory. Importing
# the module has no side effects (its main() runs only under __main__).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_wordcount import (          # noqa: E402
    compute_effective_pages,
    expand_inputs,
    FRONT_UNITS,
    FRONT_DIR,
)


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
    # Match generate_wordcount.py: allow accented letters so the two
    # scripts count the same words.
    words = re.findall(r"\b[A-Za-zÀ-ÿ]+\b", text)
    return len(words)


def count_occurrences(text, pattern):
    return len(re.findall(pattern, text))


def count_citations(text):
    # Same rule as generate_wordcount.py: count every key inside a
    # citation command, including \parencite and \textcite (which the
    # old \\cite[a-zA-Z]* pattern silently missed), and split on commas
    # so \citep{a,b} counts as two.
    matches = re.findall(
        r"\\(?:cite|citep|citet|parencite|textcite)\{([^}]*)\}",
        text
    )
    total = 0
    for m in matches:
        total += len([x for x in m.split(",") if x.strip()])
    return total


def clean_latex(text):
    # Mirror generate_wordcount.py's clean_text so both scripts exclude
    # the same material (figures, tables, captions, footnotes) and thus
    # report the same word counts for figure/table-heavy chapters such
    # as 09_results.

    # remove comments (but keep an escaped \%)
    text = re.sub(r"(?<!\\)%.*", "", text)

    # remove whole figure and table environments
    text = re.sub(r"\\begin\{figure\}.*?\\end\{figure\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\\begin\{table\}.*?\\end\{table\}", "", text, flags=re.DOTALL)

    # remove the per-chapter "Addressed: ..." keyword boxes (a bare tabular,
    # a navigation aid rather than prose) so they do not count as words.
    text = re.sub(
        r"\\begin\{tabular\}.*?\\end\{tabular\}",
        lambda m: "" if "Addressed" in m.group(0) else m.group(0),
        text, flags=re.DOTALL,
    )

    # drop captions and footnotes from the word count
    text = re.sub(r"\\caption\{.*?\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\\footnote\{.*?\}", "", text, flags=re.DOTALL)

    # remove remaining latex commands
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?", " ", text)

    text = text.replace("{", " ").replace("}", " ")

    return text


def esc(text):
    r"""
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

    # Expand \input/\include first (shared with generate_wordcount) so
    # figures and tables kept in separate files (e.g. \input{figures/...})
    # are counted, exactly like the authoritative script.
    expanded = expand_inputs(read_file(path), folder)

    words = count_words(clean_latex(expanded))

    placeholder = words < PLACEHOLDER_THRESHOLD

    if placeholder:
        pages = "-"
    else:
        pages = max(1, round(words / WORDS_PER_PAGE))

    return {
        "words": words,
        "pages": pages,
        "citations": count_citations(expanded),
        "figures": count_occurrences(expanded, r"\\begin\{figure\}"),
        "tables": count_occurrences(expanded, r"\\begin\{table\}"),
        "footnotes": count_occurrences(expanded, r"\\footnote\{"),
        "placeholder": placeholder,
    }


# =========================
# Optional LIVE watch mode
# =========================
# `python watch_wordcount.py --watch` turns this one-shot script into a
# real watcher: it re-runs itself (a normal one-shot pass) every time a
# source file changes, so the stats refresh on every save. Without the
# flag the script behaves exactly as before -- a single pass -- so any
# task/editor that already calls it is unaffected.

if "--watch" in sys.argv:
    import subprocess
    import time

    SELF = str(Path(__file__).resolve())

    def _watched_files():
        files = [ROOT / "main.tex", ROOT / "main.toc",
                 ROOT / "main.pdf", BIB_FILE]
        for d in (CHAPTERS, APPENDIX_DIR, FRONT_DIR):
            files += sorted(d.glob("*.tex"))
        return files

    def _snapshot():
        snap = {}
        for p in _watched_files():
            try:
                snap[str(p)] = p.stat().st_mtime
            except OSError:
                pass
        return snap

    print("Watching thesis sources... (save a file to refresh, Ctrl+C to stop)")
    last = None
    try:
        while True:
            snap = _snapshot()
            if snap != last:
                # Re-run myself as a plain one-shot (no --watch), which
                # regenerates thesis_statistics.tex from the saved files.
                subprocess.run([sys.executable, SELF])
                last = snap
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped watching.")
    sys.exit(0)


# =========================
# Analyse thesis
# =========================

main_text = read_file(MAIN)
parts, appendices = extract_structure(main_text)
toc_chapters, toc_appendices = extract_toc_titles()

# EFFECTIVE pages from the compiled PDF (blank pages excluded), shared
# with generate_wordcount. None when there is no PDF/pypdf yet, in which
# case we keep the fast words-per-page estimate.
page_info = compute_effective_pages()

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

        # Prefer real effective pages (blanks excluded) when we have the
        # PDF; otherwise keep the words-per-page estimate.
        if page_info and not stats["placeholder"]:
            stats["pages"] = page_info["chapters"].get(
                chapter_index + 1, stats["pages"])

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

    if page_info and not stats["placeholder"]:
        stats["pages"] = page_info["appendices"].get(
            chr(ord("A") + i), stats["pages"])

    stats["name"] = display
    appendix_results.append(stats)

    if not stats["placeholder"]:
        for k in app_acc:
            app_acc[k] += stats[k]


# front matter (Abstract, Acknowledgements): reference only, never
# added to the totals.
front_results = []
for fkey, ftitle in FRONT_UNITS:
    stats = analyse_unit(fkey, FRONT_DIR)
    if page_info:
        stats["pages"] = page_info["front"].get(fkey, "-")
    stats["name"] = ftitle
    front_results.append(stats)


bib_count = count_bib_entries()

total_words = grand["words"]
total_pages = grand["pages"]


# =========================
# Requirements check (word count only; pages are informational)
# =========================

if ACCEPTABLE_MIN <= total_words <= ACCEPTABLE_MAX:
    status = "MET"
    if TARGET_MIN <= total_words <= TARGET_MAX:
        message = (
            f"Word count ({total_words:,}) is within the ideal "
            f"15,000--18,000 target range."
        )
    else:
        message = (
            f"Word count ({total_words:,}) is within the acceptable "
            f"13,500--19,800 range -- outside the ideal 15,000--18,000 "
            f"target, but acceptable."
        )

elif total_words < ACCEPTABLE_MIN:
    status = "NOT MET"
    message = (
        f"Word count ({total_words:,}) is below the acceptable "
        f"minimum ({ACCEPTABLE_MIN:,})."
    )

else:
    status = "NOT MET"
    message = (
        f"Word count ({total_words:,}) is above the acceptable "
        f"maximum ({ACCEPTABLE_MAX:,})."
    )


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

# Front matter: shown for reference, EXCLUDED from every total.
if front_results:
    body += (
        "\\multicolumn{7}{l}{\\textbf{Front matter "
        "(excluded from totals)}} \\\\\n\\midrule\n"
    )
    for fu in front_results:
        body += data_row(fu["name"], fu)
    body += "\\midrule\n"

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


# page breakdown section (real from the PDF, or an estimate note)
if page_info:
    page_section = (
        "\\section*{Page Breakdown}\n\n\\noindent\n"
        "Page counts read directly from the compiled \\texttt{main.pdf}; "
        "blank/filler pages are excluded from the chapters figure.\n\n"
        "\\vspace{0.2cm}\n\n"
        "\\begin{tabularx}{\\textwidth}{Xr}\n\\toprule\n"
        "Section & Pages \\\\\n\\midrule\n"
        "Chapters 1--12 (content only, blank pages excluded) & "
        f"{page_info['ch1_12']} \\\\\n"
        "Everything else (front matter, part dividers, appendices, "
        f"bibliography, blank pages) & {page_info['rest']} \\\\\n"
        "\\midrule\n"
        f"\\textbf{{Total thesis pages}} & \\textbf{{{page_info['total']}}} \\\\\n"
        "\\bottomrule\n\\end{tabularx}\n\n\\vspace{0.5cm}\n\n"
    )
else:
    page_section = (
        "\\section*{Page Breakdown}\n\n\\noindent\n"
        f"\\textit{{Chapters 1--12, estimated at about {WORDS_PER_PAGE} "
        f"words per page: {total_pages} pages. The full breakdown "
        "(blank pages excluded, plus the true total) needs a compiled "
        "\\texttt{main.pdf}; run \\texttt{generate\\_wordcount.py}.}\n\n"
        "\\vspace{0.5cm}\n\n"
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

    f.write(page_section)
    f.write(appendix_section)
    f.write(bibliography_section)

    pages_note = (
        "The Pages column shows effective content pages from the compiled "
        "\\texttt{main.pdf} (blank pages excluded)."
        if page_info else
        f"The Pages column is an estimate of about {WORDS_PER_PAGE} words "
        "per page; compile and run \\texttt{generate\\_wordcount.py} for "
        "the real page counts."
    )

    f.write(
        "\\section*{Requirements Check}\n\n"
        "\\begin{itemize}\n"
        "\\item Expected word count: 15,000--18,000 words\n"
        "\\item Acceptable word range: 13,500--19,800 words\n"
        "\\item The verdict is decided by the WORD COUNT only; the page "
        "count is reported above and does not affect it\n"
        "\\item Status is computed on the main thesis only (front matter, "
        "appendices and bibliography excluded)\n"
        "\\end{itemize}\n\n"
        "\\vspace{0.5cm}\n\n\\noindent\n"
        f"\\textbf{{STATUS: {status}}}\n\n"
        "\\vspace{0.2cm}\n\n\\noindent\n"
        f"{message}\n\n"
        "\\vspace{0.3cm}\n\n\\noindent\n"
        "Placeholder chapters containing fewer than 50 words are excluded "
        f"from the totals. {pages_note}\n\n"
        "\\end{document}\n"
    )


print(f"Statistics generated: {OUTPUT}")
print(f"Total words (main thesis): {total_words:,}")
if page_info:
    print(f"Pages -> chapters 1-12: {page_info['ch1_12']} | "
          f"everything else: {page_info['rest']} | "
          f"total thesis: {page_info['total']}")
else:
    print(f"Pages (estimated, chapters 1-12): {total_pages} "
          f"(no main.pdf; run generate_wordcount.py for real pages)")
print(f"Appendices: {len(appendix_results)} | Bibliography entries: {bib_count}")
print(f"Status (word count only): {status}")