#!/usr/bin/env python3
"""
Trim orphaned leading half-lines from six Uttara Kanda rows.

Each of these rows begins with a stray half-line that duplicates text already
present one or two rows earlier in the same sarga. The rest of the row is a
complete, correctly translated verse. The fix is to drop the leading fragment
and its trailing danda, keeping everything else — the row, its stamp, and its
hindi / explanation / translation fields, all of which belong to the real verse.

DO NOT delete these rows. Each holds a full verse of finished translation.

Safety
------
- Backs up to data_7.json.bakfrag before writing.
- For every row, asserts the exact expected fragment is present before touching
  it, and refuses the whole run if any assertion fails (nothing is written).
- Asserts the verse stamp survives the trim.
- Re-running is a no-op: the guard finds no fragment and aborts cleanly.

Usage:  python3 trim_uttara_fragments.py data_7.json
"""

import json
import re
import shutil
import sys

# (sarga, shloka, exact leading fragment including its trailing danda)
FRAGMENTS = [
    (26, "8",  "भिरुद्भासितवनान्तरे ।"),
    (27, "22", "यामि ज्ञात्वा कालमुपागतम् ।"),
    (30, "13", "्वं हि कस्यचित्प्राणिनो भुवि ।"),
    (32, "29", "चः श्रुत्वा मन्त्रिणो ऽथार्जुनस्य ते ।"),
    (40, "22", "लोके च मामिका ।"),
    (95, "4",  "परिषदो मध्ये रामो वचनमब्रवीत् ।"),
]

STAMP = re.compile(r"।।\s*7\.\d+\.[\d.]+\s*।।\s*$")


def main(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    index = {(r.get("sarga"), str(r.get("shloka"))): i for i, r in enumerate(data)}

    planned = []
    problems = []

    for sarga, shloka, frag in FRAGMENTS:
        key = (sarga, shloka)
        if key not in index:
            problems.append(f"{sarga}.{shloka}: row not found")
            continue
        row = data[index[key]]
        text = (row.get("shloka_text") or "").strip()

        if not text.startswith(frag):
            problems.append(
                f"{sarga}.{shloka}: expected leading fragment not found "
                f"(starts {text[:40]!r})"
            )
            continue

        trimmed = text[len(frag):].strip()
        if not STAMP.search(trimmed):
            problems.append(f"{sarga}.{shloka}: trim would lose the verse stamp")
            continue
        if len(trimmed) < 40:
            problems.append(f"{sarga}.{shloka}: trimmed text implausibly short")
            continue

        planned.append((index[key], f"{sarga}.{shloka}", text, trimmed))

    if problems:
        print("ABORT — nothing written. Problems:")
        for p in problems:
            print("  -", p)
        sys.exit(1)

    shutil.copyfile(path, path + ".bakfrag")

    for i, label, before, after in planned:
        print(f"--- {label}")
        print(f"  before: {before[:78]}")
        print(f"  after : {after[:78]}")
        data[i]["shloka_text"] = after

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)

    print(f"\nTrimmed {len(planned)} rows. Backup at {path}.bakfrag")
    print("Row count unchanged:", len(data))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data_7.json")
