#!/usr/bin/env python3
"""
Repair malformed word-by-word gloss pairs in data_1.json … data_7.json.

Background
----------
The app splits the `translation` field on commas and expects each fragment to be
"<devanagari> <english>". Fragments that fail are dropped silently. A corpus scan
found 6,396 such fragments. The parseWordTable change in index.html rescued 1,386
of them without touching data. This script addresses the next 2,791, which are
repairable mechanically because the text is all present — only the comma
boundaries are wrong.

Three rules, in the order applied within each row:

  JOIN   An orphan fragment with no Devanagari at all is the tail of the previous
         gloss, severed by a comma inside its English. Rejoin it.
           "देवा: च celestial beings" + "devatas"
             -> "देवा: च celestial beings devatas"

  SPLIT  Two glosses run together with no comma between them. Split them.
           "सहित: accompanied सूतम् charioteer"
             -> "सहित: accompanied" , "सूतम् charioteer"

  DROP   Empty fragment from a doubled or trailing comma. Remove it.

No text is ever discarded except genuinely empty fragments: JOIN and SPLIT only
move comma boundaries. A row is rewritten only if every rule applied to it
produces fragments that the app will parse; otherwise the row is left alone and
listed in the report as skipped.

Usage
-----
  python3 repair_gloss_pairs.py                 # report only, writes no data
  python3 repair_gloss_pairs.py --apply         # applies, backs up to .bakrepair

Outputs repair_report.md (human) and repair_plan.json (machine) in both modes.
"""

import json
import re
import shutil
import sys
from collections import Counter, defaultdict

KANDA_FILES = {
    1: "data_1.json", 2: "data_2.json", 3: "data_3.json", 4: "data_4.json",
    5: "data_5.json", 6: "data_6.json", 7: "data_7.json",
}

# Mirrors parseWordTable() in index.html after the parser change.
DEVA_CLASS = r'[\u0900-\u097F\u0964\u0965:*()\[\]"\u201c\u201d\'\u2018\u2019\s-]'
PAIR = re.compile(r'^(' + DEVA_CLASS + r'+?)\s+([a-zA-Z0-9"\u201c\'\u2018(\[].*)$')
STRIP = re.compile(r'[:*()\[\]"\u201c\u201d\'\u2018\u2019]')
ZEROWIDTH = re.compile('[\ufeff\u200b-\u200d]')
HAS_DEVA = re.compile(r'[\u0900-\u097F]')
HAS_LATIN = re.compile(r'[a-zA-Z]')


def parses(fragment):
    """True if the app would render this fragment at all (permissive)."""
    t = ZEROWIDTH.sub('', fragment).strip()
    if not t or len(t) > 150:
        return False
    m = PAIR.match(t)
    if not m:
        return False
    word = STRIP.sub('', m.group(1)).strip()
    meaning = m.group(2).strip()
    return bool(word) and bool(meaning) and 1 <= len(word) < 60


def well_formed(fragment):
    """True if the fragment renders AND is a single clean pair.

    A fragment such as "सहित: accompanied सूतम् charioteer" passes parses()
    because the app is permissive, but it puts Sanskrit into the English
    column: two glosses run together. Repair targets these as well as the
    fragments that fail outright.
    """
    if not parses(fragment):
        return False
    m = PAIR.match(ZEROWIDTH.sub('', fragment).strip())
    return not HAS_DEVA.search(m.group(2))


def repair_row(raw):
    """Return (new_string, [rules_used]) or (None, reason) if not repairable."""
    parts = [ZEROWIDTH.sub('', p).strip() for p in re.split(r',\s*', raw)]
    out, used, i = [], [], 0

    while i < len(parts):
        p = parts[i]

        if p == '':
            used.append('DROP')
            i += 1
            continue

        if well_formed(p):
            out.append(p)
            i += 1
            continue

        # JOIN: no Devanagari anywhere -> tail of the previous gloss
        if not HAS_DEVA.search(p):
            if out and parses(out[-1] + ' ' + p):
                out[-1] = out[-1] + ' ' + p
                used.append('JOIN')
                i += 1
                continue
            return None, 'orphan cannot be rejoined'

        # SPLIT: two or more glosses run together
        if HAS_LATIN.search(p):
            segs = re.split(r'(?<=[^\u0900-\u097F])\s+(?=[\u0900-\u097F])', p)
            if len(segs) > 1 and all(well_formed(s) for s in segs):
                out.extend(segs)
                used.append('SPLIT' if len(segs) == 2 else 'SPLIT3+')
                i += 1
                continue
            return None, 'run-together cannot be split cleanly'

        return None, 'fragment has no English'

    if not out:
        return None, 'nothing left after repair'
    if not all(well_formed(p) for p in out):
        return None, 'result still malformed'
    return ', '.join(out), used


def main(apply_changes):
    plan = []
    stats = Counter()
    skipped = defaultdict(Counter)
    samples = defaultdict(list)

    for kanda, path in KANDA_FILES.items():
        try:
            data = json.load(open(path, encoding='utf-8'))
        except FileNotFoundError:
            print(f'skipping {path}: not found')
            continue

        for row in data:
            text = (row.get('shloka_text') or '').strip()
            if text.startswith('इत्यार्षे'):
                continue
            raw = (row.get('translation') or '').strip()
            if not raw:
                continue

            parts = [p.strip() for p in re.split(r',\s*', raw)]
            broken = [p for p in parts if not well_formed(p)]
            if not broken:
                continue

            stats['rows with at least one broken fragment'] += 1
            stats['broken fragments seen'] += len(broken)

            new, info = repair_row(raw)
            if new is None:
                stats['rows skipped'] += 1
                skipped[kanda][info] += 1
                if len(samples['skipped']) < 8:
                    samples['skipped'].append(
                        (kanda, row['sarga'], row['shloka'],
                         'REASON: ' + info, 'fragment: ' + broken[0][:80]))
                continue

            gained = len([p for p in re.split(r',\s*', new) if well_formed(p)]) - \
                     len([p for p in parts if well_formed(p)])
            stats['rows repaired'] += 1
            stats['well-formed pairs gained'] += max(gained, 0)
            for r in info:
                stats[f'rule {r}'] += 1
            plan.append({
                'kanda': kanda, 'sarga': row['sarga'], 'shloka': str(row['shloka']),
                'rules': info, 'before': raw, 'after': new,
            })
            for rule in sorted(set(info)):
                if len(samples[rule]) < 3:
                    samples[rule].append(
                        (kanda, row['sarga'], row['shloka'], raw[:100], new[:100]))

    # ---------- reports ----------
    with open('repair_plan.json', 'w', encoding='utf-8') as fh:
        json.dump(plan, fh, ensure_ascii=False, indent=1)

    lines = ['# Gloss-pair repair plan', '']
    for k in ('rows with at least one broken fragment', 'broken fragments seen',
              'rows repaired', 'rows skipped', 'well-formed pairs gained'):
        lines.append(f'- {k}: {stats[k]}')
    lines.append('')
    lines.append('## Rules applied')
    for k, v in sorted(stats.items()):
        if k.startswith('rule '):
            lines.append(f'- {k[5:]}: {v}')
    lines.append('')
    lines.append('## Rows skipped, by reason')
    for kanda in sorted(skipped):
        for reason, n in skipped[kanda].most_common():
            lines.append(f'- kanda {kanda}: {reason} — {n}')
    lines.append('')
    lines.append('## Samples')
    for tag, rows_ in samples.items():
        lines.append(f'### {tag}')
        for s in rows_:
            lines.append(f'- `{s[0]}.{s[1]}.{s[2]}`')
            lines.append(f'  - before: {s[3]}')
            lines.append(f'  - after : {s[4]}')
    open('repair_report.md', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

    print('\n'.join(lines[:12]))
    print('\nWrote repair_report.md and repair_plan.json')

    if not apply_changes:
        print('\nREPORT ONLY — no data written. Re-run with --apply to write.')
        return

    # ---------- apply ----------
    by_kanda = defaultdict(dict)
    for e in plan:
        by_kanda[e['kanda']][(e['sarga'], e['shloka'])] = e['after']

    for kanda, edits in sorted(by_kanda.items()):
        path = KANDA_FILES[kanda]
        shutil.copyfile(path, path + '.bakrepair')
        data = json.load(open(path, encoding='utf-8'))
        n = 0
        for row in data:
            key = (row.get('sarga'), str(row.get('shloka')))
            if key in edits:
                row['translation'] = edits[key]
                n += 1
        json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'{path}: {n} rows rewritten (backup at {path}.bakrepair)')


if __name__ == '__main__':
    main('--apply' in sys.argv)
