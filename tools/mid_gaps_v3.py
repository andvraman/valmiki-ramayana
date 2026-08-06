#!/usr/bin/env python3
"""
mid_gaps_v3.py — Re-run the mid-sarga gap check on the CONTENT-based sarga
pairing (dropped_tails.run_kanda already pairs by content), carrying each
candidate's exact Gita Press verse text from detection so verification never
re-fetches by sarga number. Every candidate is labelled by its source GP sarga
AND its paired data.json sarga, removing the number/content ambiguity that
produced the v2 false positives in Yuddha's offset zone.

Verifies each candidate against its paired dj sarga and its whole kanda.
Emits mid_sarga_gaps_v3.md:
  - surviving candidates (absent everywhere, best <= 0.50)
  - audit: candidates that actually sit at a real dj verse (best > 0.50),
    with the data.json sarga + verse they resolve to.
Read-only. Reuses align_recension.normalize + difflib autojunk=False.
"""
import json
from difflib import SequenceMatcher
from collections import defaultdict
import align_recension as A
import dropped_tails as D

A.FILTER_HINDI_PARA = True
KANDA = A.KANDA
NAME2NUM = {nm.split()[0]: kn for kn, (pp, nm) in KANDA.items()}
THRESH = 0.50


def ratio(a, b):
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def load_kanda_verses():
    data = json.load(open('data.json', encoding='utf-8'))
    raw = defaultdict(lambda: defaultdict(list))
    for r in data:
        nm = r.get('kanda', '')
        if nm.endswith('Kanda'):
            raw[nm][int(r['sarga'])].append((int(r['shloka']), r.get('shloka_text', '')))
    out = {}
    for nm, sargas in raw.items():
        short, knum = nm.split()[0], NAME2NUM[nm.split()[0]]
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


def main():
    KV = load_kanda_verses()
    cands = []
    for kn in range(1, 8):
        k = D.run_kanda(kn)
        short = k['name'].split()[0]
        for r in k['results']:
            dj_sarga = r['sarga']
            gp_sarga = r.get('gp_sarga', dj_sarga)
            for m in r.get('mid_missing', []):
                q = A.normalize(m['text'])
                own = KV[short]['by_sarga'].get(dj_sarga, [])
                own_r, own_sh = max(((ratio(q, nt), sh) for sh, nt in own),
                                    default=(0.0, None))
                kb_r, kb_loc = 0.0, None
                for (ss, sh, nt) in KV[short]['flat']:
                    rr = ratio(q, nt)
                    if rr > kb_r:
                        kb_r, kb_loc = rr, (ss, sh)
                cands.append({
                    'kanda': short, 'gp_sarga': gp_sarga, 'gp': m['gp'],
                    'dj_sarga': dj_sarga, 'words': m['words'],
                    'own_r': round(own_r, 3), 'own_sh': own_sh,
                    'kanda_r': round(kb_r, 3), 'kanda_loc': kb_loc,
                    'present': kb_r > THRESH})
    write_report(cands)

    present = [c for c in cands if c['present']]
    print("=" * 56)
    print(f"mid-sarga candidates (content-paired): {len(cands)}")
    print(f"surviving (absent everywhere <= {THRESH}): {len(cands) - len(present)}")
    print(f"resolved to a real dj verse (> {THRESH}): {len(present)}")
    for c in sorted(present, key=lambda x: -x['kanda_r']):
        loc = c['kanda_loc']
        print(f"   GP {c['kanda']} {c['gp_sarga']}.{c['gp']} -> dj {loc[0]}.{loc[1]} "
              f"({c['kanda_r']})")


def write_report(cands):
    present = [c for c in cands if c['present']]
    survivors = [c for c in cands if not c['present']]
    L = ['# Mid-sarga gap check v3 — content-paired sargas\n']
    L.append("Candidates come from `dropped_tails.run_kanda`, which pairs Gita "
             "Press sargas to data.json sargas **by content** (trigram-Jaccard + "
             "monotonic DP), not by number. Each candidate's exact GP verse text is "
             "carried from detection and searched against its paired data.json "
             "sarga and its whole kanda (`align_recension.normalize`, "
             "`autojunk=False`). Candidates are labelled **GP sarga.verse → paired "
             "dj sarga** so there is no number/content ambiguity. Read-only.\n")

    L.append("## 1. Summary\n")
    L.append(f"- mid-sarga candidates: **{len(cands)}**")
    L.append(f"- surviving genuine gaps (absent everywhere, best ≤ {THRESH}): "
             f"**{len(survivors)}**")
    L.append(f"- resolved to a real dj verse elsewhere (best > {THRESH}): "
             f"**{len(present)}** (§3)")
    by_k = defaultdict(lambda: [0, 0])
    for c in cands:
        by_k[c['kanda']][0 if c['present'] else 1] += 1
    L.append("- by kanda (resolved / surviving): " +
             ", ".join(f"{k} {v[0]}/{v[1]}" for k, v in by_k.items()))
    L.append("")

    L.append("## 2. Surviving mid-sarga gap candidates\n")
    L.append("| kanda | GP sarga.verse | paired dj sarga | opening words | best in dj sarga | best in kanda (at) |")
    L.append("|---|---|---|---|---|---|")
    for c in survivors:
        loc = c['kanda_loc']
        locs = f"{loc[0]}.{loc[1]}" if loc else "—"
        L.append(f"| {c['kanda']} | {c['gp_sarga']}.{c['gp']} | {c['dj_sarga']} | "
                 f"{c['words']} | {c['own_r']} (v{c['own_sh']}) | {c['kanda_r']} ({locs}) |")
    L.append("")

    L.append("## 3. Resolved by correct pairing — candidate actually sits at a real dj verse\n")
    L.append("These score > %.2f somewhere in the kanda; inserting them would "
             "duplicate existing content. Where the GP source sarga pairs to a "
             "different-numbered dj sarga, the match location reflects the "
             "recension offset/boundary shift.\n" % THRESH)
    L.append("| kanda | GP sarga.verse | paired dj sarga | opening words | actually sits at dj | score |")
    L.append("|---|---|---|---|---|---|")
    for c in sorted(present, key=lambda x: -x['kanda_r']):
        loc = c['kanda_loc']
        L.append(f"| {c['kanda']} | {c['gp_sarga']}.{c['gp']} | {c['dj_sarga']} | "
                 f"{c['words']} | **{loc[0]}.{loc[1]}** | {c['kanda_r']} |")
    L.append("")
    open('mid_sarga_gaps_v3.md', 'w', encoding='utf-8').write('\n'.join(L))
    print("Wrote mid_sarga_gaps_v3.md")


if __name__ == '__main__':
    main()
