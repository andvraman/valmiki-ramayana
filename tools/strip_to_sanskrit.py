#!/usr/bin/env python3
"""
strip_to_sanskrit.py

Strips everything except the Devanagari Sanskrit verse text from
sanskritdocuments.org / valmikiramayan.net -style downloaded files
(the ones with "Verse Locator" blocks followed by transliteration,
word-by-word gloss, and English prose translation).

Handles files containing a SINGLE sarga or MULTIPLE sargas appended
back to back -- each new "Chapter [Sarga] N" line in the source is
detected and kept as a section header in the output, so verse
numbering boundaries between sargas are never lost.

Usage:
    python3 strip_to_sanskrit.py input1_sd.txt [input2_sd.txt ...]

For each "whatever_sd.txt" it writes "whatever_sanskrit.txt" alongside it,
containing only the sarga headers and Devanagari verse lines (with stamps).
"""

import sys
import os
import re

CHAPTER_RE = re.compile(r'^\s*Chapter\s*\[Sarga\]\s*(\d+)\s*$')


def strip_file(path):
    with open(path, encoding='utf-8') as f:
        lines = f.read().split('\n')

    kept = []
    i = 0
    sarga_count = 0
    while i < len(lines):
        line = lines[i]
        m = CHAPTER_RE.match(line)
        if m:
            sarga_count += 1
            if kept:
                kept.append('')  # blank line before new sarga header (except the very first)
            kept.append(f'=== Sarga {m.group(1)} ===')
            kept.append('')
            i += 1
            continue

        if line.strip() == 'Verse Locator':
            i += 1
            while i < len(lines) and lines[i].strip() != '':
                kept.append(lines[i].rstrip())
                i += 1
            kept.append('')
        else:
            i += 1

    return '\n'.join(kept).strip() + '\n', sarga_count


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    for path in sys.argv[1:]:
        if not os.path.isfile(path):
            print(f"Skipping {path}: not found")
            continue

        cleaned, sarga_count = strip_file(path)

        base = os.path.basename(path)
        if base.endswith('_sd.txt'):
            out_name = base[: -len('_sd.txt')] + '_sanskrit.txt'
        else:
            root, ext = os.path.splitext(base)
            out_name = root + '_sanskrit' + ext

        out_path = os.path.join(os.path.dirname(path), out_name)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)

        orig_size = os.path.getsize(path)
        new_size = os.path.getsize(out_path)
        pct = 100 * new_size / orig_size if orig_size else 0
        sarga_note = f", {sarga_count} sarga(s) detected" if sarga_count else " (no 'Chapter [Sarga]' markers found -- treated as single sarga)"
        print(f"{base}: {orig_size:,} bytes -> {out_name}: {new_size:,} bytes ({pct:.0f}% of original){sarga_note}")


if __name__ == '__main__':
    main()
