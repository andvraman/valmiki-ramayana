# Marker conversion rule — the brace-marker conversion

**Rule:** The brace-marker conversion turns editor markers into embedded stamps by
**absorbing the single preceding danda-pair**, not by emitting a second one:

```
॥ {sN}  →  ॥N॥
॥ {hN}  →  ॥N॥
```

The `॥` that sits immediately before a `{sN}`/`{hN}` marker is the **opening
danda-pair of the stamp** — the conversion reuses it and appends the number + closing
`॥`. It does **not** prepend a fresh `॥`.

**Consequence for the source `.txt`:** every one of the ~418 `{sN}` markers
carries exactly one preceding `॥` (e.g. `निवेशनात्॥ {s6}`, `शीतोदका शिवा॥ {s6}`).
That single danda is correct and required. A marker preceded by `॥॥` (two pairs)
is therefore defective — one pair is spurious and must be **collapsed to one**
`॥`, never deleted outright (deleting would strip the opening danda the stamp
needs). Fixed under this rule: Ayodhyā 28 (`सुखम्॥॥ {s3}` → `सुखम्॥ {s3}`) and
Kiṣkindhā 1 (`समाकुला॥॥ {s7}` → `समाकुला॥ {s7}`).

## Permanent constraint — never convert a marker on an already-stamped line

**Any marker-to-stamp conversion pass MUST skip a `{sN}` or `{hN}` marker whose
line already ends in a full `॥N॥` stamp.** Such a marker is not an unconverted
leftover — it is a **deliberate classifier exception**, present *because* the
line is already stamped and the parser still needs the explicit S/H override to
class the block correctly. Converting it would emit a second stamp (`॥N॥ ॥N॥`)
or, under the danda-absorbing rule above, silently collapse the two and delete
the override the block depends on.

The distinction is mechanical, so the guard is mechanical:

- **Convertible marker** — the marker supplies the number; its line ends in a
  bare danda-pair with no digits (`निवेशनात्॥ {s6}`). Absorb the `॥`, emit `॥N॥`.
- **Exception marker — skip** — the line already ends in a complete `॥N॥`
  (digits between the dandas) before the marker (`…श्रीराम को भेजे॥३॥ {h3}`).
  Leave both the stamp and the marker exactly as they are.

Guard test (apply per marker before converting): if the text immediately
preceding the `{sN}`/`{hN}` matches a full stamp `[।॥]\s*[०-९…][।॥]` (i.e.
`STAMP_RE` already fires there), do not convert — skip it. Only when the
preceding token is a bare `॥`/`।` with no interior digits is the marker eligible.

This is a standing rule for **all** future conversion passes, not a one-off note
about the current exceptions. As of the brace-marker conversion's completion the only markers in the
corpus that trip it are the four `{hN}` classifier exceptions recorded below, but
the guard must hold for any marker added later under the same rationale.

## Stamp spacing — immaterial

The parser tolerates `॥N॥`, `॥ N॥` and `॥ N ॥` equally (`STAMP_RE`'s inner
class `[\s०-९\-–½/]` allows interior whitespace). **Do not mass-normalise
existing native stamps** — leave every pre-existing `॥…॥` exactly as written.

When *converting* a `{sN}`/`{hN}` marker, emit `॥N॥` **without a leading space**
(the absorbed danda-pair supplies the opening; no space is added after it).
This applies only to newly emitted stamps; it is not a licence to reflow the
spacing of stamps already in the source.

## `hindi_score()` word list — brace-marker conversion follow-up

The brace-marker conversion turned every `{sN}`/`{hN}` marker into a native stamp, removing the
explicit `S`/`H` classification override. Block classification now rests entirely
on `looks_like_sanskrit()` → `hindi_score()`. The word list in `HINDI_PATTERNS`
was re-tuned accordingly:

- **Removed** (valid Sanskrit words that were mis-scoring ślokas as Hindi):
  `को` `का` `के` `पर` — कः→को/का "who", केचित्→"के", परः→पर "other". Removing
  them fixed 6 known regressions and correctly re-classified ~102 more ślokas.
- **Added** (Hindi grammatical forms with no Sanskrit homograph):
  `तक मैं इन अब सभी तीनों मेरे रहे वाले बारंबार देकर पहुँचा हुई उस तब ऐसा कोई उठे सुनकर सुनाकर`.
  (`और गये चले लगे हुआ हुए` were already present.)

### Rejected candidates (considered, not added)
- **`वह` / `वे`** — `वह` is also the Sanskrit root वह् (to carry / to flow) and
  appears inflected across the corpus; `वे` is uncertain. Sanskrit homograph risk.
- **`इस`** — flips 8 Sanskrit colophons (`इत्याचे …सर्गः॥N॥ इस प्रकार…`) to Hindi;
  redundant anyway (`तक`+`मैं` cover the one Hindi block it would have saved).
- **`का` `के` `को` `पर`** — removed above as ambiguous Sanskrit words.
- **bare `कर` as a suffix** — Sanskrit has दिनकर, भयंकर, प्रियंकर.
- **`प्रकार`** — Sanskrit word.

### Residue — root cause (a) fixed by the trailing-boundary change
Dropping को/का/के/पर promoted ~17 short Hindi blocks (all lines <90; long
paragraphs are Hindi regardless of score) to Sanskrit. The added words rescued
10; a residue of short Hindi blocks glued to their stamp remained.

**Trailing-boundary fix.** `HINDI_PATTERNS`' two word boundaries disagreed about
whether a danda counts as punctuation: the leading `(?<![^\s।॥,।])` allows a
danda before the word, but the trailing `(?=[^ऀ-ॿ]|$)` did not — ॥ (U+0965)
and । (U+0964) sit **inside** the Devanagari block, so a word glued to its stamp
(`भेजे॥`, `चले॥`, `लगे॥`) failed the lookahead. The trailing boundary is now
`(?=[^ऀ-ॿ]|[।॥]|$)`, bringing it into line with the leading one.

Verified across the full corpus (`ramcharitdotin/*.txt`), both directions:
- **Direction A (superset):** every block's new score ≥ its old score — **0
  matches lost**. The change only ever adds matches.
- **Direction B (no bad flip):** exactly **5** stamped Sanskrit-classified
  blocks cross 0→≥1 and re-classify as Hindi, and **all 5 are genuine Hindi
  prose** — `bks1` s1 v23 (`…दे दिया॥`), `uks100-111` s100 v24 (`…आगे-आगे चले॥`),
  `uks26` s26 v57 (`…हो उठे। ॥`), `uks27` s27 v1 (`…जा पहुँचा। ॥`), `yks40-71`
  s43 v14 (`…लोहा लेने लगे॥`). **No genuine Sanskrit block flips to Hindi.**

### Residue — re-inserted `{hN}` markers (deliberate exceptions)
Four blocks remain that are genuinely Hindi translations but score 0 and cannot
be rescued by any boundary tweak, so the parser's `is_skt` branch mistakes each
for a *continuation* Sanskrit śloka (it has a stamp + short lines) and the verse
loses its translation. These carry an explicit `{hN}` marker in the source
`.txt`; `get_marker()`'s H-branch fires before the `looks_like_sanskrit()`
misread, so the verse recovers. Recorded here as intentional, not missed:

| block | verse | marker | why the word list can't reach it |
|---|---|---|---|
| `uks100-111.txt` s100 | 3 | `{h3}` | only cue is `भेजे॥` — `भेजे` is not in the list and `को` is deliberately excluded (Sanskrit homograph). |
| `uks40-49.txt` s40 | 6 | `{h6}` | cues are `देखते रहना॥` (both absent) and `को` (excluded). Sibling v3 has की+से, scores 2, needs no marker. |
| `uks50-59.txt` s51 | 20 | `{h20}` | cues are the future forms `भोगेंगे`/`रहेंगे॥` (both absent), plus `के`/`वे` (excluded / rejected as ambiguous). |
| `yks124.txt` s124 | 11 | `{h11}` | **the clearest case** — no Hindi cue at all, only the genitive `का` (excluded). Unrecoverable by any word list. |

The boundary change rescued `yks40-71` s43 and the several `…॥`/`…। ॥` cases
above, so they need **no** marker. `bks9` has no residue — every score-0 block
there is genuine Sanskrit (its Hindi translations score high and classify
correctly). These four markers do not disturb the native `॥N॥` stamps, which
stay for display; `clean()` strips both marker and stamp from the stored text.

**Direction of the flip matters:** all four blocks are Hindi mis-read as
Sanskrit, so the marker is `{hN}` (Hindi with explicit span). `{sN}` would be
wrong — it marks a *Sanskrit* block that then pairs with the next block for its
Hindi, the opposite failure. No `{sN}` re-insertion was warranted.

Impact remains bounded: `hindi_score()`'s only consumer is `parse_hindi_v4.py`,
which generates the `hindi_*.json` files being retired by the Hindi migration
into `data.json`.

