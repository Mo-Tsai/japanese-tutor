#!/usr/bin/env python3
"""
Refactor index.html:
1. Move CARDS array out → load via <script src="cards_data.js">
2. Remove level filter buttons (ALL/N5/N4), keep search bar
3. Add shuffle button to nav-row
4. Clean up filterLevel / currentLevel JS, simplify applyFilter
"""
import re, os

REPO = r"C:\Users\Mo_Tsai\AppData\Local\Temp\japanese-flashcard-repo"
path = os.path.join(REPO, 'index.html')

with open(path, encoding='utf-8') as f:
    html = f.read()

# ── 1. Remove inline CARDS array, add external script tag ─────────────────────
# Replace:  <script>\nconst CARDS = [\n  ...\n];\n
# with:     (nothing — the CARDS come from cards_data.js)
# Then wrap remaining JS in its own <script> tag

# Find: opening <script> tag immediately before const CARDS
# Pattern: the <script> on its own line, followed by const CARDS = [
html = re.sub(
    r'<script>\s*\nconst CARDS = \[[\s\S]*?\];\s*\n',
    '',            # remove it entirely
    html,
    count=1
)

# Insert <script src="cards_data.js"></script> + new <script> before the remaining JS block
# The remaining JS starts with: let filteredCards = [...CARDS];  OR  let filteredCards
# Find the opening of the remaining JS (after card data was removed)
# We need to wrap it: the last </script> before </body> closes the main script block.
# Strategy: find where the remaining inline JS starts and prepend the right tags.

# After removal, the first JS content line should be "let filteredCards" or similar.
# We'll find the point just before the JS variables and insert tags.

# Find "let filteredCards" and insert script tags before it
insert_marker = 'let filteredCards = [...CARDS];'
if insert_marker in html:
    html = html.replace(
        insert_marker,
        '<script src="cards_data.js"></script>\n<script>\n' + insert_marker,
        1
    )
else:
    print("WARNING: could not find insert_marker")

# ── 2. Remove lesson-filter div (ALL/N5/N4 buttons) but keep search-wrap ──────
# Remove the entire lesson-filter div, keep search-wrap as standalone
html = re.sub(
    r'<div class="lesson-filter-wrap">\s*<div class="lesson-filter"[^>]*>.*?</div>\s*',
    '<div class="lesson-filter-wrap">\n',
    html,
    count=1,
    flags=re.DOTALL
)

# ── 3. Add shuffle button to nav-row (after ◀, before play buttons) ───────────
html = html.replace(
    '    <button class="btn-nav" onclick="prevCard()">◀</button>',
    '    <button class="btn-nav" onclick="prevCard()">◀</button>\n'
    '    <button class="btn-nav" onclick="shuffleCards()" title="隨機">⇄</button>',
    1
)

# ── 4. Remove currentLevel variable ───────────────────────────────────────────
html = html.replace("let currentLevel = 'all';\n", '', 1)

# ── 5. Remove filterLevel() function ──────────────────────────────────────────
html = re.sub(
    r'function filterLevel\(lv\) \{[\s\S]*?\}\s*\n',
    '',
    html,
    count=1
)

# ── 6. Simplify applyFilter() — remove level check ────────────────────────────
old_apply = """function applyFilter() {
  const q = (document.getElementById('searchInput')?.value || '').trim().toLowerCase();
  filteredCards = CARDS.filter(c => {
    if (currentLevel !== 'all' && c.level !== currentLevel) return false;
    if (!q) return true;
    return c.word.includes(q) || c.reading.includes(q) ||
           c.meaning.toLowerCase().includes(q) || (c.meaningEn || '').toLowerCase().includes(q);
  });
  current = 0; renderCard();
}"""
new_apply = """function applyFilter() {
  const q = (document.getElementById('searchInput')?.value || '').trim().toLowerCase();
  filteredCards = q ? CARDS.filter(c =>
    c.word.includes(q) || c.reading.includes(q) ||
    c.meaning.toLowerCase().includes(q) || (c.meaningEn || '').toLowerCase().includes(q)
  ) : [...CARDS];
  current = 0; renderCard();
}

function shuffleCards() {
  stopPlay();
  for (let i = filteredCards.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [filteredCards[i], filteredCards[j]] = [filteredCards[j], filteredCards[i]];
  }
  current = 0; renderCard();
}"""
if old_apply in html:
    html = html.replace(old_apply, new_apply, 1)
else:
    print("WARNING: applyFilter not found verbatim")

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
print("index.html updated.")

# Quick sanity check
print(f"  <script src=\"cards_data.js\">: {'YES' if 'cards_data.js' in html else 'NO'}")
print(f"  filterLevel: {'FOUND (bad)' if 'filterLevel' in html else 'removed OK'}")
print(f"  currentLevel: {'FOUND (bad)' if 'currentLevel' in html else 'removed OK'}")
print(f"  shuffleCards: {'YES' if 'shuffleCards' in html else 'NO'}")
print(f"  inline CARDS: {'FOUND (bad)' if 'const CARDS = [' in html else 'removed OK'}")
print(f"  lesson-filter div: {'FOUND (bad)' if 'id=\"lessonFilter\"' in html else 'removed OK'}")
