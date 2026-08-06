import json

with open('data.json', encoding='utf-8') as f:
    data = json.load(f)

with open('aranya_56_1_data_entries.json', encoding='utf-8') as f:
    new_entries = json.load(f)

data.extend(new_entries)

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"data.json now has {len(data)} entries")