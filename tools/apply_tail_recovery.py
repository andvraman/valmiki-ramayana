#!/usr/bin/env python3
"""
apply_tail_recovery.py — Insert the 153 recovered verses from
tail_recovery_final.json into data.json.

Each new row gets kanda/sarga/shloka/shloka_text set and empty transliteration,
translation, explanation, comments. Rows are inserted positionally (right after
their sarga's current last row) so the file stays ordered by kanda, sarga,
shloka — data.json is NOT globally re-sorted (it has two intentionally
out-of-order rows: Uttara sarga 2 and the प्रक्षिप्त Aranya 56.1 appended at the
end). Backs up data.json first. Refuses to overwrite an existing triple.
"""
import json, shutil
from collections import defaultdict

DATA = 'data.json'
PATCH = 'tail_recovery_final.json'
BACKUP = 'data.json.pre_tail_recovery.bak'


def main():
    data = json.load(open(DATA, encoding='utf-8'))
    patch = json.load(open(PATCH, encoding='utf-8'))['kandas']
    n_before = len(data)

    # 1) back up first
    shutil.copy2(DATA, BACKUP)
    print(f"Backed up {DATA} -> {BACKUP} ({n_before} rows)")

    existing = set((r['kanda'], r['sarga'], r['shloka']) for r in data)

    # collect new rows, refusing any triple that already exists
    groups = defaultdict(list)          # (kanda, sarga) -> [(shloka, text)]
    refused = []
    affected_sargas = set()
    for kf, sargas in patch.items():
        for s, shlokas in sargas.items():
            sarga = int(s)
            affected_sargas.add((kf, sarga))
            for sh, rec in shlokas.items():
                shloka = int(sh)
                if (kf, sarga, shloka) in existing:
                    refused.append((kf, sarga, shloka))
                    continue
                groups[(kf, sarga)].append((shloka, rec['shloka_text']))

    if refused:
        print(f"\n⚠ REFUSED {len(refused)} rows — triple already exists in data.json "
              f"(not overwritten):")
        for kf, s, sh in refused:
            print(f"   {kf} sarga {s} shloka {sh}")

    # index of each sarga's current last row (affected sargas are contiguous)
    last_idx = {}
    for i, r in enumerate(data):
        last_idx[(r['kanda'], r['sarga'])] = i

    inserts = defaultdict(list)
    added = defaultdict(int)
    for (kf, sarga), verses in groups.items():
        idx = last_idx.get((kf, sarga))
        if idx is None:
            print(f"⚠ no existing rows for {kf} sarga {sarga} — cannot place; skipped")
            continue
        for shloka, text in sorted(verses):
            inserts[idx].append({
                'kanda': kf, 'sarga': sarga, 'shloka': shloka,
                'shloka_text': text, 'transliteration': '', 'translation': '',
                'explanation': '', 'comments': '',
            })
            added[kf] += 1

    # rebuild list with positional inserts
    out = []
    for i, r in enumerate(data):
        out.append(r)
        for row in inserts.get(i, ()):
            out.append(row)

    json.dump(out, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False)

    # ---- report ----
    KORDER = ['Bala Kanda', 'Ayodhya Kanda', 'Aranya Kanda', 'Kishkindha Kanda',
              'Sundara Kanda', 'Yuddha Kanda', 'Uttara Kanda']
    total_added = sum(added.values())
    print("\nRows added per kanda:")
    for k in KORDER:
        if added.get(k):
            print(f"   {k}: {added[k]}")
    print(f"total added: {total_added}")
    print(f"new total: {len(out)}  (expected {n_before} + 153 = {n_before + 153})")

    # ---- verify ----
    print("\nVERIFY")
    # (a) no duplicate triples anywhere
    seen = defaultdict(int)
    for r in out:
        seen[(r['kanda'], r['sarga'], r['shloka'])] += 1
    dups = [t for t, c in seen.items() if c > 1]
    print(f"  duplicate kanda/sarga/shloka triples: {len(dups)}"
          + ("" if not dups else f"  {dups[:10]}"))

    # (b) each affected sarga's verse numbers unbroken from 1
    by = defaultdict(list)
    for r in out:
        by[(r['kanda'], r['sarga'])].append(r['shloka'])
    broken = []
    for (kf, sarga) in sorted(affected_sargas, key=lambda x: (KORDER.index(x[0]), x[1])):
        shl = sorted(by[(kf, sarga)])
        expected = list(range(1, int(max(shl)) + 1))
        if shl != expected:
            missing = sorted(set(expected) - set(shl))
            broken.append((kf, sarga, int(max(shl)), missing))
    if not broken:
        print(f"  all {len(affected_sargas)} affected sargas run unbroken from 1 ✓")
    else:
        print(f"  {len(broken)} affected sarga(s) NOT unbroken from 1:")
        for kf, sarga, mx, missing in broken:
            print(f"   {kf} sarga {sarga}: 1..{mx} but missing {missing} "
                  f"(pre-existing data.json gap, not from this insert)")


if __name__ == '__main__':
    main()
