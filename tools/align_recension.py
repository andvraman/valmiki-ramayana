#!/usr/bin/env python3
"""
align_recension.py — Align Gita Press Sanskrit (ramcharit.in .txt files) against
AshuVj Sanskrit (data.json) so the Hindi join can be rebuilt on real verse
boundaries instead of a drifting verse-number join.

Parameterised by kanda: pass the kanda number as argv[1] (default 4 = Kishkindha).
Reads only; writes map_{kanda}_{sarga}.json per sarga and one
alignment_report_{kanda_slug}.md. Never touches data.json or the .txt files.

Method (per CONTEXT.md §2):
  * Parse each sarga's Gita Press verses (Sanskrit couplet + its stamp) from the
    .txt files.
  * Pull the same sarga's Sanskrit rows from data.json (AshuVj).
  * Normalise both sides (strip stamps/punctuation, anusvara -> म्, drop virama),
    concatenate each into a char stream, align with
    difflib.SequenceMatcher(autojunk=False).
  * Attribute matched characters back to their source verses to get the
    verse->verse correspondence, then surface every ragged join. Nothing is
    "fixed" automatically.
"""
import re, os, sys, json
from difflib import SequenceMatcher
from collections import defaultdict

# Reuse the canonical source-parsing helpers so we treat stamps, markers,
# footnotes and colophons exactly as the production parser does.
import parse_hindi_v4 as P

HERE = os.path.dirname(os.path.abspath(__file__))
TXT_DIR = os.path.join(HERE, 'ramcharitdotin')

KANDA = {
    1: ('bks', 'Bala Kanda'),
    2: ('aks', 'Ayodhya Kanda'),
    3: ('ars', 'Aranya Kanda'),
    4: ('kks', 'Kishkindha Kanda'),
    5: ('sks', 'Sundara Kanda'),
    6: ('yks', 'Yuddha Kanda'),
    7: ('uks', 'Uttara Kanda'),
}

VIRAMA   = '्'
ANUSVARA = 'ं'

# ── Normalisation ──────────────────────────────────────────────────
def normalize(text):
    """Strip stamps/markers/punctuation, anusvara -> म्, drop virama, keep only
    Devanagari letters+matras. Applied identically to both sides."""
    text = re.sub(r'\{[^}]*\}', '', text)      # {s6} {S5-6} markers
    text = P.STAMP_RE.sub('', text)            # ॥६॥ verse stamps
    text = text.replace(ANUSVARA, 'म' + VIRAMA)  # anusvara -> म्
    text = text.replace(VIRAMA, '')            # drop virama
    out = []
    for ch in text:
        o = ord(ch)
        if 0x0900 <= o <= 0x097F:
            if 0x0966 <= o <= 0x096F:          # Devanagari digits
                continue
            if ch in '।॥ऽ॰':                    # danda/avagraha punctuation
                continue
            out.append(ch)
    return ''.join(out)

# ── Gita Press verse parsing ───────────────────────────────────────
def gp_verse_num(block):
    """Verse number(s) of a Sanskrit block: (first, last) or (None, None).
    Prefers an explicit {sN}/{SN-M} marker, else the Devanagari ॥N॥ stamp."""
    m = P.get_marker(block)
    if m and m[0] == 'S':
        return m[1], m[2]
    sf, sl = P.get_span(block)
    return sf, sl

# A Hindi paragraph can slip into the Gita Press verse stream when it happens to
# carry a ॥N॥ stamp AND scores 0 on hindi_score() — the known blind spot where
# the discriminator's word-boundary regex misses Hindi postpositions glued to the
# preceding word (लक्षणोंसे, वचनके, दशरथने). We add the structural test the format
# affords: a Sanskrit verse is danda-separated short metrical padas; a Hindi
# paragraph runs straight into its ॥N॥ with no danda (। or |) before it and a long
# prose line. hindi_score>0 stays authoritative (lexical); the structural test
# only decides the score-0 cases, and every score-0 block it rules Hindi is a
# lexical/structural DISAGREEMENT — recorded for audit by classify_block() below.
FILTER_HINDI_PARA = True
LONG_LINE = 55                 # a line longer than this, with no danda, is prose

def _structural_hindi(block):
    """True if a hindi_score==0 block is structurally a Hindi paragraph: no danda
    (। or |) anywhere and a prose-length line. Sanskrit padas carry a danda or are
    short and metrical."""
    if '।' in block or '|' in block:
        return False
    lines = [l.strip() for l in block.split('\n') if l.strip()]
    if not lines:
        return False
    return max(len(l) for l in lines) > LONG_LINE

def classify_block(block):
    """Verdict for a stamped block: ('sanskrit'|'hindi', reason). Used both to
    build the verse stream and to audit what the filter drops and why."""
    if P.hindi_score(block) > 0:
        return 'hindi', 'lexical: hindi_score>0'
    if FILTER_HINDI_PARA and _structural_hindi(block):
        return 'hindi', 'structural: no danda + long line (hindi_score==0 — DISAGREEMENT)'
    m = P.get_marker(block)
    if (m and m[0] == 'S') or P.STAMP_RE.search(block):
        return 'sanskrit', 'stamp/marker, danda or short lines'
    return 'hindi', 'no stamp/marker'

def looks_like_sanskrit_block(block):
    """Sanskrit if it carries a stamp/S-marker, no Hindi prose words, and does not
    have the structural shape of a Hindi paragraph."""
    return classify_block(block)[0] == 'sanskrit'

def parse_gp_sarga(seg_text):
    """Return ordered list of {'first','last','text'} Gita Press Sanskrit verses
    for one sarga segment, plus a list of anomaly strings."""
    text = P._strip_colophon(seg_text)
    text = P.blank_footnotes(text)
    blocks = [b.strip() for b in re.split(r'\n\s*\n', text) if b.strip()]
    verses = []
    for block in blocks:
        if P.is_skip(block):
            continue
        if not looks_like_sanskrit_block(block):
            continue
        sf, sl = gp_verse_num(block)
        if sf is None:
            continue
        # strip markers/stamps out of the retained Sanskrit text
        clean_txt = re.sub(r'\{[^}]*\}', '', block)
        verses.append({'first': sf, 'last': sl, 'text': clean_txt})
    return verses

# ── data.json (AshuVj) side ────────────────────────────────────────
# data.json stores Sanskrit with an embedded "{kanda}.{sarga}.{shloka}" stamp
# trailing each verse. AshuVj sometimes assigns several shloka numbers to ONE
# combined Sanskrit block and stores that whole block, identically, on each of
# those rows (CONTEXT.md §4). Left as-is this both double-counts text in the
# alignment stream and hides the per-verse boundaries. We use the embedded
# stamps to recover the true per-shloka Sanskrit, so every data.json shloka gets
# its own verse text even inside a combined block. Read-only — data.json is
# never modified.

def _reconstruct_sarga(rows, kanda, sarga):
    """rows: sorted [(shloka, raw_shloka_text)]. Returns
    (texts: {shloka: sanskrit}, combined_runs: [[shlokas]], anomalies: [str]).
    combined_runs are AshuVj-combined verse groups (identical text across rows)."""
    present = [sh for sh, _ in rows]
    present_set = set(present)
    stamp = re.compile(rf'{kanda}\.{sarga}\.(\d+)')

    # global stamp-split: gather first non-empty segment for each stamp number
    seg_by_num = {}
    for _sh, raw in rows:
        last = 0
        for m in stamp.finditer(raw):
            n = int(m.group(1))
            seg = raw[last:m.start()]
            last = m.end()
            if n not in seg_by_num and seg.strip():
                seg_by_num[n] = seg

    anomalies = []
    texts = {}
    for sh in present:
        if sh in seg_by_num:
            texts[sh] = seg_by_num[sh]
        else:
            # merged/malformed stamp (e.g. '4.1.8283' for combined 82-83) —
            # fall back to the row's own text; normalize() strips the stamp.
            texts[sh] = dict(rows)[sh]
            anomalies.append(f"shloka {sh}: no clean embedded stamp, used raw text")

    # phantom stamp numbers (text present but no such row, e.g. verse 37 folded
    # into row 36) — append onto the largest real shloka below them so the text
    # isn't lost from the stream.
    for n in sorted(seg_by_num):
        if n not in present_set:
            host = max((s for s in present if s < n), default=present[0])
            texts[host] = texts.get(host, '') + ' ' + seg_by_num[n]
            anomalies.append(f"embedded stamp {n} has no row; text folded into shloka {host}")

    # detect AshuVj-combined runs (consecutive rows with identical raw text)
    combined_runs = []
    i = 0
    while i < len(rows):
        j = i
        while j + 1 < len(rows) and rows[j + 1][1] == rows[i][1]:
            j += 1
        if j > i:
            combined_runs.append([rows[k][0] for k in range(i, j + 1)])
        i = j + 1

    return texts, combined_runs, anomalies


def load_datajson(kanda_name, kanda_num):
    data = json.load(open(os.path.join(HERE, 'data.json'), encoding='utf-8'))
    raw_by_sarga = defaultdict(list)
    for r in data:
        if r.get('kanda') == kanda_name:
            raw_by_sarga[int(r['sarga'])].append((int(r['shloka']), r.get('shloka_text', '')))
    by_sarga = {}
    combined_by_sarga = {}
    anomalies_by_sarga = {}
    for s, rows in raw_by_sarga.items():
        rows.sort(key=lambda x: x[0])
        texts, combined, anomalies = _reconstruct_sarga(rows, kanda_num, s)
        by_sarga[s] = [(sh, texts[sh]) for sh, _ in rows]
        combined_by_sarga[s] = combined
        anomalies_by_sarga[s] = anomalies
    return by_sarga, combined_by_sarga, anomalies_by_sarga

# ── Alignment ──────────────────────────────────────────────────────
def build_stream(items):
    """items: list of (label, raw_text). Returns (stream, owner[]) where owner[i]
    is the index into items that char i belongs to."""
    stream = []
    owner = []
    for idx, (_label, raw) in enumerate(items):
        norm = normalize(raw)
        stream.append(norm)
        owner.extend([idx] * len(norm))
    return ''.join(stream), owner

def align_sarga(gp_items, dj_items):
    """gp_items / dj_items: list of (label, raw_text).
    Returns (similarity, gp_to_dj, dj_to_gp, matched_chars_matrix)."""
    gp_stream, gp_owner = build_stream(gp_items)
    dj_stream, dj_owner = build_stream(dj_items)
    sm = SequenceMatcher(None, gp_stream, dj_stream, autojunk=False)
    similarity = sm.ratio()

    # matched-char counts between gp verse i and dj verse j
    mat = defaultdict(lambda: defaultdict(int))
    for i, j, n in sm.get_matching_blocks():
        for k in range(n):
            mat[gp_owner[i + k]][dj_owner[j + k]] += 1
    return similarity, mat, len(gp_stream), len(dj_stream)

def resolve_mapping(gp_items, dj_items, mat):
    """From the matched-char matrix decide, for each gp verse, which dj verses it
    covers. A dj verse counts as covered if it received a meaningful share of the
    matched characters (guards against a few incidental matches linking verses)."""
    gp_to_dj = {}
    for gi in range(len(gp_items)):
        row = mat.get(gi, {})
        if not row:
            gp_to_dj[gi] = []
            continue
        gp_len = max(1, len(normalize(gp_items[gi][1])))
        best = max(row.values())
        covered = []
        for dj_idx, c in row.items():
            dj_len = max(1, len(normalize(dj_items[dj_idx][1])))
            # substantial if it covers a real fraction of either verse, or is the
            # dominant partner for this gp verse
            if c >= max(6, 0.25 * min(gp_len, dj_len)) or c >= 0.5 * best:
                covered.append(dj_idx)
        gp_to_dj[gi] = sorted(covered)
    # invert
    dj_to_gp = defaultdict(list)
    for gi, djs in gp_to_dj.items():
        for dj in djs:
            dj_to_gp[dj].append(gi)
    return gp_to_dj, dj_to_gp

def first_words(raw, n=5):
    norm_src = re.sub(r'\{[^}]*\}', '', raw)
    norm_src = P.STAMP_RE.sub('', norm_src)
    toks = norm_src.split()
    return ' '.join(toks[:n]).strip()

# ── Report per sarga ───────────────────────────────────────────────
def process_sarga(kanda, sarga, seg_text, dj_rows, report,
                  combined_runs=None, dj_anomalies=None, dj_sarga=None):
    gp_verses = parse_gp_sarga(seg_text)
    gp_items = [(f"{v['first']}" if v['first'] == v['last']
                 else f"{v['first']}-{v['last']}", v['text']) for v in gp_verses]
    dj_items = [(str(sh), txt) for sh, txt in dj_rows]

    if dj_sarga is None:
        dj_sarga = sarga
    r = {'sarga': sarga, 'dj_sarga': dj_sarga,
         'gp_count': len(gp_items), 'dj_count': len(dj_items),
         'ashuvj_combined': combined_runs or [], 'dj_anomalies': dj_anomalies or []}

    if not gp_items or not dj_items:
        r.update({'similarity': 0.0, 'status': 'NO_DATA', 'clean': 0,
                  'ragged': [], 'tail_closes': None})
        report.append(r)
        return {}

    similarity, mat, gp_len, dj_len = align_sarga(gp_items, dj_items)
    gp_to_dj, dj_to_gp = resolve_mapping(gp_items, dj_items, mat)

    dj_shlokas = [sh for sh, _ in dj_rows]

    # Build the emitted map: gp verse label -> [dj shlokas]
    emit = {}
    for gi, (label, _raw) in enumerate(gp_items):
        emit[label] = [dj_shlokas[dj] for dj in gp_to_dj[gi]]

    # ── per-join confidence: how well each GP verse's text matches the
    # data.json verse(s) it was mapped to. Also flags a "suspect" join where a
    # different single data.json verse matches clearly better (surfaced, not
    # auto-fixed — the rules forbid silently rerouting a ragged join). ──
    dj_norm = [normalize(t) for _, t in dj_rows]
    join_conf = {}
    low_conf = []
    for gi, (label, raw) in enumerate(gp_items):
        djs = gp_to_dj[gi]
        if not djs:
            continue
        gnorm = normalize(raw)
        if not gnorm:
            continue
        conf = SequenceMatcher(None, gnorm,
                               ''.join(dj_norm[d] for d in djs),
                               autojunk=False).ratio()
        join_conf[label] = round(conf, 2)
        if conf < 0.55:
            # is there a single data.json verse that matches much better?
            best_i, best_r = None, conf
            for di in range(len(dj_rows)):
                if di in djs or not dj_norm[di]:
                    continue
                rr = SequenceMatcher(None, gnorm, dj_norm[di],
                                     autojunk=False).ratio()
                if rr > best_r:
                    best_r, best_i = rr, di
            low_conf.append({
                'gp': label, 'dj': [dj_shlokas[d] for d in djs],
                'conf': round(conf, 2),
                'better_dj': dj_shlokas[best_i] if best_i is not None else None,
                'better_r': round(best_r, 2) if best_i is not None else None})

    # ── classify joins ──
    ragged = []
    clean = 0
    for gi, (label, raw) in enumerate(gp_items):
        djs = gp_to_dj[gi]
        if not djs:
            ragged.append({
                'kind': 'gp_unmapped',
                'gp': label, 'dj': [],
                'gp_txt': first_words(raw),
                'dj_txt': ''})
            continue
        # combine: this gp verse covers >1 dj verse
        if len(djs) > 1:
            ragged.append({
                'kind': 'gp_combines_dj',
                'gp': label, 'dj': [dj_shlokas[d] for d in djs],
                'gp_txt': first_words(raw),
                'dj_txt': ' || '.join(first_words(dj_rows[d][1]) for d in djs)})
            continue
        # single dj partner: is it a clean 1:1 or part of a split?
        dj = djs[0]
        sharers = dj_to_gp[dj]
        if len(sharers) == 1:
            clean += 1
        # split handled below (once per dj verse) to avoid double reporting

    # splits: one dj verse covered by >1 gp verse
    for dj, gis in sorted(dj_to_gp.items()):
        if len(gis) > 1:
            ragged.append({
                'kind': 'gp_splits_dj',
                'gp': [gp_items[g][0] for g in sorted(gis)],
                'dj': dj_shlokas[dj],
                'gp_txt': ' || '.join(first_words(gp_items[g][1]) for g in sorted(gis)),
                'dj_txt': first_words(dj_rows[dj][1])})

    # dj verses left entirely uncovered
    for dj, (sh, txt) in enumerate(dj_rows):
        if dj not in dj_to_gp or not dj_to_gp[dj]:
            ragged.append({
                'kind': 'dj_uncovered',
                'gp': [], 'dj': sh,
                'gp_txt': '', 'dj_txt': first_words(txt)})

    # ── tail check: last gp verse should map to last dj verse ──
    last_gp = len(gp_items) - 1
    last_dj_shloka = dj_shlokas[-1]
    tail_targets = emit[gp_items[last_gp][0]]
    tail_closes = bool(tail_targets) and (last_dj_shloka in tail_targets)

    if similarity >= 0.85:
        status = 'OK'
    elif similarity >= 0.55:
        status = 'REVIEW'          # aligned but heavily divergent
    else:
        status = 'FAILED'          # content mismatch — do not trust the map

    conf_vals = list(join_conf.values())
    median_conf = round(sorted(conf_vals)[len(conf_vals) // 2], 2) if conf_vals else None
    # "suspect" = the assigned text is weak AND a clearly better single home
    # exists (>=0.15 higher and a decent absolute match). Weaker low-confidence
    # joins where no clean alternative exists are just genuine recension
    # divergence, not mis-assignments — reported separately, not as suspect.
    suspect = [c for c in low_conf if c['better_dj'] is not None
               and c['better_r'] - c['conf'] >= 0.15 and c['better_r'] >= 0.6]

    r.update({
        'similarity': round(similarity, 4),
        'status': status,
        'clean': clean,
        'ragged': ragged,
        'low_conf': low_conf,
        'median_conf': median_conf,
        'suspect_joins': suspect,
        'tail_closes': tail_closes,
        'tail_targets': tail_targets,
        'last_dj': last_dj_shloka,
    })
    report.append(r)
    return emit

# ── Cross-sarga boundary-shift detection ───────────────────────────
# The recensions sometimes disagree on where a sarga ENDS, not just how verses
# divide inside it. Where Gita Press runs a sarga longer than AshuVj, its extra
# tail verses belong to the *next* AshuVj sarga's head — they map to nothing in
# their own sarga. We detect this rather than force a cross-sarga map: a run of
# unmapped trailing GP verses whose text matches the next sarga's opening
# data.json verses. Surfaced for the reviewer; nothing is rewritten.
def detect_boundary_shifts(emits, gp_by_sarga, dj_by_sarga, max_sarga):
    shifts = []
    for s in range(1, max_sarga):
        emit = emits.get(s)
        gp = gp_by_sarga.get(s)
        if not emit or not gp:
            continue
        items = list(emit.items())
        trail = []
        for k, v in reversed(items):
            if not v:
                trail.append(k)
            else:
                break
        trail = list(reversed(trail))
        if not trail:
            continue
        nd = dj_by_sarga.get(s + 1)
        if not nd:
            continue
        label = lambda v: (str(v['first']) if v['first'] == v['last']
                           else f"{v['first']}-{v['last']}")
        tailtext = ''.join(normalize(v['text']) for v in gp if label(v) in trail)
        best, bestk = 0.0, 0
        for k in range(1, min(len(nd), 25) + 1):
            head = ''.join(normalize(t) for _, t in nd[:k])
            r = SequenceMatcher(None, tailtext, head, autojunk=False).ratio()
            if r > best:
                best, bestk = r, k
        if best > 0.6:
            shifts.append({'gp_sarga': s, 'gp_tail': trail, 'dj_sarga': s + 1,
                           'dj_head': [nd[i][0] for i in range(bestk)],
                           'ratio': round(best, 3)})
    return shifts

# ── Inventory (step 1) ─────────────────────────────────────────────
def parse_filename_range(fname, prefix):
    base = os.path.basename(fname)
    m = re.match(rf'{prefix}(\d+)(?:-(\d+))?\.txt$', base)
    if not m:
        return None
    a = int(m.group(1))
    b = int(m.group(2)) if m.group(2) else a
    return a, b

def inventory(kanda, prefix, max_sarga):
    files = sorted(f for f in os.listdir(TXT_DIR) if re.match(rf'{prefix}\d', f)
                   and f.endswith('.txt'))
    rows = []
    sarga_to_files = defaultdict(list)
    for f in files:
        path = os.path.join(TXT_DIR, f)
        text = open(path, encoding='utf-8').read()
        rng = parse_filename_range(f, prefix)
        segs = P.split_segments(text)
        found = sorted(s for s, _ in segs) if segs else \
            ([P.detect_sarga(f, text)] if P.detect_sarga(f, text) else [])
        for s in found:
            if isinstance(s, float) and s.is_integer():
                s = int(s)
            sarga_to_files[s].append(f)
        mismatch = None
        if rng:
            expected = set(range(rng[0], rng[1] + 1))
            got = set(int(s) for s in found if float(s).is_integer())
            missing_in_file = sorted(expected - got)
            extra_in_file = sorted(got - expected)
            if missing_in_file or extra_in_file:
                mismatch = {'missing': missing_in_file, 'extra': extra_in_file}
        rows.append({'file': f, 'range': rng, 'found': found,
                     'mismatch': mismatch})

    all_expected = set(range(1, max_sarga + 1))
    all_found = set(int(s) for s in sarga_to_files if float(s).is_integer())
    missing_sargas = sorted(all_expected - all_found)
    dup_sargas = {s: fs for s, fs in sarga_to_files.items() if len(fs) > 1}
    return rows, missing_sargas, dup_sargas, files

# ── Main ───────────────────────────────────────────────────────────
def _sig(texts):
    """Content signature for a sarga: normalized concat of its verse text, capped."""
    return normalize(''.join(texts))[:900]

def pair_sargas_by_content(gp_by_sarga, dj_by_sarga, max_sarga):
    """Map each GP sarga -> its data.json sarga BY CONTENT (not number), as a
    monotonic subsequence alignment (AshuVj has extra sargas). Banded DP that
    maximizes total content similarity with a small per-skip penalty, so it finds
    a clean +1 drift (Yuddha ~89) yet stays on identity where the divergence is
    local (Ayodhya ~101) instead of runaway-drifting."""
    gp_list = [s for s in range(1, max_sarga + 1) if gp_by_sarga.get(s)]
    dj_list = sorted(dj_by_sarga)
    if not gp_list or not dj_list:
        return {s: s for s in gp_list}
    gsig = {s: _sig([v['text'] for v in gp_by_sarga[s]]) for s in gp_list}
    dsig = {s: _sig([t for _, t in dj_by_sarga[s]]) for s in dj_list}
    n, mn = len(gp_list), len(dj_list)
    extra = max(0, mn - n)
    SKIP = 0.05                                  # penalty per skipped dj sarga
    def sim(i, j):
        a, b = gsig[gp_list[i]], dsig[dj_list[j]]
        return SequenceMatcher(None, a, b, autojunk=False).ratio() if a and b else 0.0
    def inband(i, j):
        return i - 3 <= j <= i + extra + 3
    NEG = float('-inf')
    dp = [[NEG] * mn for _ in range(n)]
    bk = [[-1] * mn for _ in range(n)]
    for j in range(mn):
        if inband(0, j):
            dp[0][j] = sim(0, j) - SKIP * j
    for i in range(1, n):
        for j in range(mn):
            if not inband(i, j):
                continue
            best, bj = NEG, -1
            for jp in range(j):
                if dp[i - 1][jp] == NEG:
                    continue
                cand = dp[i - 1][jp] - SKIP * (j - jp - 1)
                if cand > best:
                    best, bj = cand, jp
            if best == NEG:
                continue
            dp[i][j] = best + sim(i, j)
            bk[i][j] = bj
    j = max(range(mn), key=lambda j: dp[n - 1][j])
    pairing = {}
    for i in range(n - 1, -1, -1):
        pairing[gp_list[i]] = dj_list[j]
        j = bk[i][j]
        if j < 0:
            break
    return pairing

def main():
    kanda = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    prefix, kanda_name = KANDA[kanda]
    slug = kanda_name.split()[0].lower()

    dj_by_sarga, combined_by_sarga, anomalies_by_sarga = load_datajson(kanda_name, kanda)
    max_sarga = max(dj_by_sarga) if dj_by_sarga else 0

    inv_rows, missing_sargas, dup_sargas, files = inventory(kanda, prefix, max_sarga)

    # Gather all sarga segments across all files
    seg_by_sarga = {}
    for f in files:
        text = open(os.path.join(TXT_DIR, f), encoding='utf-8').read()
        segs = P.split_segments(text)
        if segs:
            for s, seg in segs:
                if float(s).is_integer():
                    seg_by_sarga[int(s)] = seg
        else:
            s = P.detect_sarga(f, text)
            if s is not None and float(s).is_integer():
                seg_by_sarga[int(s)] = text

    # Build GP verses for every sarga first, then pair GP<->data.json sargas by
    # CONTENT (not number) so the Ayodhya/Yuddha offsets don't mis-target.
    gp_by_sarga = {}
    for sarga in range(1, max_sarga + 1):
        seg = seg_by_sarga.get(sarga)
        if seg is not None:
            gp_by_sarga[sarga] = parse_gp_sarga(seg)
    sarga_pairing = pair_sargas_by_content(gp_by_sarga, dj_by_sarga, max_sarga)

    report = []
    emits = {}
    dj_sarga_of = {}
    for sarga in range(1, max_sarga + 1):
        seg = seg_by_sarga.get(sarga)
        dj_sarga = sarga_pairing.get(sarga, sarga)
        dj_sarga_of[sarga] = dj_sarga
        dj_rows = dj_by_sarga.get(dj_sarga, [])
        if seg is None:
            report.append({'sarga': sarga, 'dj_sarga': dj_sarga, 'gp_count': 0,
                           'dj_count': len(dj_rows), 'similarity': 0.0,
                           'status': 'NO_TXT', 'clean': 0, 'ragged': [],
                           'tail_closes': None})
            continue
        emit = process_sarga(kanda, sarga, seg, dj_rows, report,
                             combined_by_sarga.get(dj_sarga),
                             anomalies_by_sarga.get(dj_sarga), dj_sarga=dj_sarga)
        # Don't emit a mapping for a FAILED (content-mismatch) sarga — it would
        # be misleading. The report flags it for manual attention instead.
        if emit and report[-1].get('status') != 'FAILED':
            emits[sarga] = emit
            with open(os.path.join(HERE, f'map_{kanda}_{sarga}.json'), 'w',
                      encoding='utf-8') as fh:
                json.dump(emit, fh, ensure_ascii=False, indent=2)

    shifts = detect_boundary_shifts(emits, gp_by_sarga, dj_by_sarga, max_sarga)

    # ── Consolidated mapping with (sarga, shloka) pair targets ──
    consolidated = {}
    for r in report:
        s = r['sarga']
        dj_s = r.get('dj_sarga', s)
        emit = emits.get(s, {})
        consolidated[str(s)] = {
            'dj_sarga': dj_s,
            'similarity': r.get('similarity'),
            'status': r.get('status'),
            'clean_1to1': r.get('clean'),
            'map': {label: [[dj_s, sh] for sh in targets]
                    for label, targets in emit.items()},
        }
    with open(os.path.join(HERE, f'alignment_map_{slug}.json'), 'w',
              encoding='utf-8') as fh:
        json.dump(consolidated, fh, ensure_ascii=False, indent=1)

    write_report(kanda, slug, inv_rows, missing_sargas, dup_sargas, report, shifts)
    print_summary(kanda, slug, inv_rows, missing_sargas, dup_sargas, report, shifts)

def write_report(kanda, slug, inv_rows, missing_sargas, dup_sargas, report,
                 shifts=None):
    shifts = shifts or []
    L = []
    L.append(f"# Alignment report — {KANDA[kanda][1]} (kanda {kanda})\n")
    L.append("Gita Press Sanskrit (ramcharit.in .txt) aligned against AshuVj "
             "Sanskrit (data.json). Read-only pilot; nothing was written to "
             "data.json or the source .txt files.\n")

    # ── Headline ──
    real = [r for r in report if r.get('status') in ('OK', 'REVIEW', 'FAILED')]
    ok = [r for r in real if r['status'] == 'OK']
    review = [r for r in real if r['status'] == 'REVIEW']
    failed = [r for r in real if r['status'] == 'FAILED']
    clean_through = [r for r in ok if not r.get('ragged')]
    tail_open = [r for r in real if r.get('tail_closes') is False and r['status'] != 'FAILED']
    kinds = defaultdict(int)
    for r in real:
        if r['status'] == 'FAILED':
            continue
        for x in r.get('ragged', []):
            kinds[x['kind']] += 1
    nsus = sum(len(r.get('suspect_joins', [])) for r in real)
    L.append("## Headline\n")
    L.append(f"- **{len(real)} sargas** aligned. "
             f"**{len(ok)} OK** (sim ≥ 0.85), **{len(review)} REVIEW** "
             f"(0.55–0.85, heavy but real divergence), **{len(failed)} FAILED** "
             f"(< 0.55, content mismatch).")
    L.append(f"- **{len(clean_through)} sargas clean 1:1 throughout** "
             f"{sorted(r['sarga'] for r in clean_through)}.")
    L.append(f"- Ragged-join totals (excl. FAILED): "
             f"{kinds.get('gp_combines_dj',0)} GP-combines-dj, "
             f"{kinds.get('gp_splits_dj',0)} GP-splits-dj, "
             f"{kinds.get('gp_unmapped',0)} GP-unmapped, "
             f"{kinds.get('dj_uncovered',0)} dj-uncovered.")
    L.append(f"- **{len(tail_open)} tails do not close** "
             f"{sorted(r['sarga'] for r in tail_open)} — see per-sarga notes.")
    L.append(f"- **{len(shifts)} cross-sarga boundary shifts** and **{nsus} suspect "
             f"joins** flagged below.")
    L.append(f"- **FAILED:** {sorted(r['sarga'] for r in failed)} "
             f"(sarga 16 = the .txt carries an out-of-place Aranya-kanda "
             f"hemanta/Godavari passage, not Kishkindha 16).")
    L.append("")

    if shifts:
        L.append("## 0. Cross-sarga boundary shifts (read first)\n")
        L.append("Where Gita Press ends a sarga later than AshuVj: the trailing "
                 "GP verses below belong to the *next* data.json sarga's opening "
                 "verses and map to nothing in their own sarga. Not an error in "
                 "the aligner — a genuine sarga-boundary divergence needing a "
                 "cross-sarga decision.\n")
        for sh in shifts:
            L.append(f"- **GP sarga {sh['gp_sarga']} tail {sh['gp_tail']}** "
                     f"aligns to **data.json sarga {sh['dj_sarga']} head "
                     f"{sh['dj_head'][0]}–{sh['dj_head'][-1]}** (ratio {sh['ratio']})")
        L.append("")

    # ── Inventory ──
    L.append("## 1. File inventory / integrity check\n")
    L.append("| file | filename range | sargas found inside | mismatch |")
    L.append("|---|---|---|---|")
    for r in inv_rows:
        rng = f"{r['range'][0]}–{r['range'][1]}" if r['range'] else "—"
        found = r['found']
        found_s = f"{min(found)}–{max(found)} ({len(found)})" if found else "none"
        mm = "—"
        if r['mismatch']:
            parts = []
            if r['mismatch']['missing']:
                parts.append(f"missing {r['mismatch']['missing']}")
            if r['mismatch']['extra']:
                parts.append(f"extra {r['mismatch']['extra']}")
            mm = "; ".join(parts)
        L.append(f"| `{r['file']}` | {rng} | {found_s} | {mm} |")
    L.append("")
    L.append(f"- **Sargas 1–{max(1, max((r['sarga'] for r in report), default=0))} "
             f"with no .txt coverage:** {missing_sargas or 'none'}")
    L.append(f"- **Sargas appearing in more than one file:** "
             f"{dict(dup_sargas) or 'none'}")
    L.append("")

    # ── Per-sarga alignment ──
    L.append("## 2. Per-sarga alignment\n")
    L.append("`median join` = median per-verse text match of each GP verse "
             "against the data.json verse(s) it maps to (mapping confidence). "
             "`suspect` = joins where a *different* single data.json verse "
             "matches clearly better.\n")
    L.append("| sarga | status | similarity | GP | dj | clean 1:1 | ragged | "
             "median join | suspect | tail closes |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in report:
        sim = f"{r['similarity']:.3f}" if r.get('similarity') is not None else "—"
        nrag = len(r.get('ragged', []))
        tail = ('yes' if r['tail_closes'] else 'NO') if r.get('tail_closes') is not None else '—'
        st = r.get('status')
        mc = r.get('median_conf')
        mc = f"{mc:.2f}" if mc is not None else "—"
        nsus = len(r.get('suspect_joins', []))
        L.append(f"| {r['sarga']} | {st} | {sim} | {r['gp_count']} | "
                 f"{r['dj_count']} | {r.get('clean', 0)} | {nrag} | {mc} | "
                 f"{nsus or ''} | {tail} |")
    L.append("")

    # ── Ragged join detail ──
    L.append("## 3. Ragged joins (every case, for review)\n")
    KIND = {
        'gp_splits_dj': 'GP splits one data.json verse',
        'gp_combines_dj': 'GP combines two data.json verses',
        'gp_unmapped': 'GP verse maps to nothing',
        'dj_uncovered': 'data.json verse left uncovered',
    }
    for r in report:
        failed = r.get('status') == 'FAILED'
        # a failed alignment's ragged list is noise from a mismatched text
        rag = [] if failed else r.get('ragged', [])
        tailnote = ""
        if r.get('tail_closes') is False and not failed:
            tailnote = (f"  \n  ⚠ **tail does not close** — last GP verse maps to "
                        f"{r.get('tail_targets')}, but last data.json verse is "
                        f"{r.get('last_dj')}")
        if not rag and not tailnote and not failed:
            continue
        L.append(f"### Sarga {r['sarga']} "
                 f"(sim {r.get('similarity')}, GP {r['gp_count']} / dj {r['dj_count']}, "
                 f"status {r.get('status')})")
        if r.get('status') == 'FAILED':
            L.append(f"- **⚠ ALIGNMENT FAILED (sim {r.get('similarity')})** — the "
                     f".txt and data.json texts for this sarga do not match; no map "
                     f"was emitted. Treat as a source defect needing manual review.")
        if r.get('ashuvj_combined'):
            L.append(f"- *AshuVj-combined groups (one shloka_text shared across "
                     f"rows):* {r['ashuvj_combined']}")
        for a in r.get('dj_anomalies', []):
            L.append(f"- *data.json note:* {a}")
        for sc in ([] if failed else r.get('suspect_joins', [])):
            L.append(f"- **⚠ suspect join**: GP {sc['gp']} → data.json {sc['dj']} "
                     f"(match {sc['conf']}), but data.json {sc['better_dj']} "
                     f"matches better ({sc['better_r']}) — verify manually")
        for x in rag:
            kind = KIND.get(x['kind'], x['kind'])
            if x['kind'] == 'gp_splits_dj':
                L.append(f"- **{kind}**: GP {x['gp']} → data.json {x['dj']}  \n"
                         f"    GP: {x['gp_txt']}  \n    dj: {x['dj_txt']}")
            elif x['kind'] == 'gp_combines_dj':
                L.append(f"- **{kind}**: GP {x['gp']} → data.json {x['dj']}  \n"
                         f"    GP: {x['gp_txt']}  \n    dj: {x['dj_txt']}")
            elif x['kind'] == 'gp_unmapped':
                L.append(f"- **{kind}**: GP {x['gp']}  \n    GP: {x['gp_txt']}")
            elif x['kind'] == 'dj_uncovered':
                L.append(f"- **{kind}**: data.json {x['dj']}  \n    dj: {x['dj_txt']}")
        if tailnote:
            L.append(tailnote)
        L.append("")

    out = os.path.join(HERE, f'alignment_report_{slug}.md')
    open(out, 'w', encoding='utf-8').write('\n'.join(L))
    print(f"\nWrote {out}")

def print_summary(kanda, slug, inv_rows, missing_sargas, dup_sargas, report,
                  shifts=None):
    shifts = shifts or []
    aligned = [r for r in report if r.get('status') == 'OK']
    review = [r for r in report if r.get('status') == 'REVIEW']
    failed = [r for r in report if r.get('status') == 'FAILED']
    notxt = [r for r in report if r.get('status') in ('NO_TXT', 'NO_DATA')]
    clean_throughout = [r for r in aligned if not r.get('ragged')]
    ragged = [r for r in aligned if r.get('ragged')]
    tail_open = [r for r in report
                 if r.get('tail_closes') is False and r.get('status') != 'FAILED']
    kinds = defaultdict(int)
    for r in report:
        if r.get('status') == 'FAILED':
            continue
        for x in r.get('ragged', []):
            kinds[x['kind']] += 1
    print("\n" + "=" * 60)
    print(f"SUMMARY — {KANDA[kanda][1]}")
    print("=" * 60)
    print(f"sargas total:               {len(report)}")
    print(f"aligned OK (sim>=0.85):     {len(aligned)}")
    print(f"  clean 1:1 throughout:     {len(clean_throughout)}  {sorted(r['sarga'] for r in clean_throughout)}")
    print(f"  with ragged joins:        {len(ragged)}  {sorted(r['sarga'] for r in ragged)}")
    print(f"REVIEW (0.55-0.85 divergent):{len(review)}  {sorted(r['sarga'] for r in review)}")
    print(f"FAILED (<0.55 mismatch):    {len(failed)}  {sorted(r['sarga'] for r in failed)}")
    print(f"no txt / no data:           {len(notxt)}  {sorted(r['sarga'] for r in notxt)}")
    print(f"tails that DON'T close:      {len(tail_open)}  {sorted(r['sarga'] for r in tail_open)}")
    print(f"ragged-join kinds (excl FAILED): {dict(kinds)}")
    print(f"missing sargas (no txt):    {missing_sargas or 'none'}")
    print(f"sargas in >1 file:          {dict(dup_sargas) or 'none'}")
    print(f"cross-sarga boundary shifts:{len(shifts)}  "
          f"{[(s['gp_sarga'], '->', s['dj_sarga']) for s in shifts]}")
    nsus = sum(len(r.get('suspect_joins', [])) for r in report)
    print(f"suspect joins (better dj exists): {nsus}  "
          f"{sorted(set(r['sarga'] for r in report if r.get('suspect_joins')))}")

if __name__ == '__main__':
    main()
