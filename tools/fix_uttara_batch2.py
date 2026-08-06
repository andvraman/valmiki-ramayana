#!/usr/bin/env python3
"""
Uttara Kanda text repairs, batch 2.

(a) Six rows carry U+093A DEVANAGARI VOWEL SIGN OE, an OCR artefact standing
    where a त्र conjunct (and sometimes a space) was lost. Two distinct
    corruption patterns, so each is repaired as an exact per-row substitution
    rather than a global replace.

(b) Row 94.29 begins with an orphaned half-line that duplicates text already
    present complete at 94.27. Trimmed, row and translations kept.

NOT touched: row 17.27. It also begins with a stray half-line, but that text
appears nowhere else in the sarga — in the Gita Press .txt it is the second
half of a verse whose first half is absent from data_7.json. Trimming it would
destroy genuine text. It needs the .txt to repair and is left for later.

Safety
------
- Backs up to data_7.json.bak2 before writing.
- Validates every expected substring before changing anything; if any check
  fails, nothing is written.
- Confirms no U+093A remains anywhere after the edits.
- Re-running is a no-op: guards fail and the script aborts.

Usage:  python3 fix_uttara_batch2.py data_7.json
"""

import json
import re
import shutil
import sys

OE = "\u093a"  # the offending mark

# (sarga, shloka, exact substring present, replacement)
SUBSTITUTIONS = [
    (16, "48", "क्षत्\u093aित्रया",             "क्षत्रिया"),
    (16, "49", "क्षत्\u093aित्रया",             "क्षत्रिया"),
    (35, "52", "पात्\u093aत्रैलोक्यं",          "पात् त्रैलोक्यं"),
    (36, "7",  "कुत्\u093aित्रधामा",            "कुत् त्रिधामा"),
    (60, "18", "यात्\u093aत्रातुम",             "यात् त्रातुम"),
    (85, "14", "गत्\u093aत्रासम",               "गत् त्रासम"),
]

# (sarga, shloka, exact leading fragment including trailing danda)
TRIMS = [
    (94, "29", "सोत्तराणि महात्मना ।"),
]

STAMP = re.compile(r"।।\s*7\.\d+\.[\d.]+\s*।।\s*$")


def main(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    index = {(r.get("sarga"), str(r.get("shloka"))): i for i, r in enumerate(data)}
    planned, problems = [], []

    for sarga, shloka, old, new in SUBSTITUTIONS:
        key = (sarga, shloka)
        if key not in index:
            problems.append(f"{sarga}.{shloka}: row not found")
            continue
        text = data[index[key]].get("shloka_text") or ""
        if old not in text:
            problems.append(f"{sarga}.{shloka}: expected damaged text not found")
            continue
        if text.count(old) != 1:
            problems.append(f"{sarga}.{shloka}: damaged text appears more than once")
            continue
        planned.append((index[key], f"{sarga}.{shloka}", "substitute",
                        text, text.replace(old, new)))

    for sarga, shloka, frag in TRIMS:
        key = (sarga, shloka)
        if key not in index:
            problems.append(f"{sarga}.{shloka}: row not found")
            continue
        text = (data[index[key]].get("shloka_text") or "").strip()
        if not text.startswith(frag):
            problems.append(f"{sarga}.{shloka}: expected leading fragment not found")
            continue
        trimmed = text[len(frag):].strip()
        if not STAMP.search(trimmed):
            problems.append(f"{sarga}.{shloka}: trim would lose the verse stamp")
            continue
        planned.append((index[key], f"{sarga}.{shloka}", "trim", text, trimmed))

    if problems:
        print("ABORT — nothing written. Problems:")
        for p in problems:
            print("  -", p)
        sys.exit(1)

    shutil.copyfile(path, path + ".bak2")

    for i, label, kind, before, after in planned:
        print(f"--- {label}  [{kind}]")
        print(f"  before: {before[:76]}")
        print(f"  after : {after[:76]}")
        data[i]["shloka_text"] = after

    remaining = [f"{r['sarga']}.{r['shloka']}" for r in data
                 if OE in (r.get("shloka_text") or "")]
    if remaining:
        print("\nWARNING: U+093A still present in:", remaining)
    else:
        print("\nU+093A fully cleared from the kanda.")

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)

    print(f"Changed {len(planned)} rows. Row count unchanged: {len(data)}")
    print(f"Backup at {path}.bak2")
    print("Left untouched by design: 17.27 (needs .txt — genuine text, not debris)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data_7.json")
