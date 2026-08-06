#!/usr/bin/env python3
"""
normalise_recovered_rows.py — Convert the 153 recovered rows' shloka_text from
the recovery format (multi-line, ॥N॥ stamp, U+0965) to data.json's existing
convention (single line, ' । ' pada separators, embedded ।।k.s.n।। stamp with
U+0964 doubled) so index.html strips the stamp on display.

The 153 rows are identified as those whose translation AND explanation are both
empty. If that set is not exactly 153, nothing is changed. Backs up first.
No other row is touched. Read-only on the .txt files.
"""
import json, re, shutil, sys

DATA = 'data.json'
BACKUP = 'data.json.pre_normalise.bak'
KNUM = {'Bala Kanda': 1, 'Ayodhya Kanda': 2, 'Aranya Kanda': 3,
        'Kishkindha Kanda': 4, 'Sundara Kanda': 5, 'Yuddha Kanda': 6,
        'Uttara Kanda': 7}


def convert(text, knum, sarga, shloka):
    body = text.replace('\n', ' ')
    body = re.sub(r'\s*॥\s*[०-९]+\s*॥\s*$', '', body)   # strip trailing ॥N॥ stamp
    body = body.replace('॥', '।।')                       # any remaining U+0965 → ।।
    body = re.sub(r'\s*।\s*', ' । ', body)               # ' । ' around single dandas
    body = re.sub(r'\s+', ' ', body).strip()
    return f'{body} ।।{knum}.{sarga}.{shloka}।।'


def main():
    data = json.load(open(DATA, encoding='utf-8'))
    total = len(data)

    targets = [r for r in data if r['translation'] == '' and r['explanation'] == '']
    print(f"rows with translation=='' and explanation=='': {len(targets)}")
    if len(targets) != 153:
        print(f"⚠ expected exactly 153; got {len(targets)}. STOPPING — no changes made.")
        sys.exit(1)

    shutil.copy2(DATA, BACKUP)
    print(f"Backed up {DATA} -> {BACKUP}")

    changed = 0
    for r in targets:
        knum = KNUM[r['kanda']]
        r['shloka_text'] = convert(r['shloka_text'], knum, int(r['sarga']), int(r['shloka']))
        changed += 1

    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f"converted {changed} rows")

    # ---- verify ----
    check = json.load(open(DATA, encoding='utf-8'))
    print("\nVERIFY")
    print(f"  total rows: {len(check)}  (expected 23683)  "
          f"{'OK' if len(check) == 23683 else 'MISMATCH'}")

    tgt_ids = set(id(r) for r in targets)  # not reliable across reload; re-derive:
    recovered = [r for r in check if r['translation'] == '' and r['explanation'] == '']
    rec_u0965 = [r for r in recovered if '॥' in r['shloka_text']]
    other_u0965 = [r for r in check
                   if '॥' in r['shloka_text']
                   and not (r['translation'] == '' and r['explanation'] == '')]
    print(f"  recovered rows still containing U+0965: {len(rec_u0965)}  "
          f"{'OK' if not rec_u0965 else 'FAIL'}")
    print(f"  ALL rows containing U+0965: {len(rec_u0965) + len(other_u0965)}")
    if other_u0965:
        print(f"  ⚠ {len(other_u0965)} PRE-EXISTING rows still contain U+0965 — these are "
              f"NOT recovered rows (they have English text) and were not touched, "
              f"per 'no other row should be touched'. They are a separate pre-existing "
              f"data.json issue:")
        for r in other_u0965:
            print(f"     {r['kanda']} {r['sarga']}.{r['shloka']}")

    # sample
    s = next(r for r in recovered if r['kanda'] == 'Sundara Kanda' and int(r['sarga']) == 67)
    print(f"\n  sample (Sundara 67.{s['shloka']}): {s['shloka_text']!r}")


if __name__ == '__main__':
    main()
