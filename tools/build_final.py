#!/usr/bin/env python3
"""
build_final.py — Produce tail_recovery_final.json from tail_recovery.json:
  * Re-extract Ayodhya 50 and Sundara 67 from the corrected .txt, cutting each
    verse as the lines up to and including its own ॥N॥ stamp (one verse/entry).
  * Drop Kishkindha 57 slots 21 & 24 (GP 14, 17 — verified already in data.json)
    and renumber the rest contiguously.
  * Validate every entry, then write the file and a summary.
Read-only on data.json and the .txt files.
"""
import json, re
from difflib import SequenceMatcher
from collections import defaultdict
import parse_hindi_v4 as P
import align_recension as A

A.FILTER_HINDI_PARA = True
DEV = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6',
       '७': '7', '८': '8', '९': '9'}
STAMP_EOL = re.compile(r'॥\s*([०-९]+)\s*॥\s*$')


def deva(s):
    return int(''.join(DEV[c] for c in s if c in DEV))


def seg_of(fname, sarga):
    for s, seg in P.split_segments(open('ramcharitdotin/' + fname, encoding='utf-8').read()):
        if float(s).is_integer() and int(s) == sarga:
            return seg
    return None


def extract_verses(seg):
    """Collect Sanskrit lines across blocks (skipping Hindi/skip blocks) and cut
    into verses each ending at its own ॥N॥ stamp."""
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
        cur.append(ln)
        m = STAMP_EOL.search(ln)
        if m:
            verses.append((deva(m.group(1)), '\n'.join(cur)))
            cur = []
    trailing = '\n'.join(cur) if cur else None
    return {n: t for n, t in verses}, trailing


def dj_last_map():
    data = json.load(open('data.json', encoding='utf-8'))
    mx = defaultdict(lambda: defaultdict(int))
    for r in data:
        nm = r.get('kanda', '')
        if nm.endswith('Kanda'):
            mx[nm][int(r['sarga'])] = max(mx[nm][int(r['sarga'])], int(r['shloka']))
    return mx


def entry(text, gp_num, gp_sarga, appended_after):
    lines = [l for l in text.split('\n') if l.strip()]
    return {
        'shloka_text': '\n'.join(lines),
        'line_count': len(lines),
        'gp_label': str(gp_num),
        'gp_sarga': gp_sarga,
        'appended_after': appended_after,
        'contiguous': True, 'overlap': False, 'multiverse': False,
        'block_spans': None,
    }


def main():
    patch = json.load(open('tail_recovery.json', encoding='utf-8'))
    kandas = patch['kandas']
    djlast = dj_last_map()
    summary = {'changes': [], 'human': []}

    # ---------- Re-extract the affected sargas from the corrected .txt ----------
    # (kanda_full, sarga, file, gp_min-of-tail, note). The two the user named
    # (Ayodhya 50, Sundara 67) plus Ayodhya 35 & Yuddha 17, which held the same
    # multi-verse-in-one-entry defect and would fail the whole-file validation.
    RECUT = [
        ('Ayodhya Kanda', 35, 'aks5-38.txt', 36,
         'boundary clean (dj v35 = GP v35)'),
        ('Ayodhya Kanda', 50, 'aks39-76.txt', 28,
         'corrected source now stamps verse 39; no unstamped verse remains'),
        ('Sundara Kanda', 67, 'sks50-68.txt', 18,
         'data.json v16 combines GP 16+17, so the tail starts at GP 18; '
         'duplicate-text pair eliminated'),
        ('Yuddha Kanda', 17, 'yks1-39.txt', 65,
         'boundary clean (dj v64 = GP v64)'),
    ]
    recut_totals = {}
    for kf, sarga, fname, gp_min, note in RECUT:
        last = djlast[kf][sarga]
        verses, trail = extract_verses(seg_of(fname, sarga))
        tail = sorted(n for n in verses if n >= gp_min)
        new = {}
        slot = last + 1
        for gp in tail:
            new[str(slot)] = entry(verses[gp], gp, sarga, last)
            slot += 1
        old = len(kandas[kf].get(str(sarga), {}))
        kandas[kf][str(sarga)] = new
        recut_totals[(kf.split()[0], sarga)] = len(new)
        summary['changes'].append(
            f"{kf.split()[0]} {sarga} re-cut: {old} → {len(new)} verses "
            f"(slots {last+1}–{slot-1}, GP {tail[0]}–{tail[-1]}) — {note}.")
        if trail:
            summary['human'].append(
                f"{kf.split()[0]} {sarga}: trailing Sanskrit with no stamp "
                f"'{trail[:40]}' — check.")

    # ---------- Kishkindha 57: drop slots 21 & 24, renumber ----------
    k57 = kandas['Kishkindha Kanda']['57']
    k_last = djlast['Kishkindha Kanda'][57]           # 19
    keep = [(int(sh), rec) for sh, rec in sorted(k57.items(), key=lambda x: int(x[0]))
            if int(sh) not in (21, 24)]
    new_k = {}
    slot = k_last + 1
    dropped_gp = [k57[str(s)]['gp_label'] for s in (21, 24)]
    for _oldslot, rec in keep:
        rec = dict(rec)
        rec['appended_after'] = k_last
        new_k[str(slot)] = rec
        slot += 1
    kandas['Kishkindha Kanda']['57'] = new_k
    summary['changes'].append(f"Kishkindha 57: dropped slots 21 & 24 (GP {dropped_gp[0]},"
                              f" {dropped_gp[1]} — present in data.json at 0.76/0.71); "
                              f"{len(keep)} verses remain, renumbered {k_last+1}–{slot-1}.")
    summary['human'].append("Kishkindha 57's remaining 5 verses (GP 13,15,16,18,19) still "
                            "score 0.41–0.45 in-kanda (boundary-shift sarga 56→57) — "
                            "verify before applying.")

    # ---------- validate whole file ----------
    problems = []
    total = 0
    per_kanda = defaultdict(int)
    for kf, sargas in kandas.items():
        short = kf.split()[0]
        for s, shl in sargas.items():
            last = djlast[kf].get(int(s), 0)
            slots = sorted(int(x) for x in shl)
            # contiguity from dj_last+1
            if slots != list(range(last + 1, last + 1 + len(slots))):
                problems.append(f"{short} {s}: slots {slots} not unbroken from {last+1}")
            texts = defaultdict(list)
            for sh, rec in shl.items():
                total += 1
                per_kanda[short] += 1
                lines = [l for l in rec['shloka_text'].split('\n') if l.strip()]
                if not lines or not STAMP_EOL.search(lines[-1]):
                    problems.append(f"{short} {s}.{sh}: last line has no ॥N॥ stamp "
                                    f"('{lines[-1][-20:] if lines else ''}')")
                nstamps = sum(1 for l in lines if STAMP_EOL.search(l))
                if nstamps != 1:
                    problems.append(f"{short} {s}.{sh}: holds {nstamps} verses (want 1)")
                texts[rec['shloka_text']].append(sh)
            for t, shs in texts.items():
                if len(shs) > 1:
                    problems.append(f"{short} {s}: identical text in slots {shs}")

    with open('tail_recovery_final.json', 'w', encoding='utf-8') as f:
        json.dump({'_note': patch.get('_note', ''), 'kandas': kandas}, f,
                  ensure_ascii=False, indent=2)

    print("Wrote tail_recovery_final.json")
    print("=" * 56)
    print("final verses per kanda:", dict(per_kanda))
    print("final total:", total)
    print("re-cut sargas:", {f"{k[0]} {k[1]}": v for k, v in recut_totals.items()},
          "| Kishkindha 57:", len(new_k))
    print("\nCHANGES:")
    for c in summary['changes']:
        print("  -", c)
    print("\nNEEDS HUMAN DECISION:")
    for h in summary['human']:
        print("  -", h)
    print("\nVALIDATION:", "ALL PASS" if not problems else f"{len(problems)} PROBLEMS")
    for p in problems:
        print("  !", p)


if __name__ == '__main__':
    main()
