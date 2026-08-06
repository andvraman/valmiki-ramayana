#!/usr/bin/env python3
"""
patch_data_v2.py — Split Ayodhya Kanda Sarga 1 verse 50 into verses 50 + 51
in data.json. The AshuVj dataset combines these two Gita Press verses into one.

Run from the same folder as data.json:
    python3 patch_data_v2.py
"""
import json, shutil, os, sys

DATA_FILE = 'data.json'

if not os.path.exists(DATA_FILE):
    print(f"ERROR: {DATA_FILE} not found. Run from the repo root.")
    sys.exit(1)

shutil.copy(DATA_FILE, DATA_FILE + '.bak')
print(f"Backup saved: {DATA_FILE}.bak")

print("Loading data.json...")
with open(DATA_FILE, encoding='utf-8') as f:
    data = json.load(f)
print(f"Total entries: {len(data)}")

# ── Find the sarga 1 block ─────────────────────────────────────────
ak1 = [(i, e) for i, e in enumerate(data)
       if e.get('kanda') == 'Ayodhya Kanda' and e.get('sarga') == 1]
print(f"Ayodhya Kanda Sarga 1 entries: {len(ak1)}")

if len(ak1) == 51:
    print("Already 51 verses — no patch needed.")
    sys.exit(0)

# ── Find existing shloka 50 ────────────────────────────────────────
idx_50, entry_50 = next((i, e) for i, e in ak1 if e['shloka'] == 50)
print(f"\nExisting shloka 50 at data[] index {idx_50}:")
print(f"  shloka_text: {entry_50.get('shloka_text','')[:120]}")
print(f"  explanation: {entry_50.get('explanation','')[:120]}")

# ── Build the two replacement entries ─────────────────────────────
# Verse 50: अथ राजवितीर्णेषु...
verse_50 = dict(entry_50)
verse_50['shloka'] = 50
verse_50['shloka_text'] = (
    "अथ राजवितीर्णेषु विविधेष्वासनेषु च । "
    "राजानमेवाभिमुखा निषेदुर्नियता नृपाः ॥ ५० ॥"
)
verse_50['transliteration'] = (
    "atha rājavitīrṇeṣu vividheṣvāsaneṣu ca | "
    "rājānamevābhimukhā niṣedurṇiyatā nṛpāḥ || 50 ||"
)
verse_50['explanation'] = (
    "When the kings had been given the various seats by the king, "
    "the assembled monarchs sat facing King Dasharatha alone."
)
verse_50['translation'] = ''

# Verse 51: स लब्धमानैर्विनयान्वितैर्नृपैः...
verse_51 = dict(entry_50)   # copy structure from original entry
verse_51['shloka'] = 51
verse_51['shloka_text'] = (
    "स लब्धमानैर्विनयान्वितैर्नृपैः पुरालयैर्जानपदैश्च मानवैः । "
    "उपोपविष्टैर्नृपतिर्वृतो बभौ सहस्रचक्षुर्भगवानिवामरैः ॥ ५१ ॥"
)
verse_51['transliteration'] = (
    "sa labdhamānairvinayānvitairnṛpaiḥ purālayairjānapadaiśca mānavaiḥ | "
    "upopaviṣṭairnṛpatirvṛto babhau sahasracakṣurbhagavānivāmaraiḥ || 51 ||"
)
verse_51['explanation'] = (
    "Surrounded by the honoured and humble kings, city-dwellers and "
    "country folk seated around him, the king shone like the thousand-eyed "
    "Lord Indra surrounded by the gods."
)
verse_51['translation'] = ''

# ── Replace entry at idx_50 with the two new entries ──────────────
data[idx_50] = verse_50
data.insert(idx_50 + 1, verse_51)
print(f"\nReplaced shloka 50 with two entries at indices {idx_50} and {idx_50+1}")

# ── Verify ─────────────────────────────────────────────────────────
ak1_after = [e for e in data
             if e.get('kanda') == 'Ayodhya Kanda' and e.get('sarga') == 1]
shlokas_after = sorted(e['shloka'] for e in ak1_after)
print(f"Ayodhya Kanda Sarga 1 now has {len(ak1_after)} verses: {shlokas_after}")
assert len(ak1_after) == 51, "Expected 51!"
print(f"Total entries in data.json: {len(data)}")

# ── Save ───────────────────────────────────────────────────────────
print("\nSaving data.json...")
with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print("Done. data.json updated.")
print(f"Backup is at {DATA_FILE}.bak — delete once you've verified the app.")
