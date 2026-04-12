#!/usr/bin/env python3
"""
Merge JLPT CSV files into cards_data.js.
- Skips words already in cards_data.js (matched by word OR reading).
- N5_800.csv: '中文' column → meaningEn (it's English), meaning = ''
- N4 CSVs: '中文' column → meaning (Chinese), meaningEn = ''
- ruby: if word == reading → word as-is; else "word|reading"
- N4_CSV_FILES: list of N4 CSV files to process
"""

import csv, re, os, shutil, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = r"C:\Users\Mo_Tsai\AppData\Local\Temp\japanese-flashcard-repo"
cards_path = os.path.join(BASE_DIR, 'cards_data.js')

# ── 1. Load existing words/readings from cards_data.js ───────────────────────
with open(cards_path, encoding='utf-8') as f:
    existing_js = f.read()

existing_words    = set(re.findall(r"word:\s*'([^']+)'", existing_js))
existing_readings = set(re.findall(r"reading:\s*'([^']+)'", existing_js))

print(f"Existing cards: words={len(existing_words)}, readings={len(existing_readings)}")

def js_esc(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")

def make_ruby(word, reading):
    """If word == reading (kana only), no pipe needed. Else word|reading."""
    if word == reading:
        return word
    return f"{word}|{reading}"

def already_exists(word, reading):
    return word in existing_words or reading in existing_readings

new_cards = []

# ── 2. Parse JLPT_N5_800.csv ─────────────────────────────────────────────────
n5_path = os.path.join(BASE_DIR, 'JLPT_N5_800.csv')
with open(n5_path, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        raw_word = row['單字'].strip()
        reading  = row['假名'].strip()
        meaning_en = row['中文'].strip()   # actually English
        level    = row.get('程度', 'N5').strip() or 'N5'

        # Take first form if "word1; word2"
        word = raw_word.split(';')[0].strip()
        if not word or not reading:
            continue
        if already_exists(word, reading):
            continue

        ruby = make_ruby(word, reading)
        card = (
            f"  {{ level: '{level}', word: '{js_esc(word)}', ruby: '{js_esc(ruby)}', "
            f"reading: '{js_esc(reading)}', type: '', meaning: '', "
            f"meaningEn: '{js_esc(meaning_en)}', sentence: '', sentenceMeaning: '', sentenceMeaningEn: '' }}"
        )
        new_cards.append(card)
        existing_words.add(word)
        existing_readings.add(reading)

print(f"New N5 cards to add: {len(new_cards)}")
n5_added = len(new_cards)

# ── 3. Parse N4 CSVs ─────────────────────────────────────────────────────────
n4_start = len(new_cards)
N4_CSV_FILES = ['JLPT_N4.csv', '20260330JLPT_N4.csv']
for n4_file in N4_CSV_FILES:
    n4_path = os.path.join(BASE_DIR, n4_file)
    if not os.path.exists(n4_path):
        print(f"  Skipping {n4_file} (not found)")
        continue
    print(f"  Processing {n4_file}...")
    with open(n4_path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            word    = row['單字'].strip()
            reading = row['假名'].strip()
            meaning = row['中文'].strip()   # Chinese

            if not word or not reading:
                continue
            # Skip if reading looks like kanji (not hiragana/katakana) — bad data
            if not re.search(r'[\u3040-\u30ff]', reading):
                print(f"  SKIP bad reading: {word} / {reading}")
                continue
            if already_exists(word, reading):
                continue

            ruby = make_ruby(word, reading)
            card = (
                f"  {{ level: 'N4', word: '{js_esc(word)}', ruby: '{js_esc(ruby)}', "
                f"reading: '{js_esc(reading)}', type: '', meaning: '{js_esc(meaning)}', "
                f"meaningEn: '', sentence: '', sentenceMeaning: '', sentenceMeaningEn: '' }}"
            )
            new_cards.append(card)
            existing_words.add(word)
            existing_readings.add(reading)

n4_added = len(new_cards) - n5_added
print(f"New N4 cards to add: {n4_added}")
print(f"Total new cards: {len(new_cards)}")

if not new_cards:
    print("Nothing to add.")
    exit(0)

# ── 4. Append to cards_data.js ────────────────────────────────────────────────
pos = existing_js.rfind('];')
if pos == -1:
    raise ValueError("No ]; found in cards_data.js")

before = existing_js[:pos].rstrip()
sep = ',\n' if not before.endswith(',') else '\n'
new_js = before + sep + ',\n'.join(new_cards) + '\n];\n'

with open(cards_path, 'w', encoding='utf-8') as f:
    f.write(new_js)

total = new_js.count("level:")
print(f"\ncards_data.js updated. Total cards now: {total}")

# ── 5. Copy to repo ───────────────────────────────────────────────────────────
shutil.copy2(cards_path, os.path.join(REPO_DIR, 'cards_data.js'))
print("Copied to repo.")
