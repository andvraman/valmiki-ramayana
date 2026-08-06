#!/usr/bin/env python3
"""
half_verse_markers2.py — Reissue half_verse_markers.md covering BOTH notations:
brace-delimited {…} and native Devanagari stamps ॥…॥. Step 1 enumerates every
distinct marker shape (digit runs normalised: ASCII -> #, Devanagari -> #द,
whitespace -> single space). Step 2 lists every occurrence carrying a range or a
fraction, with effective coverage. Read-only — no .txt file is modified.

Coverage rule (per spec): a fraction १/२ (or 1/2) means "+ line 1 of the verse
AFTER the last one named", never half of the named verse.
  ॥ १९-२०॥       -> 19–20 complete
  ॥ ३० १/२॥      -> 30 complete, + line 1 of 31
  ॥ ३४-३५ १/२॥   -> 34–35 complete, + line 1 of 36
"""
import os, re
from collections import defaultdict, OrderedDict
import parse_hindi_v4 as P

TXT = 'ramcharitdotin'
KANDA = {'bks': 'Bala', 'aks': 'Ayodhya', 'ars': 'Aranya', 'kks': 'Kishkindha',
         'sks': 'Sundara', 'yks': 'Yuddha', 'uks': 'Uttara'}
KORDER = ['Bala', 'Ayodhya', 'Aranya', 'Kishkindha', 'Sundara', 'Yuddha', 'Uttara']
DEV = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5',
       '६': '6', '७': '7', '८': '8', '९': '9'}
BRACE = re.compile(r'\{[^}]{1,30}\}')
STAMP = re.compile(r'॥[^॥]{0,25}॥')
FRAC = re.compile(r'[०-९0-9]\s*/\s*[०-९0-9]')
FRAC_TAIL = re.compile(r'\s*[१1]\s*/\s*[२2]\s*$')


def kof(f):
    for p, n in KANDA.items():
        if f.startswith(p):
            return n
    return None


def deva(s):
    return int(''.join(DEV.get(c, '') for c in s))


def shape(s):
    s = re.sub(r'[०-९]+', '#द', s)
    s = re.sub(r'[0-9]+', '#', s)
    return re.sub(r'\s+', ' ', s)


def numstr(tok):
    return deva(tok) if re.match(r'[०-९]', tok) else int(tok)


def parse_marker(inner):
    """inner = text inside {} (minus s/h prefix) or between ॥…॥.
    Returns (named_vals, has_fraction) or (None, None) if no verse numbers."""
    has_frac = bool(FRAC.search(inner))
    named = FRAC_TAIL.sub('', inner) if has_frac else inner
    named = re.sub(r'[–—]', '-', named)                 # unify dash variants
    toks = re.findall(r'[०-९]+|[0-9]+', named)
    if not toks:
        return None, None
    return [numstr(t) for t in toks], has_frac


def opening(line, marker, n=9):
    t = line.replace(marker, ' ')
    t = re.sub(r'\{[^}]*\}', ' ', t)
    t = re.sub(r'[॥।]', ' ', t)
    return ' '.join(t.split()[:n])


def main():
    shapes = defaultdict(lambda: {'n': 0, 'k': set(), 'ex': None})
    occ = []          # dict per range/fraction occurrence

    for f in sorted(os.listdir(TXT)):
        if not f.endswith('.txt'):
            continue
        k = kof(f)
        if not k:
            continue
        text = open(os.path.join(TXT, f), encoding='utf-8').read()
        # shape inventory over the whole file
        for rx in (BRACE, STAMP):
            for m in rx.finditer(text):
                d = shapes[shape(m.group(0))]
                d['n'] += 1; d['k'].add(k)
                if d['ex'] is None:
                    d['ex'] = m.group(0)
        # per-sarga occurrences
        segs = P.split_segments(text)
        if not segs:
            s = P.detect_sarga(f, text)
            segs = [(s, text)] if s is not None else []
        for sarga, seg in segs:
            sfmt = str(int(sarga)) if float(sarga).is_integer() else str(sarga)
            for line in seg.split('\n'):
                if not line.strip():
                    continue
                htype = 'Hindi' if P.hindi_score(line) > 0 else 'Sanskrit'
                for m in BRACE.finditer(line):
                    full = m.group(0)
                    pm = re.match(r'\{([SsHh])(.*)\}$', full)
                    if not pm:
                        continue
                    prefix, inner = pm.group(1), pm.group(2)
                    vals, frac = parse_marker(inner)
                    if vals is None or (len(vals) < 2 and not frac):
                        continue
                    occ.append(record(k, sfmt, vals, frac, full,
                                      f'brace {{{prefix}}}', htype, line))
                for m in STAMP.finditer(line):
                    full = m.group(0)
                    inner = full[1:-1]
                    vals, frac = parse_marker(inner)
                    if vals is None or (len(vals) < 2 and not frac):
                        continue
                    occ.append(record(k, sfmt, vals, frac, full,
                                      'stamp', htype, line))

    write_report(shapes, occ)
    nfrac = sum(1 for o in occ if o['frac'])
    nrange = sum(1 for o in occ if o['is_range'])
    print(f"distinct shapes: {len(shapes)}")
    print(f"range/fraction occurrences: {len(occ)}  (fraction {nfrac}, range {nrange})")
    print("Wrote half_verse_markers.md")


def record(k, sarga, vals, frac, full, notation, htype, line):
    lo, hi = vals[0], vals[-1]
    named = str(lo) if len(vals) == 1 else f"{lo}-{hi}"
    if frac:
        cover = f"{named} complete, + line 1 of {hi + 1}"
    else:
        cover = f"{named} complete"
    anomaly = ''
    if len(vals) >= 2 and not (lo < hi):
        anomaly = ' ⚠ non-ascending'
    return {'k': k, 'sarga': sarga, 'named': named, 'notation': notation,
            'form': full, 'cover': cover + anomaly, 'htype': htype,
            'frac': bool(frac), 'is_range': len(vals) >= 2,
            'open': opening(line, full), 'sortv': float(lo)}


def write_report(shapes, occ):
    L = ['# Marker inventory & half-verse / range coverage — both notations\n']
    L.append("From ramcharit.in/ .txt. Two notations: brace `{…}` and native "
             "Devanagari stamps `॥…॥`. A fraction `१/२` (or `1/2`) means **+ line 1 "
             "of the verse after the last one named**, never half the named verse. "
             "Read-only.\n")

    # ── Step 1: shape inventory ──
    L.append("## 1. Marker shape inventory\n")
    L.append("Digit runs normalised: ASCII → `#`, Devanagari → `#द`, whitespace → "
             "one space. Every distinct shape, most frequent first.\n")
    L.append("| count | shape | kandas | example |")
    L.append("|---|---|---|---|")
    for sh, d in sorted(shapes.items(), key=lambda x: -x[1]['n']):
        ks = ','.join(sorted(d['k'], key=lambda x: KORDER.index(x)))
        L.append(f"| {d['n']} | `{sh}` | {ks} | `{d['ex']!r}`".replace("`'", "`").replace("'`", "`") + " |")
    L.append("")

    # ── summary of range/fraction occurrences ──
    byk = defaultdict(lambda: defaultdict(int))
    for o in occ:
        byk[o['k']]['frac' if o['frac'] else 'range'] += 1
        byk[o['k']][o['notation'] + '/' + o['htype']] += 1
    L.append("## 2. Range / fraction occurrences — counts\n")
    L.append("| kanda | fraction (…१/२) | range only | total |")
    L.append("|---|---|---|---|")
    tf = tr = 0
    for k in KORDER:
        if k in byk:
            fr, rg = byk[k]['frac'], byk[k]['range']
            tf += fr; tr += rg
            L.append(f"| {k} | {fr} | {rg} | {fr + rg} |")
    L.append(f"| **total** | **{tf}** | **{tr}** | **{tf + tr}** |")
    L.append("")
    # notation × line-type breakdown
    nt = defaultdict(int)
    for o in occ:
        nt[(o['notation'], o['htype'])] += 1
    L.append("By notation × line the marker sits on:\n")
    L.append("| notation | on Sanskrit line | on Hindi line |")
    L.append("|---|---|---|")
    notations = sorted(set(o['notation'] for o in occ))
    for n in notations:
        L.append(f"| {n} | {nt[(n, 'Sanskrit')]} | {nt[(n, 'Hindi')]} |")
    L.append("")

    # ── Step 2: full list ──
    L.append("## 3. Full list — every range / fraction occurrence\n")
    L.append("Grouped by kanda → sarga. `coverage` is the effective span (named "
             "verses complete, plus any spill line). `line` = Sanskrit couplet or "
             "Hindi paragraph the marker sits on.\n")
    bysarga = defaultdict(list)
    for o in occ:
        bysarga[(o['k'], o['sarga'])].append(o)
    for k in KORDER:
        sargas = sorted((s for (kk, s) in bysarga if kk == k), key=float)
        if not sargas:
            continue
        L.append(f"### {k}\n")
        L.append("| sarga | named | notation | line | form | coverage | opening words |")
        L.append("|---|---|---|---|---|---|---|")
        for s in sargas:
            for o in sorted(bysarga[(k, s)], key=lambda x: (x['sortv'], x['notation'])):
                L.append(f"| {s} | {o['named']} | {o['notation']} | {o['htype']} | "
                         f"`{o['form']}` | {o['cover']} | {o['open']} |")
        L.append("")

    open('half_verse_markers.md', 'w', encoding='utf-8').write('\n'.join(L))


if __name__ == '__main__':
    main()
