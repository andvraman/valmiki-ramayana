#!/usr/bin/env python3
"""
half_verse_markers.py — Extract every {n 1/2} and {n-m 1/2} half-verse marker
from ramcharit.in/ .txt files to a reference, and count {hN-M} range markers.
These hand-annotated markers record where a Hindi paragraph's coverage spills
past a verse boundary; they must be preserved before any {sN}/{hN} -> ॥N॥ pass.
Read-only — no .txt file is modified.
"""
import os, re
from collections import defaultdict, Counter
import parse_hindi_v4 as P

TXT_DIR = 'ramcharitdotin'
KANDA = {'bks': ('Bala', 1), 'aks': ('Ayodhya', 2), 'ars': ('Aranya', 3),
         'kks': ('Kishkindha', 4), 'sks': ('Sundara', 5), 'yks': ('Yuddha', 6),
         'uks': ('Uttara', 7)}
KORDER = ['Bala', 'Ayodhya', 'Aranya', 'Kishkindha', 'Sundara', 'Yuddha', 'Uttara']

HALF = re.compile(r'\{[hH](\d+)(?:-(\d+))?\s+1/2\}')          # {h9 1/2} / {h9-10 1/2}
HRANGE = re.compile(r'\{[hH](\d+)-(\d+)\}')                   # {h9-10}  (no fraction)


def kanda_of(fname):
    for pre, (name, num) in KANDA.items():
        if fname.startswith(pre):
            return name, num
    return None, None


def opening(line, marker, n=9):
    t = line.replace(marker, ' ')
    t = re.sub(r'\{[^}]*\}', ' ', t)                          # drop any other markers
    t = re.sub(r'[॥।]', ' ', t)
    return ' '.join(t.split()[:n])


def main():
    half = []                      # (kanda, sarga, verse_str, marker, opening)
    hrange_count = defaultdict(int)
    hrange_half_count = defaultdict(int)   # {hN-M 1/2} subset, for context

    files = sorted(f for f in os.listdir(TXT_DIR) if f.endswith('.txt'))
    for f in files:
        kname, knum = kanda_of(f)
        if kname is None:
            continue
        text = open(os.path.join(TXT_DIR, f), encoding='utf-8').read()
        segs = P.split_segments(text)
        if not segs:
            s = P.detect_sarga(f, text)
            segs = [(s, text)] if s is not None else []
        for sarga, seg in segs:
            sfmt = str(int(sarga)) if float(sarga).is_integer() else str(sarga)
            for line in seg.split('\n'):
                for m in HALF.finditer(line):
                    verse = m.group(1) if not m.group(2) else f"{m.group(1)}-{m.group(2)}"
                    if m.group(2):
                        hrange_half_count[kname] += 1
                    half.append((kname, sfmt, verse, m.group(0),
                                 opening(line, m.group(0))))
                for _m in HRANGE.finditer(line):
                    # exclude the {hN-M 1/2} ones (HRANGE won't match them — the
                    # ' 1/2}' tail differs), so this counts plain range markers only
                    hrange_count[kname] += 1

    write_report(half, hrange_count, hrange_half_count)
    print(f"half-verse {{n 1/2}}/{{n-m 1/2}} markers: {len(half)}")
    print(f"plain {{hN-M}} range markers: {sum(hrange_count.values())}")


def main_sortkey(k):
    return KORDER.index(k) if k in KORDER else 9


def write_report(half, hrange_count, hrange_half_count):
    L = ['# Half-verse markers ({n 1/2}, {n-m 1/2}) — reference\n']
    L.append("Hand-annotated ragged-join markers from ramcharit.in/ .txt: they "
             "record where a Hindi paragraph's coverage spills half a verse past "
             "a boundary. Preserve before any `{sN}`/`{hN}` → `॥N॥` conversion. "
             "Read-only extraction.\n")

    by_k = defaultdict(list)
    for rec in half:
        by_k[rec[0]].append(rec)

    L.append("## Per-kanda count — half-verse markers\n")
    L.append("| kanda | {n 1/2} + {n-m 1/2} | of which ranges {n-m 1/2} |")
    L.append("|---|---|---|")
    tot = 0
    for k in KORDER:
        if k in by_k:
            n = len(by_k[k])
            tot += n
            L.append(f"| {k} | {n} | {hrange_half_count.get(k, 0)} |")
    L.append(f"| **total** | **{tot}** | **{sum(hrange_half_count.values())}** |")
    L.append("")

    L.append("## {hN-M} range markers (no fraction) — count only\n")
    L.append("| kanda | {hN-M} |")
    L.append("|---|---|")
    rtot = 0
    for k in KORDER:
        if hrange_count.get(k):
            rtot += hrange_count[k]
            L.append(f"| {k} | {hrange_count[k]} |")
    L.append(f"| **total** | **{rtot}** |")
    L.append("")

    L.append("## Full list — half-verse markers\n")
    L.append("| kanda | sarga | verse(s) | marker | Hindi paragraph opening |")
    L.append("|---|---|---|---|---|")
    for k in KORDER:
        for kn, sarga, verse, marker, op in sorted(
                by_k.get(k, []), key=lambda r: (float(r[1]), r[2])):
            L.append(f"| {kn} | {sarga} | {verse} | `{marker}` | {op} |")
    L.append("")

    open('half_verse_markers.md', 'w', encoding='utf-8').write('\n'.join(L))
    print("Wrote half_verse_markers.md")


if __name__ == '__main__':
    main()
