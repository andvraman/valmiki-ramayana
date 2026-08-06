#!/usr/bin/env python3
"""
normalise_preexisting_rows.py — Remove U+0965 (॥) from the 7 pre-existing rows
that still carry it, using data.json's convention. Two cases, decided by whether
the row ALREADY has an embedded ।।k.s.n।। stamp:

  * has a ।।k.s.n।। stamp already (a stray ॥ sits mid-verse):
        Araṇya 56.1.3, 56.1.4, 56.1.9, 56.1.10
    → replace the stray ॥ with a ' । ' pada separator; keep the existing stamp
      (do NOT add a second stamp).
  * no ।।-stamp (the ॥ IS the trailing verse stamp):
        Ayodhyā 1.50 (॥ ५० ॥), 1.51 (॥ ५१ ॥), Sundara 59.3 (॥ 5.59.3 ॥)
    → replace the trailing ॥…॥ with ।।k.s.n।। (k = kanda number).

Targets = exactly the rows that still contain ॥ (the recovered rows were already
normalised, so these 7 are all that remain). Backs up first; touches no other row.
"""
import json, re, shutil, sys

DATA = 'data.json'
BACKUP = 'data.json.pre_preexisting_normalise.bak'
KNUM = {'Bala Kanda': 1, 'Ayodhya Kanda': 2, 'Aranya Kanda': 3,
        'Kishkindha Kanda': 4, 'Sundara Kanda': 5, 'Yuddha Kanda': 6,
        'Uttara Kanda': 7}


def fmt_sarga(s):
    return str(int(s)) if float(s).is_integer() else str(s)


def convert(text, kanda, sarga, shloka):
    if '।।' in text:                      # already has an embedded stamp
        # strip the stray ॥ (mid-verse) → single pada danda; keep the stamp
        out = re.sub(r'\s*॥\s*', ' । ', text)
    else:                                 # the ॥…॥ is the trailing verse stamp
        stamp = f"।।{KNUM[kanda]}.{fmt_sarga(sarga)}.{shloka}।।"
        out = re.sub(r'\s*॥[^॥]*॥\s*$', ' ' + stamp, text)
        out = out.replace('॥', '।।')      # safety: any remaining U+0965
    return re.sub(r'\s+', ' ', out).strip()


EXPECTED = {
    ('Ayodhya Kanda', 1, 50), ('Ayodhya Kanda', 1, 51),
    ('Sundara Kanda', 59, 3),
    ('Aranya Kanda', 56.1, 3), ('Aranya Kanda', 56.1, 4),
    ('Aranya Kanda', 56.1, 9), ('Aranya Kanda', 56.1, 10),
}


def main():
    data = json.load(open(DATA, encoding='utf-8'))

    targets = [r for r in data if '॥' in r['shloka_text']]
    ids = set((r['kanda'], r['sarga'], r['shloka']) for r in targets)
    print(f"rows still containing U+0965: {len(targets)}")
    for r in targets:
        print(f"   {r['kanda']} {r['sarga']}.{r['shloka']}")
    if len(targets) != 7 or ids != EXPECTED:
        print(f"⚠ expected exactly the 7 named rows; got {len(targets)} "
              f"({sorted(ids ^ EXPECTED)} differ). STOPPING — no changes made.")
        sys.exit(1)

    shutil.copy2(DATA, BACKUP)
    print(f"Backed up {DATA} -> {BACKUP}")

    for r in targets:
        before = r['shloka_text']
        r['shloka_text'] = convert(before, r['kanda'], r['sarga'], r['shloka'])
        print(f"\n{r['kanda']} {r['sarga']}.{r['shloka']}"
              f"  ({'strip stray ॥' if '।।' in before else 'convert ॥-stamp'})")
        print(f"   BEFORE: {before!r}")
        print(f"   AFTER : {r['shloka_text']!r}")

    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False)

    # ---- verify ----
    check = json.load(open(DATA, encoding='utf-8'))
    u0965 = [r for r in check if '॥' in r['shloka_text']]
    print("\nVERIFY")
    print(f"  total rows: {len(check)}  (expected 23683)  "
          f"{'OK' if len(check) == 23683 else 'MISMATCH'}")
    print(f"  rows anywhere still containing U+0965: {len(u0965)}  "
          f"{'OK — none' if not u0965 else 'FAIL: ' + str([(r['kanda'], r['sarga'], r['shloka']) for r in u0965])}")


if __name__ == '__main__':
    main()
