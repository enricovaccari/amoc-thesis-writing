#!/usr/bin/env python
"""
Build the TWO thesis PDFs from the single source main.tex:

    main_digital.pdf    -> digital copy   (typed signature)
    main_printable.pdf  -> print   copy   (blank rule, signed by hand)

The digital/print switch is chosen automatically from the job name
(see the block near the top of main.tex). Both PDFs are built from the
exact same sources; they differ only in the Declaration signature block.

Usage (run in the amoc-thesis conda env):
    python build_versions.py            build both versions once
    python build_versions.py --watch    rebuild both on every source save
    python build_versions.py --clean    sweep iCloud conflict copies into
                                         TO_BE_DELETED/build_junk/
"""

from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
MAIN = "main.tex"
JOBS = ["main_digital", "main_printable"]
# All LaTeX output (aux, logs AND the two PDFs) goes here, keeping the
# project root clean. The PDFs are build/main_digital.pdf and
# build/main_printable.pdf.
BUILD_DIR = "build"


# ------------------------------------------------------------------ build --

def build_one(job, force=False):
    args = ["latexmk", "-pdf", "-interaction=nonstopmode",
            "-synctex=1", f"-outdir={BUILD_DIR}", f"-jobname={job}"]
    if force:
        # -g forces this run even if latexmk thinks nothing changed, which
        # defeats the stale-mtime confusion iCloud Drive causes.
        args.append("-g")
    args.append(MAIN)
    return subprocess.run(args, cwd=str(ROOT)).returncode


def build_all(force=False):
    ok = True
    for job in JOBS:
        print(f"\n=== building {job}.pdf ===")
        rc = build_one(job, force=force)
        ok = ok and rc == 0
    tag = "OK" if ok else "WITH ERRORS (see log)"
    print(f"\nBuilt {', '.join(BUILD_DIR + '/' + j + '.pdf' for j in JOBS)} [{tag}]")
    return ok


def refresh_stats():
    """Regenerate the word-count statistics from the fresh build."""
    gen = ROOT / "statistics" / "generate_wordcount.py"
    if gen.exists():
        print("\n=== refreshing thesis statistics ===")
        subprocess.run([sys.executable, str(gen)], cwd=str(ROOT))


# ------------------------------------------------------------------ watch --

def watched_files():
    files = [ROOT / MAIN, ROOT / "references.bib"]
    for d in (ROOT / "chapters", ROOT / "appendix", ROOT / "frontmatter"):
        files += sorted(d.glob("*.tex"))
    files += sorted((ROOT / "figures").rglob("*.tex"))
    return files


def snapshot():
    snap = {}
    for p in watched_files():
        try:
            snap[str(p)] = p.stat().st_mtime
        except OSError:
            pass
    return snap


def watch():
    print("Watching thesis sources... rebuilding main_digital.pdf + "
          "main_printable.pdf on every save (Ctrl+C to stop).")
    last = None
    try:
        while True:
            snap = snapshot()
            if snap != last:
                build_all(force=True)
                refresh_stats()
                last = snapshot()   # re-snapshot AFTER build; mtimes shift
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nStopped watching.")


# ------------------------------------------------------------------ clean --

def clean_junk():
    """Move iCloud conflict copies (e.g. 'main 2.pdf', 'main.run(1).xml')
    into TO_BE_DELETED/build_junk/. Never touches main.tex or the two
    current version PDFs/aux."""
    dest = ROOT / "TO_BE_DELETED" / "build_junk"
    dest.mkdir(parents=True, exist_ok=True)
    moved = 0
    for p in ROOT.iterdir():
        if not p.is_file():
            continue
        n = p.name
        # " 2.", " 10.", "(1)." before an extension, or a *-SAVE-ERROR file
        if re.search(r"[ (]\d+\)?\.", n) or n.endswith("-SAVE-ERROR"):
            try:
                shutil.move(str(p), str(dest / n))
                moved += 1
            except Exception as ex:            # noqa: BLE001
                print("  skip", n, "->", ex)
    print(f"moved {moved} conflict/junk files -> TO_BE_DELETED/build_junk/")


# ------------------------------------------------------------------- main --

if __name__ == "__main__":
    if "--watch" in sys.argv:
        watch()
    elif "--clean" in sys.argv:
        clean_junk()
    else:
        build_all(force=("--force" in sys.argv or "-g" in sys.argv))
        if "--no-stats" not in sys.argv:
            refresh_stats()
