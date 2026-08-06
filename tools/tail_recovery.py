#!/usr/bin/env python3
"""
tail_recovery.py — For every DJ_SHORT verse (data.json missing a trailing verse
its paired Gita Press sarga has), pull the full Sanskrit from the .txt with line
breaks preserved and emit:
  - tail_recovery_sanskrit.md : grouped kanda -> sarga, each verse's data.json
    sarga, the append verse number, full Sanskrit, line count, contiguity flag.
  - tail_recovery.json : patch keyed kanda / sarga / shloka for an applier.

Read-only on data.json and the .txt files. Uses the content-based sarga pairing
from dropped_tails.run_kanda (so the GP verse comes from the correctly paired GP
sarga, not the same-numbered one).
"""
import json
from collections import defaultdict
import align_recension as A
import dropped_tails as D

A.FILTER_HINDI_PARA = True
KANDA = A.KANDA
KANDA_ORDER = [KANDA[k][1].split()[0] for k in range(1, 8)]


def parse_label(lbl):
    if '-' in lbl:
        a, b = lbl.split('-')
        return int(a), int(b)
    return int(lbl), int(lbl)


def dj_last_by_sarga():
    data = json.load(open('data.json', encoding='utf-8'))
    mx = defaultdict(lambda: defaultdict(int))
    for r in data:
        nm = r.get('kanda', '')
        if nm.endswith('Kanda'):
            short, s, sh = nm.split()[0], int(r['sarga']), int(r['shloka'])
            if sh > mx[short][s]:
                mx[short][s] = sh
    return mx


def main():
    dj_last = dj_last_by_sarga()
    entries = []
    for kn in range(1, 8):
        k = D.run_kanda(kn)
        short = k['name'].split()[0]
        for r in k['results']:
            if r['klass'] != 'DJ_SHORT':
                continue
            djs = r['sarga']
            gps = r.get('gp_sarga', djs)
            last = dj_last[short].get(djs, 0)
            next_ap = last + 1        # next contiguous data.json shloka to append at
            exp_gp = last + 1         # GP number we'd expect if numbering agreed
            verses = []
            for m in r['missing']:
                first, lastnum = parse_label(m['gp'])
                ngp = lastnum - first + 1
                lines = [l.rstrip() for l in m['text'].split('\n') if l.strip()]
                append_shlokas = list(range(next_ap, next_ap + ngp))
                contiguous = (first == exp_gp)
                overlap = (first <= last)      # GP number within dj's existing range
                multiverse = (ngp > 1) or (len(lines) > 3)
                verses.append({
                    'gp_label': m['gp'], 'gp_first': first, 'gp_last': lastnum,
                    'gp_span': ngp, 'expected_gp': exp_gp,
                    'append_shlokas': append_shlokas,
                    'contiguous': contiguous, 'overlap': overlap,
                    'multiverse': multiverse,
                    'line_count': len(lines), 'lines': lines,
                    'text': '\n'.join(lines), 'words': m['words'], 'best': m['best'],
                })
                next_ap += ngp
                exp_gp = lastnum + 1
            entries.append({
                'kanda': short, 'kanda_full': k['name'], 'kanda_num': kn,
                'dj_sarga': djs, 'gp_sarga': gps, 'dj_last': last,
                'verses': verses,
            })
    entries.sort(key=lambda e: (KANDA_ORDER.index(e['kanda']), e['dj_sarga']))
    write_md(entries)
    write_json(entries)

    nv = sum(len(e['verses']) for e in entries)
    overlap = [(e, v) for e in entries for v in e['verses'] if v['overlap']]
    offset = [(e, v) for e in entries for v in e['verses']
              if not v['contiguous'] and not v['overlap']]
    oddlc = [(e, v) for e in entries for v in e['verses'] if v['line_count'] not in (2, 3)]
    print("=" * 56)
    print(f"DJ_SHORT sargas: {len(entries)}   verses: {nv}")
    print(f"OVERLAP (GP number <= dj_last — suspect, may not be a real drop): {len(overlap)}")
    for e, v in overlap:
        print(f"   {e['kanda']} sarga {e['dj_sarga']}: dj_last={e['dj_last']} "
              f"but GP verse {v['gp_label']}")
    print(f"numbering offset (GP number != expected, no overlap): {len(offset)}")
    print(f"multi-verse / line-count not 2-3: {len(oddlc)}")
    for e, v in oddlc:
        print(f"   {e['kanda']} {e['dj_sarga']}.{v['gp_label']}: {v['line_count']} lines "
              f"(GP span {v['gp_span']})")


def write_md(entries):
    L = ['# Tail recovery — Sanskrit for DJ_SHORT verses\n']
    L.append("Full Gita Press Sanskrit (from ramcharit.in/ .txt, content-paired "
             "sarga) for every trailing verse data.json is missing. Line breaks "
             "preserved. Append numbers are **sequential from data.json's current "
             "last verse** (the correct data.json shloka numbers). The Gita Press "
             "number is shown alongside; flags:\n")
    L.append("- **⚠ offset** — GP number ≠ the expected sequential number "
             "(recensions number differently before the tail; append number still valid).")
    L.append("- **⚠ OVERLAP** — GP number ≤ data.json's last verse; the verse may "
             "not be a genuine tail drop (boundary shift / mis-pairing). Verify.")
    L.append("- **⚠ multi-verse** — the block holds more than one verse (GP range "
             "or >3 lines); split before applying.\n")
    nv = sum(len(e['verses']) for e in entries)
    nov = sum(1 for e in entries for v in e['verses'] if v['overlap'])
    noff = sum(1 for e in entries for v in e['verses']
               if not v['contiguous'] and not v['overlap'])
    nmv = sum(1 for e in entries for v in e['verses'] if v['multiverse'])
    L.append(f"**{len(entries)} sargas, {nv} verses; {nov} overlap, {noff} offset, "
             f"{nmv} multi-verse.**\n")
    cur_k = None
    for e in entries:
        if e['kanda'] != cur_k:
            cur_k = e['kanda']
            L.append(f"\n## {e['kanda_full']}\n")
        L.append(f"### Sarga {e['dj_sarga']} — append after verse {e['dj_last']}"
                 + (f"  *(Gita Press source sarga {e['gp_sarga']})*"
                    if e['gp_sarga'] != e['dj_sarga'] else "") + "\n")
        for v in e['verses']:
            aps = v['append_shlokas']
            appn = str(aps[0]) if len(aps) == 1 else f"{aps[0]}–{aps[-1]}"
            fl = []
            if v['overlap']:
                fl.append("⚠ **OVERLAP** (GP " + v['gp_label'] +
                          f" ≤ dj last {e['dj_last']})")
            elif not v['contiguous']:
                fl.append(f"⚠ offset (GP {v['gp_label']}, expected {v['expected_gp']})")
            if v['multiverse']:
                fl.append("⚠ multi-verse — split")
            flag = ("  " + "; ".join(fl)) if fl else ""
            L.append(f"- **append as verse {appn}** (GP {v['gp_label']}) · "
                     f"{v['line_count']} lines{flag}")
            L.append("  ```")
            for ln in v['lines']:
                L.append("  " + ln)
            L.append("  ```")
        L.append("")
    open('tail_recovery_sanskrit.md', 'w', encoding='utf-8').write('\n'.join(L))
    print("Wrote tail_recovery_sanskrit.md")


def write_json(entries):
    """Patch form: kanda -> sarga -> shloka -> {shloka_text, line_count, ...}."""
    patch = {}
    for e in entries:
        ks = patch.setdefault(e['kanda_full'], {})
        ss = ks.setdefault(str(e['dj_sarga']), {})
        for v in e['verses']:
            aps = v['append_shlokas']
            for sh in aps:
                ss[str(sh)] = {
                    'shloka_text': v['text'],
                    'line_count': v['line_count'],
                    'gp_label': v['gp_label'],
                    'gp_sarga': e['gp_sarga'],
                    'appended_after': e['dj_last'],
                    'contiguous': v['contiguous'],
                    'overlap': v['overlap'],
                    'multiverse': v['multiverse'],
                    # when a GP block spans >1 verse, the same block text is placed
                    # on each shloka it covers and must be split by hand
                    'block_spans': aps if len(aps) > 1 else None,
                }
    meta = {
        '_note': 'Recovered trailing Sanskrit for DJ_SHORT verses; append to '
                 'data.json at the given (sequential) shloka numbers. shloka_text '
                 'has newline-separated lines. VERIFY before applying any entry '
                 'with overlap=true (may not be a real drop) or multiverse=true '
                 '(block holds >1 verse; split it).',
        'kandas': patch,
    }
    with open('tail_recovery.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("Wrote tail_recovery.json")


if __name__ == '__main__':
    main()
