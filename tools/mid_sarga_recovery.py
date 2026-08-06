#!/usr/bin/env python3
"""
mid_sarga_recovery.py — Merge the two mid-sarga lists into one recovery set:
the 42 surviving candidates from mid_sarga_gaps_v3.md and the 12 genuine holes
from numbering_gaps.md. De-duplicated at verse level (same GP verse inserted at
the same data.json position = one entry). Pulls Sanskrit from ramcharit.in/ .txt
(cut so each verse ends at its stamp) and assigns shloka numbers:
  * a verse filling a free integer slot (dj has 20 and 22) -> 21
  * a verse inserted where no integer is free (between 20 and 21) -> 20.1, 20.2…
Emits mid_sarga_recovery.json (shape of tail_recovery_final.json) + a summary.
Read-only on data.json and the .txt files.
"""
import json, re
from difflib import SequenceMatcher
from collections import defaultdict, OrderedDict
import align_recension as A
import parse_hindi_v4 as P
import dropped_tails as D

A.FILTER_HINDI_PARA = True
KANDA = A.KANDA
KNUM = {nm: kn for kn, (pp, nm) in KANDA.items()}
SHORT2FULL = {nm.split()[0]: nm for pp, nm in KANDA.values()}
STAMP_EOL = re.compile(r'॥\s*[०-९]+\s*॥\s*$')
STAMP_NUM = re.compile(r'॥\s*([०-९]+)\s*॥\s*$')
DEV = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5',
       '६': '6', '७': '7', '८': '8', '९': '9'}


def deva(s):
    return int(''.join(DEV[c] for c in s if c in DEV))


TODEV = {v: k for k, v in DEV.items()}


def to_deva(n):
    return ''.join(TODEV[c] for c in str(n))


def extract_gp(seg):
    """Cut GP verses at their ॥N॥ stamp: collect Sanskrit lines across blocks
    (reassembling half-verses split around Hindi paragraphs) and split at each
    trailing stamp. Returns ordered list of (label_str, text) ending at ॥N॥."""
    text = P.blank_footnotes(P._strip_colophon(seg))
    skt = []
    for b in (x for x in re.split(r'\n\s*\n', text) if x.strip()):
        if P.is_skip(b):
            continue
        if A.classify_block(b)[0] == 'sanskrit':
            for ln in b.split('\n'):
                if ln.strip():
                    skt.append(ln.rstrip())
    verses, cur = [], []
    for ln in skt:
        sm = STAMP_NUM.search(ln)
        mm = MARKER_EOL.search(ln)
        if sm:
            cur.append(ln)
            verses.append((str(deva(sm.group(1))), '\n'.join(cur)))
            cur = []
        elif mm:                                  # {s10}-style editor marker
            num = mm.group(1)
            cur.append(MARKER_EOL.sub('॥' + to_deva(num) + '॥', ln))  # -> ॥N॥ (Devanagari)
            verses.append((num, '\n'.join(cur)))
            cur = []
        else:
            cur.append(ln)
    return verses


MARKER_EOL = re.compile(r'[॥।\s]*\{[SsHh]?(\d+)(?:-\d+)?(?:\s+1/2)?\}\s*$')


# ── per-kanda caches ────────────────────────────────────────────────
_seg, _dj, _pair = {}, {}, {}


def kanda_data(short):
    if short in _seg:
        return _seg[short], _dj[short], _pair[short]
    prefix, full = KANDA[KNUM[SHORT2FULL[short]]]
    seg, _f, _i, _d = D.gather_segments(prefix)
    djb, _c, _a = A.load_datajson(SHORT2FULL[short], KNUM[SHORT2FULL[short]])
    dj2gp, _g = D.pair_sargas(seg, djb)
    _seg[short], _dj[short], _pair[short] = seg, djb, dj2gp
    return seg, djb, dj2gp


_align_cache = {}


def align(short, dj_sarga):
    """Return (gp_items, gp_to_dj, dj_rows, gp_sarga) for a dj sarga, content-paired."""
    key = (short, dj_sarga)
    if key in _align_cache:
        return _align_cache[key]
    seg, djb, dj2gp = kanda_data(short)
    gp_sarga = dj2gp.get(dj_sarga, dj_sarga)
    gp_items = extract_gp(seg[gp_sarga]) if gp_sarga in seg else []
    dj_rows = djb.get(dj_sarga, [])
    if gp_items and dj_rows:
        _sim, mat, _gl, _dl = A.align_sarga(gp_items, dj_items := [(str(s), t) for s, t in dj_rows])
        gp_to_dj, _ = A.resolve_mapping(gp_items, dj_items, mat)
    else:
        gp_to_dj = {}
    out = (gp_items, gp_to_dj, dj_rows, gp_sarga)
    _align_cache[key] = out
    return out


def nearest_mapped(gp_to_dj, gi, n, step):
    j = gi + step
    while 0 <= j < n:
        if gp_to_dj.get(j):
            return (max if step < 0 else min)(gp_to_dj[j])
        j += step
    return None


# ── parse the two source lists ──────────────────────────────────────
def parse_v3():
    rows = []
    in2 = False
    for line in open('mid_sarga_gaps_v3.md', encoding='utf-8'):
        if line.startswith('## 2.'):
            in2 = True; continue
        if in2 and line.startswith('## 3.'):
            break
        if in2 and line.startswith('|'):
            c = [x.strip() for x in line.strip().strip('|').split('|')]
            if len(c) >= 3 and c[0] not in ('kanda',) and '---' not in c[0]:
                gp_s, gp_v = c[1].split('.', 1)
                try:
                    rows.append((c[0], int(gp_s), gp_v, int(c[2])))
                except ValueError:
                    pass
    return rows


def parse_holes():
    """GENUINE-tagged missing numbers from numbering_gaps.md §1."""
    holes = []
    cur = None
    for line in open('numbering_gaps.md', encoding='utf-8'):
        h = re.match(r'### (\w+) sarga (\d+)', line)
        if h:
            cur = (h.group(1), int(h.group(2)))
        m = re.match(r'- \*\*missing (\d+)\*\* — \*\*GENUINE\*\*', line)
        if m and cur:
            holes.append((cur[0], cur[1], int(m.group(1))))
    return holes


# ── main ────────────────────────────────────────────────────────────
def main():
    data = json.load(open('data.json', encoding='utf-8'))
    existing = defaultdict(set)          # (kanda_full, sarga) -> set of shloka values
    for r in data:
        existing[(r['kanda'], r['sarga'])].add(r['shloka'])

    v3 = parse_v3()
    holes = parse_holes()
    print(f"v3 candidates parsed: {len(v3)}   genuine holes parsed: {len(holes)}")

    excluded = []      # (short, dj_sarga, m, reason)
    # each recovery target -> dict; key it by (short, dj_sarga, normalized gp_text)
    targets = OrderedDict()

    def norm_key(short, dj_sarga, text):
        return (short, dj_sarga, A.normalize(text))

    # v3 candidates
    for short, gp_sarga, gp_v, dj_sarga in v3:
        gp_items, gp_to_dj, dj_rows, paired = align(short, dj_sarga)
        want = gp_v.split('-')[0]                      # range label -> first number
        gi = next((i for i, (L, _) in enumerate(gp_items) if L == want), None)
        if gi is None:
            print(f"  ⚠ v3 {short} {dj_sarga} GP {gp_v}: not found in parse"); continue
        text = gp_items[gi][1]
        a = nearest_mapped(gp_to_dj, gi, len(gp_items), -1)
        b = nearest_mapped(gp_to_dj, gi, len(gp_items), +1)
        db = dj_rows[a][0] if a is not None else None
        da = dj_rows[b][0] if b is not None else None
        k = norm_key(short, dj_sarga, text)
        targets.setdefault(k, {'short': short, 'dj_sarga': dj_sarga,
                               'gp_sarga': paired, 'gp_label': gp_v, 'text': text,
                               'dj_before': db, 'dj_after': da, 'src': set()})
        targets[k]['src'].add('v3')

    # holes
    for short, dj_sarga, m in holes:
        gp_items, gp_to_dj, dj_rows, paired = align(short, dj_sarga)
        dj_norm = [A.normalize(t) for _, t in dj_rows]
        # Primary: the GP verse labelled m (works when GP and dj share within-sarga
        # numbering, i.e. diagonal sargas and aligned-offset ones). Accept only if
        # its text is genuinely absent from the dj sarga.
        gi = None
        cand = next((j for j, (L, _) in enumerate(gp_items) if L == str(m)), None)
        if cand is not None:
            q = A.normalize(gp_items[cand][1])
            best = max((SequenceMatcher(None, q, d, autojunk=False).ratio()
                        for d in dj_norm if d), default=0)
            if best < 0.5:
                gi = cand
        # Fallback: unmapped GP verse flanked by dj m-1 and m+1
        if gi is None:
            dj_shlokas = [s for s, _ in dj_rows]
            try:
                ib, ia = dj_shlokas.index(m - 1), dj_shlokas.index(m + 1)
            except ValueError:
                ib = ia = None
            for j, (L, _) in enumerate(gp_items):
                if gp_to_dj.get(j):
                    continue
                below = nearest_mapped(gp_to_dj, j, len(gp_items), -1)
                above = nearest_mapped(gp_to_dj, j, len(gp_items), +1)
                if below == ib and above == ia:
                    gi = j; break
        if gi is None:
            reason = ("no genuinely-absent GP verse at this position "
                      f"(data.json sarga has {len(dj_rows)} verses vs Gita Press "
                      f"{len(gp_items)}; the missing integer is a data.json "
                      f"numbering artifact, not absent content)")
            excluded.append((short, dj_sarga, m, reason))
            print(f"  ⚠ hole {short} {dj_sarga}.{m}: excluded — {reason}")
            continue
        text = gp_items[gi][1]
        k = norm_key(short, dj_sarga, text)
        t = targets.setdefault(k, {'short': short, 'dj_sarga': dj_sarga,
                                   'gp_sarga': paired, 'gp_label': gp_items[gi][0],
                                   'text': text, 'dj_before': m - 1, 'dj_after': m + 1,
                                   'src': set()})
        t['src'].add('hole')
        t['hole_int'] = m

    assign_numbers_and_emit(targets, existing, excluded)


def assign_numbers_and_emit(targets, existing, excluded):
    # group by (short, dj_sarga, dj_before) to assign integers / fractions in order
    groups = defaultdict(list)
    for t in targets.values():
        groups[(t['short'], t['dj_sarga'], t['dj_before'])].append(t)

    entries = []           # (kanda_full, sarga, shloka_value, shloka_str, t)
    problems = []
    for (short, dj_sarga, db), grp in groups.items():
        full = SHORT2FULL[short]
        exist = existing[(full, dj_sarga)]
        da = grp[0]['dj_after']
        free_ints = [i for i in range(int(db) + 1, int(da))] if (db is not None and da is not None) else []
        frac_used = 1
        grp.sort(key=lambda t: (t.get('hole_int', 1e9), t['gp_label']))
        for idx, t in enumerate(grp):
            if 'hole_int' in t and t['hole_int'] not in exist:
                # a raw data.json numbering gap — fill the free integer
                val, s = t['hole_int'], str(t['hole_int'])
            elif idx < len(free_ints) and free_ints[idx] not in exist:
                val = free_ints[idx]; s = str(val)
            else:
                # fractional: db + .k, skipping collisions
                while True:
                    val = round(int(db) + frac_used / 10, 1)
                    frac_used += 1
                    if val not in exist:
                        break
                s = str(val)
            t['shloka_val'], t['shloka_str'] = val, s
            entries.append((full, dj_sarga, val, s, t))

    # ── validate ──
    for full, sarga, val, s, t in entries:
        lines = [l for l in t['text'].split('\n') if l.strip()]
        if not lines or not STAMP_EOL.search(lines[-1].rstrip()):
            problems.append(f"{t['short']} {sarga} -> {s}: last line has no ॥N॥ stamp")
        if val in existing[(full, sarga)]:
            problems.append(f"{t['short']} {sarga} -> {s}: COLLIDES with existing row")

    # ── emit (shape of tail_recovery_final.json) ──
    patch = {}
    for full, sarga, val, s, t in entries:
        ks = patch.setdefault(full, {})
        ss = ks.setdefault(str(sarga), {})
        lines = [l.rstrip() for l in t['text'].split('\n') if l.strip()]
        ss[s] = {
            'shloka_text': '\n'.join(lines),
            'line_count': len(lines),
            'gp_label': t['gp_label'],
            'gp_sarga': t['gp_sarga'],
            'source': '+'.join(sorted(t['src'])),
            'inserted_between': [t['dj_before'], t['dj_after']],
        }
    out = {'_note': 'Merged mid-sarga recovery set (v3 candidates + numbering-gap '
                    'holes, de-duplicated at verse level). shloka_text ends at its '
                    '॥N॥ stamp; normalise before applying. Read-only artifact.',
           'kandas': patch,
           'excluded_holes': [{'kanda': SHORT2FULL[s], 'sarga': sg, 'missing': m,
                               'reason': r} for s, sg, m, r in excluded]}
    json.dump(out, open('mid_sarga_recovery.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)

    # ── summary ──
    from collections import Counter
    srcs = Counter(e[4]['source'] if False else '+'.join(sorted(e[4]['src'])) for e in entries)
    print("\n" + "=" * 56)
    print(f"merged recovery entries: {len(entries)}")
    print(f"  by source: {dict(srcs)}")
    print(f"  integer-fill: {sum(1 for e in entries if float(e[2]).is_integer())}, "
          f"fractional: {sum(1 for e in entries if not float(e[2]).is_integer())}")
    print(f"validation problems: {len(problems)}")
    for p in problems:
        print("  !", p)
    if excluded:
        print(f"excluded holes (not recoverable): {len(excluded)}")
        for s, sg, m, r in excluded:
            print(f"  - {s} {sg}.{m}")
    print("Wrote mid_sarga_recovery.json")


if __name__ == '__main__':
    main()
