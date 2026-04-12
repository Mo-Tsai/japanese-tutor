#!/usr/bin/env python3
"""Fix duplicate sentences: replace the less-natural one in each pair."""
import re, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = r"C:\Users\Mo_Tsai\AppData\Local\Temp\japanese-flashcard-repo"
cards_path = os.path.join(BASE_DIR, 'cards_data.js')

def esc(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")

# (target_word, new_sentence, new_meaning, new_meaning_en)
FIXES = [
    # 重複: これ は 何 です か → keep for これ, replace for 何
    ('何',
     'この 漢字|かんじ は 何|なん と 読み|よみ ます か。',
     '這個漢字怎麼讀？',
     'How do you read this kanji?'),

    # 重複: 机 の 上 に 本 が あります → keep for 机, replace for 上
    ('上',
     '山|やま の 上|うえ から 景色|けしき が きれい です。',
     '從山頂看風景很美。',
     'The scenery from the top of the mountain is beautiful.'),

    # 重複: 公園 に 子供 が います → keep for 公園, replace for います
    ('います',
     '教室|きょうしつ に 学生|がくせい が 三|さん 人|にん います。',
     '教室裡有三個學生。',
     'There are three students in the classroom.'),

    # 重複: 昨日 映画 を 見ました → keep for 映画, replace for 昨日
    ('昨日',
     '昨日|きのう は とても 忙しかっ|いそがしかっ た です。',
     '昨天非常忙碌。',
     'Yesterday was very busy.'),

    # 重複: この ケーキ は とても おいしい → keep for おいしい, replace for とても
    ('とても',
     '今日|きょう は とても 暑い|あつい です ね。',
     '今天真的很熱呢。',
     'It is very hot today, isn\'t it?'),

    # 重複: 日本語 が できます か → keep for できます, replace for できる
    ('できる',
     '料理|りょうり が できる 人|ひと は すてき です。',
     '會做料理的人很棒。',
     'A person who can cook is wonderful.'),

    # 重複: 財布 を なくしてしまいました → keep for 財布, replace for なくします
    ('なくします',
     '鍵|かぎ を なくして しまいました。',
     '把鑰匙弄丟了。',
     'I lost my key.'),

    # 重複: 足 が 痛い → keep for 足; 脚, replace for 痛い
    ('痛い',
     '頭|あたま が 痛い|いたい から 薬|くすり を 飲み|のみ ました。',
     '頭痛所以吃了藥。',
     'My head hurt so I took medicine.'),

    # 重複: あの 人 は 誰 です か → keep for 誰, replace for あの
    ('あの',
     'あの 山|やま は とても 高い|たかい です ね。',
     '那座山真的很高呢。',
     'That mountain is very tall, isn\'t it?'),
]

with open(cards_path, encoding='utf-8') as f:
    js = f.read()

patched = 0
for word, new_sent, new_meaning, new_meaning_en in FIXES:
    # Find the block for this word
    block_pat = re.compile(
        r'(\{[^{}]*?word: \'' + re.escape(word) + r'\'[^{}]*?\})',
        re.DOTALL
    )
    m = block_pat.search(js)
    if not m:
        print(f'NOT FOUND: {word}')
        continue

    start, end = m.start(), m.end()
    block = js[start:end]

    new_block = re.sub(
        r"sentence: '([^']*)'",
        f"sentence: '{esc(new_sent)}'",
        block, count=1
    )
    new_block = re.sub(
        r"sentenceMeaning: '([^']*)'",
        f"sentenceMeaning: '{esc(new_meaning)}'",
        new_block, count=1
    )
    new_block = re.sub(
        r"sentenceMeaningEn: '([^']*)'",
        f"sentenceMeaningEn: '{esc(new_meaning_en)}'",
        new_block, count=1
    )

    js = js[:start] + new_block + js[end:]
    print(f'✓ {word}: {new_sent[:40]}')
    patched += 1

with open(cards_path, 'w', encoding='utf-8') as f:
    f.write(js)
shutil.copy2(cards_path, os.path.join(REPO_DIR, 'cards_data.js'))
print(f'\nPatched {patched} cards. Copied to repo.')
