"""
Fix a single OCR typo in Yuddha Kanda sarga 88, verse 37's shloka_text.

Usage:
    python3 fix_yks88_v37_typo.py [data.json]
"""

import json
import sys

def main():
    data_path = sys.argv[1] if len(sys.argv) > 1 else 'data.json'

    with open(data_path, encoding='utf-8') as f:
        data = json.load(f)

    old = "बहूनवष्^इजन्तौ"
    new = "बहूनवसृजन्तौ"

    fixed = 0
    for e in data:
        if e.get('kanda') == 'Yuddha Kanda' and e.get('sarga') == 88 and e.get('shloka') == 37:
            if old in e.get('shloka_text', ''):
                e['shloka_text'] = e['shloka_text'].replace(old, new)
                fixed += 1

    if fixed == 0:
        print("No matching text found — nothing changed. Check the entry manually.")
        return

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Fixed {fixed} entry(ies).")

if __name__ == '__main__':
    main()
