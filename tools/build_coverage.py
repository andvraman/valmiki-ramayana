#!/usr/bin/env python3
"""Stream C step 1 — build the Hindi coverage map (READ-ONLY).

For every Hindi paragraph in ramcharitdotin/*.txt, determine which Gita Press
verses it covers (from its terminal stamp / surviving {hN} marker), and emit
hindi_coverage_map.json keyed by kanda -> sarga.

Coverage semantics:
  ॥३०॥            -> verse 30
  ॥ १९-२०॥        -> verses 19 and 20
  ॥ ३० १/२॥       -> verse 30, plus line 1 of verse 31   (forward spill)
  ॥ ३४-३५ १/२॥    -> verses 34, 35, plus line 1 of verse 36
The १/२ ALWAYS means line 1 of the verse after the LAST named one.
"""
import re, glob, os, json, collections
import parse_hindi_v4 as m

CORPUS = 'ramcharitdotin'
OUT = 'hindi_coverage_map.json'

KANDA_NAME = {1:'bala',2:'ayodhya',3:'aranya',4:'kishkindha',
              5:'sundara',6:'yuddha',7:'uttara'}

# Use the parser's own stamp matcher — the corpus mixes danda forms
# (॥२१॥, । २१-२२॥ single-danda-led, and space-led ` २५॥`). Footnotes are blanked
# first, so STAMP_RE's single-danda branch can't catch a citation.
STAMP    = m.STAMP_RE
HALF_RE  = re.compile(r'१\s*/\s*२|1\s*/\s*2|½')
FRAC_RE  = re.compile(r'[०-९0-9]+\s*/\s*[०-९0-9]+')

def is_colophon(block):
    """Sarga-end colophons carry the SARGA number as a stamp; never a verse.
    Mirror _strip_colophon exactly: 'आदिकाव्य'+'सर्ग', or the ADJACENT phrase
    'पूरा हुआ' (m._PURA_HUA_RE). Do NOT test पूरा and हुआ separately — both are
    ordinary words and co-occur in real verses (e.g. bks14 v1)."""
    if m.is_skip(block):
        return True
    if 'आदिकाव्य' in block and 'सर्ग' in block:
        return True
    if m._PURA_HUA_RE.search(block):
        return True
    return False

def parse_stamp(stamp):
    """(named_verses, spill_bool, extra) for one stamp string."""
    half = bool(HALF_RE.search(stamp))
    core = FRAC_RE.sub(' ', stamp).replace('½', ' ')
    nums = [m.deva_to_int(x) for x in re.findall(r'[०-९]+', core)]
    nums = [n for n in nums if n]
    return nums, half

def coverage_for_block(block):
    """Return dict describing a Hindi paragraph's coverage, or None if the block
    carries no usable stamp/marker. Also returns flags for anomalies."""
    stamps = STAMP.findall(block)
    marker = m.get_marker(block)          # ('H',sf,sl) etc., or None
    flags = []

    if stamps:
        per = [parse_stamp(s) for s in stamps]
        named = sorted({v for nums, _ in per for v in nums})
        half = per[-1][1]                 # spill governed by the terminal stamp
        raw = stamps[-1].strip()
        if len(stamps) > 1:
            flags.append('multi-stamp-block')
    elif marker and marker[0] == 'H':
        # marker-only Hindi (no native stamp) — cover the marker span
        named = list(range(marker[1], marker[2] + 1))
        half = False
        raw = None
        flags.append('marker-only')
    else:
        return None

    if not named:
        return None
    first, last = min(named), max(named)
    verses = list(range(first, last + 1))
    if last - first > 6:
        flags.append('wide-span')         # keep full range; just surface it
    spill_verse = last + 1 if half else None
    return {
        'span': [first, last],
        'verses': verses,
        'spill': bool(half),
        'spill_verse': spill_verse,
        'stamp': raw,
        'is_range': len(verses) > 1,
        'flags': flags,
    }

def classify(block):
    """'H' Hindi paragraph, 'S' Sanskrit sloka, 'A' ambiguous."""
    marker = m.get_marker(block)
    if marker and marker[0] == 'H':
        return 'H'
    if marker and marker[0] == 'S':
        return 'S'
    if m.looks_like_sanskrit(block):
        return 'S'
    if m.hindi_score(block) >= 1:
        return 'H'
    # score 0 and NOT looks_like_sanskrit: by that function's own logic the block
    # must have a >=90-char line (else it would be Sanskrit). Long prose with a
    # stamp is a Hindi paragraph with no bounded Hindi cue — the same class as the
    # four documented {hN} exceptions, just long. A stampless score-0 block is a
    # heading / navigation junk → genuinely ambiguous.
    if STAMP.search(block):
        return 'H'
    return 'A'

def looks_translational(block):
    """Guard for the Sanskrit-pairing fallback: an unstamped block only earns a
    verse if it plausibly translates one. Website-menu junk ('धर्म और श्रद्धा',
    'शब्दकोश और विश्वकोश') scores as Hindi solely on और/व and would otherwise be
    paired to the preceding śloka. Real translations are substantial or a ragged
    em-dash continuation; the shortest genuine paired translation in the corpus is
    36 chars, the junk is 15 — a clean gap. Keep em-dash fragments and multi-cue
    blocks regardless of length."""
    core = block.strip().strip('“”\'"‘’—-।॥ \t')
    if len(core) >= 25:
        return True
    if block.rstrip().endswith('—') or block.lstrip().startswith('—'):
        return True
    if m.hindi_score(block) >= 2:
        return True
    return False

def iter_sargas(path):
    """Yield (sarga, [(block_text, start_line_1based), ...]) preserving line #s."""
    raw = open(path, encoding='utf-8').read()
    lines = raw.split('\n')
    titles = [(i, m.parse_sarga_num(mt.group(1)))
              for i, l in enumerate(lines)
              if (mt := m.TITLE_RE.match(l.strip()))]
    if titles:
        segs = []
        for k, (idx, sn) in enumerate(titles):
            end = titles[k + 1][0] if k + 1 < len(titles) else len(lines)
            segs.append((sn, idx, end))
    else:
        segs = [(m.detect_sarga(path, raw), 0, len(lines))]

    for sn, start, end in segs:
        seg_lines = lines[start:end]
        # footnote-blank preserves line count
        seg_lines = m.blank_footnotes('\n'.join(seg_lines)).split('\n')
        blocks, cur, cur_start = [], [], None
        for off, ln in enumerate(seg_lines):
            if ln.strip():
                if cur_start is None:
                    cur_start = start + off
                cur.append(ln)
            else:
                if cur:
                    blocks.append(('\n'.join(cur).strip(), cur_start + 1))
                    cur, cur_start = [], None
        if cur:
            blocks.append(('\n'.join(cur).strip(), cur_start + 1))
        yield sn, blocks

# ── build ──────────────────────────────────────────────────────────
cmap = collections.defaultdict(dict)          # kanda -> sarga(str) -> record
dup_sargas = []

for path in sorted(glob.glob(os.path.join(CORPUS, '*.txt'))):
    kanda = m.detect_kanda(path)
    fn = os.path.basename(path)
    for sarga, blocks in iter_sargas(path):
        skey = str(sarga)
        paras, skt_named, ambiguous = [], set(), []
        seq = 0
        pending = []          # Sanskrit verses seen since the last Hindi paragraph
        seen_sanskrit = False  # suppress the pre-verse sarga heading (unstamped Hindi)
        for text, line in blocks:
            if is_colophon(text):
                continue
            cls = classify(text)
            if cls == 'S':
                vs = []
                for s in STAMP.findall(text):
                    nums, _ = parse_stamp(s)
                    vs += nums
                skt_named.update(vs)
                pending += vs
                seen_sanskrit = True
                continue
            if cls == 'A':
                if STAMP.search(text) or m.get_marker(text):
                    ambiguous.append({'line': line,
                                      'text': ' / '.join(l.strip() for l in text.split('\n'))[:160]})
                continue
            # cls == 'H'
            cov = coverage_for_block(text)      # from the paragraph's OWN stamp/marker
            if cov is None:
                # Unstamped Hindi (Uttara convention) — pair with the preceding
                # Sanskrit sloka(s). No stamp means no half-verse spill.
                if not looks_translational(text):
                    # website-menu junk mis-scored as Hindi via और/व — not a verse.
                    # Skip WITHOUT consuming pending, so the real translation (if
                    # unstamped) still pairs to its śloka.
                    ambiguous.append({'line': line, 'issue': 'non-verse-junk-skipped',
                                      'text': ' / '.join(l.strip() for l in text.split('\n'))[:160]})
                    continue
                if not pending:
                    # Before the first sloka this is just the sarga heading — ignore.
                    # After sloka(s) have appeared, an unstamped Hindi with nothing
                    # pending is a genuine oddity (two Hindi paragraphs in a row).
                    if seen_sanskrit:
                        ambiguous.append({'line': line, 'issue': 'unstamped-hindi-no-pending',
                                          'text': ' / '.join(l.strip() for l in text.split('\n'))[:160]})
                    continue
                verses = sorted(set(pending))
                cov = {'span': [verses[0], verses[-1]], 'verses': verses,
                       'spill': False, 'spill_verse': None, 'stamp': None,
                       'is_range': len(verses) > 1, 'flags': ['paired-with-sanskrit']}
                cov['source'] = 'sanskrit-pairing'
            else:
                cov['source'] = 'marker' if (m.get_marker(text) and not cov['stamp']) \
                                else ('marker+stamp' if m.get_marker(text) else 'stamp')
            cov['seq'] = seq
            cov['line'] = line
            paras.append(cov)
            seq += 1
            pending = []        # consumed by this Hindi paragraph

        rec = {'file': fn, 'kanda': kanda, 'kanda_name': KANDA_NAME.get(kanda),
               'sarga': sarga, 'paragraphs': paras,
               'sanskrit_verses': sorted(skt_named), 'ambiguous': ambiguous}
        if skey in cmap[kanda]:
            dup_sargas.append((kanda, skey, fn, cmap[kanda][skey]['file']))
            skey = f'{skey}#{fn}'
        cmap[kanda][skey] = rec

# ── validate ───────────────────────────────────────────────────────
# The core invariant (user spec): every GP verse is covered by EXACTLY ONE Hindi
# paragraph, except a spilled first line which is legitimately shared. So the real
# coverage defects are: covered 0 times (gap) or >1 times (double). A verse the
# Hindi covers but the Sanskrit side never stamps is NOT a Hindi-coverage defect —
# it is a Sanskrit-side missing stamp; recorded separately as informational.
for kanda, sargas in cmap.items():
    for skey, rec in sargas.items():
        cover = collections.Counter()
        multi_owner = {}                       # verse -> True if any owner is a merged block
        for p in rec['paragraphs']:
            merged = 'multi-stamp-block' in p['flags']
            for v in p['verses']:
                cover[v] += 1
                if merged:
                    multi_owner[v] = True
        skt = set(rec['sanskrit_verses'])
        anomalies = []
        # gaps: a Sanskrit-attested verse with no Hindi paragraph
        for v in sorted(skt - set(cover)):
            anomalies.append({'verse': v, 'issue': 'uncovered'})
        # doubles: a verse named by more than one Hindi paragraph
        for v in sorted(cover):
            if cover[v] > 1:
                a = {'verse': v, 'issue': f'covered_{cover[v]}x'}
                if multi_owner.get(v):
                    a['likely_cause'] = 'merged-block (missing blank line before next sloka)'
                anomalies.append(a)
        # spill consistency: spilled first line should belong to the next paragraph
        paras = rec['paragraphs']
        for i, p in enumerate(paras):
            if p['spill_verse'] is None:
                continue
            nxt = paras[i + 1] if i + 1 < len(paras) else None
            if nxt is None or nxt['span'][0] != p['spill_verse']:
                anomalies.append({'verse': p['spill_verse'], 'issue': 'spill_target_mismatch',
                                  'from_seq': p['seq'],
                                  'next_span': (nxt['span'] if nxt else None)})
        # informational (not coverage defects)
        sanskrit_stamp_gaps = sorted(set(cover) - skt)   # Hindi-covered, Sanskrit unstamped
        rec['max_verse'] = max(set(cover) | skt) if (cover or skt) else 0
        rec['verses_covered'] = sorted(cover)
        rec['anomalies'] = anomalies
        rec['sanskrit_stamp_gaps'] = sanskrit_stamp_gaps

# ── emit ───────────────────────────────────────────────────────────
out = {str(k): cmap[k] for k in sorted(cmap)}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

# ── report ─────────────────────────────────────────────────────────
print(f"wrote {OUT}\n")
if dup_sargas:
    print("DUPLICATE (kanda,sarga) across files:")
    for d in dup_sargas: print("  ", d)
    print()

hdr = (f"{'kanda':<11}{'sargas':>7}{'paras':>7}{'verses':>7}{'ranges':>7}"
       f"{'spills':>7}{'gaps':>6}{'dbl':>5}{'sktgap':>7}{'ambig':>6}")
print(hdr); print('-'*len(hdr))
tot = collections.Counter()
gap_detail, dbl_detail, spill_detail = [], [], []
for k in sorted(cmap):
    sargas = cmap[k]
    paras = sum(len(r['paragraphs']) for r in sargas.values())
    verses = sum(len(r['verses_covered']) for r in sargas.values())
    ranges = sum(1 for r in sargas.values() for p in r['paragraphs'] if p['is_range'])
    spills = sum(1 for r in sargas.values() for p in r['paragraphs'] if p['spill'])
    gaps = dbls = spmis = 0
    sktgap = sum(len(r['sanskrit_stamp_gaps']) for r in sargas.values())
    ambig = sum(len(r['ambiguous']) for r in sargas.values())
    for skey, r in sargas.items():
        for a in r['anomalies']:
            iss = a['issue']
            if iss == 'uncovered': gaps += 1; gap_detail.append((KANDA_NAME[k], skey, a))
            elif iss.startswith('covered_'): dbls += 1; dbl_detail.append((KANDA_NAME[k], skey, a))
            elif iss == 'spill_target_mismatch': spmis += 1; spill_detail.append((KANDA_NAME[k], skey, a))
    print(f"{KANDA_NAME[k]:<11}{len(sargas):>7}{paras:>7}{verses:>7}{ranges:>7}"
          f"{spills:>7}{gaps:>6}{dbls:>5}{sktgap:>7}{ambig:>6}")
    for key, val in [('sargas',len(sargas)),('paras',paras),('verses',verses),
                     ('ranges',ranges),('spills',spills),('gaps',gaps),('dbls',dbls),
                     ('sktgap',sktgap),('ambig',ambig),('spmis',spmis)]:
        tot[key]+=val
print('-'*len(hdr))
print(f"{'TOTAL':<11}{tot['sargas']:>7}{tot['paras']:>7}{tot['verses']:>7}{tot['ranges']:>7}"
      f"{tot['spills']:>7}{tot['gaps']:>6}{tot['dbls']:>5}{tot['sktgap']:>7}{tot['ambig']:>6}")

print("\nColumns: gaps=verse with 0 Hindi paragraphs (real gap); dbl=verse named by >1"
      " paragraph;\n  sktgap=Hindi-covered but Sanskrit stamp missing (informational);"
      " ambig=unclassifiable/junk blocks.")

print(f"\n=== REAL GAPS — verse covered by zero Hindi paragraphs: {len(gap_detail)} ===")
for kn, skey, a in gap_detail:
    print(f"  [{kn} s{skey}] verse {a['verse']}")
print(f"\n=== DOUBLES — verse covered by >1 Hindi paragraph: {len(dbl_detail)} ===")
for kn, skey, a in dbl_detail[:80]:
    cause = f"  ({a['likely_cause']})" if 'likely_cause' in a else ''
    print(f"  [{kn} s{skey}] verse {a['verse']} {a['issue']}{cause}")
if len(dbl_detail) > 80: print(f"  … and {len(dbl_detail)-80} more")
print(f"\n=== SPILL mismatches: {len(spill_detail)} ===")
for kn, skey, a in spill_detail:
    print(f"  [{kn} s{skey}] {a}")

# ── markdown report ────────────────────────────────────────────────
REPORT = 'hindi_coverage_report.md'
L = []
L.append('# Hindi coverage map — stream C step 1\n')
L.append('Built by `build_coverage.py` from `ramcharitdotin/*.txt` (read-only). '
         'Output: `hindi_coverage_map.json`, keyed `kanda → sarga → {paragraphs, '
         'sanskrit_verses, anomalies, …}`. Each paragraph records its verse `span`, '
         '`spill`/`spill_verse` (the `१/२` first-line carry), `stamp`, `source`, '
         'and file `line`.\n')
L.append('## Per-kanda summary\n')
L.append('| kanda | sargas | paragraphs | verses covered | ranges | spills | gaps | doubles | skt-stamp gaps | ambiguous |')
L.append('|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|')
for k in sorted(cmap):
    sg = cmap[k]
    paras = sum(len(r['paragraphs']) for r in sg.values())
    verses = sum(len(r['verses_covered']) for r in sg.values())
    ranges = sum(1 for r in sg.values() for p in r['paragraphs'] if p['is_range'])
    spills = sum(1 for r in sg.values() for p in r['paragraphs'] if p['spill'])
    gaps = sum(1 for r in sg.values() for a in r['anomalies'] if a['issue']=='uncovered')
    dbls = sum(1 for r in sg.values() for a in r['anomalies'] if a['issue'].startswith('covered_'))
    sktg = sum(len(r['sanskrit_stamp_gaps']) for r in sg.values())
    amb = sum(len(r['ambiguous']) for r in sg.values())
    L.append(f"| {KANDA_NAME[k]} | {len(sg)} | {paras} | {verses} | {ranges} | {spills} | {gaps} | {dbls} | {sktg} | {amb} |")
L.append(f"| **total** | **{tot['sargas']}** | **{tot['paras']}** | **{tot['verses']}** | "
         f"**{tot['ranges']}** | **{tot['spills']}** | **{tot['gaps']}** | **{tot['dbls']}** | "
         f"**{tot['sktgap']}** | **{tot['ambig']}** |\n")
L.append('- **gaps** — a Sanskrit-attested verse with **zero** Hindi paragraphs. The real '
         'coverage holes; each needs a Hindi paragraph (often a short, cue-less line the '
         'classifier reads as Sanskrit, like the four documented `{hN}` exceptions).')
L.append('- **doubles** — a verse named by **>1** Hindi paragraph. Mostly source defects: a '
         'missing blank line merging a Hindi paragraph with the next śloka, or two '
         'overlapping range/summary paragraphs.')
L.append('- **skt-stamp gaps** *(informational)* — Hindi covers the verse fine, but the '
         'Sanskrit śloka there is missing its own `॥N॥` stamp. A Sanskrit-side issue, not a '
         'Hindi-coverage defect.')
L.append('- **ambiguous** *(informational)* — stampless non-verse blocks (site navigation, '
         'credits) and any block the classifier could not place.\n')

L.append(f'## Real gaps — {len(gap_detail)}\n')
L.append('| kanda | sarga | verse |')
L.append('|---|---|--:|')
for kn, skey, a in gap_detail:
    L.append(f"| {kn} | {skey} | {a['verse']} |")
L.append('')

L.append(f'## Doubles — {len(dbl_detail)}\n')
L.append('| kanda | sarga | verse | likely cause |')
L.append('|---|---|--:|---|')
for kn, skey, a in dbl_detail:
    L.append(f"| {kn} | {skey} | {a['verse']} | {a.get('likely_cause','overlapping paragraphs')} |")
L.append('')

if spill_detail:
    L.append(f'## Spill mismatches — {len(spill_detail)}\n')
    L.append('The `१/२` first-line carry did not land on the next paragraph’s first verse.\n')
    for kn, skey, a in spill_detail:
        L.append(f"- {kn} s{skey}: spill→verse {a['verse']} from seq {a['from_seq']}, "
                 f"next paragraph span {a['next_span']}")
    L.append('')

if dup_sargas:
    L.append('## Duplicate (kanda, sarga) across files\n')
    L.append('Both kept in the JSON (second under a `sarga#file` key); pick one for the migration.\n')
    for k, skey, fn, existing in dup_sargas:
        L.append(f"- {KANDA_NAME[k]} s{skey}: `{fn}` duplicates `{existing}`")
    L.append('')

open(REPORT, 'w', encoding='utf-8').write('\n'.join(L))
print(f"\nwrote {REPORT}")
