Follow-up to the Kishkindha alignment pilot. New evidence, then a new task.

## Evidence

Kishkindha sarga 16's Sanskrit was sourced fresh from sanskritdocuments.org and has 39
verses. data.json has 38. Aligning them verse by verse:

  - sd 1..25   -> dj 1..25    clean 1:1 (ratios 0.71-0.98)
  - sd 26..28  -> dj 26,26,27 ragged; dj 28 never matched
  - sd 29..38  -> dj 29..38   clean 1:1
  - sd 39      -> NO MATCH    best ratio 0.24 against any dj verse

data.json simply stops at 38. The final verse is absent, not misnumbered. That is the
same signature as the 14 "tail does not close" cases your pilot already reported for
Kishkindha, and as the known-dropped final verses recorded in data_json_issues.md for
Uttara sargas 72, 74, 77 and 78.

Hypothesis: data.json systematically drops trailing verses of sargas. Unknown how many.

## Task: quantify the dropped-tail problem across all seven kandas

Do NOT modify data.json or any .txt file. Produce a report only.

1. For every sarga in every kanda, compare data.json's verse count and last-verse text
   against the Gita Press .txt files in ramcharit.in/. Reuse align_recension.py's
   normalisation and alignment; this is the tail-close check from the pilot, run
   everywhere rather than only on Kishkindha.

2. For each sarga classify the tail as one of:
   - CLOSES        last GP verse maps to last dj verse
   - DJ_SHORT      GP has trailing verse(s) with no dj counterpart (the suspected defect)
   - GP_SHORT      dj has trailing verse(s) with no GP counterpart
   - RAGGED        tails overlap but do not correspond cleanly
   - UNALIGNABLE   similarity too low to judge; report separately, do not guess

3. For DJ_SHORT, record how many verses are missing and quote the first few words of
   each absent verse, so they can be recovered.

4. Emit dropped_tails_report.md with:
   - a per-kanda summary table: sargas, and counts in each class
   - the full DJ_SHORT list: kanda, sarga, number of verses missing, opening words
   - the UNALIGNABLE list, which may hide further content defects like the sarga 16 one

5. Also check the opposite end. Does data.json ever drop the FIRST verse of a sarga, or
   verses mid-sarga where GP has no corresponding split? Report separately if found —
   the pilot's 37 "dj-uncovered" joins in Kishkindha suggest mid-sarga gaps exist too.

## Rules

- Report only. No writes to data.json, .txt files, or hindi_*.json.
- Do not fill anything in. Recovering missing verses is a separate decision.
- Where a sarga will not align, say so and move on. Sarga 16 taught us that low
  similarity can mean a content defect rather than a division difference, so treat
  UNALIGNABLE as "needs a human look", not as noise.
- Bala Kanda is expected to be the least consistent. Report it, but do not spend
  disproportionate effort forcing its alignments.

## When done

Report the headline: how many sargas across the whole text have DJ_SHORT tails, how many
verses that amounts to in total, whether it clusters by kanda, and whether any further
content defects like sarga 16 turned up. Then stop.
