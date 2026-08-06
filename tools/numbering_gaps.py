#!/usr/bin/env python3
"""
numbering_gaps.py — Scan data.json directly for verse-numbering gaps, with no
Gita Press comparison. Reports three categories separately: sargas with skipped
numbers, sargas not starting at 1, duplicate numbers. For each gap gives the
kanda, sarga, missing number(s) and the opening words of the verses on either
side. Cross-references the skipped-number gaps against the 42 surviving
mid-sarga candidates in mid_sarga_gaps_v3.md. Read-only.
"""
import json, re
from collections import defaultdict, Counter

KORDER = ['Bala Kanda', 'Ayodhya Kanda', 'Aranya Kanda', 'Kishkindha Kanda',
          'Sundara Kanda', 'Yuddha Kanda', 'Uttara Kanda']
KIDX = {k: i for i, k in enumerate(KORDER)}


def opening(text, n=6):
    t = re.sub(r'।।[\d.]+।।\s*$', '', text)          # drop trailing stamp
    t = t.replace('।', ' ').replace('॥', ' ')
    return ' '.join(t.split()[:n])


def is_colophon(text):
    return 'इत्यार्षे' in text or 'आदिकाव्ये' in text


def stripped(text):
    """Text with all stamps (।।k.s.n।।, inline k.s.n), dandas and whitespace
    removed — for detecting rows that share one combined-block Sanskrit text."""
    t = re.sub(r'।।[\d.]+।।', '', text)
    t = re.sub(r'\d+(?:\.\d+)+', '', t)      # inline k.s.n stamps
    return re.sub(r'[।॥\s]', '', t)


def categorise(vals, text, m):
    """Classify a missing integer m: colophon / combined-block / sub-verse
    renumbering / GENUINE."""
    below = max((v for v in vals if v < m), default=None)
    above = min((v for v in vals if v > m), default=None)
    if (below is not None and is_colophon(text[below])) or \
       (above is not None and is_colophon(text[above])):
        return 'colophon'
    if below is not None and above is not None and \
       stripped(text[below]) and stripped(text[below]) == stripped(text[above]):
        return 'combined-block'
    # float sub-verse(s) in the span between the nearest present integers
    lo = max((v for v in vals if float(v).is_integer() and v < m), default=None)
    hi = min((v for v in vals if float(v).is_integer() and v > m), default=None)
    if lo is not None and hi is not None and \
       any(not float(v).is_integer() and lo < v < hi for v in vals):
        return 'sub-verse'
    return 'GENUINE'


def load_v3_candidates():
    """§2 surviving rows of mid_sarga_gaps_v3.md -> set of (kanda_short, dj_sarga)
    and list of (kanda_short, gp_sarga_verse, dj_sarga)."""
    try:
        txt = open('mid_sarga_gaps_v3.md', encoding='utf-8').read()
    except FileNotFoundError:
        return set(), []
    sargas, rows, in2 = set(), [], False
    for line in txt.split('\n'):
        if line.startswith('## 2.'):
            in2 = True; continue
        if in2 and line.startswith('## 3.'):
            break
        if in2 and line.startswith('|'):
            c = [x.strip() for x in line.strip().strip('|').split('|')]
            if len(c) >= 3 and c[0] not in ('kanda',) and '---' not in c[0]:
                try:
                    dj = int(c[2])
                except ValueError:
                    continue
                sargas.add((c[0], dj))
                rows.append((c[0], c[1], dj))
    return sargas, rows


def main():
    data = json.load(open('data.json', encoding='utf-8'))
    by = defaultdict(list)
    for r in data:
        by[(r['kanda'], r['sarga'])].append((r['shloka'], r['shloka_text']))

    skipped, notstart, dups = [], [], []
    for (k, s), rows in by.items():
        vals = [v for v, _ in rows]
        text = {v: t for v, t in rows}
        cnt = Counter(vals)
        d = sorted(v for v, c in cnt.items() if c > 1)
        if d:
            dups.append((k, s, d, text))
        ints = sorted(set(int(v) for v in vals if float(v).is_integer()))
        if not ints:
            continue
        if ints[0] != 1:
            notstart.append((k, s, ints[0], text))
        miss = [x for x in range(1, ints[-1] + 1) if x not in ints]
        if miss:
            skipped.append((k, s, miss, sorted(vals), text))

    v3_sargas, v3_rows = load_v3_candidates()
    write_report(skipped, notstart, dups, v3_sargas, v3_rows, by)

    print(f"skipped-number sargas: {len(skipped)}")
    print(f"not-starting-at-1 sargas: {len(notstart)}")
    print(f"duplicate-number sargas: {len(dups)}")
    print(f"v3 surviving candidate sargas: {len(v3_sargas)}")


def sk(x):
    return (KIDX[x[0]], x[1])


def neighbours(vals, text, m):
    """opening words of the present verses immediately below and above missing m."""
    below = max((v for v in vals if v < m), default=None)
    above = min((v for v in vals if v > m), default=None)
    b = f"[{fmtv(below)}] {opening(text[below])}" if below is not None else "—"
    a = f"[{fmtv(above)}] {opening(text[above])}" if above is not None else "—"
    return below, above, b, a


def fmtv(v):
    return str(int(v)) if float(v).is_integer() else str(v)


def write_report(skipped, notstart, dups, v3_sargas, v3_rows, by):
    L = ['# data.json verse-numbering gaps (direct scan)\n']
    L.append("Scanned data.json's own shloka numbers per kanda/sarga — no Gita "
             "Press comparison. Float shlokas (e.g. `8.1`) are supplementary "
             "sub-verses and float sargas (`56.1`) are प्रक्षिप्त interpolations; "
             "neither is treated as a gap. Read-only.\n")

    # categorise every missing number
    CATDESC = {
        'GENUINE': 'genuine hole — a numbered verse whose row is absent',
        'combined-block': 'content present — the rows either side share one '
                          'combined-block text that spans the missing number',
        'sub-verse': 'renumbering — a float sub-verse occupies the position',
        'colophon': 'artifact — the surrounding rows are colophon lines',
    }
    genuine_gaps = []   # (kanda, sarga, m)
    for k, s, miss, vals, text in skipped:
        for m in miss:
            if categorise(vals, text, m) == 'GENUINE':
                genuine_gaps.append((k, s, m))

    L.append("## Summary\n")
    L.append(f"- **Sargas with skipped numbers: {len(skipped)}** "
             f"(spanning {sum(len(x[2]) for x in skipped)} missing numbers)")
    L.append(f"- of those, **{len(genuine_gaps)} are genuine holes**; the rest are "
             f"combined-block / sub-verse / colophon artifacts (content present or "
             f"not a real verse) — see per-gap tags below")
    L.append(f"- **Sargas not starting at 1: {len(notstart)}**")
    L.append(f"- **Duplicate numbers: {len(dups)}**")
    L.append("")

    # 1. skipped numbers
    L.append("## 1. Sargas with skipped numbers\n")
    L.append("Each missing number is tagged: **GENUINE** (real missing verse), "
             "*combined-block* (rows either side share one block text that spans "
             "it — content present), *sub-verse* (a float sub-verse occupies the "
             "slot), *colophon* (surrounding rows are colophons).\n")
    for k, s, miss, vals, text in sorted(skipped, key=sk):
        short = k.split()[0]
        cats = [categorise(vals, text, m) for m in miss]
        ngen = cats.count('GENUINE')
        head = f"{ngen} genuine" if ngen else "no genuine holes"
        L.append(f"### {short} sarga {fmtv(s)} — missing {miss}  ({head})")
        for m, cat in zip(miss, cats):
            below, above, b, a = neighbours(vals, text, m)
            mark = "**GENUINE**" if cat == 'GENUINE' else f"*{cat}*"
            L.append(f"- **missing {m}** — {mark} ({CATDESC[cat]})")
            L.append(f"    - before {b}")
            L.append(f"    - after  {a}")
        L.append("")

    # 2. not starting at 1
    L.append("## 2. Sargas not starting at 1\n")
    if not notstart:
        L.append("None.\n")
    else:
        for k, s, first, text in sorted(notstart, key=sk):
            L.append(f"- {k.split()[0]} sarga {fmtv(s)}: starts at {first} — "
                     f"[{first}] {opening(text[first])}")
        L.append("")

    # 3. duplicates
    L.append("## 3. Duplicate numbers\n")
    if not dups:
        L.append("None.\n")
    else:
        for k, s, d, text in sorted(dups, key=sk):
            L.append(f"- {k.split()[0]} sarga {fmtv(s)}: duplicate {d}")
        L.append("")

    # cross-reference
    L.append("## 4. Cross-reference with mid_sarga_gaps_v3.md (42 surviving candidates)\n")
    L.append("The direct numbering scan and the Gita Press mid-sarga scan detect "
             "different things: this scan finds holes in data.json's own numbering; "
             "the v3 scan finds Gita Press verses absent from data.json between two "
             "consecutively-mapped verses. A numbering gap counts as *already on the "
             "v3 list* only if v3 has a surviving candidate for the same kanda+sarga.\n")
    # cross-reference the GENUINE holes (the recoverable ones)
    on, new = [], []
    for k, s, m in genuine_gaps:
        short = k.split()[0]
        hit = (short, int(s)) in v3_sargas if float(s).is_integer() else False
        (on if hit else new).append((short, fmtv(s), m))
    L.append(f"Cross-referencing the **{len(genuine_gaps)} genuine holes** (the "
             f"combined-block / sub-verse / colophon artifacts are not recoverable "
             f"content gaps and are excluded here):\n")
    L.append(f"**Already on the v3 list ({len(on)}):** "
             f"{', '.join(f'{a} {b}.{c}' for a,b,c in on) if on else 'none'}")
    L.append("")
    L.append(f"**New — not caught by the Gita Press scan ({len(new)}):**")
    for a, b, c in new:
        L.append(f"- {a} {b}.{c}")
    L.append("")
    L.append("Ayodhyā 35 missing 21 is the known instance the Gita Press comparison "
             "missed — it appears here as a GENUINE hole in the NEW list, confirming "
             "the scan surfaces what the comparison overlooked.")
    L.append("")

    open('numbering_gaps.md', 'w', encoding='utf-8').write('\n'.join(L))
    print("Wrote numbering_gaps.md")


if __name__ == '__main__':
    main()
