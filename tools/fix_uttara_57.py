#!/usr/bin/env python3
"""
Repair Uttara Kanda sarga 57.

Problem
-------
Row 57.21 holds the sarga colophon as its shloka_text, but its `hindi` field
carries the translation of verse 21 proper. The Sanskrit of verse 21 was lost;
the colophon displaced it. This is the only sarga in the kanda where the
half-line streams never re-converge.

Fix
---
1. Row 57.21  -> shloka_text becomes verse 21 (stamp added, tight format).
                 hindi kept as-is (already correct).
                 explanation replaced (was colophon boilerplate).
                 translation (w2w) filled.
2. New row 57.22 -> the colophon, with standard colophon hindi/explanation,
                 inserted immediately after 57.21.

Backs up to data_7.json.bak57 before writing. Report-then-write: prints a
diff summary and refuses if the file is not in the expected state.

Usage:  python3 fix_uttara_57.py data_7.json
"""

import json
import shutil
import sys

VERSE_21 = (
    "इति सर्वमशेषतो मया कथितं संभवकारणं तु सौम्य । "
    "नृपपुङ्गवशापजं द्विजस्य द्विजशापाच्च यदद्भुतं नृपस्य ।। 7.57.21 ।।"
)

VERSE_21_ENGLISH = (
    "'Thus, gentle one, I have told you the whole cause of their coming to be, "
    "leaving nothing out — how the brahmin fared through the curse of a bull among "
    "kings, and what wonder befell the king through the curse of the brahmin.'"
)

VERSE_21_W2W = (
    "सौम्य O gentle one, इति thus, संभवकारणम् the cause of their coming to be, "
    "सर्वम् entire, अशेषतः without omission, मया by me, कथितं तु has indeed been told, "
    "नृपपुङ्गवशापजम् born of the curse of a bull among kings, द्विजस्य of the brahmin, "
    "द्विजशापात् from the curse of the brahmin, नृपस्य of the king, यत् what, "
    "अद्भुतम् wonder came about"
)

COLOPHON = (
    "इत्यार्षे श्रीमद्रामायणे वाल्मीकीये आदिकाव्ये "
    "श्रीमदुत्तरकाण्डे सप्तपञ्चाशः सर्गः ।। 57 ।।"
)

COLOPHON_HINDI = (
    "इस प्रकार श्रीवाल्मीकि निर्मित आर्षरामायण आदिकाव्य के "
    "उत्तरकाण्ड में सत्तावनवाँ सर्ग पूरा हुआ॥५७॥"
)

COLOPHON_ENGLISH = (
    "Thus ends the fifty-seventh canto of the Uttara Kanda in the Ramayana, "
    "the first poem, composed by the sage Valmiki."
)


def main(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    idx = [i for i, r in enumerate(data)
           if r.get("sarga") == 57 and str(r.get("shloka")) == "21"]
    if len(idx) != 1:
        sys.exit(f"ABORT: expected exactly one row 57.21, found {len(idx)}")
    i = idx[0]
    row = data[i]

    if not (row.get("shloka_text") or "").strip().startswith("इत्यार्षे"):
        sys.exit("ABORT: row 57.21 does not hold the colophon — already repaired?")

    if any(r.get("sarga") == 57 and str(r.get("shloka")) == "22" for r in data):
        sys.exit("ABORT: row 57.22 already exists — already repaired?")

    kept_hindi = row.get("hindi") or ""
    if "संभव" not in kept_hindi:
        sys.exit("ABORT: row 57.21 hindi is not the verse-21 translation")

    shutil.copyfile(path, path + ".bak57")

    print("BEFORE")
    print("  57.21 skt:", (row.get("shloka_text") or "")[:60])
    print("  57.21 hin:", kept_hindi[:60])
    print("  sarga 57 rows:", sum(1 for r in data if r.get("sarga") == 57))

    # 1. correct row 21
    row["shloka_text"] = VERSE_21
    row["explanation"] = VERSE_21_ENGLISH
    row["translation"] = VERSE_21_W2W
    # hindi left untouched

    # 2. colophon as new row 22, same field shape as its neighbours
    colophon_row = {k: "" for k in row}
    colophon_row.update({
        "kanda": row.get("kanda", "Uttara Kanda"),
        "sarga": 57,
        "shloka": 22,
        "shloka_text": COLOPHON,
        "hindi": COLOPHON_HINDI,
        "explanation": COLOPHON_ENGLISH,
        "translation": "",
    })
    if "transliteration" in row:
        colophon_row["transliteration"] = ""
    data.insert(i + 1, colophon_row)

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)

    print("AFTER")
    print("  57.21 skt:", VERSE_21[:60])
    print("  57.22 skt:", COLOPHON[:60])
    print("  sarga 57 rows:", sum(1 for r in data if r.get("sarga") == 57))
    print("  total rows:", len(data))
    print("Backup at", path + ".bak57")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data_7.json")
