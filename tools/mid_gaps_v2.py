#!/usr/bin/env python3
"""
mid_gaps_v2.py — Re-run the mid-sarga gap check with the Hindi-paragraph filter
(align_recension.FILTER_HINDI_PARA) and emit an auditable mid_sarga_gaps_v2.md.

Compares the candidate list with the filter OFF (reproduces the v1 report's 50)
against the filter ON, so every dropped candidate is explained by which test
(lexical hindi_score, or the structural no-danda/long-line test) caught it.
Read-only.
"""
import re, importlib
from collections import defaultdict
import parse_hindi_v4 as P
import align_recension as A
import dropped_tails as D

KANDA = A.KANDA


def mid_candidates():
    """{(kanda_name, sarga): [ {gp,words,best}, ... ]} for the current filter state."""
    out = {}
    for kn in range(1, 8):
        k = D.run_kanda(kn)
        for r in k['results']:
            for m in r.get('mid_missing', []):
                out.setdefault((k['name'], r['sarga']), []).append(m)
    return out


def key(name, sarga, m):
    return (name, sarga, m['gp'])


def find_block(prefix, sarga, gp_label):
    """Return the .txt block(s) whose stamp matches gp_label in a sarga."""
    seg, _, _, _ = D.gather_segments(prefix)
    if sarga not in seg:
        return []
    text = P.blank_footnotes(P._strip_colophon(seg[sarga]))
    hits = []
    for b in (x.strip() for x in re.split(r'\n\s*\n', text) if x.strip()):
        if P.is_skip(b):
            continue
        m = P.get_marker(b)
        has = (m and m[0] == 'S') or bool(P.STAMP_RE.search(b))
        if not has:
            continue
        sf, sl = A.gp_verse_num(b)
        lbl = str(sf) if sf == sl else f"{sf}-{sl}"
        if lbl == str(gp_label):
            hits.append(b)
    return hits


def corpus_disagreements():
    """Every stamped block the structural test rules Hindi while hindi_score==0
    (lexical/structural disagreement) — the audit trail for the filter."""
    rows = []
    for kn in range(1, 8):
        prefix, name = KANDA[kn]
        seg, _, _, _ = D.gather_segments(prefix)
        for s, segtext in sorted(seg.items()):
            text = P.blank_footnotes(P._strip_colophon(segtext))
            for b in (x.strip() for x in re.split(r'\n\s*\n', text) if x.strip()):
                if P.is_skip(b):
                    continue
                verdict, reason = A.classify_block(b)
                if verdict == 'hindi' and 'DISAGREEMENT' in reason:
                    lines = [l for l in b.split('\n') if l.strip()]
                    rows.append({'kanda': name.split()[0], 'sarga': s,
                                 'first': lines[0][:60],
                                 'maxlen': max(len(l) for l in lines)})
    return rows


def main():
    A.FILTER_HINDI_PARA = False
    before = mid_candidates()
    A.FILTER_HINDI_PARA = True
    after = mid_candidates()

    before_keys, after_keys = {}, {}
    for d, tag in [(before, before_keys), (after, after_keys)]:
        for (name, sarga), ms in d.items():
            for m in ms:
                tag[key(name, sarga, m)] = (name, sarga, m)

    survivors = sorted(after_keys)
    dropped = sorted(set(before_keys) - set(after_keys))
    appeared = sorted(set(after_keys) - set(before_keys))

    # classify each dropped candidate by which test caught it
    drop_reasons = []
    for kk in dropped:
        name, sarga, gp = kk
        prefix = NAME2PREFIX[name.split()[0]]
        blocks = find_block(prefix, sarga, gp)
        reason = 'removed (alignment shifted after filter)'
        for b in blocks:
            v, rsn = A.classify_block(b)
            if v == 'hindi':
                reason = rsn
                break
        _, _, m = before_keys[kk]
        drop_reasons.append((name, sarga, gp, m['words'], m.get('best'), reason))

    disagreements = corpus_disagreements()
    write_report(before_keys, after_keys, survivors, dropped, appeared,
                 drop_reasons, disagreements, after)

    print("=" * 56)
    print(f"v1 candidates (filter off): {len(before_keys)}")
    print(f"v2 survivors  (filter on):  {len(survivors)}")
    print(f"dropped by filter:          {len(dropped)}")
    print(f"newly appeared:             {len(appeared)}")
    from collections import Counter
    phantoms = [d for d in drop_reasons if d[5].startswith(('lexical', 'structural'))]
    print(f"  of which Hindi phantoms:  {len(phantoms)}")
    print(f"    lexical / structural:   "
          f"{sum(1 for d in phantoms if d[5].startswith('lexical'))} / "
          f"{sum(1 for d in phantoms if d[5].startswith('structural'))}")
    print(f"dropped by kanda: {dict(Counter(d[0].split()[0] for d in drop_reasons))}")
    print(f"structural disagreements corpus-wide: {len(disagreements)}")


NAME2PREFIX = {nm.split()[0]: pp for pp, nm in KANDA.values()}


def write_report(before_keys, after_keys, survivors, dropped, appeared,
                 drop_reasons, disagreements, after):
    L = ['# Mid-sarga gap check v2 — with Hindi-paragraph filter\n']
    L.append("The `.txt` reader now rejects a stamped block as a Gita Press verse "
             "unless it passes **both** tests: lexical (`parse_hindi_v4.hindi_score()"
             "` == 0) **and** structural (a danda `।`/`|` present, or short metrical "
             "lines — not a long paragraph running into `॥N॥`). A block ruled Hindi "
             "on the structural test alone (score 0) is a lexical/structural "
             "disagreement and is listed in §3 for a human look. Read-only.\n")

    L.append("## 1. Summary\n")
    L.append(f"- v1 mid-sarga candidates (filter off): **{len(before_keys)}**")
    L.append(f"- v2 survivors (filter on): **{len(survivors)}**")
    L.append(f"- dropped by the filter: **{len(dropped)}**")
    if appeared:
        L.append(f"- newly appeared after filtering: {len(appeared)} "
                 f"{[f'{a[0]} {a[1]}.{a[2]}' for a in appeared]}")
    by_k = defaultdict(int)
    for d in dropped:
        by_k[d[0]] += 1
    L.append(f"- dropped by kanda: {dict(by_k)}")
    L.append("")

    L.append("## 2. Candidates dropped by the filter (audit)\n")
    L.append("| kanda | sarga | GP verse | opening words | v1 best | caught by |")
    L.append("|---|---|---|---|---|---|")
    for name, sarga, gp, words, best, reason in drop_reasons:
        short = ('lexical (hindi_score>0)' if reason.startswith('lexical')
                 else 'structural (no danda + long line; score 0)'
                 if reason.startswith('structural')
                 else reason)
        L.append(f"| {name} | {sarga} | {gp} | {words} | {best} | {short} |")
    L.append("")

    L.append("## 3. Surviving mid-sarga gap candidates (genuine absences)\n")
    L.append("| kanda | sarga | GP verse | opening words | best match |")
    L.append("|---|---|---|---|---|")
    for (name, sarga) in sorted(after, key=lambda x: (list(NAME2PREFIX).index(x[0].split()[0]) if x[0].split()[0] in NAME2PREFIX else 9, x[1])):
        for m in after[(name, sarga)]:
            L.append(f"| {name.split()[0]} | {sarga} | {m['gp']} | {m['words']} | {m.get('best')} |")
    L.append("")

    L.append("## 4. Structural disagreements corpus-wide (needs a human look)\n")
    L.append("Stamped blocks the structural test ruled Hindi while `hindi_score()`"
             " scored 0 (its glued-postposition / name-list blind spot). Most are "
             "Hindi paragraph phantoms; a few long compound Sanskrit lines without "
             "an internal danda can appear here and should be rescued by eye.\n")
    L.append(f"Total: **{len(disagreements)}** blocks.\n")
    L.append("| kanda | sarga | max line | opening words |")
    L.append("|---|---|---|---|")
    for r in disagreements:
        L.append(f"| {r['kanda']} | {r['sarga']} | {r['maxlen']} | {r['first']} |")
    L.append("")

    open('mid_sarga_gaps_v2.md', 'w', encoding='utf-8').write('\n'.join(L))
    print("Wrote mid_sarga_gaps_v2.md")


if __name__ == '__main__':
    main()
