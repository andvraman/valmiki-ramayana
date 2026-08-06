#!/usr/bin/env python3
"""
search_candidates.py — For each surviving mid-sarga gap candidate in
mid_sarga_gaps_v2.md, search its Gita Press Sanskrit against (a) every verse in
its own data.json sarga and (b) every verse in its whole data.json kanda.
Report the best match and location for each. Anything scoring > 0.50 anywhere in
its kanda is flagged PRESENT-ELSEWHERE (possible same verse under the other
recension's wording — inserting it would duplicate content).

Read-only. Reuses align_recension.normalize and difflib autojunk=False.
"""
import re, json
from difflib import SequenceMatcher
from collections import defaultdict
import align_recension as A
import parse_hindi_v4 as P
import dropped_tails as D

A.FILTER_HINDI_PARA = True
KANDA = A.KANDA
NAME2PREFIX = {nm.split()[0]: pp for pp, nm in KANDA.values()}
NAME2NUM = {nm.split()[0]: kn for kn, (pp, nm) in KANDA.items()}
FULLNAME = {nm.split()[0]: nm for pp, nm in KANDA.values()}
THRESH = 0.50


def parse_candidates(path='mid_sarga_gaps_v2.md'):
    """Read §3 survivors: (kanda_short, sarga, gp_label, words, v1_best)."""
    cands, in3 = [], False
    for line in open(path, encoding='utf-8'):
        if line.startswith('## 3.'):
            in3 = True; continue
        if in3 and line.startswith('## 4.'):
            break
        if in3 and line.startswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            # the opening-words cell can itself contain a literal '|' (a danda),
            # producing >5 cells — rejoin the middle cells as the words field
            if len(cells) >= 5 and cells[0] not in ('kanda', '---') and '---' not in cells[0]:
                k, s, gp = cells[0], cells[1], cells[2]
                best = cells[-1]
                words = '|'.join(cells[3:-1]).strip()
                cands.append((k, int(s), gp, words, best))
    return cands


def gp_text(prefix, sarga, gp_label, words=None):
    """Return the Gita Press verse text for a candidate. A label can occur on
    more than one block in a sarga (e.g. two verses stamped 19), so disambiguate
    by the candidate's recorded opening words; fall back to the first by label."""
    seg = SEG_CACHE.setdefault(prefix, D.gather_segments(prefix)[0])
    if sarga not in seg:
        return None
    matches = []
    for v in A.parse_gp_sarga(seg[sarga]):
        lbl = str(v['first']) if v['first'] == v['last'] else f"{v['first']}-{v['last']}"
        if lbl == gp_label:
            matches.append(v['text'])
    if not matches:
        return None
    if words:
        for t in matches:
            if A.first_words(t).startswith(words[:20]) or words.startswith(A.first_words(t)[:20]):
                return t
    return matches[0]


SEG_CACHE = {}


def load_kanda_verses():
    """data.json -> {kanda_short: {'by_sarga': {s:[(shloka,norm)]}, 'flat':[(s,shloka,norm)]}}
    using align_recension's per-shloka reconstruction."""
    data = json.load(open('data.json', encoding='utf-8'))
    raw = defaultdict(lambda: defaultdict(list))
    for r in data:
        nm = r.get('kanda', '')
        if nm.endswith('Kanda'):
            raw[nm][int(r['sarga'])].append((int(r['shloka']), r.get('shloka_text', '')))
    out = {}
    for nm, sargas in raw.items():
        short = nm.split()[0]
        knum = NAME2NUM[short]
        by_sarga, flat = {}, []
        for s, rows in sargas.items():
            rows.sort()
            texts, _c, _a = A._reconstruct_sarga(rows, knum, s)
            vs = [(sh, A.normalize(texts[sh])) for sh, _ in rows]
            by_sarga[s] = vs
            for sh, nt in vs:
                flat.append((s, sh, nt))
        out[short] = {'by_sarga': by_sarga, 'flat': flat}
    return out


def ratio(a, b):
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def main():
    cands = parse_candidates()
    KV = load_kanda_verses()
    rows = []
    for k, s, gp, words, v1best in cands:
        raw = gp_text(NAME2PREFIX[k], s, gp, words)
        if raw is None:
            rows.append({'k': k, 's': s, 'gp': gp, 'words': words,
                         'err': 'GP verse not found'})
            continue
        q = A.normalize(raw)
        kv = KV.get(k, {'by_sarga': {}, 'flat': []})
        # own sarga
        own = kv['by_sarga'].get(s, [])
        own_best_r, own_best_sh = 0.0, None
        for sh, nt in own:
            r = ratio(q, nt)
            if r > own_best_r:
                own_best_r, own_best_sh = r, sh
        # whole kanda
        kb_r, kb_loc = 0.0, None
        for (ss, sh, nt) in kv['flat']:
            r = ratio(q, nt)
            if r > kb_r:
                kb_r, kb_loc = r, (ss, sh)
        rows.append({'k': k, 's': s, 'gp': gp, 'words': words,
                     'own_r': round(own_best_r, 3), 'own_sh': own_best_sh,
                     'kanda_r': round(kb_r, 3), 'kanda_loc': kb_loc,
                     'present_elsewhere': kb_r > THRESH})
    write_report(rows)
    pe = [r for r in rows if r.get('present_elsewhere')]
    print("=" * 56)
    print(f"candidates searched: {len(rows)}")
    print(f"PRESENT-ELSEWHERE (>{THRESH} somewhere in kanda): {len(pe)}")
    for r in pe:
        loc = r['kanda_loc']
        print(f"   {r['k']} {r['s']}.{r['gp']} -> best {r['kanda_r']} at "
              f"sarga {loc[0]} v{loc[1]}")
    absent = [r for r in rows if not r.get('present_elsewhere') and 'err' not in r]
    print(f"absent everywhere (<= {THRESH}): {len(absent)}")


def write_report(rows):
    L = ['# Mid-sarga candidate verification — sarga vs whole-kanda search\n']
    L.append(f"Each surviving mid-sarga gap candidate's Gita Press Sanskrit, "
             f"searched against every data.json verse in its own sarga and its "
             f"whole kanda (normalisation + `autojunk=False` from "
             f"`align_recension.py`). **> {THRESH} anywhere in the kanda → "
             f"PRESENT-ELSEWHERE** (may be the same verse under the other "
             f"recension's wording; inserting would duplicate). Read-only.\n")
    pe = [r for r in rows if r.get('present_elsewhere')]
    L.append("## Summary\n")
    L.append(f"- candidates: **{len(rows)}**")
    L.append(f"- **PRESENT-ELSEWHERE (>{THRESH} in kanda): {len(pe)}**")
    L.append(f"- absent everywhere (best ≤ {THRESH}): "
             f"{sum(1 for r in rows if not r.get('present_elsewhere') and 'err' not in r)}")
    L.append("")
    if pe:
        L.append("## PRESENT-ELSEWHERE — verify before inserting\n")
        L.append("| kanda | sarga.verse | opening words | best in kanda | at |")
        L.append("|---|---|---|---|---|")
        for r in sorted(pe, key=lambda x: -x['kanda_r']):
            loc = r['kanda_loc']
            L.append(f"| {r['k']} | {r['s']}.{r['gp']} | {r['words']} | "
                     f"**{r['kanda_r']}** | sarga {loc[0]} v{loc[1]} |")
        L.append("")
    L.append("## All candidates\n")
    L.append("| kanda | sarga.verse | opening words | best in own sarga | best in kanda | kanda location | verdict |")
    L.append("|---|---|---|---|---|---|---|")
    order = {short: i for i, short in enumerate(NAME2PREFIX)}
    for r in sorted(rows, key=lambda x: (order.get(x['k'], 9), x['s'])):
        if 'err' in r:
            L.append(f"| {r['k']} | {r['s']}.{r['gp']} | {r['words']} | — | — | — | {r['err']} |")
            continue
        loc = r['kanda_loc']
        verdict = 'PRESENT-ELSEWHERE' if r['present_elsewhere'] else 'absent'
        L.append(f"| {r['k']} | {r['s']}.{r['gp']} | {r['words']} | "
                 f"{r['own_r']} (v{r['own_sh']}) | {r['kanda_r']} | "
                 f"sarga {loc[0]} v{loc[1]} | {verdict} |")
    L.append("")
    open('candidate_search_report.md', 'w', encoding='utf-8').write('\n'.join(L))
    print("Wrote candidate_search_report.md")


if __name__ == '__main__':
    main()
