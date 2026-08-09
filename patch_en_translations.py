#!/usr/bin/env python3
"""
Patch N5 cards in japanese-tutor.html with meaningEn and sentenceMeaningEn
from n5_cards_batch_1.js through n5_cards_batch_8.js
"""

import re
import os

ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), '_archive')
HTML_FILE = os.path.join(os.path.dirname(__file__), 'japanese-tutor.html')


def extract_field(line, field):
    """Extract a string field value from a JS object line."""
    # Match: field: 'value' or field: "value"
    pattern = rf"{re.escape(field)}:\s*'((?:[^'\\]|\\.)*)'"
    m = re.search(pattern, line)
    if m:
        return m.group(1)
    pattern = rf'{re.escape(field)}:\s*"((?:[^"\\]|\\.)*)"'
    m = re.search(pattern, line)
    if m:
        return m.group(1)
    return None


def build_lookup():
    lookup = {}
    for i in range(1, 9):
        batch_file = os.path.join(ARCHIVE_DIR, f'n5_cards_batch_{i}.js')
        if not os.path.exists(batch_file):
            print(f"WARNING: {batch_file} not found")
            continue
        with open(batch_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line.startswith('{'):
                    continue
                word = extract_field(line, 'word')
                meaning_en = extract_field(line, 'meaningEn')
                sentence_meaning_en = extract_field(line, 'sentenceMeaningEn')
                if word and (meaning_en or sentence_meaning_en):
                    lookup[word] = {
                        'meaningEn': meaning_en or '',
                        'sentenceMeaningEn': sentence_meaning_en or '',
                    }
    print(f"Built lookup with {len(lookup)} entries from batch files")
    return lookup


def patch_html(lookup):
    with open(HTML_FILE, encoding='utf-8') as f:
        lines = f.readlines()

    patched_count = 0
    no_match_count = 0
    new_lines = []

    for line in lines:
        # Only process N5 card lines that don't already have meaningEn
        if 'jlpt:"N5"' in line and 'meaningEn:' not in line:
            # Extract jp value: jp:"..."
            jp_match = re.search(r'jp:"([^"]*)"', line)
            if jp_match:
                jp_word = jp_match.group(1)
                if jp_word in lookup:
                    entry = lookup[jp_word]
                    meaning_en = entry['meaningEn']
                    sentence_meaning_en = entry['sentenceMeaningEn']

                    # Insert meaningEn after meaning:"..."
                    # Pattern: meaning:"...",
                    if meaning_en:
                        line = re.sub(
                            r'(meaning:"[^"]*")',
                            lambda m: m.group(1) + f',meaningEn:"{meaning_en}"',
                            line,
                            count=1
                        )

                    # Insert sentenceMeaningEn before closing }
                    # The line ends with: sentenceMeaning:"..."},
                    if sentence_meaning_en:
                        # Insert before closing brace
                        line = re.sub(
                            r'(\},\s*$)',
                            f',sentenceMeaningEn:"{sentence_meaning_en}"' + r'\1',
                            line,
                            count=1
                        )

                    patched_count += 1
                else:
                    no_match_count += 1

        new_lines.append(line)

    print(f"Patched: {patched_count} N5 cards")
    print(f"No match found: {no_match_count} N5 cards")

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    return patched_count


def verify(lookup):
    """Quick verification: check a few known words"""
    with open(HTML_FILE, encoding='utf-8') as f:
        content = f.read()

    test_words = ['ああ', '会う', '朝', '本', 'かぎ']
    print("\nVerification:")
    for word in test_words:
        # Find the line containing jp:"word"
        pattern = rf'jp:"{re.escape(word)}"[^\n]*'
        m = re.search(pattern, content)
        if m:
            line = m.group(0)
            has_meaning_en = 'meaningEn:' in line
            has_sentence_en = 'sentenceMeaningEn:' in line
            jlpt = re.search(r'jlpt:"([^"]*)"', line)
            jlpt_val = jlpt.group(1) if jlpt else '?'
            print(f"  {word} (JLPT:{jlpt_val}): meaningEn={has_meaning_en}, sentenceMeaningEn={has_sentence_en}")
            if has_meaning_en:
                me = re.search(r'meaningEn:"([^"]*)"', line)
                if me:
                    print(f"    -> {me.group(1)}")
        else:
            print(f"  {word}: NOT FOUND in HTML")


if __name__ == '__main__':
    lookup = build_lookup()
    count = patch_html(lookup)
    verify(lookup)
    print(f"\nDone. Total cards patched: {count}")
