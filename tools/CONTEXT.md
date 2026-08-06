# Valmiki Ramayana study app — working context

App: https://andvraman.github.io/valmiki-ramayana · Repo: `andvraman/valmiki-ramayana`

A verse-by-verse Sanskrit study PWA. Each verse shows the Sanskrit, with tabs toggling
Hindi and English meaning, plus an English word-by-word table.

---

## 1. Data model

**`data.json`** — one JSON array, 23,530 objects, ~24 MB, loaded once at startup.

| field | contents |
|---|---|
| `kanda`, `sarga`, `shloka` | verse identity |
| `shloka_text` | Sanskrit |
| `transliteration` | IAST |
| `translation` | **English word-by-word** (misleading field name) |
| `explanation` | **English prose translation** |
| `comments` | notes |

**`hindi_{kanda}_{sarga}.json`** — 549 files, `[{shloka, hindi, notice}]`, fetched on
demand and joined to `data.json` **by verse number**. These live **in the GitHub repo
only, not in the local folder**. They are *derived* artefacts — `parse_hindi_v4.py`
generates them from the `.txt` files — and are slated for retirement (§3). Nothing in
the alignment work needs them: the mapping is computed Sanskrit-against-Sanskrit, and
when the Hindi is migrated it should be sourced from the `.txt` files, which are one
layer closer to the reviewed text and cannot disagree with the boundaries the mapping
was computed against.

**The `.txt` files in `ramcharit.in/` are the source of truth for Hindi.**

**`.txt` source files** — ramcharit.in format (Sanskrit couplets + Hindi paragraph,
`॥N॥` stamps), covering **every kanda and every sarga**. These carry *both* the Gita
Press Sanskrit and the Hindi, which makes them the key to the alignment work below.
Bala Kanda early sargas are less consistent — they predate the `auto_stamp_editor.html`
tooling.

### Folder layout

```
02ValmikiRamayana/            <- project root (Mac); index.html, data.json,
                                 the .py tools.  NOTE: hindi_*.json are NOT here —
                                 they exist only in the GitHub repo
└── ramcharit.in/             <- ALL the .txt source files (Sanskrit + Hindi)
```

### `.txt` naming convention

`{prefix}{sarga}.txt` for a single sarga, or `{prefix}{first}-{last}.txt` for a batch —
e.g. `bks41-66.txt`, `sks30-49.txt`, `uks40-49.txt`.

| prefix | kanda | | prefix | kanda |
|---|---|---|---|---|
| `bks` | 1 Bala | | `sks` | 5 Sundara |
| `aks` | 2 Ayodhya | | `yks` | 6 Yuddha |
| `ars` | 3 Aranya | | `uks` | 7 Uttara |
| `kks` | 4 Kishkindha | | | |

Note `aks` for Ayodhya, not `ays`.

**The filename range is an integrity check.** A file named `bks41-66.txt` should contain
exactly sargas 41–66. Parse the range from the name, count the sarga headings inside,
and flag any mismatch — a batch file missing a sarga would otherwise pass unnoticed.

**Only final edited files are present** — no intermediates, no `_v2`/`_v3`/`review`
layers. Any file in `ramcharit.in/` is the current text for its sargas.

### Provenance and attribution

- `data.json` Sanskrit, word-by-word and English prose derive from the **AshuVj**
  dataset (MIT licensed as a compilation), which traces to **Desiraju Hanumanta Rao's**
  work at valmikiramayan.net and **IIT Kanpur**. To be acknowledged in the app.
- Hindi derives from **ramcharit.in**, following the **Gita Press** verse division.
- **New material written for the gaps is original work composed from the Sanskrit
  itself**, not sourced or reworded from the Desiraju translation. Only the *format*
  is matched (Devanagari word, space, English gloss, comma-separated, ordered by
  construal). Expect new entries to read slightly differently from their neighbours in
  connective phrasing; that is intentional and correct.

---

## 2. THE ALIGNMENT PROBLEM (current priority)

**`data.json` and the Hindi files follow two different recensions with different verse
divisions.** The app joins them by verse number. Wherever the divisions diverge, the
numbering drifts and the Hindi shown against a verse belongs to a different verse.

Because the UI keeps the Sanskrit on screen while Hindi toggles against it, every
misaligned verse is *visibly* wrong.

### Evidence

Kishkindha sarga 1 — correct through verse 40, then:

| verse | Sanskrit (`data.json`) | Hindi shown |
|---|---|---|
| 40 | `मयूरस्य वने नूनं` | ✓ correct |
| 41 | `मम त्वयं विना वासः` | **blank** |
| 42 | `मामप्येवं विशालाक्षी` | translation of 41 |
| 43 | `पश्य लक्ष्मण पुष्पाणि` | translation of 42 |
| 44 | `रुचिराण्यपि पुष्पाणि` | translation of 43 |

Blank Hindi entries mark the shift points. Sampled counts:

| file | Hindi entries | `data.json` verses | blanks |
|---|---|---|---|
| `hindi_4_1` | 130 | 130 | 4 (41, 81, 99, 113) |
| `hindi_4_2` | 29 | 29 | 1 |
| `hindi_5_1` | 200 | **201** | 16 |
| `hindi_1_1` | 100 | 100 | 16 |

Uttara Kanda is the widest divergence: **70 of 72 sargas (40–111) differ in verse
count**; 1,798 verses in `data.json` against 1,722 in the restamped Gita Press text.

### What is NOT affected

Sanskrit, word-by-word and English all live on the **same `data.json` row**, so they
cannot drift. Verified by alignment test — each row's gloss scores 0.57–0.82 against
its own verse and 0.05–0.12 against either neighbour, a five- to tenfold margin, across
all six kandas. **Only the Hindi join is broken.**

### The mapping is computable

Both sides carry Sanskrit, so the two recensions can be aligned automatically by text
matching. Demonstrated on Uttara sarga 40: character-level similarity 0.917, mapping
falls out cleanly —

```
our 5, 6  -> data.json 5      (Gita Press splits what AshuVj combines)
our 8     -> data.json 6, 7   (Gita Press combines what AshuVj splits)
rest      -> 1:1
```

It is **not** 1:1, so ragged joins need explicit handling (see §3).

---

## 3. Agreed plan

### Canonical Sanskrit

- **Six kandas (Bala…Yuddha): AshuVj stays canonical.** The word-by-word and English
  are already locked to those rows — 238,753 gloss pairs. Re-keying would mean
  splitting word-level glosses across re-divided verses. Map Hindi *onto* AshuVj
  instead and leave everything else untouched.
- **Uttara: switch to the Gita Press restamped text.** `data.json`'s Uttara rows hold
  Sanskrit and nothing else — no English, no glosses — so replacing that Sanskrit costs
  nothing. Sanskrit and Hindi then already agree, and English/glosses written later land
  on the same structure. It is also the text reviewed verse by verse.

Each kanda ends up internally consistent, which is all the display requires.

### Target structure

Write the Hindi into a **`hindi` field on each `data.json` row**, simplify the app to
read it from there, and retire the 549 `hindi_*.json` files. Adds roughly 4 MB to a
24 MB file — not duplication. Once done all four columns sit on one row and cannot
drift again.

### Ragged join rules — NEED DECISION per case

1. **1:1** — majority. Write the Hindi into the row.
2. **Gita Press splits one AshuVj verse in two** — two Hindi paragraphs, one row.
   Concatenate.
3. **Gita Press combines two AshuVj verses** — one paragraph, two rows. Either repeat
   on both, or place on the first and mark the second a continuation. `parse_hindi_v4.py`
   already has `combined_from`/`combined_to`, and the schema has `notice`.
4. **Tail does not close** — e.g. Uttara 40: our verse 31 maps to `data.json` 29 while
   `data.json` has 30. Every sarga needs this check. **Not safe to automate away.**

### Sequence

1. **Pilot: Kishkindha** (67 sargas). Where the bug surfaced, English recently
   completed, big enough to be representative.
2. Remaining kandas once ragged-join handling is settled.
3. **Bala last** — early sargas predate the editor and showed the worst blank ratio
   (16 blanks in 100 verses).

---

## 4. Known bugs and anomalies

**`parseWordTable()` in `index.html` silently discards 3.9% of all glosses.** The regex
`^([\u0900-\u097F\u0964\u0965:*\s-]+?)\s+([a-zA-Z].{2,})$` requires the English gloss to
be **3+ characters**, so two-letter glosses (`he`, `it`, `by`, `to`) never render.
**9,277 pairs across 534 sargas** are affected; 4,040 are the short-gloss case, the rest
fail for other reasons. Widening `.{2,}` to `.*` recovers most of them — one character.

**Uttara 40 tail does not close** against `data.json` (see §3.4).

**Recurring `data.json` issues** — combined entries where two verses share one
`shloka_text` (e.g. Kishkindha 4.9/4.10, 17.16/17.17); colophon lines becoming spurious
verses; stray Devanagari-range characters used as spaces (U+093A found and fixed in
Uttara 60.18 and 85.14).

---

## 5. Completed

- **Uttara Kanda Hindi: sargas 1–111 complete.** Sargas 40–111 restamped to the Gita
  Press division with per-batch review, translated, parsed to `hindi_7_*.json`.
- **Kishkindha English: 78 gaps filled** — the kanda now has complete English coverage.
- **Yuddha 84 word-by-word: 14 verses**, plus Sanskrit correction `बाणीम्` → `वज्रं`
  (verse 22, Gita Press reading).

## 6. Outstanding backlog

| task | scope |
|---|---|
| English gaps, non-Uttara | 97 verses — Sundara 49, Ayodhya 15, Yuddha 16, Bala 12, Aranya 5 |
| Uttara Kanda English | 3,574 verses, 111 sargas |
| All word-by-word, one batch | 115 non-Uttara + 3,574 Uttara |

Word-by-word to be done in a **single batch** to avoid repeated 24 MB uploads. Note git
retains every version, so each `data.json` push adds ~24 MB to repo history permanently.

---

## 7. Tools

| file | purpose |
|---|---|
| `parse_hindi_v4.py` | canonical validator/parser; `.txt` → `hindi_{kanda}_{sarga}.json` |
| `auto_stamp_editor.html` | browser editor for verse-stamp fixes before parsing |
| `apply_english_patch.py` | merges an English patch into `data.json`; fills blanks only, backs up first |
| `apply_w2w_patch.py` | same for word-by-word, plus targeted Sanskrit corrections |
| `strip_to_sanskrit.py` | strips English/commentary from sanskritdocuments.org downloads |

### Conventions for new content

- **Hindi**: essential-meaning flowing prose, ramcharit.in style; Sanskrit proper names
  and epithets preserved; continuous dialogue kept as one quote across verses.
- **English prose**: plain past-tense narrative; speech in single quotes with vocatives;
  names in the dataset's undiacriticked romanisation (Rama, Laksmana, Sita, Sugriva).
- **Word-by-word**: Devanagari word, space, English gloss, comma-separated; pausal forms
  cited rather than the verse's sandhi (`दुराधर्षः` where the verse reads `दुराधर्षो`);
  compounds split; ordered by construal. **Avoid 1–2 character glosses** until the
  parser regex is widened.
