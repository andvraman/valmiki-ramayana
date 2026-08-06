# PLAN.md — where things stand and what happens next

Companion to `CONTEXT.md`. Read that first for background; this is the running order.
Last updated after the half-verse marker discovery and anomaly cleanup.

---

## Current state

`data.json` holds **23,728 rows**. Verse recovery is **complete**:

| stage | rows | added |
|---|---|---|
| original | 23,530 | — |
| tail appends | 23,683 | +153 |
| mid-sarga insertions | 23,733 | +50 |
| dedup (5 spurious Yuddha `N.1` copies) | 23,728 | −5 |

**203 verses recovered** that were absent from the source dataset. All rows use the
`।।k.s.n।।` convention; zero U+0965 anywhere; no duplicate kanda/sarga/shloka triples.

Backups: `data.json.pre_tail_recovery.bak`, `.pre_normalise.bak`,
`.pre_preexisting_normalise.bak`, `.pre_mid_sarga.bak`.

The 203 recovered rows carry **Sanskrit only** — `transliteration`, `translation`
and `explanation` are empty. Their Hindi arrived with stream C; English and
word-by-word remain (stream E).

### ⚠ All alignment mappings are stale

The Kishkindha pilot, every `map_4_*.json`, and the ragged-join counts (218 GP-combines,
54 GP-splits, 42 unmapped, 37 uncovered) were computed against the **23,530-row**
`data.json`. Adding 203 verses invalidated all of it; stream C re-ran alignment against the
current file and is complete.

---

## The marker discovery — this changes stream C

The `.txt` files carry **2,427 hand-annotated range and half-verse markers**, recording
exactly which Gita Press verses each Hindi paragraph covers.

| kanda | markers | | | fraction | range |
|---|---|---|---|---|---|
| Bala | 488 | | **total** | **1,297** | **1,130** |
| Yuddha | 443 | | | | |
| Aranya | 439 | | | | |
| Sundara | 383 | | | | |
| Ayodhya | 362 | | | | |
| Kishkindha | 312 | | | | |

Almost all sit on Hindi paragraph lines (2,174 stamp-form, 251 brace-form; only ~2 on
Sanskrit), confirming they annotate Hindi coverage.

### Notation and semantics

Two parallel notations exist — the native Devanagari stamps, and a brace overlay added
later through `auto_stamp_editor.html`:

| form | covers |
|---|---|
| `॥ १९-२०॥` | verses 19 and 20, complete |
| `॥ ३० १/२॥` | verse 30 complete, **plus line 1 of verse 31** |
| `॥ ३४-३५ १/२॥` | verses 34 and 35 complete, **plus line 1 of verse 36** |

**`१/२` always means the first line of the verse *after* the last one named.** It never
means half of the named verse. The spill is always exactly one line forward.

### Why this reshapes stream C

The aligner computes ragged joins statistically. These markers record them **by hand,
by someone reading both languages**. Kishkindha alone has 312 markers against the
aligner's 272 computed joins for the same kanda.

So the mapping decomposes cleanly:

- **Hindi paragraph → Gita Press verse span** — *known* from the markers, not inferred
- **Gita Press verse → `data.json` verse** — the only part needing computation

Compose the two for Hindi → `data.json`. Open decisions #2 and #3 shrink from "rule on
79 ambiguous joins" to "read what is already written down."

### The conversion rule — recorded in `marker_conversion_rule.md`

Stream D converts `॥ {sN}` → `॥N॥` and `॥ {hN}` → `॥N॥`, **absorbing the single
preceding danda-pair** and reusing it as the stamp's opening. It never prepends a
second. Every one of the 418 `{sN}` markers carries exactly one preceding `॥`, so a
`॥॥` before a marker is defective and collapses to one — never deleted.

### Anomalies — all resolved

15 defective or ambiguous markers were found and fixed. Backup of the pre-fix state:
`ramcharitdotin.pre_final_marker_fixes/` (186 files).

- stray danda inside the stamp ×3 · glued verse+half ×4 · `{S12}` typo ×1
- `॥॥` before `{sN}` ×2 — collapsed to one
- Bala 37 stray leading `॥` ×1 · Bala 29 missing dash · Kishkindha 4 empty stamp ·
  Aranya 64 stray digit

**One known artifact remains and needs no fix:** Aranya 75's `॥\n\n॥` is the Hindi
colophon's closing danda and the `॥अरण्यकाण्डं सम्पूर्णम्॥` kanda marker on the next
line, joined across a blank by the extraction regex. Not a real marker.

---

## Work streams, in dependency order

### A. Verse recovery — COMPLETE

- **A1 tail appends — done.** 153 verses.
- **A2 format normalisation — done.** 153 recovered rows plus 7 pre-existing.
- **A3 numbering-gap scan — done.** 12 genuine holes, 9 recoverable.
- **A4 mid-sarga insertions — done.** 50 verses, fractional numbering.

**Open decision #1 resolved:** `data.json` already held 32 rows with fractional shloka
numbers (`76.80.1`, `102.30.2`) plus a fractional sarga (Aranya 56.1). Fractional
insertion is the file's existing convention, so nothing was renumbered.

### B. Stamp-format standardisation in the `.txt` files — COMPLETE

Replace the `{sN}` / `{hN}` brace overlay with native `॥N॥` stamps, per
`marker_conversion_rule.md`. **Must precede stream C**, since the `.txt` files are the
migration's source.

Scope is larger than first thought: **48 distinct marker shapes**, including hyphen,
en-dash and em-dash variants, and spacing variants on both sides of the stamp.

1. Decide the target form. `॥ N॥` (leading space) is the majority at 8,567 + 495 range
   occurrences; `॥N॥` is 29,512. Pick one and normalise all shapes to it.
2. Range and fraction forms **must survive** — `॥ ३४-३५ १/२॥` carries information a
   plain `॥३५॥` destroys.
3. Re-validate with `parse_hindi_v4.py` against the current `hindi_*.json`. Any sarga
   whose coverage drops means a marker was load-bearing — restore and investigate.
4. `ramcharit.in/` is already backed up at `ramcharitdotin.pre_final_marker_fixes/`.

### C. Hindi migration into `data.json` — COMPLETE

Blocked on B. Once the `.txt` files are consistent:

1. **Build the Hindi coverage map from the 2,427 markers** — each Hindi paragraph to its
   Gita Press verse span, including forward spill. This replaces inferring ragged joins.
2. **Re-run alignment** against the 23,733-row `data.json` for the Gita Press →
   `data.json` half only.
3. Compose the two into Hindi → `data.json`.
4. Ragged-join rules, now needed only where markers are absent:
   - **GP splits one dj verse** — concatenate into the one row, space-joined.
   - **GP combines two dj verses** — full Hindi on the *first* row, a `notice` on the
     following row(s) pointing back.
5. Write Hindi into a `hindi` field on each row, sourced from the `.txt` files.
6. Simplify `index.html` to read `hindi` from the row; retire the JSON files.

**Until this lands, the 203 recovered verses show a blank Hindi tab.** Accepted — the
app is still being built.

### D. Split `data.json` by kanda — fetch on demand — NEXT

`data.json` is now ~31 MB and the app loads **all of it** before rendering anything.
That is a slow first paint on mobile, and it grows with every stream below: the
word-by-word backlog alone will add several MB.

**Do this before the word-by-word batch.** Splitting after that work means shipping a
~37 MB file in the meantime and re-splitting later.

Estimated per-kanda sizes at the pre-Hindi baseline (they are larger now, and Uttara
will roughly double once its word-by-word lands):

| kanda | rows | approx |
|---|--:|--:|
| Bala | 2,217 | 2.3 MB |
| Ayodhya | 4,263 | 4.3 MB |
| Aranya | 2,465 | 2.4 MB |
| Kishkindha | 2,445 | 2.6 MB |
| Sundara | 2,772 | 3.0 MB |
| Yuddha | 5,794 | 5.6 MB |
| Uttara | 3,574 | 1.8 MB |

**Steps:**

1. Emit `data_{1..7}.json`, one per kanda, preserving row order and every field. Keep
   the two intentionally out-of-order rows where they are (Uttara sarga 2, and the
   प्रक्षिप्त Aranya 56.1 at the end of its kanda).
2. Change `index.html` to fetch the kanda being read rather than the whole corpus, and
   to cache what it has already fetched so switching back is instant.
3. Consider a small `index.json` — kanda and sarga names with verse counts — so the
   navigation renders before any kanda file loads.
4. Verify: total rows across the seven files equals `data.json`; every kanda opens; a
   verse in each of the seven renders with all four columns.
5. Retire `data.json` from the repo **only after** the split is confirmed live.

**Secondary benefit:** pushes stop being 31 MB. Editing one kanda pushes 2–6 MB, and
git history stops growing by a full copy each time.

### E. English and word-by-word for the recovered verses

The 203 new rows need English prose and word-by-word. Same conventions as the
Kishkindha 78 and Yuddha 84 work — see `CONTEXT.md` §7.

### F. English backlog

- Non-Uttara: **97 verses** — Sundara 49, Ayodhya 15, Yuddha 16, Bala 12, Aranya 5.
- **Uttara: COMPLETE.** All 3,574 verses drafted and pushed.

Kishkindha's 78 are done and pushed.

### G. Word-by-word backlog

- Non-Uttara: **115 verses** (Yuddha 84's 14 done and pushed).
- Uttara: **3,574 verses**.

To run as a **single batch** to avoid repeated 24 MB uploads.

### H. Independent fixes — any time

1. **Duplicate-file sweep.** `hindi_4_16.json` was a byte-identical copy of
   `hindi_3_16.json` — Aranya's content served under Kishkindha, live and undetected,
   now fixed. Hash the first entry of all 549 files and look for further collisions.

### I. LAST STEP — push the tooling to git

**Do this when everything else is done.** Two folders exist and they hold different
things:

- **`vr-repo`** — a clone of GitHub. Disposable; `git clone` gets it back at any time.
- **`02ValmikiRamayana`** — the working folder. Holds material that exists **nowhere
  else**.

`ramcharitdotin/` is already in git and safe. What is **not** in git:

- the Python tooling — `parse_hindi_v4.py` (with its tuned `HINDI_PATTERNS` word list),
  `apply_english_patch.py`, `apply_w2w_patch.py`, `align_recension.py`,
  `build_coverage.py`, `restamp.py`, `strip_to_sanskrit.py`, and the rest
- `CONTEXT.md`, `PLAN.md`, `marker_conversion_rule.md`
- the generated reports — `hindi_coverage_map.json`, `alignment_map_*.json`,
  `hindi_migration_shortfall.json`, the marker inventories

The scripts matter most. Re-parsing a `.txt`, fixing a stamp or re-running alignment
after any future change is minutes with them and a rebuild without. `parse_hindi_v4.py`
carries a word list that took several rounds to tune.

```
cd ~/vr-repo
cp ~/02ValmikiRamayana/*.py .
cp ~/02ValmikiRamayana/*.md .
git add *.py *.md
git commit -m "Add project tooling and documentation"
git push
```

A few hundred KB. After this, `02ValmikiRamayana` becomes a working directory that can
be deleted whenever convenient — everything that matters lives in the repo. **No hurry;
keep both folders as long as you like.** The generated `.json` reports are optional,
being regenerable from the scripts, though slowly.

---

## Open decisions

| # | Decision | Status |
|---|---|---|
| 1 | Mid-sarga insertion numbering | **Resolved** — fractional, matching existing convention |
| 2 | GP-combines rule | Largely superseded by the markers; needed only where absent |
| 3 | GP-unmapped / dj-uncovered joins | Largely superseded by the markers |
| 4 | Normalise sanskritdocuments.org word-spacing? | Live — `kks16.txt` keeps its padded form |
| 5 | Target stamp form for stream B | **Resolved** — spacing is immaterial; the parser tolerates all forms, so pre-existing stamps were left as written |

---

## Completed

- **Uttara Kanda Hindi, sargas 1–111.** Restamped to the Gita Press division with
  per-batch review, translated, parsed to `hindi_7_*.json`.
- **Kishkindha English** — 78 gaps filled. Pushed.
- **Yuddha 84 word-by-word** — 14 verses, plus a Sanskrit correction at verse 22. Pushed.
- **Kishkindha 16 repaired** — was serving Aranya 16's Hindi. 39 verses translated and
  pushed.
- **Verse recovery** — 203 verses restored to `data.json`.
- **Marker inventory and cleanup** — 2,427 markers catalogued, 48 shapes, 15 anomalies
  fixed.

- **Uttara Kanda English — COMPLETE.** All 3,574 verses drafted from the Sanskrit and
  pushed, plus the colophon pass across all kandas.
- **Hindi migration — COMPLETE.** 22,955 rows carry a `hindi` field; `index.html` reads
  from the row. The original misalignment cannot recur.
- **`parseWordTable` regex widened** — 3,923 gloss pairs recovered across 498 sargas.
- **Brace-marker conversion and classifier close** — all `{sN}`/`{hN}` converted to
  native stamps; four documented `{hN}` exceptions remain by design.

---

## Method notes worth keeping

1. **`difflib.SequenceMatcher` needs `autojunk=False`.** The default heuristic corrupts
   similarity ratios on Devanagari.
2. **`data.json` stores AshuVj's combined verse blocks redundantly** on every shloka
   number they span. Reconstruct per-shloka Sanskrit by splitting `shloka_text` on its
   embedded `k.s.n` stamps. Took Kishkindha 29 from 0.50 to 0.95.
3. **Pair sargas by content, not number.** Ayodhya diverges from ~sarga 101, Yuddha from
   ~sarga 89 (131 dj sargas against 128 Gita Press). Number-pairing produced 5 false
   "missing verse" reports in Yuddha alone.
4. **Cut verses at the stamp *end*, not the stamp *start*.** Cutting at the start yields
   entries holding the tail of one verse plus the head of the next — 19 bad entries in
   Ayodhya 50 and Sundara 67.
5. **Validation test for any verse extraction: every entry's last line must end with a
   stamp.** One line of code, caught all 19.
6. **Hindi paragraphs can be misread as Sanskrit verses.** Reuse `hindi_score()` from
   `parse_hindi_v4.py`, but note it under-scores blocks that are almost all proper names.
   Combine with the structural test — Sanskrit verses are 2–3 short lines each ending
   ` ।`; Hindi is one long paragraph.
7. **Two danda characters exist and are not interchangeable.** U+0964 DANDA `।` doubled
   makes the `।।k.s.n।।` stamps in `data.json`; U+0965 DOUBLE DANDA `॥` is one character
   and is what the `.txt` files use. A regex for one silently misses the other.
8. **Enumerate marker shapes before writing any conversion regex.** A brace-only pattern
   found 70 markers; shape enumeration across both notations found 2,427. Normalise digit
   runs to a placeholder and count distinct shapes — it surfaces variants nobody
   anticipated.
9. **Truncating output at 80 characters hides defects.** The Bala 37 "empty stamp" was
   actually a stray danda before an existing `॥ १७ १/२ ॥`; applying the reported fix
   would have written a duplicate.
