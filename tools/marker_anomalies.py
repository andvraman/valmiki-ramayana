#!/usr/bin/env python3
"""
marker_anomalies.py — Locate the 15 defective/ambiguous marker occurrences from
half_verse_markers.md §1 and report, for each: kanda, sarga, file, line number,
surrounding verse context (the verse before and after), and a proposed correct
marker. Read-only — NO .txt file is modified.
"""
import os, re
from collections import defaultdict
import parse_hindi_v4 as P

TXT = 'ramcharitdotin'
KANDA = {'bks': 'Bala', 'aks': 'Ayodhya', 'ars': 'Aranya', 'kks': 'Kishkindha',
         'sks': 'Sundara', 'yks': 'Yuddha', 'uks': 'Uttara'}
DEV = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5',
       '६': '6', '७': '7', '८': '8', '९': '9'}
BRACE = re.compile(r'\{[^}]{1,30}\}')
STAMP = re.compile(r'॥[^॥]{0,25}॥')
# a "clean" verse number on a line: ॥N॥ / ॥ N ॥ / ॥N-M॥ / {sN}/{hN}
CLEAN = re.compile(r'॥\s*([०-९]+(?:\s*[-–—]\s*[०-९]+)?)\s*(?:[०-९]\s*/\s*[०-९]\s*)?॥|'
                   r'\{[SsHh](\d+)(?:-\d+)?(?:\s+1/2)?\}')


def deva(s):
    return int(''.join(DEV.get(c, '') for c in s))


def shape(s):
    s = re.sub(r'[०-९]+', '#द', s)
    s = re.sub(r'[0-9]+', '#', s)
    return re.sub(r'\s+', ' ', s)


TARGET = {'॥॥', '॥ ॥', '॥।#द॥', '॥ । #द॥', '॥ #द #द ॥', '॥ #द #द॥',
          '{S#}', '॥ #द/#द॥', '॥#द/#द॥'}


def kof(f):
    for p, n in KANDA.items():
        if f.startswith(p):
            return n
    return None


def line_number(text, pos):
    return text.count('\n', 0, pos) + 1


def verse_num_of_line(line):
    """A resolvable verse number from a line's stamp/marker, or None."""
    m = CLEAN.search(line)
    if not m:
        return None
    if m.group(1):
        toks = re.findall(r'[०-९]+', m.group(1))
        return '-'.join(str(deva(t)) for t in toks)
    return m.group(2)


def opening(line, n=8):
    t = re.sub(r'\{[^}]*\}', ' ', line)
    t = re.sub(r'[॥।]', ' ', t)
    return ' '.join(t.split()[:n])


def neighbour(lines, i, step):
    """nearest line with a resolvable verse number, in direction step."""
    j = i + step
    while 0 <= j < len(lines):
        v = verse_num_of_line(lines[j])
        if v is not None:
            return v, opening(lines[j])
        j += step
    return None, ''


def sarga_at(seg_bounds, lineno):
    for (lo, hi, sarga) in seg_bounds:
        if lo <= lineno <= hi:
            return sarga
    return '?'


def propose(sh, form, line, before, after):
    b = before[0]; a = after[0]
    def i(x):
        try:
            return int(x)
        except (TypeError, ValueError):
            return None
    bi, ai = i(b), i(a)
    is_hindi = P.hindi_score(line) > 0
    is_colophon = ('इत्याचे' in line or 'इत्यार्षे' in line or 'आदिकाव्य' in line
                   or 'सम्पूर्णम्' in line or '\n' in form)
    if sh in ('॥॥', '॥ ॥'):
        if '\n' in form or is_colophon:
            return ("regex artifact — two separate dandas across a blank line at a "
                    "colophon / kanda boundary; not one marker, no fix needed")
        mk = re.search(r'\{[SsHh](\d+)(?:-(\d+))?\}', line)
        if mk:
            v = mk.group(1) if not mk.group(2) else f"{mk.group(1)}-{mk.group(2)}"
            return (f"doubled danda ॥॥ before a valid `{{{mk.group(0)[1:-1]}}}` marker "
                    f"→ collapse to a single ॥; verse number is {v} (from the marker)")
        if is_hindi:
            return (f"empty stamp on a Hindi paragraph → number lost. It translates "
                    f"verse {b}, so likely ॥{b}॥ (confirm whether coverage also spills "
                    f"— then ॥{b} १/२॥)")
        return "indeterminate — inspect"
    if sh in ('॥।#द॥', '॥ । #द॥'):
        num = re.search(r'[०-९]+', line)
        n = deva(num.group(0)) if num else '?'
        return f"stray danda inside stamp → ॥{n}॥ (number {n}"+ (f", fits between {b} and {a})" if bi is not None else ")")
    if sh in ('॥ #द #द ॥', '॥ #द #द॥'):
        nums = [deva(x) for x in re.findall(r'[०-९]+', line)]
        if len(nums) == 2:
            n1, n2 = nums
            if n2 == n1 + 1:
                return f"missing dash → ॥{n1}-{n2}॥ (range) — but verify vs a two-verse split"
            return f"two numbers {n1} {n2}: {'range ॥%d-%d॥?' % (n1,n2) if n2>n1 else 'second looks like a typo — probably ॥%d॥' % n1}"
        return "inspect"
    if sh == '{S#}':
        num = re.search(r'\d+', line)
        return f"capital S → lowercase {{s{num.group(0) if num else '?'}}}"
    if sh in ('॥ #द/#द॥', '॥#द/#द॥'):
        # glued verse+fraction: the trailing 1/2 is the half; the rest is the verse
        inner = re.search(r'॥([^॥]*)॥', line)
        s = inner.group(1) if inner else ''
        s2 = re.sub(r'\s*[१1]\s*/\s*[२2]\s*$', '', s)
        v = deva(re.sub(r'[^०-९]', '', s2)) if re.search(r'[०-९]', s2) else '?'
        fits = ''
        if bi is not None:
            fits = f" — surrounding verses {b}/{a}, so {v}½ (verse {v} + line 1 of {v+1 if isinstance(v,int) else '?'}), not literal fraction"
        return f"glued → ॥ {v} १/२॥{fits}"
    return "inspect"


def main():
    occ = []
    for f in sorted(os.listdir(TXT)):
        if not f.endswith('.txt'):
            continue
        k = kof(f)
        if not k:
            continue
        text = open(os.path.join(TXT, f), encoding='utf-8').read()
        lines = text.split('\n')
        # segment line ranges
        seg_bounds = []
        titles = [(idx, P.parse_sarga_num(m.group(1)))
                  for idx, ln in enumerate(lines)
                  for m in [P.TITLE_RE.match(ln.strip())] if m]
        for n, (idx, sn) in enumerate(titles):
            end = titles[n + 1][0] - 1 if n + 1 < len(titles) else len(lines) - 1
            sfmt = str(int(sn)) if float(sn).is_integer() else str(sn)
            seg_bounds.append((idx, end, sfmt))
        if not seg_bounds:
            sn = P.detect_sarga(f, text)
            seg_bounds = [(0, len(lines) - 1, str(sn) if sn else '?')]

        for rx in (BRACE, STAMP):
            for m in rx.finditer(text):
                sh = shape(m.group(0))
                if sh not in TARGET:
                    continue
                lineno = line_number(text, m.start())     # 1-based
                i0 = lineno - 1
                # the match may span blank lines; find the line holding it
                line = lines[i0]
                before = neighbour(lines, i0, -1)
                after = neighbour(lines, i0, +1)
                occ.append({
                    'k': k, 'file': f, 'lineno': lineno,
                    'sarga': sarga_at(seg_bounds, i0),
                    'shape': sh, 'form': repr(m.group(0)),
                    'line': line.strip()[:80],
                    'before': before, 'after': after,
                    'proposal': propose(sh, m.group(0), line, before, after),
                })

    write_report(occ)
    print(f"anomaly occurrences located: {len(occ)} (expected 15)")
    from collections import Counter
    print("by shape:", dict(Counter(o['shape'] for o in occ)))


def write_report(occ):
    KORDER = ['Bala', 'Ayodhya', 'Aranya', 'Kishkindha', 'Sundara', 'Yuddha', 'Uttara']
    order = {'॥॥': 0, '॥ ॥': 1, '॥।#द॥': 2, '॥ । #द॥': 3, '॥ #द #द ॥': 4,
             '॥ #द #द॥': 5, '{S#}': 6, '॥ #द/#द॥': 7, '॥#द/#द॥': 8}
    L = ['# Marker anomalies — investigation (read-only)\n']
    L.append("The 15 defective/ambiguous marker occurrences from "
             "`half_verse_markers.md` §1, with location, surrounding verse "
             "context, and a proposed correction. **No `.txt` file has been "
             "modified — awaiting confirmation per resolution.**\n")
    L.append(f"Located: **{len(occ)}** occurrences.\n")
    L.append("| # | kanda | sarga | file | line | shape | exact form | verse before | verse after | proposed correction |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for n, o in enumerate(sorted(occ, key=lambda x: (order.get(x['shape'], 9),
                                                     KORDER.index(x['k']), x['lineno'])), 1):
        bef = f"{o['before'][0]}: {o['before'][1]}" if o['before'][0] else "—"
        aft = f"{o['after'][0]}: {o['after'][1]}" if o['after'][0] else "—"
        L.append(f"| {n} | {o['k']} | {o['sarga']} | `{o['file']}` | {o['lineno']} | "
                 f"`{o['shape']}` | `{o['form']}` | {bef} | {aft} | {o['proposal']} |")
    L.append("")
    L.append("## Per-anomaly context (the line, with the verse on each side)\n")
    for n, o in enumerate(sorted(occ, key=lambda x: (order.get(x['shape'], 9),
                                                     KORDER.index(x['k']), x['lineno'])), 1):
        L.append(f"### {n}. {o['k']} sarga {o['sarga']} — `{o['file']}` line {o['lineno']} — shape `{o['shape']}`")
        L.append(f"- exact form: `{o['form']}`")
        L.append(f"- line: {o['line']}")
        L.append(f"- verse before: {o['before'][0] or '—'} — {o['before'][1]}")
        L.append(f"- verse after: {o['after'][0] or '—'} — {o['after'][1]}")
        L.append(f"- **proposed:** {o['proposal']}")
        L.append("")
    open('marker_anomalies.md', 'w', encoding='utf-8').write('\n'.join(L))


if __name__ == '__main__':
    main()
