#!/usr/bin/env python3
"""
Generate example sentences for cards that have empty sentence fields.
Uses Claude API to generate JLPT N4-level sentences with ruby markup.
"""

import re, os, json, time, sys
sys.stdout.reconfigure(encoding='utf-8')
import anthropic

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = r"C:\Users\Mo_Tsai\AppData\Local\Temp\japanese-flashcard-repo"
cards_path = os.path.join(BASE_DIR, 'cards_data.js')

# ── Load cards ────────────────────────────────────────────────────────────────
with open(cards_path, encoding='utf-8') as f:
    js = f.read()

# Extract all card blocks
card_blocks = re.findall(r'\{[^{}]+\}', js, re.DOTALL)

def extract_field(block, field):
    m = re.search(r"(?<!" + r"\w)" + field + r":\s*'((?:[^'\\]|\\.)*)'", block)
    return m.group(1) if m else ''

# Find cards with empty sentence
missing = []
for i, block in enumerate(card_blocks):
    sentence = extract_field(block, 'sentence')
    if sentence == '':
        missing.append({
            'idx': i,
            'word': extract_field(block, 'word'),
            'reading': extract_field(block, 'reading'),
            'meaning': extract_field(block, 'meaning'),
            'meaningEn': extract_field(block, 'meaningEn'),
            'type': extract_field(block, 'type'),
            'level': extract_field(block, 'level'),
        })

print(f"Cards needing sentences: {len(missing)}")

# ── Claude API ────────────────────────────────────────────────────────────────
client = anthropic.Anthropic()

SYSTEM = """You generate Japanese example sentences for vocabulary flashcards.
Rules:
1. Sentence difficulty: JLPT N4 level (simple, natural, practical)
2. Ruby markup format: 漢字|よみ (pipe between kanji and reading, space between tokens)
   Examples: '先生|せんせい は 親切|しんせつ です。'  '毎日|まいにち 運動|うんどう します。'
   Katakana/hiragana words: no pipe needed, just write as-is
3. The target word must appear in the sentence (use its kanji form if it has one)
4. sentenceMeaning: Traditional Chinese translation (繁體中文)
5. sentenceMeaningEn: English translation
6. Return ONLY valid JSON, no markdown fences:
   {"sentence": "...", "sentenceMeaning": "...", "sentenceMeaningEn": "..."}"""

def gen_sentence(word, reading, meaning, meaning_en, word_type):
    prompt = f"""Word: {word}
Reading: {reading}
Meaning (Chinese): {meaning if meaning else meaning_en}
Type: {word_type}

Generate one natural N4-level example sentence using this word."""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = msg.content[0].text.strip()
    # Strip markdown fences if present
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw)

# ── Generate ──────────────────────────────────────────────────────────────────
results = {}
for i, card in enumerate(missing):
    print(f"[{i+1}/{len(missing)}] {card['word']} ({card['reading']})... ", end='', flush=True)
    try:
        data = gen_sentence(
            card['word'], card['reading'],
            card['meaning'], card['meaningEn'], card['type']
        )
        results[card['idx']] = data
        print(f"✓  {data['sentence'][:30]}")
    except Exception as e:
        print(f"✗ {e}")
        results[card['idx']] = None
    time.sleep(0.1)  # gentle rate limit

# ── Patch cards_data.js ───────────────────────────────────────────────────────
new_blocks = list(card_blocks)
patched = 0
for idx, data in results.items():
    if not data:
        continue
    block = new_blocks[idx]

    def esc(s):
        return s.replace("\\", "\\\\").replace("'", "\\'")

    block = re.sub(r"sentence: ''", f"sentence: '{esc(data['sentence'])}'", block)
    block = re.sub(r"sentenceMeaning: ''", f"sentenceMeaning: '{esc(data['sentenceMeaning'])}'", block)
    block = re.sub(r"sentenceMeaningEn: ''", f"sentenceMeaningEn: '{esc(data['sentenceMeaningEn'])}'", block)
    new_blocks[idx] = block
    patched += 1

# Reconstruct JS
# Find all { } positions in original and replace
new_js = js
offset = 0
orig_positions = [(m.start(), m.end()) for m in re.finditer(r'\{[^{}]+\}', js, re.DOTALL)]
for block_idx, (start, end) in enumerate(orig_positions):
    if block_idx in results and results[block_idx]:
        old = js[start:end]
        new = new_blocks[block_idx]
        adj_start = start + offset
        adj_end = end + offset
        new_js = new_js[:adj_start] + new + new_js[adj_end:]
        offset += len(new) - len(old)

with open(cards_path, 'w', encoding='utf-8') as f:
    f.write(new_js)

import shutil
shutil.copy2(cards_path, os.path.join(REPO_DIR, 'cards_data.js'))

total_cards = new_js.count("level:")
print(f"\n✓ Patched {patched} cards. Total cards: {total_cards}")
print("Copied to repo.")
