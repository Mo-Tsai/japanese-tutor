#!/usr/bin/env python3
"""Validate all cards in cards_data.js across 100 simulated runs."""
import re, sys, random
sys.stdout.reconfigure(encoding='utf-8')

with open('C:/Users/Mo_Tsai/AppData/Local/Temp/japanese-flashcard-repo/cards_data.js', encoding='utf-8') as f:
    content = f.read()

# ── Parse all cards ───────────────────────────────────────────────────────────
blocks = re.findall(r'\{[^{}]+\}', content, re.DOTALL)
REQUIRED = ['level', 'word', 'ruby', 'reading', 'type', 'meaning',
            'meaningEn', 'sentence', 'sentenceMeaning', 'sentenceMeaningEn']

def parse_card(block):
    card = {}
    for field in REQUIRED:
        m = re.search(r"(?<!\w)" + field + r":\s*['\"]([^'\"]*)['\"]", block)
        card[field] = m.group(1) if m else None
    return card

cards = [parse_card(b) for b in blocks]
print(f"Total cards parsed: {len(cards)}")

# ── Static checks ─────────────────────────────────────────────────────────────
errors = []
warnings = []

for i, c in enumerate(cards):
    w = c.get('word', '?')

    # Required fields
    for f in ['level', 'word', 'reading']:
        if not c.get(f):
            errors.append(f"Card {i} ({w}): missing required field '{f}'")

    # Level must be N4 or N5
    if c.get('level') not in ('N4', 'N5', None):
        errors.append(f"Card {i} ({w}): invalid level '{c['level']}'")

    # No None fields (all should be at least empty string)
    for f in REQUIRED:
        if c[f] is None:
            errors.append(f"Card {i} ({w}): field '{f}' could not be parsed (possible quote issue)")

    # Ruby format: each token with | should have exactly one |
    if c.get('ruby'):
        for token in c['ruby'].split(' '):
            if token.count('|') > 1:
                warnings.append(f"Card {i} ({w}): ruby token '{token}' has multiple pipes")

    # Sentence ruby format
    if c.get('sentence'):
        for token in c['sentence'].split(' '):
            if token.count('|') > 1:
                warnings.append(f"Card {i} ({w}): sentence token '{token}' has multiple pipes")

    # Double comma remnant check
    if ',,' in (c.get('sentence') or ''):
        errors.append(f"Card {i} ({w}): double comma in sentence")

# Duplicate word+reading check
seen = {}
for i, c in enumerate(cards):
    key = (c.get('word',''), c.get('reading',''))
    if key in seen:
        warnings.append(f"Duplicate word: '{c['word']}' (cards {seen[key]} and {i})")
    else:
        seen[key] = i

# Duplicate sentence check
sent_seen = {}
for i, c in enumerate(cards):
    s = c.get('sentence','')
    if s and s in sent_seen:
        errors.append(f"Duplicate sentence: card {sent_seen[s]} ({cards[sent_seen[s]]['word']}) and card {i} ({c['word']})")
    elif s:
        sent_seen[s] = i

print(f"Errors:   {len(errors)}")
print(f"Warnings: {len(warnings)}")
for e in errors:   print(f"  ERROR: {e}")
for w in warnings: print(f"  WARN:  {w}")

# ── 100 simulated shuffle+render runs ────────────────────────────────────────
print(f"\nRunning 100 simulated shuffle+render cycles...")
run_errors = 0
for run in range(100):
    deck = cards.copy()
    random.shuffle(deck)
    for card in deck:
        # Simulate renderCard()
        if card.get('word') is None:
            run_errors += 1
            print(f"  Run {run}: renderCard got None word")
            break
        # Simulate rawText(sentence)
        sent = card.get('sentence') or ''
        raw = re.sub(r'\|[^\s|]*', '', sent).replace(' ', '')
        # Simulate checkAnswer
        norm = lambda s: re.sub(r'\s', '', s).lower()
        _ = norm(card.get('word',''))
        _ = norm(card.get('reading',''))
        _ = norm(raw)

if run_errors == 0:
    print("  All 100 runs passed — no runtime errors.")
else:
    print(f"  {run_errors} runs had errors.")

# ── Summary ───────────────────────────────────────────────────────────────────
n5 = sum(1 for c in cards if c.get('level') == 'N5')
n4 = sum(1 for c in cards if c.get('level') == 'N4')
no_sent = sum(1 for c in cards if not c.get('sentence'))
print(f"\n── Summary ──────────────────────")
print(f"N5: {n5}  N4: {n4}  Total: {len(cards)}")
print(f"Cards without sentence: {no_sent}")
print(f"All good!" if not errors else f"{len(errors)} errors need fixing.")
