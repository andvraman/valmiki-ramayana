#!/usr/bin/env python3
"""
Repair displaced Hindi in Uttara Kanda sargas 17 and 51.

Findings (from hindi_alignment_report.json, then verified row by row against the
Sanskrit actually sitting on each row):

  Sarga 51 — row 51.5 carries Sanskrit identical to row 51.4.1: a duplicate row,
  flagged in the original Sanskrit alignment audit. It displaced every following
  row's Hindi by one. Two runs result:
    * 51.5 .. 51.11  — each row's Hindi translates the NEXT row's Sanskrit,
                       so each moves DOWN one row (51.5's -> 51.6, etc.).
                       51.11's Hindi lands on 51.12, replacing a paraphrase.
                       Row 51.5 is then empty and is DELETED as the duplicate.
    * 51.27 .. 51.32 — each row's Hindi translates the PREVIOUS row's Sanskrit,
                       so each moves UP one row (51.27's -> 51.26, etc.).
                       51.32 is the colophon and correctly ends with no Hindi.

  Sarga 17 — rows 17.39 .. 17.43 each carry the NEXT row's Hindi; each moves DOWN
  one row. 17.43's lands on 17.44, replacing a paraphrase. Row 17.39 is then
  empty and receives newly written Hindi for its own Sanskrit.

Rows 17.36-17.38 and 51.12-51.25 were checked and are correctly aligned; they are
not touched. Sarga 12's nine flagged rows were checked and are FALSE ALARMS — the
Hindi there was written from the row's own Sanskrit and simply does not match the
Gita Press wording verbatim, which is what the report's fuzzy score picked up.

Usage
-----
  python3 fix_hindi_17_51.py                 # report only
  python3 fix_hindi_17_51.py --apply         # applies, backs up to .bakhindi
"""

import json
import shutil
import sys

PATH = "data_7.json"

# (sarga, from_shloka, to_shloka) — move the Hindi from one row to another.
# Order matters: each list is applied in the order given, reading values from a
# snapshot taken before any writes, so a cascade cannot overwrite itself.
MOVES = [
    # sarga 17: shift down one
    (17, "39", "40"), (17, "40", "41"), (17, "41", "42"),
    (17, "42", "43"), (17, "43", "44"),
    # sarga 51 head: shift down one
    (51, "5", "6"), (51, "6", "7"), (51, "7", "8"), (51, "8", "9"),
    (51, "9", "10"), (51, "10", "11"), (51, "11", "12"),
    # sarga 51 tail: shift up one
    (51, "27", "26"), (51, "28", "27"), (51, "29", "28"),
    (51, "30", "29"), (51, "31", "30"), (51, "32", "31"),
]

# Rows left empty by the cascade that need fresh Hindi written for their own
# Sanskrit (rather than being deleted).
NEW_HINDI = {
    (17, "39"): "‘श्रीराम! यह सुनकर रावण ने उसे समुद्र में फेंक दिया; "
                "और वह पृथ्वी पर पहुँचकर यज्ञभूमि के बीच जा पड़ी।",
}

# Rows left empty by the cascade that are duplicates and should be deleted.
DELETE = [(51, "5")]


def key(row):
    return (row.get("sarga"), str(row.get("shloka")))


def main(apply_changes):
    data = json.load(open(PATH, encoding="utf-8"))
    index = {key(r): r for r in data}

    problems = []
    for sarga, src, dst in MOVES:
        if (sarga, src) not in index:
            problems.append(f"missing source row {sarga}.{src}")
        if (sarga, dst) not in index:
            problems.append(f"missing target row {sarga}.{dst}")
    for k in DELETE:
        if k not in index:
            problems.append(f"missing row to delete {k[0]}.{k[1]}")
    for k in NEW_HINDI:
        if k not in index:
            problems.append(f"missing row for new Hindi {k[0]}.{k[1]}")
    if problems:
        print("ABORT — nothing written:")
        for p in problems:
            print("  -", p)
        sys.exit(1)

    # snapshot before any writes, so the cascade reads original values
    before = {k: (r.get("hindi") or "") for k, r in index.items()}

    print("PLANNED MOVES\n")
    for sarga, src, dst in MOVES:
        s, d = (sarga, src), (sarga, dst)
        print(f"  {sarga}.{src} -> {sarga}.{dst}")
        print(f"      moving : {before[s][:78]}")
        print(f"      target Sanskrit : {(index[d]['shloka_text'] or '')[:78]}")
        if before[d].strip():
            print(f"      REPLACES        : {before[d][:78]}")
        print()
    for k, v in NEW_HINDI.items():
        print(f"  new Hindi written for {k[0]}.{k[1]}: {v[:78]}\n")
    for k in DELETE:
        print(f"  DELETE duplicate row {k[0]}.{k[1]}: "
              f"{(index[k]['shloka_text'] or '')[:70]}\n")

    if not apply_changes:
        print("REPORT ONLY — no data written. Re-run with --apply.")
        return

    shutil.copyfile(PATH, PATH + ".bakhindi")

    for sarga, src, dst in MOVES:
        index[(sarga, dst)]["hindi"] = before[(sarga, src)]
    # any source that was not itself a target is now stale; clear it
    targets = {(s, d) for s, _, d in MOVES}
    for sarga, src, _ in MOVES:
        if (sarga, src) not in targets:
            index[(sarga, src)]["hindi"] = ""
    for k, v in NEW_HINDI.items():
        index[k]["hindi"] = v

    delete_set = set(DELETE)
    kept = [r for r in data if key(r) not in delete_set]
    removed = len(data) - len(kept)

    json.dump(kept, open(PATH, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"Applied. Rows moved: {len(MOVES)}. New Hindi: {len(NEW_HINDI)}. "
          f"Rows deleted: {removed}.")
    print(f"Row count {len(data)} -> {len(kept)}. Backup at {PATH}.bakhindi")


if __name__ == "__main__":
    main("--apply" in sys.argv)
