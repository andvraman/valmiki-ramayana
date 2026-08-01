# Yuddha Kanda 72–128 Sanskrit Update — Consolidated Flags
*Generated 18 Jul 2026. Companion to the updated data.json (Gita Press text applied to sargas 72–131).*

## 1. Sarga numbering map (Gita Press ↔ data.json)

Gita Press merges three pairs of the source's sargas. Established by content matching, verse 1 of every sarga verified:

| Gita Press (your files) | data.json |
|---|---|
| 72–87 | 72–87 (same) |
| 88 (77 verses) | 88 (verses 1–36) + 89 (verses 1–41) |
| 89–101 | 90–102 (+1) |
| 102 (70 verses) | 103 + 104 (split falls mid-verse 39) |
| 103–106 | 105–108 (+2) |
| 107 (67 verses) | 109 + 110 (split near verse 29, half-verse shift) |
| 108–128 | 111–131 (+3) |

This fully explains data.json's 131 sargas vs Gita Press's 128.

## 2. Final verses missing from data.json (dropped-verse pattern)

Your files contain these; data.json has no entries for them. Sanskrit is preserved in the extracts zip for future append work (would need translation fields via append_entries.py):

- One final verse missing in each: GP 73, 74, 76, 77, 78, 79, 80, 82, 83, 85, 86, 87, 92, 93, 94, 96, 97, 98, 99 → and later GP 103–106, 108–110, 112, 114–116, 118–128 (mapped dj sargas accordingly)
- Two or more missing: GP 72 (18–19), GP 91 (28–29), GP 124 (22–23 → dj 127), GP 127 (62–64 → dj 130)

## 3. Large gaps in data.json (multiple missing verses)

| data.json sarga | Missing verses | Available in your file |
|---|---|---|
| 84 | 11–23 (13 verses) | GP 84 |
| 96 | 44–54 (11 verses) | GP 95 |
| 101 | 47–62 (16 verses) | GP 100 |
| 102 | 49–56 (8 verses) | GP 101 |

## 4. data.json-only verses (not in Gita Press)

Left untouched: 75.70, 88.78–79, 91.95–96, 114.125. These are source-recension extras.

## 5. Duplicate content: data.json 88.37–79 vs sarga 89

The verses appended to sarga 88 earlier (English-gap fill) are the same content as data.json's sarga 89 (source numbering). The app currently shows this stretch twice. Decision needed: delete entries 88.37–79, or leave. (Sarga 89's Sanskrit has been updated from your yks88 either way.)

## 6. Possible typo in yks88

Verse 37: your file reads ततः श्रान्तः दाशरथिः सन्धाय...; the source text reads ततः शरान् ("arrows", object of सन्धाय). श्रान्तः ("tired") may be a slip — worth a glance. The update used your text as given.

## 7. Entries with variant/partially resolved segments (352)

Where data.json's reading differs from Gita Press (recension variants), matching segments were replaced with your text; genuinely variant segments got spacing-only correction or were left as-is. Full list in update_flags.json (kept aside); heaviest sargas: dj 114 (18), dj 131 (17), dj 93 (17), dj 89 (15), dj 100 (15), dj 129 (13), dj 116 (13).

## 8. Pre-existing data.json defects observed (not caused by this update)

- 47 entries in 72–131 have no verse stamp at all (e.g. 78.7, 90.15, 98.17)
- Some entries carry wrong-kanda stamps (e.g. "1.107.21" instead of 6.107.21)
- Duplicated bundled entries persist (e.g. 73.10/11/12 hold identical multi-verse text; 75.68/69; 131.84/85) — the known data_yuddha_uttara dedup issue. Sanskrit within them is now corrected, but the duplication itself remains.

## 9. Notes on style

- Sargas 72–131 now use your files' word-split (पदच्छेद) style; sargas 1–71 remain in sandhi-joined style from the earlier spacing fix.
- A few of your files (esp. yks73–76) keep long compounds joined; those entries may still trip crude "unspaced" heuristics but are faithful to your checked text.
- yks120–124 files use pipe-style stamps and glossaries; both handled. Combined-verse stamps (e.g. ६-१२४-५, ६) preserved under the first verse number in the extracts.

## Glossary

- **GP** — Gita Press Gorakhpur edition (your hard copy and files' numbering)
- **dj** — data.json (the app's verse database, source-recension numbering)
- **Stamp** — the verse locator at the end of each shloka, e.g. ।।6.72.1।।
- **Sarga** — chapter; **Kanda** — book of the Ramayana
- **पदच्छेद (padachchheda)** — word-split style, sandhi dissolved for readability
- **Recension** — textual lineage of an edition; GP and the app's source differ slightly in verse readings and sarga divisions
- **append_entries.py** — your script for adding new entries to data.json
