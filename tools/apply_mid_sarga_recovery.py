#!/usr/bin/env python3
"""
apply_mid_sarga_recovery.py — Insert the 50 verses from mid_sarga_recovery.json
into data.json, normalising the stamp format in the same pass.

Each new row: shloka_text joined to one line with ' । ' pada separators
(preserving the source's real dandas, no danda inserted at line breaks) and the
trailing ॥N॥ replaced by ।।k.s.n।। (k = kanda number, sarga, shloka — the shloka
may be fractional, e.g. 5.60.3.1). transliteration/translation/explanation/
comments are empty. Rows are inserted positionally within their sarga so 3.1
sits between 3 and 4; data.json is NOT globally re-sorted (it has two
intentionally out-of-order rows: Uttara 2 and Araṇya 56.1). Backs up first;
refuses to overwrite an existing triple.
"""
import json, re, shutil
from collections import defaultdict

DATA = 'data.json'
PATCH = 'mid_sarga_recovery.json'
BACKUP = 'data.json.pre_mid_sarga.bak'
KNUM = {'Bala Kanda': 1, 'Ayodhya Kanda': 2, 'Aranya Kanda': 3,
        'Kishkindha Kanda': 4, 'Sundara Kanda': 5, 'Yuddha Kanda': 6,
        'Uttara Kanda': 7}


def normalise(text, knum, sarga, shloka_str):
    body = text.replace('\n', ' ')
    body = re.sub(r'\s*॥\s*[०-९]+\s*॥\s*$', '', body)   # strip trailing ॥N॥ stamp
    body = body.replace('॥', '।।')                       # safety: any stray U+0965
    body = re.sub(r'\s*।\s*', ' । ', body)               # ' । ' around single dandas
    body = re.sub(r'\s+', ' ', body).strip()
    return f'{body} ।।{knum}.{sarga}.{shloka_str}।।'


def main():
    data = json.load(open(DATA, encoding='utf-8'))
    patch = json.load(open(PATCH, encoding='utf-8'))['kandas']
    n_before = len(data)

    existing = set((r['kanda'], r['sarga'], r['shloka']) for r in data)

    new_by_sarga = defaultdict(list)
    refused = []
    added = defaultdict(int)
    for kf, sargas in patch.items():
        knum = KNUM[kf]
        for sg, shlokas in sargas.items():
            sarga = int(sg)
            for sh, e in shlokas.items():
                shloka = int(sh) if '.' not in sh else float(sh)
                if (kf, sarga, shloka) in existing:
                    refused.append((kf, sarga, sh))
                    continue
                row = {
                    'kanda': kf, 'sarga': sarga, 'shloka': shloka,
                    'shloka_text': normalise(e['shloka_text'], knum, sarga, sh),
                    'transliteration': '', 'translation': '',
                    'explanation': '', 'comments': '',
                }
                new_by_sarga[(kf, sarga)].append(row)
                added[kf] += 1

    if refused:
        print(f"⚠ REFUSED {len(refused)} rows — triple already exists (not inserted):")
        for kf, sarga, sh in refused:
            print(f"   {kf} {sarga}.{sh}")

    # back up only once we know what we're doing
    shutil.copy2(DATA, BACKUP)
    print(f"Backed up {DATA} -> {BACKUP} ({n_before} rows)")

    # contiguous block range for each affected sarga
    block = {}
    for i, r in enumerate(data):
        block.setdefault((r['kanda'], r['sarga']), [i, i])[1] = i

    # rebuild list, replacing each affected sarga's block with a locally
    # merge-sorted block (existing + new), by numeric shloka. No global re-sort.
    out, i = [], 0
    while i < len(data):
        key = (data[i]['kanda'], data[i]['sarga'])
        if key in new_by_sarga and i == block[key][0]:
            start, end = block[key]
            merged = sorted(data[start:end + 1] + new_by_sarga[key],
                            key=lambda r: float(r['shloka']))
            out.extend(merged)
            i = end + 1
        else:
            out.append(data[i]); i += 1

    json.dump(out, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False)

    total_added = sum(added.values())
    print("\nRows added per kanda:")
    for k in KNUM:
        if added.get(k):
            print(f"   {k}: {added[k]}")
    print(f"total added: {total_added}  |  new total: {len(out)}  "
          f"(expected {n_before} + 50 = {n_before + 50})")

    verify(out, new_by_sarga)


def verify(out, new_by_sarga):
    print("\nVERIFY")
    print(f"  total rows: {len(out)}  {'OK (23733)' if len(out) == 23733 else 'MISMATCH'}")

    u = sum(1 for r in out if '॥' in r['shloka_text'])
    print(f"  rows with U+0965: {u}  {'OK — none' if u == 0 else 'FAIL'}")

    seen = defaultdict(int)
    for r in out:
        seen[(r['kanda'], r['sarga'], r['shloka'])] += 1
    dups = [t for t, c in seen.items() if c > 1]
    print(f"  duplicate triples: {len(dups)}  {dups[:5] if dups else 'OK'}")

    # every new row sits in correct numeric position relative to its neighbours
    pos = {id(r): i for i, r in enumerate(out)}
    bad = []
    newset = set()
    for rows in new_by_sarga.values():
        for r in rows:
            newset.add(id(r))
    for rows in new_by_sarga.values():
        for r in rows:
            i = pos[id(r)]
            # previous / next row within the same sarga
            prev = out[i - 1] if i > 0 else None
            nxt = out[i + 1] if i + 1 < len(out) else None
            if prev is not None and (prev['kanda'], prev['sarga']) == (r['kanda'], r['sarga']):
                if not (float(prev['shloka']) < float(r['shloka'])):
                    bad.append(f"{r['kanda']} {r['sarga']}.{r['shloka']}: prev {prev['shloka']} not < it")
            if nxt is not None and (nxt['kanda'], nxt['sarga']) == (r['kanda'], r['sarga']):
                if not (float(r['shloka']) < float(nxt['shloka'])):
                    bad.append(f"{r['kanda']} {r['sarga']}.{r['shloka']}: next {nxt['shloka']} not > it")
    print(f"  new rows out of numeric position: {len(bad)}  {'OK' if not bad else ''}")
    for b in bad:
        print("   !", b)


if __name__ == '__main__':
    main()
