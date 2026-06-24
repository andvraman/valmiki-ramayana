# Valmiki Ramayana Reader — Project Context

## App
Single-file web app `index.html` hosted at **https://andvraman.github.io/valmiki-ramayana/**  
GitHub repo: **andvraman/valmiki-ramayana**  
Stack: vanilla HTML/JS, no build step, GitHub Pages.

## Data sources
| File | Purpose |
|---|---|
| `data.json` | AshuVj dataset — Sanskrit, IAST, English word-by-word, English prose. ~23,400 entries, MIT licence. Loaded once at startup. |
| `hindi_1_N.json` | Per-sarga Hindi translations parsed from ramcharit.in (Gita Press). One file per sarga, fetched on demand. |

## Hindi JSON format
```json
{"shloka": 5, "hindi": "translation text", "notice": null}
{"shloka": 19, "hindi": "", "notice": "श्लोक १९ से २० का अनुवाद सम्मिलित है। अनुवाद श्लोक २० के साथ दिखाया जाएगा।", "combined_from": 19, "combined_to": 20}
{"shloka": 20, "hindi": "combined translation", "notice": null, "combined_from": 19, "combined_to": 20}
```

## Parser — parse_hindi.py
Converts ramcharit.in Reader Mode `.txt` files → `hindi_K_S.json`.  
**Markers** (added manually where stamps missing):
- `{S5}` end of Sanskrit line — verse 5
- `{H5}` end of Hindi line — verse 5  
- `{H5-6}` or `{H5-6 1/2}` for combined/half-verse spans
- Typo detector flags `{H117}` style errors (warns, skips, does not parse)

**Stamp formats handled:** `॥N॥` standard · `N॥` trailing (no leading danda) · `॥N १/२॥` half-verse · `॥N-M॥` range  
**Multi-sarga files:** auto-split on `.*?सर्गः\s*\((?:सर्ग\s+)?(\d+)\s*\)` title lines  
**Post-processing:** `validate_output()` detects and corrects wrong combined_from spans

## Source file workflow
1. Open ramcharit.in sarga page in Safari → `Cmd+Shift+R` (Reader Mode) → `Cmd+A` `Cmd+C` → paste to `bks{N}.txt`
2. Add `{S5}` / `{H5}` markers where stamps are missing
3. Upload `.txt` file(s) here → get back `hindi_1_N.json` ZIP
4. Upload JSON files to GitHub repo root

## Bala Kanda status
All 77 sargas complete and stable. Hindi JSONs: `hindi_1_1.json` through `hindi_1_77.json`.  
Next: Ayodhya Kanda (119 sargas) — use `aks{N}.txt` naming.

## Known data.json issues
AshuVj dataset has duplicate `shloka_text` for consecutive verses where translations are combined (~432 sargas affected across all kandas). `index.html` detects this at render time and shows a Devanagari notice instead of repeating Sanskrit. Sarga 74 was manually corrected in `data.json`.

## Key conventions
- Verse numbers: Devanagari throughout UI, Arabic in JSON `shloka` field
- Hindi lookup uses `v.shloka` from `data.json` (not array index) to avoid misalignment
- CORS proxy not used — all content served from same GitHub Pages origin
- No build tools — edit `index.html` directly, upload to GitHub
