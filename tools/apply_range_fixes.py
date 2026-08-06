#!/usr/bin/env python3
"""Apply category A (trim inflated range stamps) and B (split merged blocks with
a blank line) to ramcharitdotin/*.txt. Category C (malformed Sanskrit stamps) is
held. Re-derives the defect sets from the live files, asserts the expected counts,
then edits per file bottom-to-top so line numbers stay valid. Logs every change.
"""
import re, os
import parse_hindi_v4 as m

DIAG = "/private/tmp/claude-501/-Users-macbookair-02ValmikiRamayana/386bc1b0-07c5-4934-acf1-36c5ae48b606/scratchpad/diag_ranges.py"
exec(open(DIAG).read().split('infl = [')[0])          # provides rows, merged

# 6 review cases held (malformed Sanskrit stamp / ayodhya-2 already fixed by user)
REVIEW = {('ayodhya','2'), ('ayodhya','11'), ('ayodhya','59'),
          ('bala','70'), ('yuddha','121'), ('yuddha','123')}
infl = [r for r in rows if r['kind'] == 'inflated' and (r['kanda'], r['sarga']) not in REVIEW]
assert len(infl) == 31, f"expected 31 inflated, got {len(infl)}"
assert len(merged) == 15, f"expected 15 merged, got {len(merged)}"

# group edits per file: ('A', line, correct_stamp) or ('B', line)
byfile = {}
for r in infl:
    byfile.setdefault(r['file'], []).append(('A', r['line'], r['stamp'], r['correct']))
for r in merged:
    byfile.setdefault(r['file'], []).append(('B', r['line'], r['stamps'][0], None))

log = []
for fn, edits in byfile.items():
    path = os.path.join('ramcharitdotin', fn)
    lines = open(path, encoding='utf-8').read().split('\n')
    # bottom-to-top so edits below don't shift lines above
    for e in sorted(edits, key=lambda e: -e[1]):
        kind, ln, cur, new = e
        idx = ln - 1
        line = lines[idx]
        stamps = list(m.STAMP_RE.finditer(line))
        assert stamps, f"{fn}:{ln} no stamp on line: {line!r}"
        if kind == 'A':
            last = stamps[-1]
            before = line
            lines[idx] = line[:last.start()] + new + line[last.end():]
            log.append(f"A  {fn}:{ln}  {cur}  ->  {new}")
        else:  # B: insert blank line after the Hindi line (block start)
            lines.insert(idx + 1, '')
            log.append(f"B  {fn}:{ln}  split after Hindi stamp {cur!r} (blank line inserted)")
    open(path, 'w', encoding='utf-8').write('\n'.join(lines))

for l in sorted(log):
    print(l)
print(f"\napplied: {sum(1 for l in log if l.startswith('A'))} A-edits, "
      f"{sum(1 for l in log if l.startswith('B'))} B-edits, across {len(byfile)} files")
