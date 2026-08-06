#!/usr/bin/env python3
"""
parse_hindi.py — Master parser for Valmiki Ramayana Hindi text files
Version 3.0 — includes:
  - S/H manual marker support (S5, S5-6, H5, H5-6, case-insensitive, end of line)
  - Fraction stripping (१/२ ½) to prevent false span starts
  - Word-boundary Hindi detection (avoids Sanskrit substring matches)
=====================================================================
Usage:
    python3 parse_hindi.py bks10.txt bks11.txt bks12.txt ...

Naming: bks<N>.txt (Bala), aks<N>.txt (Ayodhya), ars<N>.txt (Aranya),
        kks<N>.txt (Kishkindha), sks<N>.txt (Sundara),
        yks<N>.txt (Yuddha), uks<N>.txt (Uttara)
"""
import re, json, zipfile, os, sys

# ── Verse counts ───────────────────────────────────────────────────
VERSE_COUNTS = {
    1: {1:100,2:43,3:39,4:36,5:23,6:28,7:24,8:24,9:20,
        10:33,11:31,12:22,13:41,14:60,15:34,16:32,17:30,
        18:47,19:37,20:25,21:23,22:18,23:22,24:18,25:26,
        26:28,27:16,28:25,29:26,30:25,31:27,32:31,33:28,
        34:31,35:27,36:21,37:28,38:22,39:26,40:30,41:22,
        42:22,43:65,44:31,45:31,46:30,47:20,48:31,49:27,
        50:19,51:24,52:25,53:33,54:31,55:21,56:28,57:16,
        58:22,59:21,60:25,61:26,62:23,63:23,64:29,65:30,
        66:30,67:30,68:30,69:26,70:26,71:30,72:18,73:34,
        74:31,75:26,76:22,77:30},
    2:{}, 3:{}, 4:{}, 5:{}, 6:{}, 7:{},
}

KANDA_PREFIX = {
    'bk':1,'bal':1,'aks':2,'ayo':2,'ars':3,'ara':3,
    'kk':4,'kis':4,'sk':5,'sun':5,'yk':6,'yud':6,'uk':7,'utt':7,
}

def detect_kanda(filename):
    base = os.path.basename(filename).lower()
    for prefix, k in sorted(KANDA_PREFIX.items(), key=lambda x: -len(x[0])):
        if base.startswith(prefix): return k
    return 1

def parse_sarga_num(s):
    """Parses a sarga-number string as int, or float if it has a decimal point
    (used for interpolated/प्रक्षिप्त sargas like '56.1' that sit between two
    regularly-numbered sargas but aren't part of the standard sequence)."""
    return float(s) if '.' in s else int(s)

def detect_sarga(filename, text):
    sm = re.search(r'सर्ग\s+(\d+(?:\.\d+)?)', text.split('\n')[0])
    if sm: return parse_sarga_num(sm.group(1))
    dm = re.search(r'(\d+(?:\.\d+)?)', os.path.basename(filename))
    if dm: return parse_sarga_num(dm.group(1))
    return None

# ── Regex constants ────────────────────────────────────────────────
STAMP_RE = re.compile(
    r'(?:[।॥]\s*[०-९][\s०-९\-–½/]*[।॥]'
    r'|(?<=[^\u0966-\u096F])\s[०-९][\s०-९\-–½/]*॥)',
    re.MULTILINE
)

# Primary marker: {S5} {H5-6} {S5-6 1/2} — curly brace format (strict, no typo tolerance)
MARKER_RE = re.compile(
    r'\{([SsHh])(\d+)(?:-(\d+))?(?:\s+1/2)?\}\s*$',
    re.MULTILINE
)
# Fallback marker: bare S5 H5 at end of line (old format, backward compat)
MARKER_OLD_RE = re.compile(
    r'(?<!\{)\s+([SsHh])(\d+)(?:-(\d+))?(?:\s+1/2)?\s*$',
    re.MULTILINE
)
SKIP_MARKERS = [
    'Spread the Glory','बालकाण्डम्','अयोध्याकाण्डम्','अरण्यकाण्डम्',
    'किष्किन्धाकाण्डम्','सुन्दरकाण्डम्','युद्धकाण्डम्','उत्तरकाण्डम्',
    'श्रीसीतारामचन्द्राभ्यां','हिंदी अर्थ सहित','इत्यार्षे','इत्याचे',
    'इस प्रकार श्रीवाल्मीकि','सर्गः (सर्ग','Valmiki Ramayana',
    'वाल्मीकि रामायण',
]

# Word-boundary Hindi patterns — avoids Sanskrit substring false positives
HINDI_PATTERNS = re.compile(
    r'(?<![^\s।॥,।])'
    r'('
    r'हुए|हैं|थे|किया|गये|हुआ|करके|लिये|उन्होंने|'
    r'बोले|देखा|कहा|दिया|लिया|गया|आया|होकर|लगे|'
    r'उसने|कहते|रहते|करते|जाते|आते|होती|जाती|करती|'
    r'पूछा|सुना|माना|चाहा|सोचा|पहुँचे|बताया|मिला|'
    r'मिली|चले|गयी|आयी|रहा|रही|बोली|मारा|लड़े|'
    r'थे।|थी।|है।|हैं।|गया।|गयी।|हुआ।|हुई।|'
    r'किया।|दिया।|लिया।|गये।|आया।|आयी।|चले।|'
    r'बोले।|कहा।|देखा।|सुना।|रहा।|रही।|'
    r'उनका|उनके|उनसे|उनकी|उनको|अपने|अपनी|अपना|'
    r'उसका|उसके|उसकी|उसको|इसका|इसके|इसकी|'
    r'वहाँ|यहाँ|उसी|इसी|यही|वही|'
    r'तदनन्तर|तत्पश्चात्|'
    r'राजाने|मुनिने|ऋषिने|'
    r'नामसे|नाम से|नामकी|'
    r'इसलिये|इसलिए|क्योंकि|'
    r'जिन्हें|जिनमें|जिन्होंने|जिसमें|'
    # NB: को/का/के/पर deliberately EXCLUDED — they are valid Sanskrit words
    # (कः→को/का "who", केचित्→"के", परः→पर "other"), so counting them as Hindi
    # signals mis-scored genuine Sanskrit ślokas as Hindi. Postpositions में/से/
    # की/ने and है/और have no standalone Sanskrit use and stay.
    r'में|से|की|ने|है|और|तुम्हें|मुझे|उसे|इसे|हूँ|मेरी|'
    r'कभी|पहले|फिर|यहाँ|वहाँ|कैसे|क्यों|कहाँ|'
    r'तक|मैं|इन|अब|सभी|तीनों|मेरे|रहे|वाले|बारंबार|देकर|पहुँचा|'
    r'हुई|उस|तब|ऐसा|कोई|उठे|सुनकर|सुनाकर'
    r')'
    # Trailing boundary mirrors the leading one (?<![^\s\u0964\u0965,\u0964]): both must treat a
    # danda as punctuation. \u0965 (U+0965) and \u0964 (U+0964) live INSIDE the Devanagari
    # block, so a bare [^\u0900-\u097F] lookahead rejects a word glued to its
    # stamp (\u092D\u0947\u091C\u0947\u0965, \u091A\u0932\u0947\u0965, \u0932\u0917\u0947\u0965). Adding [\u0964\u0965] lets those match \u2014 it only ADDS
    # matches (verified: 0 lost, 5 Sanskrit\u2192Hindi flips, all genuine Hindi prose).
    r'(?=[^\u0900-\u097F]|[\u0964\u0965]|$)'
)

# ── Utilities ──────────────────────────────────────────────────────
def deva_to_int(s):
    dm = {'०':'0','१':'1','२':'2','३':'3','४':'4',
          '५':'5','६':'6','७':'7','८':'8','९':'9'}
    digits = ''.join(dm.get(c,'') for c in s if c in dm)
    return int(digits) if digits else None

def to_deva(n):
    dm = {0:'०',1:'१',2:'२',3:'३',4:'४',5:'५',6:'६',7:'७',8:'८',9:'९'}
    return ''.join(dm[int(d)] for d in str(n))

def hindi_score(block):
    return len(HINDI_PATTERNS.findall(block))

# Kanda-completion marker (e.g. "॥अरण्यकाण्डं सम्पूर्णम्॥") — appears once, on its
# own, in the last sarga of each kanda. SKIP_MARKERS above only lists the kanda
# names with the "...काण्डम्" (virama-म्) ending used in title lines elsewhere in
# these files, but this completion line instead uses the "...काण्डं" (anusvara)
# ending — a different Unicode string that `in` never matches. Rather than adding
# 7 more exact strings (one per kanda, times two possible ..म्/..ं endings), match
# generically on "काण्ड...सम्पूर्णम्" / "...संपूर्णम्" so it's caught regardless of
# kanda or which of the two valid nasalization spellings the source page used.
KANDA_COMPLETE_RE = re.compile(r'काण्ड\S*\s*(?:सम्पूर्णम्|संपूर्णम्)')

def is_skip(block):
    if any(m in block for m in SKIP_MARKERS):
        return True
    return bool(KANDA_COMPLETE_RE.search(block))

# ── Footnote blanking (ported from stamp_gap_finder.html) ──────────
# Footnotes are sometimes glued directly onto the end of a verse/translation
# with no blank line separating them (and the next verse follows immediately
# after with no blank line either). Left alone, the footnote text merges into
# whatever block it's touching, and any digit inside it — e.g. a citation like
# "(२। ५४। १६)" — can be misread by STAMP_RE as a real verse stamp (its
# "। ५४।" segment is indistinguishable from "॥ ५४॥"), corrupting both that
# verse's span and the sarga's detected verse count. We blank footnote lines
# out (replacing with spaces, so character positions don't shift) before
# splitting into blocks, so footnotes never merge with real content and never
# contribute spurious digits.
def is_footnote_start(line):
    t = line.strip()
    return t.startswith('*') or bool(re.match(r'^[०-९]+\.\s', t))

def looks_like_verse_resuming(line):
    if STAMP_RE.search(line): return True
    t = line.strip()
    return len(t) < 90 and hindi_score(line) == 0

def blank_footnotes(text):
    lines = text.split('\n')
    in_footnote = False
    for i, line in enumerate(lines):
        if not line.strip():
            in_footnote = False
            continue
        if is_footnote_start(line):
            in_footnote = True
            lines[i] = ' ' * len(line)
            continue
        if in_footnote:
            if looks_like_verse_resuming(line):
                in_footnote = False
            else:
                lines[i] = ' ' * len(line)
    return '\n'.join(lines)

def get_span(block):
    """Extract verse span from stamps, stripping ½ fractions to avoid false starts."""
    nums = []
    for st in STAMP_RE.findall(block):
        inner = re.sub(r'^[।॥]\s*', '', st)
        inner = re.sub(r'\s*[।॥]$', '', inner).strip()
        inner = re.sub(r'[०-९]+\s*/\s*[०-९]+', '', inner)  # strip N/M fractions
        inner = re.sub(r'½', '', inner)                      # strip ½
        for n in re.findall(r'[०-९]+', inner):
            v = deva_to_int(n)
            if v and 1 <= v <= 500: nums.append(v)
    if not nums: return None, None
    sf, sl = min(nums), max(nums)
    if sl - sf > 10: sf = sl = max(nums)
    return sf, sl

def get_marker(block):
    """Extract S/H manual marker from end of any line in block.
    Tries {S5} format first, then bare S5 fallback.
    """
    # Primary: {S5} curly-brace format
    m = MARKER_RE.search(block)
    if m:
        mtype = m.group(1).upper()
        sf = int(m.group(2))
        sl = int(m.group(3)) if m.group(3) else sf
        return mtype, sf, sl
    # Fallback: bare S5 format (old files)
    m = MARKER_OLD_RE.search(block)
    if not m: return None
    mtype = m.group(1).upper()
    sf = int(m.group(2))
    sl = int(m.group(3)) if m.group(3) else sf
    return mtype, sf, sl

def strip_marker(text):
    text = MARKER_RE.sub('', text)
    text = MARKER_OLD_RE.sub('', text)
    return text.strip()

def looks_like_sanskrit(block):
    """True if block is a Sanskrit verse — has stamp, short lines, no Hindi prose."""
    if hindi_score(block) >= 2: return False
    lines = [l.strip() for l in block.split('\n') if l.strip()]
    if not lines: return True
    if STAMP_RE.search(block) and all(len(l) < 90 for l in lines):
        return hindi_score(block) <= 0
    return False

def clean(h):
    h = strip_marker(h)
    h = STAMP_RE.sub('', h).strip()
    h = re.sub(r"^['\"\[\]।॥ॐ\s]+", '', h).strip()
    return h.rstrip("'\"॥।–").strip()

def max_verse_in_file(path):
    text = open(path, encoding='utf-8').read()
    text = _strip_colophon(text)
    text = blank_footnotes(text)
    nums = []
    for st in STAMP_RE.findall(text):
        inner = re.sub(r'^[।॥]\s*', '', st)
        inner = re.sub(r'\s*[।॥]$', '', inner).strip()
        inner = re.sub(r'[०-९]+\s*/\s*[०-९]+', '', inner)
        inner = re.sub(r'½', '', inner)
        for n in re.findall(r'[०-९]+', inner):
            v = deva_to_int(n)
            if v and 1 <= v <= 200: nums.append(v)
    for rx in [MARKER_RE, MARKER_OLD_RE]:
        for m in rx.finditer(text):
            v = int(m.group(3) if m.group(3) else m.group(2))
            if 1 <= v <= 200: nums.append(v)
    return max(nums) if nums else 30

_PURA_HUA_RE = re.compile(r'पूरा\s*हुआ')  # tolerates both "पूरा हुआ" and "पूराहुआ"

def _strip_colophon(text):
    """Remove closing colophon lines before scanning for verse stamps — the
    trailing number there is the SARGA number, not a verse number, and can
    be miscounted as a spurious high verse stamp. Two line variants appear,
    with a spelling difference in the opening word (इत्यार्षे / इत्याचे):
      '<इत्यार्षे|इत्याचे> ...आदिकाव्ये...सर्गः॥ N॥'
      '...सर्ग पूरा हुआ॥ N॥'
    Matched generically: any line containing both 'आदिकाव्य' and 'सर्ग'
    (checking the bare stem 'सर्ग' rather than 'सर्गः' also catches source
    typos that drop the trailing विसर्ग — e.g. '...सर्ग॥४९॥' instead of the
    expected '...सर्गः॥४९॥' — which otherwise slip past this check and let
    the sarga number get misread as a spurious final verse stamp, inflating
    the detected verse count for the whole sarga), or containing 'पूरा हुआ'
    (with or without the space — source files are inconsistent about it,
    e.g. 'पूराहुआ', and a missed match here has the same failure mode)."""
    lines = [l for l in text.split('\n')
             if not (('आदिकाव्य' in l and 'सर्ग' in l) or _PURA_HUA_RE.search(l))]
    return '\n'.join(lines)

def max_verse_in_segment(text):
    """Same as max_verse_in_file() but operates on an in-memory text segment
    (used for multi-sarga files, where each segment isn't its own file)."""
    text = _strip_colophon(text)
    text = blank_footnotes(text)
    nums = []
    for st in STAMP_RE.findall(text):
        inner = re.sub(r'^[।॥]\s*', '', st)
        inner = re.sub(r'\s*[।॥]$', '', inner).strip()
        inner = re.sub(r'[०-९]+\s*/\s*[०-९]+', '', inner)
        inner = re.sub(r'½', '', inner)
        for n in re.findall(r'[०-९]+', inner):
            v = deva_to_int(n)
            if v and 1 <= v <= 200: nums.append(v)
    for rx in [MARKER_RE, MARKER_OLD_RE]:
        for m in rx.finditer(text):
            v = int(m.group(3) if m.group(3) else m.group(2))
            if 1 <= v <= 200: nums.append(v)
    return max(nums) if nums else 30

# ── Multi-sarga split ──────────────────────────────────────────────
# Matches title lines like "पञ्चमः सर्गः (सर्ग 5)" / "चतुर्दशःसर्गः (सर्ग 14)"
# Also accepts a decimal sarga number like "(सर्ग 56.1)" for an interpolated/
# प्रक्षिप्त sarga that sits between two regularly-numbered sargas.
TITLE_RE = re.compile(r'.*?सर्गः\s*\((?:सर्ग\s+)?(\d+(?:\.\d+)?)\s*\).*')

def split_segments(text):
    """Split a multi-sarga source file into (sarga_num, segment_text) pairs
    using the '<...> सर्गः (सर्ग N)' title lines as boundaries.
    Returns [] if no title lines found (i.e. single-sarga file)."""
    lines = text.split('\n')
    matches = []
    for idx, line in enumerate(lines):
        m = TITLE_RE.match(line.strip())
        if m:
            matches.append((idx, parse_sarga_num(m.group(1))))
    if not matches:
        return []
    segments = []
    for k, (idx, sarga_num) in enumerate(matches):
        end = matches[k+1][0] if k+1 < len(matches) else len(lines)
        seg_text = '\n'.join(lines[idx:end])
        segments.append((sarga_num, seg_text))
    return segments

# ── Core parser ────────────────────────────────────────────────────
def parse_segment(text, kanda, sarga):
    """Parse a single sarga's worth of text (already isolated) into an
    entry_map. Shared by parse_sarga() (single-file) and the multi-sarga
    splitter."""
    text = blank_footnotes(text)
    blocks = [b.strip() for b in re.split(r'\n\s*\n', text) if b.strip()]
    entry_map = {}

    i = 0
    while i < len(blocks):
        block = blocks[i]
        if is_skip(block): i += 1; continue

        marker = get_marker(block)
        has_stamp = bool(STAMP_RE.search(block))

        # ── Manual S marker: Sanskrit block, pair with next for Hindi ──
        if marker and marker[0] == 'S':
            _, sf, sl = marker
            j = i + 1
            while j < len(blocks) and j <= i + 2:
                nb = blocks[j]
                if is_skip(nb): j += 1; continue
                nb_marker = get_marker(nb)
                if nb_marker and nb_marker[0] == 'H':
                    sf, sl = nb_marker[1], nb_marker[2]
                elif STAMP_RE.search(nb):
                    nb_sf, nb_sl = get_span(nb)
                    if nb_sf and nb_sl: sf, sl = nb_sf, nb_sl
                h = clean(nb)
                if h and len(h) >= 6:
                    for v in range(sf, sl+1):
                        if v not in entry_map:
                            entry_map[v] = {'hindi': h, 'sf': sf, 'sl': sl}
                i = j + 1
                break
            else:
                i = j
            continue

        # ── Manual H marker: Hindi block with explicit span ──
        if marker and marker[0] == 'H':
            _, sf, sl = marker
            h = clean(block)
            if h and len(h) >= 6:
                for v in range(sf, sl+1):
                    if v not in entry_map:
                        entry_map[v] = {'hindi': h, 'sf': sf, 'sl': sl}
            i += 1
            continue

        # ── No marker — stamp-based logic ──
        if not has_stamp: i += 1; continue

        hs = hindi_score(block)
        is_skt = looks_like_sanskrit(block)

        if is_skt:
            sf, sl = get_span(block)
            if sf is None: i += 1; continue
            j = i + 1
            while j < len(blocks) and j <= i + 2:
                nb = blocks[j]
                if is_skip(nb): j += 1; continue
                nb_marker = get_marker(nb)
                nb_stamps = STAMP_RE.findall(nb)
                if nb_marker and nb_marker[0] == 'H':
                    sf, sl = nb_marker[1], nb_marker[2]
                    h = clean(nb)
                    if h and len(h) >= 6:
                        for v in range(sf, sl+1):
                            if v not in entry_map:
                                entry_map[v] = {'hindi': h, 'sf': sf, 'sl': sl}
                    i = j + 1
                    break
                if looks_like_sanskrit(nb) and nb_stamps:
                    nb_sf, nb_sl = get_span(nb)
                    if nb_sf and nb_sf <= sl + 1:
                        sl = max(sl, nb_sl or sl)
                        j += 1; continue
                    else: break
                if nb_stamps:
                    nb_sf, nb_sl = get_span(nb)
                    if nb_sf and nb_sl: sf, sl = nb_sf, nb_sl
                h = clean(nb)
                if h and len(h) >= 6:
                    for v in range(sf, sl+1):
                        if v not in entry_map:
                            entry_map[v] = {'hindi': h, 'sf': sf, 'sl': sl}
                i = j + 1
                break
            else:
                i = j
        elif hs >= 1:
            sf, sl = get_span(block)
            if sf is None: i += 1; continue
            h = clean(block)
            if h and len(h) >= 6:
                for v in range(sf, sl+1):
                    if v not in entry_map:
                        entry_map[v] = {'hindi': h, 'sf': sf, 'sl': sl}
            i += 1
        else:
            i += 1

    return entry_map


def parse_sarga(path):
    """Single-file entry point (backward compatible). Detects kanda/sarga
    from filename/first-line, then delegates to parse_segment()."""
    text = open(path, encoding='utf-8').read()
    kanda = detect_kanda(path)
    sarga = detect_sarga(path, text)
    entry_map = parse_segment(text, kanda, sarga)
    return kanda, sarga, entry_map

# ── Output builder ─────────────────────────────────────────────────
def build_output(entry_map, max_verse):
    out = []
    for v in range(1, max_verse+1):
        e = entry_map.get(v)
        if not e:
            out.append({'shloka': v, 'hindi': '', 'notice': None})
            continue
        sf, sl = e['sf'], e['sl']
        is_range = sl > sf
        if not is_range or v == sl:
            item = {'shloka': v, 'hindi': e['hindi'], 'notice': None}
            if is_range:
                item['combined_from'] = sf
                item['combined_to'] = sl
            out.append(item)
        else:
            notice = (f"श्लोक {to_deva(sf)} से {to_deva(sl)} का अनुवाद "
                      f"सम्मिलित है। अनुवाद श्लोक {to_deva(sl)} के साथ "
                      f"दिखाया जाएगा।")
            out.append({'shloka': v, 'hindi': '', 'notice': notice,
                        'combined_from': sf, 'combined_to': sl})
    return out

# ── Output validator ───────────────────────────────────────────────
def validate_output(out, sarga):
    """
    Post-processing check: detect notices whose combined_from is earlier
    than the first verse in their span that actually has individual hindi.
    This catches the sarga-1-verse-14 class of error where a combined span
    was incorrectly set to start before verses that have their own translations.
    Prints warnings and returns a corrected list.
    """
    d = {e['shloka']: e for e in out}
    warnings = []
    corrected = list(out)  # copy

    for i, e in enumerate(corrected):
        if not e.get('notice'): continue
        sf = e.get('combined_from', e['shloka'])
        sl = e.get('combined_to', e['shloka'])
        v  = e['shloka']

        # Find the last verse before v that has individual hindi
        # If any verse between sf and v-1 has its own hindi, the span start is wrong
        bad_start = None
        for prev in range(sf, v):
            prev_e = d.get(prev, {})
            if prev_e.get('hindi') and not prev_e.get('notice'):
                bad_start = prev
                break

        if bad_start is not None:
            # The notice span starts too early — it includes verses that have
            # individual translations. The real combined span starts at v.
            warnings.append(
                f"  ⚠ Sarga {sarga} v{v}: notice says combined from {sf}-{sl} "
                f"but v{bad_start} has individual hindi — fixing combined_from to {v}"
            )
            corrected[i] = dict(e, combined_from=v, notice=(
                f"श्लोक {to_deva(v)} से {to_deva(sl)} का अनुवाद "
                f"सम्मिलित है। अनुवाद श्लोक {to_deva(sl)} के साथ दिखाया जाएगा।"
            ))

    if warnings:
        for w in warnings: print(w)
    return corrected


# ── Main ───────────────────────────────────────────────────────────
def main(files):
    if not files:
        print("Usage: python3 parse_hindi.py bks10.txt bks11.txt ...")
        return

    results = {}
    def process_one(kanda, sarga, entry_map, max_v):
        out = build_output(entry_map, max_v)
        out = validate_output(out, sarga)   # ← post-processing check
        with_h = sum(1 for e in out if e.get('hindi'))
        with_n = sum(1 for e in out if e.get('notice'))
        missing = [e['shloka'] for e in out
                   if not e.get('hindi') and not e.get('notice')]
        covered = with_h + with_n
        pct = 100*covered//max_v if max_v else 0
        fname = f'hindi_{kanda}_{sarga}.json'
        results[fname] = out
        print(f"{fname}: {covered}/{max_v} ({pct}%) | "
              f"{with_h} trans | {with_n} notices | missing: {missing}")

    for path in files:
        if not os.path.exists(path):
            print(f"File not found: {path}"); continue
        text = open(path, encoding='utf-8').read()
        kanda = detect_kanda(path)
        segments = split_segments(text)

        if segments:
            # Multi-sarga file — process each title-delimited segment
            print(f"{path}: detected {len(segments)} sargas "
                  f"({segments[0][0]}\u2013{segments[-1][0]})")
            for sarga, seg_text in segments:
                entry_map = parse_segment(seg_text, kanda, sarga)
                max_v = VERSE_COUNTS.get(kanda, {}).get(sarga,
                            max_verse_in_segment(seg_text))
                process_one(kanda, sarga, entry_map, max_v)
        else:
            # Single-sarga file — original behaviour
            kanda, sarga, entry_map = parse_sarga(path)
            if sarga is None:
                print(f"Could not detect sarga from {path}"); continue
            max_v = VERSE_COUNTS.get(kanda, {}).get(sarga,
                        max_verse_in_file(path))
            process_one(kanda, sarga, entry_map, max_v)

    if not results: return

    for fname, data in results.items():
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    zipname = 'hindi_output.zip'
    with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as z:
        for fname, data in results.items():
            z.writestr(fname, json.dumps(data, ensure_ascii=False, indent=2))
    print(f"\nSaved: {list(results.keys())}")
    print(f"ZIP:   {zipname} ({os.path.getsize(zipname)//1024}KB)")

if __name__ == '__main__':
    main(sys.argv[1:])
