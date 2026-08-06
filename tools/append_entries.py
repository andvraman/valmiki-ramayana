"""
Append new verse entries into data.json, skipping any that already exist.

Usage:
    python3 append_entries.py <new_entries.json> [data.json]

If data.json path is omitted, defaults to 'data.json' in the current folder.

A "duplicate" is any existing entry with the same (kanda, sarga, shloka).
Duplicates are skipped and reported, never overwritten -- if you need to
replace existing entries, fix them by hand or ask for a separate
"replace" script.
"""

import json
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 append_entries.py <new_entries.json> [data.json]")
        sys.exit(1)

    new_entries_path = sys.argv[1]
    data_path = sys.argv[2] if len(sys.argv) > 2 else 'data.json'

    with open(data_path, encoding='utf-8') as f:
        data = json.load(f)

    with open(new_entries_path, encoding='utf-8') as f:
        new_entries = json.load(f)

    existing_keys = {(e.get('kanda'), e.get('sarga'), e.get('shloka')) for e in data}

    to_add = []
    skipped = []
    for e in new_entries:
        key = (e.get('kanda'), e.get('sarga'), e.get('shloka'))
        if key in existing_keys:
            skipped.append(key)
        else:
            to_add.append(e)
            existing_keys.add(key)  # guard against duplicates within new_entries itself

    data.extend(to_add)

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Added {len(to_add)} new entries.")
    if skipped:
        print(f"Skipped {len(skipped)} entries already present (kanda, sarga, shloka):")
        for k in skipped:
            print(f"  {k}")
    print(f"data.json now has {len(data)} entries.")

if __name__ == '__main__':
    main()
