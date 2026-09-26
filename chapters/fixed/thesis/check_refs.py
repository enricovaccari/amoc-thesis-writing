#!/usr/bin/env python3
"""Cross-reference, caption and graphics audit for the AMOC thesis.
Run from the directory containing main.tex:   python check_refs.py
Pure stdlib; works on Windows.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEX = [p for p in ROOT.rglob("*.tex") if ".git" not in p.parts]
if not TEX:
    sys.exit("No .tex files found. Run this from the folder containing main.tex.")

strip = lambda t: re.sub(r'(?<!\\)%.*', '', t)
labels, refs, captions, graphics, inputs = {}, {}, [], [], set()

for p in TEX:
    rel = p.relative_to(ROOT).as_posix()
    txt = strip(p.read_text(encoding="utf-8", errors="replace"))
    for m in re.finditer(r'\\label\{([^}]+)\}', txt):
        labels.setdefault(m.group(1), []).append((rel, txt[:m.start()].count("\n") + 1))
    for m in re.finditer(r'\\(?:ref|autoref|eqref|pageref|cref|Cref)\{([^}]+)\}', txt):
        for k in m.group(1).split(','):
            refs.setdefault(k.strip(), []).append((rel, txt[:m.start()].count("\n") + 1))
    for m in re.finditer(r'\\caption(\[[^\]]*\])?\s*\{', txt):
        captions.append((rel, txt[:m.start()].count("\n") + 1, bool(m.group(1))))
    for m in re.finditer(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', txt):
        graphics.append((rel, txt[:m.start()].count("\n") + 1, m.group(1)))
    for m in re.finditer(r'\\(?:input|include)\{([^}]+)\}', txt):
        inputs.add(m.group(1))

def head(s): print("\n" + "=" * 78); print(s); print("=" * 78)

head("1. BROKEN REFERENCES  ->  these print '??' in the PDF")
broken = {k: v for k, v in refs.items() if k not in labels}
print("  none - all references resolve" if not broken else "")
for k in sorted(broken):
    print(f"  {k}")
    for f, l in broken[k]: print(f"        referenced at {f}:{l}")

head("2. EVERY LABEL DEFINED UNDER figures/  (match these against block 1)")
for k in sorted(labels):
    if any(f.startswith("figures/") for f, _ in labels[k]):
        print(f"  {k:34s} {labels[k][0][0]}:{labels[k][0][1]}")

head("3. LABELS DEFINED BUT NEVER REFERENCED")
for k in sorted(labels):
    if k not in refs:
        tag = "   <-- FLOAT: must be referenced in the text" if k.split(":")[0] in ("fig","tab","eq") else ""
        print(f"  {k:34s} {labels[k][0][0]}:{labels[k][0][1]}{tag}")

head("4. DUPLICATE LABELS")
dups = {k: v for k, v in labels.items() if len(v) > 1}
print("  none" if not dups else "")
for k, v in dups.items(): print(f"  {k}: " + ", ".join(f"{f}:{l}" for f, l in v))

head("5. CAPTIONS WITHOUT A SHORT FORM  ->  full caption leaks into LoF/LoT")
bad = [c for c in captions if not c[2]]
print(f"  {len(captions)} captions total, {len(bad)} missing \\caption[short]{{long}}")
for f, l, _ in bad: print(f"        {f}:{l}")

head("6. MISSING IMAGE FILES")
exts = ["", ".pdf", ".png", ".jpg", ".jpeg", ".eps"]
bases = [ROOT, ROOT / "figures"]          # matches \graphicspath{{figures/}}
miss = [(f, l, g) for f, l, g in graphics
        if not any((b / (g + e)).exists() for b in bases for e in exts)]
print("  none" if not miss else "")
for f, l, g in miss: print(f"  MISSING: {g}    (referenced at {f}:{l})")

head("7. \\input / \\include TARGETS THAT DO NOT EXIST")
gone = [i for i in sorted(inputs) if not (ROOT / i).exists() and not (ROOT / (i + ".tex")).exists()]
print("  none" if not gone else "")
for i in gone: print(f"  MISSING: {i}")

head("8. LEFTOVER PLACEHOLDERS  ->  these print in the PDF")
n = 0
for p in TEX:
    rel = p.relative_to(ROOT).as_posix()
    for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
        if line.strip().startswith("%"): continue
        if re.search(r'\[FILL|\bTODO\b|\bFIXME\b|\[TBD|\[The verbatim|\[The full participant', line):
            n += 1; print(f"  {rel}:{i}  {line.strip()[:100]}")
print("  none" if not n else "")

head("SUMMARY")
print(f"  .tex files scanned : {len(TEX)}")
print(f"  labels defined     : {len(labels)}")
print(f"  references made    : {len(refs)}")
print(f"  BROKEN references  : {len(broken)}")
print(f"  orphan floats      : {len([k for k in labels if k not in refs and k.split(':')[0] in ('fig','tab','eq')])}")
print(f"  captions w/o short : {len(bad)}")
print(f"  missing images     : {len(miss)}")
print(f"  placeholders       : {n}")
