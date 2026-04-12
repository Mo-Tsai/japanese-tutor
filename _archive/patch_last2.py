import re, sys, shutil
sys.stdout.reconfigure(encoding='utf-8')
path = 'C:/Users/Mo_Tsai/Desktop/Google Drive/自動化測試資料夾/Japanese-tutor/cards_data.js'
with open(path, encoding='utf-8') as f:
    js = f.read()

def esc(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")

fixes = [
    ('～時', 'とき',
     '子供|こども の 時|とき 、よく 公園|こうえん で 遊|あそ びました。',
     '小時候常常在公園玩。',
     'When I was a child, I often played in the park.'),
    ('～人', 'じん',
     'クラス に アメリカ 人|じん が 二|ふた 人|り います。',
     '班上有兩個美國人。',
     'There are two Americans in the class.'),
]

for word, reading, sent, meaning, meaning_en in fixes:
    pat = re.compile(
        r"(word: '" + re.escape(word) + r"'[^}]*?reading: '" + re.escape(reading) + r"'[^}]*?)"
        r"sentence: null([^}]*?)sentenceMeaning: null([^}]*?)sentenceMeaningEn: null",
        re.DOTALL
    )
    repl = (r"\1sentence: '" + esc(sent) +
            r"'\2sentenceMeaning: '" + esc(meaning) +
            r"'\3sentenceMeaningEn: '" + esc(meaning_en) + r"'")
    new_js, n = pat.subn(repl, js, count=1)
    if n:
        js = new_js
        print(f'  patched: {word} ({reading})')
    else:
        print(f'  not found: {word} ({reading})')

with open(path, 'w', encoding='utf-8') as f:
    f.write(js)
shutil.copy2(path, r'C:/Users/Mo_Tsai/AppData/Local/Temp/japanese-flashcard-repo/cards_data.js')
print('nulls remaining:', js.count('sentence: null'))
