# Hindi / English pairing drift — measurement

The concern: Hindi and English prose were drafted against Gita Press verse
divisions, while the Sanskrit in `data_*.json` uses a different pāda grouping.
Where the two disagree, a row's prose belongs to a neighbouring verse. Sargas 51
and 54 of the Uttara Kāṇḍa were confirmed by hand. Nobody had measured the rest.

**Headline: the drift is far less extensive than feared.** Three independent
checks across all seven kāṇḍas found confirmed drift confined to four sargas of
the Uttara Kāṇḍa. No systematic drift was found anywhere in kāṇḍas 1–6.

---

## Method

No `.txt` files were available, so detection had to work from signals internal to
the data. Three checks, each using a different anchor.

**Check 1 — gloss against Sanskrit.** A row's word-by-word gloss cites Devanagari
words that should occur in that row's own `shloka_text`. Score each row's gloss
words against the Sanskrit of rows N−2 … N+2; flag rows where a neighbour scores
materially better. Works on all seven kāṇḍas and all 23,487 glossed rows. This is
the most reliable of the three because the match is on identical strings.

**Check 2 — English against the gloss.** For the Uttara Kāṇḍa, the glosses were
produced in this project directly from each row's Sanskrit, so they are known to
be aligned. They therefore serve as a bridge: score each row's `explanation`
against the English halves of neighbouring rows' glosses. Reliable for Uttara
only — in kāṇḍas 1–6 the inherited glosses and the English come from the same
source and would drift together, so disagreement between them proves nothing.

**Check 3 — Hindi against Sanskrit.** Hindi retains Sanskrit proper nouns and
loanwords in Devanagari, so a stemmed bag-of-words score against neighbouring
verses' Sanskrit is possible. This check turned out to be **unreliable** — see
the caveat below.

---

## Results

### Check 1 — gloss alignment: 72 rows of 23,487

| kāṇḍa | flagged | where |
|---|---|---|
| 1 Bala | 10 | all in sarga 1 |
| 2 Ayodhya | 0 | — |
| 3 Aranya | 0 | — |
| 4 Kishkindha | 0 | — |
| 5 Sundara | 1 | sarga 61 |
| 6 Yuddha | 61 | scattered; no sarga above 4 rows |
| 7 Uttara | 0 | — |

0.3% of glossed rows. The gloss layer is essentially correctly aligned to the
Sanskrit throughout. Whatever drift exists is in the prose, not the glosses.

### Check 2 — English drift in Uttara: 14 rows, 3 sargas

| row | offset |
|---|---|
| 30.9 | +2 |
| 30.10, 30.11 | −1 |
| 48.15, 48.24 | −1 |
| 54.10, 54.12–54.19 | −1 |

All hand-verified as genuine. Sarga 54 is the previously known case and is the
largest single run: ten consecutive rows whose English renders the preceding
verse. Sarga 30 is not a uniform shift — row 9's English renders row 11's
Sanskrit while row 10's renders row 9's, which is the pāda-regrouping signature
rather than a simple offset. Sarga 48 is a half-verse offset across a boundary.

### Check 3 — Hindi: no systematic drift found, method unreliable

Row-level scoring flagged 194 rows of 20,617 (under 1%), but sarga-level
aggregation produced a false alarm: sargas 31–39 of the Uttara Kāṇḍa appeared as
a contiguous block shifted +1 or +2. **Hand-checking every real-Hindi row in that
block found all of them correctly aligned** — 31.1, 31.5, 31.9, 32.1, 32.5, 32.8,
34.1, 34.4, 34.11, 35.1, 36.13, 38.1, 38.6, 38.9, 38.14 all match their own
Sanskrit.

The cause is the continuous-dialogue Hindi style, which is a deliberate feature of
this edition: one Hindi paragraph covers several verses, so its vocabulary
overlaps the Sanskrit of neighbouring verses as much as its own. In sargas where
most rows carry the "shown with verse N" placeholder, only 5–17 rows have real
Hindi, and that is a small enough sample for the spillover to tip the vote.

**Conclusion: this check cannot certify Hindi alignment either way.** It found no
evidence of systematic Hindi drift, but it is not sensitive enough for that to
count as evidence of absence. The known partial drift in sarga 51 — where the
`51.4.1` / `51.5` duplicate pushes later rows out of step — registered only as a
split vote (6 rows at −1, 9 at 0, 7 at +1), which is exactly what partial drift
inside a sarga looks like and also what noise looks like.

---

## What this means for the work

The pairing problem is **not systemic**. It does not require re-aligning the
kāṇḍa or re-keying the translations. It is a short list of specific rows.

Confirmed and actionable:

- **Uttara 54.10–54.19** — English shifted −1, ten rows
- **Uttara 30.9–30.11** — English misaligned, pāda-regrouping
- **Uttara 48.15, 48.24** — English shifted −1
- **Uttara 51** — Hindi partially shifted from verse 5 onward, caused by the
  `51.4.1` / `51.5` duplicate row; fixing the duplicate may resolve it
- **72 rows** where the gloss matches a neighbour better, mostly Yuddha

Not established:

- Whether Hindi drifts anywhere beyond sarga 51. The only way to settle this is a
  direct diff against the Gita Press `.txt` files, the way the Sanskrit alignment
  audit was done. That is the one remaining measurement worth taking, and it
  needs the `.txt` files rather than cleverness with the data alone.

---

## Glossary

| term | meaning |
|---|---|
| **drift** | translation sitting one or more rows away from the Sanskrit it belongs to |
| **offset** | how many rows away, signed: −1 means the prose belongs to the previous verse |
| **pāda** | a quarter-verse; two pādas per printed line |
| **pāda regrouping** | the same text divided into verses differently by two editions, so row boundaries do not correspond |
| **gloss** | the word-by-word `translation` field, rendered as a two-column table |
| **placeholder** | the "अनुवाद श्लोक N के साथ दिखाया गया है" notice on rows whose Hindi is carried by a neighbour |
| **continuous-dialogue style** | this edition's Hindi convention of keeping a speech as one paragraph across several verses |
| **stemmed bag-of-words** | comparison method: reduce words to their first few characters, compare as unordered sets |
| **Gita Press** | the edition whose verse divisions the `.txt` files follow |
