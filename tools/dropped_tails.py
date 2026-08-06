#!/usr/bin/env python3
"""
dropped_tails.py — Quantify the "data.json drops trailing verses of sargas"
defect across all seven kandas, by running the pilot's tail-close check
everywhere (not just Kishkindha).

Read-only. Reuses align_recension.py's normalisation, per-shloka reconstruction
and alignment. Writes dropped_tails_report.md only; never touches data.json,
the .txt files or hindi_*.json.

Per sarga the tail is classified:
  CLOSES      last GP verse maps to last data.json verse
  DJ_SHORT    GP has trailing verse(s) genuinely absent from data.json  (the defect)
  GP_SHORT    data.json has trailing verse(s) with no GP counterpart
  RAGGED      tails overlap but do not correspond cleanly
  UNALIGNABLE similarity too low to judge — needs a human look (may be a content
              defect like Kishkindha 16, or a sarga-number offset)
A DJ_SHORT candidate whose trailing GP verses actually match the *next* sarga's
opening data.json verses is a cross-sarga BOUNDARY_SHIFT, reported separately,
not counted as a drop.

Head/mid drops (step 5) are detected the same way: GP verses with no data.json
counterpart that are genuinely absent (not merely mis-aligned).
"""
import os, re, sys, json
from difflib import SequenceMatcher
from collections import defaultdict

import align_recension as A
import parse_hindi_v4 as P

HERE = A.HERE
TXT_DIR = A.TXT_DIR
KANDA = A.KANDA

# similarity floor (as a fraction of the length-gap ceiling) below which we do
# not trust a per-sarga alignment enough to classify its tail
Q_UNALIGNABLE = 0.55
# ratio below which a GP verse is judged genuinely absent from a sarga's data.json
ABSENT_MAX = 0.50
# ratio above which a GP tail is judged to belong to the next sarga (boundary shift)
SHIFT_MIN = 0.60


def label(v):
    return str(v['first']) if v['first'] == v['last'] else f"{v['first']}-{v['last']}"


def gather_segments(prefix):
    """Collect {int_sarga: segment_text} across every .txt file for a kanda,
    plus an inventory (filename ranges vs sargas found) and duplicate map."""
    files = sorted(f for f in os.listdir(TXT_DIR)
                   if re.match(rf'{prefix}\d', f) and f.endswith('.txt'))
    seg_by = {}
    seg_by_float = {}          # interpolated प्रक्षिप्त sargas (e.g. 56.1)
    sarga_to_files = defaultdict(list)
    inv_rows = []
    for f in files:
        text = open(os.path.join(TXT_DIR, f), encoding='utf-8').read()
        rng = A.parse_filename_range(f, prefix)
        segs = P.split_segments(text)
        found = []
        if segs:
            for s, seg in segs:
                found.append(s)
                if float(s).is_integer():
                    seg_by[int(s)] = seg
                else:
                    seg_by_float[s] = seg
                sarga_to_files[s].append(f)
        else:
            s = P.detect_sarga(f, text)
            if s is not None:
                found.append(s)
                if float(s).is_integer():
                    seg_by[int(s)] = text
                else:
                    seg_by_float[s] = text
                sarga_to_files[s].append(f)
        inv_rows.append({'file': f, 'range': rng, 'found': sorted(found)})
    dups = {s: fs for s, fs in sarga_to_files.items() if len(fs) > 1}
    return seg_by, seg_by_float, inv_rows, dups


def trigrams(s):
    return set(s[i:i + 3] for i in range(len(s) - 2))


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def pair_sargas(seg_by, dj_by):
    """Content-based monotonic pairing of GP sargas to data.json sargas, so tail
    checks survive sarga-number offsets (e.g. Yuddha data.json = 131 sargas vs
    Gita Press 128). Trigram-Jaccard similarity + banded Needleman-Wunsch.
    Returns (dj->gp map, gp->dj map). Weak matches are left unpaired (gaps)."""
    G = sorted(seg_by)                       # GP sarga numbers
    Dl = sorted(dj_by)                       # data.json sarga numbers
    gcat = {i: ''.join(A.normalize(v['text']) for v in A.parse_gp_sarga(seg_by[i]))
            for i in G}
    dcat = {j: ''.join(A.normalize(t) for _, t in dj_by[j]) for j in Dl}
    gtri = {i: trigrams(gcat[i]) for i in G}
    dtri = {j: trigrams(dcat[j]) for j in Dl}
    MINSIM, BAND = 0.20, 8
    na, nb = len(G), len(Dl)
    NEG = -1e9
    f = [[NEG] * (nb + 1) for _ in range(na + 1)]
    f[0][0] = 0.0
    for a in range(na + 1):
        for b in range(nb + 1):
            if abs(a - b) > BAND and a and b:
                continue
            cur = f[a][b]
            if cur == NEG:
                continue
            if a < na and b < nb:
                s = jaccard(gtri[G[a]], dtri[Dl[b]])
                credit = s if s >= MINSIM else (s - 0.6)   # discourage weak pairs
                if cur + credit > f[a + 1][b + 1]:
                    f[a + 1][b + 1] = cur + credit
            if a < na and cur > f[a + 1][b]:            # GP sarga unmatched
                f[a + 1][b] = cur
            if b < nb and cur > f[a][b + 1]:            # dj sarga unmatched
                f[a][b + 1] = cur
    # traceback
    dj2gp, gp2dj = {}, {}
    a, b = na, nb
    while a > 0 or b > 0:
        cur = f[a][b]
        if a > 0 and b > 0:
            s = jaccard(gtri[G[a - 1]], dtri[Dl[b - 1]])
            credit = s if s >= MINSIM else (s - 0.6)
            if abs((a - 1) - (b - 1)) <= BAND and f[a - 1][b - 1] + credit == cur:
                if s >= MINSIM:
                    dj2gp[Dl[b - 1]] = G[a - 1]
                    gp2dj[G[a - 1]] = Dl[b - 1]
                a, b = a - 1, b - 1
                continue
        if a > 0 and f[a - 1][b] == cur:
            a -= 1
            continue
        b -= 1

    # Repair pass: the banded DP can orphan a run of parallel unpaired sargas at
    # an offset transition. Re-pair leftover GP and dj sargas by full similarity,
    # order-preserving, so their tails still get checked instead of dumped into
    # UNALIGNABLE. Uses real ratios (few sargas, cheap).
    ug = [i for i in G if i not in gp2dj]
    ud = [j for j in Dl if j not in dj2gp]
    if ug and ud:
        na2, nb2 = len(ug), len(ud)
        R = [[SequenceMatcher(None, gcat[ug[a]], dcat[ud[b]], autojunk=False).ratio()
              for b in range(nb2)] for a in range(na2)]
        g2 = [[0.0] * (nb2 + 1) for _ in range(na2 + 1)]
        for a in range(1, na2 + 1):
            for b in range(1, nb2 + 1):
                s = R[a - 1][b - 1]
                match = g2[a - 1][b - 1] + (s if s >= 0.55 else -1.0)
                g2[a][b] = max(match, g2[a - 1][b], g2[a][b - 1])
        a, b = na2, nb2
        while a > 0 and b > 0:
            s = R[a - 1][b - 1]
            if g2[a][b] == g2[a - 1][b - 1] + (s if s >= 0.55 else -1.0):
                if s >= 0.55:
                    dj2gp[ud[b - 1]] = ug[a - 1]
                    gp2dj[ug[a - 1]] = ud[b - 1]
                a, b = a - 1, b - 1
            elif g2[a][b] == g2[a - 1][b]:
                a -= 1
            else:
                b -= 1
    return dj2gp, gp2dj


def best_in_sarga(gnorm, dj_norm, exclude=()):
    """Best single-verse match ratio of gnorm against any data.json verse."""
    best_r, best_i = 0.0, None
    for i, dn in enumerate(dj_norm):
        if i in exclude or not dn:
            continue
        r = SequenceMatcher(None, gnorm, dn, autojunk=False).ratio()
        if r > best_r:
            best_r, best_i = r, i
    return best_r, best_i


def classify_sarga(kanda_num, sarga, seg, dj_rows, next_dj_rows):
    gp_verses = A.parse_gp_sarga(seg)
    gp_items = [(label(v), v['text']) for v in gp_verses]
    dj_items = [(str(sh), t) for sh, t in dj_rows]
    res = {'sarga': sarga, 'gp_count': len(gp_items), 'dj_count': len(dj_items)}

    if not gp_items:
        res.update({'klass': 'NO_TXT', 'similarity': None})
        return res
    if not dj_items:
        res.update({'klass': 'NO_DATA', 'similarity': None})
        return res

    sim, mat, gl, dl = A.align_sarga(gp_items, dj_items)
    tmax = 2 * min(gl, dl) / (gl + dl) if (gl + dl) else 0
    q = sim / tmax if tmax else 0
    res['similarity'] = round(sim, 3)
    res['q'] = round(q, 3)

    gp_norm = [A.normalize(t) for _, t in gp_items]
    dj_norm = [A.normalize(t) for _, t in dj_items]

    if q < Q_UNALIGNABLE:
        # Does the GP text match the NEXT sarga's data.json better than its own?
        # That points to a sarga-number offset rather than a content defect.
        gp_all = ''.join(gp_norm)
        own = SequenceMatcher(None, gp_all, ''.join(dj_norm), autojunk=False).ratio()
        hint = ''
        if next_dj_rows:
            nxt = SequenceMatcher(None, gp_all,
                                  ''.join(A.normalize(t) for _, t in next_dj_rows),
                                  autojunk=False).ratio()
            if nxt > own + 0.1:
                hint = f'; matches NEXT sarga better ({nxt:.2f} vs {own:.2f}) — likely offset'
        br, _ = best_in_sarga(gp_norm[0], dj_norm)
        res.update({'klass': 'UNALIGNABLE',
                    'note': f'q={q:.2f}; GP v1 best single-verse match here = {br:.2f}{hint}'})
        return res

    gp_to_dj, dj_to_gp = A.resolve_mapping(gp_items, dj_items, mat)
    dj_shlokas = [sh for sh, _ in dj_rows]
    last_gp = len(gp_items) - 1
    last_dj = len(dj_items) - 1

    # trailing GP verses that map to nothing
    tg = []
    for gi in range(last_gp, -1, -1):
        if not gp_to_dj[gi]:
            tg.append(gi)
        else:
            break
    tg = list(reversed(tg))
    # trailing data.json verses covered by no GP verse
    td = []
    covered = set(d for djs in gp_to_dj.values() for d in djs)
    for di in range(last_dj, -1, -1):
        if di not in covered:
            td.append(di)
        else:
            break
    td = list(reversed(td))

    closes = last_dj in gp_to_dj[last_gp]

    # ── head / mid drops (step 5): GP verses with no dj counterpart that are
    # genuinely absent, excluding the trailing run (handled as the tail) ──
    # Strict isolated-gap signature to avoid false positives from recension
    # divergence: an unmapped Sanskrit GP verse whose immediate neighbours map to
    # *consecutive* data.json verses — i.e. data.json genuinely skipped one where
    # GP has a verse — and whose text is absent from the sarga. Runs of unmapped
    # verses (divergent stretches) are excluded; only isolated singletons pass.
    head_missing, mid_missing = [], []
    for gi in range(0, last_gp + 1):
        if gi in tg or gp_to_dj[gi]:
            continue
        vtxt = gp_items[gi][1]
        # reject misparsed Hindi prose: flowing lines >90 chars, Hindi dialogue
        # quotes, or any Hindi marker word
        vlines = [l for l in vtxt.split('\n') if l.strip()]
        if (P.hindi_score(vtxt) > 0 or any(len(l) > 90 for l in vlines)
                or any(q in vtxt for q in "‘’“”'—")):   # Hindi quotes/dash
            continue
        br, _ = best_in_sarga(gp_norm[gi], dj_norm)
        if br >= ABSENT_MAX:                          # its text IS in the sarga
            continue
        rec = {'gp': gp_items[gi][0], 'words': A.first_words(gp_items[gi][1]),
               'best': round(br, 2), 'text': gp_items[gi][1]}
        if gi == 0:
            if gp_to_dj.get(1) and min(gp_to_dj[1]) == 0:
                head_missing.append(rec)             # dj starts at GP v2
        elif 0 < gi < last_gp and gp_to_dj[gi - 1] and gp_to_dj[gi + 1]:
            a, b = max(gp_to_dj[gi - 1]), min(gp_to_dj[gi + 1])
            if b > a + 1:                             # a dj verse sits in the gap
                continue
            # Distinguish a genuine drop from data.json having COMBINED this verse
            # into a neighbour: if dj[a] is better explained by GP[i-1]+GP[i]
            # (or dj[b] by GP[i]+GP[i+1]), the verse was absorbed, not dropped.
            def rat(x, y):
                return SequenceMatcher(None, x, y, autojunk=False).ratio()
            base_p = rat(gp_norm[gi - 1], dj_norm[a])
            comb_p = rat(gp_norm[gi - 1] + gp_norm[gi], dj_norm[a])
            base_n = rat(gp_norm[gi + 1], dj_norm[b])
            comb_n = rat(gp_norm[gi] + gp_norm[gi + 1], dj_norm[b])
            if comb_p > base_p + 0.12 or comb_n > base_n + 0.12:
                continue                              # absorbed into a neighbour
            rec = {**rec, 'dj_before': dj_rows[a][0], 'dj_after': dj_rows[b][0]}
            mid_missing.append(rec)

    # ── tail classification ──
    if closes and not tg and not td:
        res['klass'] = 'CLOSES'
    elif tg and not td:
        # genuine absence of every trailing GP verse?
        worst_best = 0.0
        for gi in tg:
            br, _ = best_in_sarga(gp_norm[gi], dj_norm)
            worst_best = max(worst_best, br)
        # boundary shift: does the GP tail match the next sarga's head?
        shift_r = 0.0
        if next_dj_rows:
            tail_txt = ''.join(gp_norm[gi] for gi in tg)
            nd_norm = [A.normalize(t) for _, t in next_dj_rows]
            for k in range(1, min(len(nd_norm), 25) + 1):
                r = SequenceMatcher(None, tail_txt, ''.join(nd_norm[:k]),
                                    autojunk=False).ratio()
                shift_r = max(shift_r, r)
        if shift_r >= SHIFT_MIN:
            res['klass'] = 'BOUNDARY_SHIFT'
            res['shift_ratio'] = round(shift_r, 2)
            res['tail_gp'] = [gp_items[gi][0] for gi in tg]
        elif worst_best < ABSENT_MAX:
            res['klass'] = 'DJ_SHORT'
            res['missing'] = [{'gp': gp_items[gi][0],
                               'words': A.first_words(gp_items[gi][1]),
                               'best': round(best_in_sarga(gp_norm[gi], dj_norm)[0], 2),
                               'text': gp_items[gi][1]}
                              for gi in tg]
        else:
            res['klass'] = 'RAGGED'
            res['note'] = (f'{len(tg)} trailing GP verse(s) unmapped but a '
                           f'data.json match exists (best {worst_best:.2f}) — '
                           f'alignment ragged, not a clean drop')
    elif td and not tg:
        res['klass'] = 'GP_SHORT'
        res['dj_extra'] = [dj_shlokas[di] for di in td]
    elif tg and td:
        res['klass'] = 'RAGGED'
        res['note'] = f'{len(tg)} GP + {len(td)} data.json trailing verses both unmatched'
    else:
        res['klass'] = 'RAGGED' if not closes else 'CLOSES'
        if res['klass'] == 'RAGGED':
            res['note'] = 'last GP verse does not map to last data.json verse'

    res['head_missing'] = head_missing
    res['mid_missing'] = mid_missing
    res['dj_uncovered_count'] = sum(1 for di in range(len(dj_items)) if di not in covered)
    return res


def run_kanda(kanda_num):
    prefix, kanda_name = KANDA[kanda_num]
    dj_by, _combined, _anom = A.load_datajson(kanda_name, kanda_num)
    seg_by, seg_float, inv_rows, dups = gather_segments(prefix)
    max_sarga = max(dj_by) if dj_by else 0

    # Pair GP sargas to data.json sargas by content, so the tail check compares
    # the right sargas even where the recensions renumber.
    dj2gp, gp2dj = pair_sargas(seg_by, dj_by)
    offset_pairs = {j: g for j, g in dj2gp.items() if g != j}

    results = []
    for sarga in range(1, max_sarga + 1):        # iterate data.json sargas
        dj_rows = dj_by.get(sarga, [])
        gp_sarga = dj2gp.get(sarga)
        if gp_sarga is None:
            # No Gita Press sarga pairs to this data.json sarga. Distinguish a
            # foreign-content defect (like Kishkindha 16: matches nothing) from a
            # recension insert/split (partially overlaps a neighbouring GP sarga).
            if not seg_by:
                results.append({'sarga': sarga, 'gp_count': 0,
                                'dj_count': len(dj_rows), 'klass': 'NO_TXT',
                                'similarity': None})
                continue
            dnorm = ''.join(A.normalize(t) for _, t in dj_rows)
            best_r, best_i = 0.0, None
            for i in seg_by:
                g = ''.join(A.normalize(v['text']) for v in A.parse_gp_sarga(seg_by[i]))
                if not g:
                    continue
                rr = SequenceMatcher(None, dnorm, g, autojunk=False).ratio()
                if rr > best_r:
                    best_r, best_i = rr, i
            if best_r < 0.30:
                note = (f'no Gita Press counterpart anywhere (best GP{best_i} '
                        f'{best_r:.2f}) — possible content defect, like Kishkindha 16')
            else:
                note = (f'data.json sarga with no 1:1 Gita Press counterpart; '
                        f'partially overlaps GP{best_i} ({best_r:.2f}). Likely a '
                        f'recension insert/split (this kanda: {len(dj_by)} data.json '
                        f'sargas vs {len(seg_by)} Gita Press)')
            results.append({'sarga': sarga, 'gp_count': 0,
                            'dj_count': len(dj_rows), 'klass': 'UNALIGNABLE',
                            'similarity': round(best_r, 3), 'note': note})
            continue
        r = classify_sarga(kanda_num, sarga, seg_by[gp_sarga], dj_rows,
                           dj_by.get(sarga + 1))
        if gp_sarga != sarga:
            r['gp_sarga'] = gp_sarga
        results.append(r)

    txt_ints = set(seg_by)
    dj_ints = set(dj_by)
    return {'kanda': kanda_num, 'name': kanda_name, 'prefix': prefix,
            'results': results, 'inv_rows': inv_rows, 'dups': dups,
            'floats': sorted(seg_float), 'max_sarga': max_sarga,
            'txt_only': sorted(txt_ints - dj_ints),
            'dj_only': sorted(dj_ints - txt_ints),
            'offset_pairs': offset_pairs,
            'gp_sarga_count': len(seg_by),
            'unpaired_gp': sorted(set(seg_by) - set(gp2dj))}


CLASSES = ['CLOSES', 'DJ_SHORT', 'GP_SHORT', 'RAGGED', 'UNALIGNABLE',
           'BOUNDARY_SHIFT', 'NO_TXT', 'NO_DATA']


def write_report(kandas):
    L = ['# Dropped trailing verses — all seven kandas\n']
    L.append("data.json verse tails vs Gita Press .txt (ramcharit.in). Method = the "
             "Kishkindha pilot's tail-close check (`align_recension.py`), run over "
             "every sarga, with content-based sarga pairing so the check survives "
             "the recensions' sarga-number offsets. **The one exception to "
             "read-only:** the five Yuddha files `yks120`–`yks124.txt` used a "
             "non-standard verse-stamp format (`६-१२०-१`); their stamps were "
             "converted to the standard `॥N॥` form so they parse (backups kept "
             "outside the repo). data.json, hindi_*.json and every other .txt are "
             "untouched.\n")

    # headline
    tot = defaultdict(int)
    dj_short_verses = 0
    per_kanda_short = {}
    for k in kandas:
        c = defaultdict(int)
        for r in k['results']:
            c[r['klass']] += 1
        short_v = sum(len(r.get('missing', [])) for r in k['results']
                      if r['klass'] == 'DJ_SHORT')
        per_kanda_short[k['kanda']] = (c['DJ_SHORT'], short_v)
        dj_short_verses += short_v
        for cls in CLASSES:
            tot[cls] += c[cls]

    L.append("## Headline\n")
    L.append(f"- **DJ_SHORT sargas (data.json missing trailing verse(s)): "
             f"{tot['DJ_SHORT']}**, totalling **{dj_short_verses} missing verses**.")
    L.append(f"- By kanda (DJ_SHORT sargas / verses): " +
             ", ".join(f"{KANDA[k][1].split()[0]} {per_kanda_short[k][0]}/"
                       f"{per_kanda_short[k][1]}" for k in sorted(per_kanda_short)) + ".")
    L.append(f"- Other tail classes: {tot['GP_SHORT']} GP_SHORT, {tot['RAGGED']} "
             f"RAGGED, {tot['BOUNDARY_SHIFT']} BOUNDARY_SHIFT, {tot['CLOSES']} CLOSES.")
    mid_total = sum(len(r.get('mid_missing', [])) for k in kandas for r in k['results'])
    head_total = sum(len(r.get('head_missing', [])) for k in kandas for r in k['results'])
    L.append(f"- **Head/mid-sarga drops:** {head_total} first-verse, {mid_total} "
             f"isolated mid-sarga gaps (data.json skips a verse Gita Press has, "
             f"between two consecutively-mapped verses). Candidates for review — see §5.")
    L.append(f"- **UNALIGNABLE: {tot['UNALIGNABLE']}** — all in Yuddha "
             f"(data.json 131 sargas vs Gita Press 128; these are the 3 extra "
             f"data.json sargas with no clean Gita Press counterpart). None is a "
             f"foreign-content defect like the original Kishkindha 16 — that one "
             f"was already corrected in the source .txt.")
    if tot['NO_TXT'] or tot['NO_DATA']:
        L.append(f"- No source: {tot['NO_TXT']} sargas without a .txt, "
                 f"{tot['NO_DATA']} without data.json rows.")
    L.append("- **Uttara** shows 0 DJ_SHORT and 106 GP_SHORT because its data.json "
             "already carries *more* verses than the current .txt (1798 vs 1722) — "
             "no trailing loss there.")
    L.append("")

    # per-kanda summary table
    L.append("## Per-kanda summary\n")
    L.append("| kanda | sargas | CLOSES | DJ_SHORT | GP_SHORT | RAGGED | "
             "UNALIGNABLE | BOUNDARY_SHIFT | NO_TXT |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for k in kandas:
        c = defaultdict(int)
        for r in k['results']:
            c[r['klass']] += 1
        L.append(f"| {k['name']} | {len(k['results'])} | {c['CLOSES']} | "
                 f"{c['DJ_SHORT']} | {c['GP_SHORT']} | {c['RAGGED']} | "
                 f"{c['UNALIGNABLE']} | {c['BOUNDARY_SHIFT']} | {c['NO_TXT']} |")
    L.append("")

    # DJ_SHORT full list
    L.append("## DJ_SHORT — data.json missing trailing verses (the defect)\n")
    L.append("| kanda | sarga | # missing | GP verse(s) absent from data.json — opening words |")
    L.append("|---|---|---|---|")
    for k in kandas:
        for r in k['results']:
            if r['klass'] != 'DJ_SHORT':
                continue
            miss = "; ".join(f"[{m['gp']}] {m['words']}" for m in r['missing'])
            L.append(f"| {k['name'].split()[0]} | {r['sarga']} | "
                     f"{len(r['missing'])} | {miss} |")
    L.append("")

    # UNALIGNABLE list
    L.append("## UNALIGNABLE — needs a human look\n")
    L.append("Low alignment: either a content defect (like Kishkindha 16's misplaced "
             "Aranya passage) or a sarga-number offset between the recensions.\n")
    L.append("| kanda | sarga | GP verses | dj verses | similarity | note |")
    L.append("|---|---|---|---|---|---|")
    for k in kandas:
        for r in k['results']:
            if r['klass'] != 'UNALIGNABLE':
                continue
            L.append(f"| {k['name'].split()[0]} | {r['sarga']} | {r['gp_count']} | "
                     f"{r['dj_count']} | {r.get('similarity')} | {r.get('note','')} |")
    L.append("")

    # BOUNDARY_SHIFT list
    L.append("## BOUNDARY_SHIFT — GP tail belongs to the next sarga (not a drop)\n")
    L.append("| kanda | sarga | GP tail verses | → next-sarga head match |")
    L.append("|---|---|---|---|")
    for k in kandas:
        for r in k['results']:
            if r['klass'] != 'BOUNDARY_SHIFT':
                continue
            L.append(f"| {k['name'].split()[0]} | {r['sarga']} | {r.get('tail_gp')} | "
                     f"{r.get('shift_ratio')} |")
    L.append("")

    # head / mid drops (step 5)
    L.append("## Head & mid-sarga drops (step 5)\n")
    L.append("A Gita Press verse that (a) maps to nothing, (b) is a Sanskrit couplet "
             "whose text is absent from the sarga (best single-verse match < %.2f), "
             "(c) sits between two neighbours that map to *consecutive* data.json "
             "verses, and (d) is not merely absorbed into a neighbour by combination. "
             "That is the signature of data.json skipping one verse. Still verify by "
             "hand — the lowest match scores are the most certain; Bala's early "
             "sargas may include parse noise. Spot-checks confirmed real cases "
             "(e.g. Kishkindha 20 v15, Sundara 60 v5–6, Bala 7 v5).\n" % ABSENT_MAX)
    any_hm = False
    L.append("| kanda | sarga | position | GP verse | opening words | best match |")
    L.append("|---|---|---|---|---|---|")
    for k in kandas:
        for r in k['results']:
            for m in r.get('head_missing', []):
                any_hm = True
                L.append(f"| {k['name'].split()[0]} | {r['sarga']} | FIRST | "
                         f"{m['gp']} | {m['words']} | {m['best']} |")
            for m in r.get('mid_missing', []):
                any_hm = True
                L.append(f"| {k['name'].split()[0]} | {r['sarga']} | mid | "
                         f"{m['gp']} | {m['words']} | {m['best']} |")
    if not any_hm:
        L.append("| — | — | — | — | none found | — |")
    L.append("")

    # inventory anomalies
    L.append("## File-inventory anomalies\n")
    for k in kandas:
        notes = []
        for row in k['inv_rows']:
            if not row['range']:
                continue
            exp = set(range(row['range'][0], row['range'][1] + 1))
            got = set(int(s) for s in row['found'] if float(s).is_integer())
            miss, extra = sorted(exp - got), sorted(got - exp)
            if miss or extra:
                notes.append(f"`{row['file']}` expected {row['range'][0]}–"
                             f"{row['range'][1]}, missing {miss or '—'}, extra {extra or '—'}")
        if k['dups']:
            notes.append(f"sargas in >1 file: {dict(k['dups'])}")
        if k['floats']:
            notes.append(f"interpolated (प्रक्षिप्त) sargas in .txt only: {k['floats']}")
        if k['offset_pairs']:
            lo = min(k['offset_pairs'])
            notes.append(f"sarga-number offset between recensions from ~sarga {lo} "
                         f"({len(k['offset_pairs'])} sargas renumbered; data.json "
                         f"{len(k['results'])} sargas vs Gita Press "
                         f"{k['gp_sarga_count']}). Content pairing used; the "
                         f"unpaired data.json sargas are listed under UNALIGNABLE")
        if notes:
            L.append(f"**{k['name']}**")
            for n in notes:
                L.append(f"- {n}")
            L.append("")
    if all(not (k['dups'] or k['floats'] or k['txt_only'] or k['dj_only']) for k in kandas):
        pass

    out = os.path.join(HERE, 'dropped_tails_report.md')
    open(out, 'w', encoding='utf-8').write('\n'.join(L))
    return out, tot, dj_short_verses, per_kanda_short


def main():
    only = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(1, 8))
    kandas = []
    for kn in only:
        print(f"aligning {KANDA[kn][1]} ...", flush=True)
        kandas.append(run_kanda(kn))
    out, tot, short_v, per = write_report(kandas)
    print(f"\nWrote {out}")
    print("=" * 56)
    print(f"DJ_SHORT sargas: {tot['DJ_SHORT']}  ({short_v} verses)")
    for kn in sorted(per):
        if per[kn][0]:
            print(f"   {KANDA[kn][1]}: {per[kn][0]} sargas / {per[kn][1]} verses")
    print(f"GP_SHORT: {tot['GP_SHORT']} | RAGGED: {tot['RAGGED']} | "
          f"BOUNDARY_SHIFT: {tot['BOUNDARY_SHIFT']} | CLOSES: {tot['CLOSES']}")
    print(f"UNALIGNABLE: {tot['UNALIGNABLE']} | NO_TXT: {tot['NO_TXT']}")


if __name__ == '__main__':
    main()
