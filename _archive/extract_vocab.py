import sys
import io
import re
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pypdf import PdfReader

reader = PdfReader('C:/Users/Mo_Tsai/Desktop/Google Drive/自動化測試資料夾/Japanese-tutor/PDF.pdf')

# Map of vocabulary page indices (0-based) to lesson numbers
vocab_page_map = {
    47: 1,
    57: 2,
    67: 3,
    77: 4,
    93: 5,
    103: 6,
    113: 7,
    123: 8,
    139: 9,
    149: 10,
    159: 11,
    169: 12,
    185: 13,
    195: 14,
    205: 15,
    215: 16,
    231: 17,
    241: 18,
    251: 19,
    261: 20,
    277: 21,
    287: 22,
    297: 23,
    307: 24,
}

# Bracket pattern: ［type］ where type is at most ~15 chars
# Using fullwidth brackets U+FF3B/U+FF3D, standard brackets, and also 」(U+300D) as close
# Also handle entries where bracket is used like ［名」 (mixed bracket types)
BRACKET_RE = re.compile(
    r'[\uff3b\[]'                           # opening bracket [ or ［
    r'([^\]\uff3d\uff3b\[\(\)（）\u300d]{1,15})'  # type content (1-15 chars)
    r'[\uff3d\]\u300d]'                     # closing bracket ], ］, or 」
)

def extract_type_from_bracket(type_inner):
    """Standardize the word type"""
    content = type_inner.strip()
    type_patterns = [
        (r'動[1１!！]|动[1１!！]', '動詞1'),
        (r'動[2２]|动[2２]', '動詞2'),
        (r'動[3３]|动[3３]', '動詞3'),
        (r'形\s*[1１!！]', 'い形容詞'),
        (r'形\s*[2２]', 'な形容詞'),
        (r'形\s*[3３]', 'な形容詞'),
        (r'^名$|名\]', '名詞'),
        (r'名', '名詞'),
        (r'代', '代名詞'),
        (r'副', '副詞'),
        (r'叹|嘆|感', '感嘆詞'),
        (r'连体|連体', '連体詞'),
        (r'疑', '疑問詞'),
        (r'专|專', '固有名詞'),
        (r'接続|接|连', '接続詞'),
    ]
    for pattern, word_type in type_patterns:
        if re.search(pattern, content):
            return word_type
    return '名詞'

def clean_reading(s):
    """Clean reading: remove tone marks, apostrophes, spaces"""
    s = re.sub(r"['\u2019\u2018`・]", '', s)
    s = re.sub(r'\s+', '', s)
    return s.strip()

def clean_meaning(s):
    """Clean meaning text"""
    s = s.strip()
    s = re.sub(r'\s*[─━\.…]+\s*$', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def find_last_jp_word(text):
    """Find the last Japanese word (reading) in text.
    Returns (word, start_pos) or (None, -1)
    Handles apostrophes (U+2019, U+0027) as valid chars within readings (tone marks).
    """
    # Remove apostrophes temporarily to not split words
    # The textbook uses ' (U+2019) as a tone/accent marker within words
    # We want to find the last contiguous Japanese sequence

    # Pattern: hiragana/katakana chars, possibly with apostrophe/tone marks
    # The reading continues through apostrophes that appear between kana
    jp_iter = list(re.finditer(
        r'[ぁ-んァ-ヶー\u3040-\u30ff\uff65-\uff9f]'
        r'(?:[ぁ-んァ-ヶー\u3040-\u30ff\u4e00-\u9fff\uff65-\uff9f\w\u2019\u0027])*',
        text
    ))
    if jp_iter:
        return jp_iter[-1].group(), jp_iter[-1].start()
    # Fallback: any non-space sequence at end
    words = text.strip().split()
    if words:
        last = words[-1]
        pos = text.rfind(last)
        return last, pos
    return None, -1

def parse_line_entries(line):
    """
    Parse all vocabulary entries from a line.
    Handles both single-entry and two-column (two-entry) lines.

    Algorithm:
    1. Find all type brackets in the line
    2. For each bracket, work backwards to find reading (and optional kanji form)
    3. Meaning = text from bracket end to start of next entry's reading
    """
    entries = []

    brackets = list(BRACKET_RE.finditer(line))
    if not brackets:
        return entries

    # For each bracket, find the entry reading
    entry_data = []

    for bi, bracket in enumerate(brackets):
        pre = line[:bracket.start()]

        # Check for （kanji）or (kanji) immediately before bracket
        paren_match = re.search(r'[（(]([^）)（(]{1,30})[）)]\s*$', pre)
        if paren_match:
            kanji_form = paren_match.group(1).strip()
            base = pre[:paren_match.start()].strip()
        else:
            kanji_form = None
            base = pre.strip()

        # Find the reading (last Japanese word in base)
        reading, reading_start_in_base = find_last_jp_word(base)

        if reading is None:
            # No reading found, skip this bracket
            continue

        # Find absolute position of this reading in the line
        # (reading_start_in_base is relative to base, which starts at 0 of pre[:paren_match.start()])
        if paren_match:
            reading_abs_start = reading_start_in_base
        else:
            reading_abs_start = reading_start_in_base

        type_str = bracket.group(1).strip()
        word_type = extract_type_from_bracket(type_str)

        # Determine word form
        if kanji_form:
            kanji_has_kanji = any('\u4e00' <= c <= '\u9fff' for c in kanji_form)
            kanji_has_hira = any('\u3041' <= c <= '\u309f' for c in kanji_form)
            if kanji_has_kanji and not kanji_has_hira:
                # parens is the kanji word
                word = kanji_form
            elif kanji_has_hira:
                # parens is the reading
                word = reading.strip()
                reading = kanji_form
            else:
                word = kanji_form
        else:
            word = reading.strip()

        entry_data.append({
            'word': word,
            'reading': reading,
            'type': word_type,
            'bracket_end': bracket.end(),
            'reading_abs_start': reading_abs_start,
        })

    # Now determine meanings:
    # Meaning of entry i = text from bracket_end[i] to reading_abs_start[i+1]
    for i, ed in enumerate(entry_data):
        if i + 1 < len(entry_data):
            next_reading_start = entry_data[i+1]['reading_abs_start']
            meaning_raw = line[ed['bracket_end']:next_reading_start]
        else:
            meaning_raw = line[ed['bracket_end']:]

        meaning = clean_meaning(meaning_raw)

        if ed['word'] and meaning:
            entries.append({
                'word': ed['word'].strip(),
                'reading': clean_reading(ed['reading']),
                'type': ed['type'],
                'meaning': meaning,
            })

    return entries


def extract_vocab_from_text(page_text, lesson_num):
    """Extract all vocabulary from a page's text"""

    # Find start of vocab section
    vocab_start = -1
    for marker in ['生词表', '生 词表']:
        idx = page_text.find(marker)
        if idx >= 0:
            vocab_start = idx + len(marker)
            break

    if vocab_start < 0:
        match = re.search(r'生\s*词\s*表', page_text)
        if match:
            vocab_start = match.end()

    if vocab_start < 0:
        vocab_start = 0

    vocab_text = page_text[vocab_start:]

    # Find end of vocab section (dotted line separator)
    end_pos = len(vocab_text)
    for pat in [r'\.{10,}', r'─{5,}']:
        m = re.search(pat, vocab_text)
        if m:
            end_pos = min(end_pos, m.start())

    vocab_text = vocab_text[:end_pos]

    # Split into lines and handle multi-line entries
    lines = vocab_text.split('\n')
    processed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Check for bracket at line end without meaning
        has_bracket = bool(BRACKET_RE.search(line))
        if has_bracket:
            last_bracket = list(BRACKET_RE.finditer(line))[-1]
            after_bracket = line[last_bracket.end():].strip()
            if not after_bracket:
                # Meaning might be on next line(s)
                j = i + 1
                extra = []
                while j < len(lines) and j < i + 5:
                    next_l = lines[j].strip()
                    if not next_l:
                        j += 1
                        continue
                    # Check if next line is a meaning (Chinese text, no Japanese reading patterns)
                    has_jp_hira = bool(re.search(r'[ぁ-んァ-ヶ]', next_l))
                    has_bracket2 = bool(BRACKET_RE.search(next_l))
                    if not has_jp_hira and not has_bracket2 and 1 <= len(next_l) <= 30:
                        extra.append(next_l)
                        j += 1
                    else:
                        break
                if extra:
                    line = line + ' ' + '，'.join(extra)
                    i = j
                else:
                    i += 1
            else:
                i += 1
        else:
            i += 1

        processed_lines.append(line)

    # Parse entries
    all_entries = []
    seen = set()

    for line in processed_lines:
        line = line.strip()
        if not line:
            continue

        # Skip non-vocab lines
        if re.match(r'^(第\d|单元|练习|语法|表达|附录)', line):
            continue
        if re.match(r'^\d+$', line):
            continue

        entries = parse_line_entries(line)
        for entry in entries:
            if entry['word'] and entry.get('meaning'):
                key = entry['word'] + entry.get('reading', '')
                if key and key not in seen:
                    seen.add(key)
                    entry['lesson'] = lesson_num
                    all_entries.append(entry)

    return all_entries


# Main extraction
all_vocab = []
lesson_counts = {}

for page_idx, lesson_num in sorted(vocab_page_map.items()):
    text = reader.pages[page_idx].extract_text()
    if not text:
        print(f"Lesson {lesson_num}: No text on page {page_idx+1}")
        lesson_counts[lesson_num] = 0
        continue

    entries = extract_vocab_from_text(text, lesson_num)
    lesson_counts[lesson_num] = len(entries)
    all_vocab.extend(entries)
    print(f"Lesson {lesson_num} (page {page_idx+1}): {len(entries)} words extracted")

print(f"\nTotal: {len(all_vocab)} words extracted across {len(lesson_counts)} lessons")

# Save to JSON
output_path = 'C:/Users/Mo_Tsai/Desktop/Google Drive/自動化測試資料夾/Japanese-tutor/vocabulary.json'

formatted_vocab = []
for entry in all_vocab:
    formatted_vocab.append({
        'lesson': entry['lesson'],
        'word': entry['word'],
        'reading': entry['reading'],
        'type': entry['type'],
        'meaning': entry['meaning'],
    })

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(formatted_vocab, f, ensure_ascii=False, indent=2)

print(f"\nSaved to: {output_path}")
print("\nWords per lesson:")
for lesson_num in sorted(lesson_counts.keys()):
    print(f"  Lesson {lesson_num}: {lesson_counts[lesson_num]} words")
