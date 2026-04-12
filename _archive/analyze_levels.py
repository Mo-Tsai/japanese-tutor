#!/usr/bin/env python3
"""
Analyze which existing lesson 1-24 cards appear in the N5 word list.
Outputs: matched (N5), unmatched (N4), and ambiguous cases.
"""
import re, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, 'cards_data.js'), encoding='utf-8') as f:
    content = f.read()

# Parse all card objects via regex
# Each card: { lesson: X, word: '...', ruby: '...', reading: '...', ... }
card_re = re.compile(
    r'\{[^{}]*?lesson:\s*(\d+)[^{}]*?word:\s*[\'"]([^\'"]+)[\'"][^{}]*?reading:\s*[\'"]([^\'"]+)[\'"][^{}]*?\}',
    re.DOTALL
)

cards = []
for m in card_re.finditer(content):
    cards.append({
        'lesson': int(m.group(1)),
        'word': m.group(2),
        'reading': m.group(3),
    })

print(f"Total cards parsed: {len(cards)}")

# Separate N5 (lesson 100) from existing (lesson 1-24)
n5_cards = [c for c in cards if c['lesson'] == 100]
existing = [c for c in cards if c['lesson'] != 100]

print(f"N5 cards (lesson 100): {len(n5_cards)}")
print(f"Existing cards (lesson 1-24): {len(existing)}")

# Build N5 lookup sets
n5_words   = {c['word']    for c in n5_cards}
n5_readings = {c['reading'] for c in n5_cards}

# Match existing cards
matched = []
unmatched = []

for c in existing:
    if c['word'] in n5_words or c['reading'] in n5_readings:
        matched.append(c)
    else:
        unmatched.append(c)

print(f"\n--- Matches (will become N5): {len(matched)} ---")
for c in sorted(matched, key=lambda x: x['reading']):
    print(f"  {c['word']} ({c['reading']})  [lesson {c['lesson']}]")

print(f"\n--- No match (will become N4): {len(unmatched)} ---")
for c in sorted(unmatched, key=lambda x: x['reading']):
    print(f"  {c['word']} ({c['reading']})  [lesson {c['lesson']}]")

print(f"\nSummary: {len(matched)} → N5,  {len(unmatched)} → N4")
