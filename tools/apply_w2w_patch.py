#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply a word-by-word patch to a kanda file.

    python3 apply_w2w_patch.py data_7.json uttara_w2w_1-2_patch.json

Patch format (entries keyed "sarga.shloka", spanning any number of sargas):

    {
      "kanda": "Uttara Kanda",
      "field": "translation",
      "entries": { "1.1": "...", "1.2": "...", "2.1": "..." },
      "shloka_text_fix": {
        "84.22": {"from": "...", "to": "...", "note": "why"}
      }
    }

Fills only blank fields; never overwrites existing text. Backs up first.
Accepts fractional shloka numbers (e.g. "51.4.1" = sarga 51, shloka 4.1).
"""
import json, sys, shutil

if len(sys.argv) != 3:
    sys.exit(__doc__)

data_path, patch_path = sys.argv[1], sys.argv[2]
d = json.load(open(data_path, encoding='utf-8'))
p = json.load(open(patch_path, encoding='utf-8'))

kanda = p['kanda']
field = p.get('field', 'translation')


def split_key(key):
    """'2.15' -> (2, 15);  '51.4.1' -> (51, 4.1)"""
    head, _, tail = key.partition('.')
    sarga = int(head)
    shloka = float(tail) if '.' in tail else int(tail)
    return sarga, shloka


# Two patch shapes are accepted:
#   new: {"entries": {"2.15": ...}}                 — keys are "sarga.shloka"
#   old: {"sarga": 84, "translation": {"22": ...}}  — one sarga, bare shloka keys
if 'entries' in p:
    want = {split_key(k): v for k, v in p['entries'].items()}
    fixes = {split_key(k): v for k, v in p.get('shloka_text_fix', {}).items()}
elif 'sarga' in p:
    s = p['sarga']
    def bare(k):
        return (s, float(k) if '.' in k else int(k))
    want = {bare(k): v for k, v in p.get(field, {}).items()}
    fixes = {bare(k): v for k, v in p.get('shloka_text_fix', {}).items()}
else:
    sys.exit("ERROR: patch has neither 'entries' nor 'sarga'. Unrecognised format.")

# sanity: is this the right kanda file?
kandas_in_file = {x['kanda'] for x in d}
if kanda not in kandas_in_file:
    sys.exit(f"ERROR: patch is for '{kanda}' but {data_path} contains "
             f"{sorted(kandas_in_file)}. Wrong file?")

filled = skipped = textfix = 0
seen = set()

for x in d:
    if x['kanda'] != kanda:
        continue
    k = (x['sarga'], x['shloka'])

    if k in want:
        seen.add(k)
        if (x.get(field) or '').strip():
            print(f"  SKIP {k[0]}.{k[1]}: {field} already present")
            skipped += 1
        else:
            x[field] = want[k]
            filled += 1

    fx = fixes.get(k)
    if fx and fx['from'] in (x.get('shloka_text') or ''):
        x['shloka_text'] = x['shloka_text'].replace(fx['from'], fx['to'])
        textfix += 1
        print(f"  TEXT {k[0]}.{k[1]}: {fx['from']} -> {fx['to']}  ({fx.get('note','')})")

missing = sorted(set(want) - seen)
sargas = sorted({k[0] for k in want})
span = f"{sargas[0]}-{sargas[-1]}" if len(sargas) > 1 else str(sargas[0])

print(f"\nkanda: {kanda} | sargas {span} | field: {field}")
print(f"filled {filled} | skipped {skipped} | {textfix} Sanskrit correction(s) | "
      f"not found: {missing or 'none'}")

if filled or textfix:
    shutil.copy(data_path, data_path + '.bak')
    json.dump(d, open(data_path, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f"wrote {data_path} (backup at {data_path}.bak)")
else:
    print("nothing to do — file untouched")
