import re, sys, shutil
sys.stdout.reconfigure(encoding='utf-8')
path = 'C:/Users/Mo_Tsai/Desktop/Google Drive/自動化測試資料夾/Japanese-tutor/cards_data.js'
with open(path, encoding='utf-8') as f:
    js = f.read()

def esc(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")

# Fix 1: ～人 (にん) still has null
pat = re.compile(
    r"(word: '～人'[^}]*?reading: 'にん'[^}]*?)"
    r"sentence: null([^}]*?)sentenceMeaning: null([^}]*?)sentenceMeaningEn: null",
    re.DOTALL
)
sent1 = 'この 部屋|へや に 三|さん 人|にん 入れ|はいれ ます。'
js, n = pat.subn(
    r"\1sentence: '" + esc(sent1) + r"'\2sentenceMeaning: '三個人可以進入這個房間。'\3sentenceMeaningEn: 'Three people can fit in this room.'",
    js, count=1
)
print(f'Fix 1 (～人/にん): {"ok" if n else "not found"}')

# Fix 2: ～円 duplicates 百's sentence → change ～円 to a different sentence
old_sent = "sentence: 'この りんご は 百|ひゃく 円|えん です。'"
new_sent = "sentence: '入場料|にゅうじょうりょう は 五百|ごひゃく 円|えん です。'"
if old_sent in js:
    js = js.replace(old_sent, new_sent, 1)
    # Also fix sentenceMeaning and sentenceMeaningEn for that card
    # Find the block with 入場料 sentence and fix meaning
    js = js.replace(
        "sentence: '入場料|にゅうじょうりょう は 五百|ごひゃく 円|えん です。', sentenceMeaning: '這個蘋果是一百日圓。'",
        "sentence: '入場料|にゅうじょうりょう は 五百|ごひゃく 円|えん です。', sentenceMeaning: '入場費是五百日圓。'"
    )
    js = js.replace(
        "sentenceMeaningEn: 'This apple costs 100 yen.'",
        "sentenceMeaningEn: 'The admission fee is 500 yen.'",
        1  # only replace the first occurrence (the ～円 card)
    )
    print('Fix 2 (～円 duplicate): ok')
else:
    print('Fix 2: pattern not found')

with open(path, 'w', encoding='utf-8') as f:
    f.write(js)
shutil.copy2(path, r'C:/Users/Mo_Tsai/AppData/Local/Temp/japanese-flashcard-repo/cards_data.js')
print('nulls remaining:', js.count('sentence: null'))
