#!/usr/bin/env python3
"""
Migrate cards_data.js: replace lesson:X with level:'N5'|'N4'
- lesson:100 cards → level:'N5'
- lesson:1-24 cards: if word/reading appears in N5 set → 'N5', else → 'N4'
"""
import re, os, shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = r"C:\Users\Mo_Tsai\AppData\Local\Temp\japanese-flashcard-repo"

cards_path = os.path.join(BASE_DIR, 'cards_data.js')
with open(cards_path, encoding='utf-8') as f:
    content = f.read()

# Build N5 lookup from lesson:100 cards
card_re = re.compile(
    r'\{[^{}]*?lesson:\s*(\d+)[^{}]*?word:\s*[\'"]([^\'"]+)[\'"][^{}]*?reading:\s*[\'"]([^\'"]+)[\'"][^{}]*?\}',
    re.DOTALL
)
n5_words    = set()
n5_readings = set()
for m in card_re.finditer(content):
    if int(m.group(1)) == 100:
        n5_words.add(m.group(2))
        n5_readings.add(m.group(3))

print(f"N5 reference set: {len(n5_words)} words, {len(n5_readings)} readings")

# Replace each card object's lesson field with level
def replace_lesson(m):
    obj = m.group(0)
    lesson_num = int(re.search(r'lesson:\s*(\d+)', obj).group(1))

    if lesson_num == 100:
        level = 'N5'
    else:
        word    = re.search(r"word:\s*['\"]([^'\"]+)['\"]", obj)
        reading = re.search(r"reading:\s*['\"]([^'\"]+)['\"]", obj)
        w = word.group(1) if word else ''
        r = reading.group(1) if reading else ''
        level = 'N5' if (w in n5_words or r in n5_readings) else 'N4'

    # Replace  lesson: X  with  level: 'N5'  (or N4)
    obj = re.sub(r"lesson:\s*\d+", f"level: '{level}'", obj)
    return obj

# Match full card objects (single-line or multi-line within { })
obj_re = re.compile(r'\{[^{}]+?\}', re.DOTALL)
new_content = obj_re.sub(replace_lesson, content)

# Verify counts
n5_count  = new_content.count("level: 'N5'")
n4_count  = new_content.count("level: 'N4'")
print(f"After migration: N5={n5_count}, N4={n4_count}, total={n5_count+n4_count}")

with open(cards_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print("cards_data.js written.")

shutil.copy2(cards_path, os.path.join(REPO_DIR, 'cards_data.js'))
print("Copied to repo.")
