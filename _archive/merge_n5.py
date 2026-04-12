#!/usr/bin/env python3
"""
Merges all 8 N5 batch JS files into cards_data.js and updates index.html.
- Changes lesson: 0 → lesson: 100 in all N5 cards
- Appends N5 cards to cards_data.js
- Patches buildFilter() to label lesson 100 as "N5" instead of "第100課"
"""

import re, os, shutil

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_DIR  = r"C:\Users\Mo_Tsai\AppData\Local\Temp\japanese-flashcard-repo"

cards_data_path = os.path.join(BASE_DIR, "cards_data.js")
index_html_path = os.path.join(REPO_DIR, "index.html")
repo_cards_path = os.path.join(REPO_DIR, "cards_data.js")

# ── Step 1: Collect N5 card objects from all 8 batch files ───────────────────

segments = []
total = 0
for i in range(1, 9):
    path = os.path.join(BASE_DIR, f"n5_cards_batch_{i}.js")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    start = text.index("[") + 1
    end   = text.rindex("]")
    inner = text[start:end].strip()
    # Change lesson: 0 → lesson: 100
    inner, n = re.subn(r'\blesson:\s*0\b', 'lesson: 100', inner)
    total += n
    segments.append(inner)
    print(f"  batch {i}: {n} cards")

n5_block = ",\n  ".join(s for s in segments if s)
print(f"\nTotal N5 cards: {total}")

# ── Step 2: Append N5 cards to cards_data.js ─────────────────────────────────

with open(cards_data_path, encoding="utf-8") as f:
    cards = f.read()

# Insert before final ];
pos = cards.rfind("];")
if pos == -1:
    raise ValueError("No ]; found in cards_data.js")

before = cards[:pos].rstrip()
sep = ",\n  " if not before.endswith(",") else "\n  "
new_cards = before + sep + n5_block + "\n];\n"

with open(cards_data_path, "w", encoding="utf-8") as f:
    f.write(new_cards)
print("cards_data.js updated.")

# ── Step 3: Copy cards_data.js to repo ───────────────────────────────────────

shutil.copy2(cards_data_path, repo_cards_path)
print(f"Copied to {repo_cards_path}")

# ── Step 4: Patch index.html buildFilter() label ─────────────────────────────

with open(index_html_path, encoding="utf-8") as f:
    html = f.read()

# Patch: replace   b.textContent = '第' + l + '課';
# with a label-aware version
old_label = "    b.textContent = '第' + l + '課';"
new_label = "    const LABELS = { 100: 'N5' };\n    b.textContent = LABELS[l] || ('第' + l + '課');"

if old_label not in html:
    raise ValueError("Could not find button label line in index.html")

html = html.replace(old_label, new_label, 1)
print("Patched buildFilter() label logic.")

with open(index_html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("\nDone. Ready to git add / commit / push.")
