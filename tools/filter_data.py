import json

# Load the full file
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Keep only Yuddha Kanda and Uttara Kanda entries
kandas_wanted = {'Yuddha Kanda', 'Uttara Kanda'}
filtered = [entry for entry in data if entry.get('kanda') in kandas_wanted]

# Save the smaller file
with open('data_yuddha_uttara.json', 'w', encoding='utf-8') as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)

print(f"Kept {len(filtered)} of {len(data)} entries")
print("Saved as data_yuddha_uttara.json")