#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply an English-translation patch to data.json.
   Usage: python3 apply_english_patch.py data.json kishkindha_english_patch.json
   Fills only blank fields; never overwrites existing text. Backs up first."""
import json, sys, shutil

data_path, patch_path = sys.argv[1], sys.argv[2]
d = json.load(open(data_path, encoding='utf-8'))
p = json.load(open(patch_path, encoding='utf-8'))
kanda, field, entries = p['kanda'], p['field'], p['entries']

want = {}
for key, text in entries.items():
    s, v = key.split('.')
    want[(int(s), int(v))] = text

filled = skipped = 0
seen = set()
for x in d:
    if x['kanda'] != kanda:
        continue
    k = (x['sarga'], x['shloka'])
    if k not in want:
        continue
    seen.add(k)
    if (x.get(field) or '').strip():
        print(f"  SKIP {k[0]}.{k[1]}: {field} already present")
        skipped += 1
    else:
        x[field] = want[k]
        filled += 1

missing = sorted(set(want) - seen)
print(f"\nfilled {filled} | skipped {skipped} | not found in data.json: {missing or 'none'}")
if filled:
    shutil.copy(data_path, data_path + '.bak')
    json.dump(d, open(data_path, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f"wrote {data_path} (backup at {data_path}.bak)")
else:
    print("nothing to do — file untouched")
