import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('C:/Users/Mo_Tsai/AppData/Local/Temp/japanese-flashcard-repo/cards_data.js', encoding='utf-8') as f:
    lines = f.readlines()

problems = []
for i, line in enumerate(lines, 1):
    # Count unescaped single quotes (not preceded by backslash)
    count = 0
    j = 0
    while j < len(line):
        if line[j] == '\\':
            j += 2  # skip escaped char
            continue
        if line[j] == "'":
            count += 1
        j += 1
    # A valid JS line should have even number of single quotes
    # (each string opens and closes)
    if count % 2 != 0:
        problems.append((i, line.rstrip()[:150]))

print(f"Lines with odd quote count: {len(problems)}")
for ln, txt in problems:
    print(f"  Line {ln}: {txt}")
