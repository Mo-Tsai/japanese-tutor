#!/usr/bin/env python3
import re, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = r"C:\Users\Mo_Tsai\AppData\Local\Temp\japanese-flashcard-repo"
cards_path = os.path.join(BASE_DIR, 'cards_data.js')

SENTENCES = {
    '～円':   ('この りんご は 百|ひゃく 円|えん です。', '這個蘋果是一百日圓。', 'This apple costs 100 yen.'),
    '～回':   ('一|いち 週間|しゅうかん に 三|さん 回|かい 運動|うんどう します。', '一週運動三次。', 'I exercise three times a week.'),
    '～階':   ('私|わたし の 部屋|へや は 三|さん 階|かい です。', '我的房間在三樓。', 'My room is on the third floor.'),
    '～か月': ('日本語|にほんご を 六|ろく か月|かげつ 勉強|べんきょう しました。', '學了六個月日語。', 'I studied Japanese for six months.'),
    '～月':   ('私|わたし の 誕生日|たんじょうび は 三|さん 月|がつ です。', '我的生日在三月。', 'My birthday is in March.'),
    '～個':   ('りんご を 三|みっ 個|こ 買い|かい ました。', '買了三個蘋果。', 'I bought three apples.'),
    '～語':   ('彼女|かのじょ は フランス 語|ご が 話せ|はなせ ます。', '她會說法語。', 'She can speak French.'),
    '～歳':   ('私|わたし は 二十|はたち 歳|さい です。', '我二十歲。', 'I am twenty years old.'),
    '～冊':   ('図書館|としょかん で 本|ほん を 二|に 冊|さつ 借り|かり ました。', '在圖書館借了兩本書。', 'I borrowed two books from the library.'),
    '～時':   ('授業|じゅぎょう は 九|く 時|じ に 始まり|はじまり ます。', '課從九點開始。', 'Class starts at nine o\'clock.'),
    '～時間': ('映画|えいが は 二|に 時間|じかん あります。', '電影有兩個小時。', 'The movie is two hours long.'),
    '～週間': ('夏休み|なつやすみ は 三|さん 週間|しゅうかん です。', '暑假有三週。', 'Summer vacation is three weeks long.'),
    '～人':   ('このクラス に は 二十|にじゅう 人|にん います。', '這個班有二十個人。', 'There are twenty people in this class.'),
    '～台':   ('駐車場|ちゅうしゃじょう に 車|くるま が 五|ご 台|だい あります。', '停車場有五輛車。', 'There are five cars in the parking lot.'),
    '～中':   ('会議|かいぎ 中|ちゅう は 電話|でんわ を しないで ください。', '開會中請不要打電話。', 'Please do not call during the meeting.'),
    '～度':   ('今日|きょう の 気温|きおん は 三十|さんじゅう 度|ど です。', '今天氣溫三十度。', 'Today\'s temperature is 30 degrees.'),
    '～日':   ('今月|こんげつ の 十五|じゅうご 日|にち に 試験|しけん が あります。', '這個月十五號有考試。', 'There is an exam on the 15th of this month.'),
    '～年':   ('日本語|にほんご を 三|さん 年|ねん 勉強|べんきょう して います。', '已經學了三年日語。', 'I have been studying Japanese for three years.'),
    '～杯':   ('コーヒー を 一|いっ 杯|ぱい ください。', '請給我一杯咖啡。', 'Please give me one cup of coffee.'),
    '～番':   ('私|わたし は 三|さん 番|ばん です。', '我是三號。', 'I am number three.'),
    '～匹':   ('猫|ねこ が 三|さん 匹|びき います。', '有三隻貓。', 'There are three cats.'),
    '～分':   ('駅|えき まで 十|じゅっ 分|ぷん かかります。', '到車站要十分鐘。', 'It takes ten minutes to the station.'),
    '～本':   ('鉛筆|えんぴつ が 三|さん 本|ぼん あります。', '有三支鉛筆。', 'There are three pencils.'),
    '～枚':   ('切手|きって を 五|ご 枚|まい 買い|かい ました。', '買了五張郵票。', 'I bought five stamps.'),
    '～前':   ('三|さん 年|ねん 前|まえ に 日本|にほん に 来|き ました。', '三年前來到了日本。', 'I came to Japan three years ago.'),
    '～屋':   ('あの 本|ほん 屋|や は 大きい|おおきい です。', '那家書店很大。', 'That bookstore is large.'),
}

def esc(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")

with open(cards_path, encoding='utf-8') as f:
    js = f.read()

patched = 0
for word, (sent, meaning, meaning_en) in SENTENCES.items():
    # Find card with this word that has sentence: null
    pat = re.compile(
        r"(\{[^{}]*?word: '" + re.escape(word) + r"'[^{}]*?)"
        r"sentence: null"
        r"([^{}]*?sentenceMeaning: null)"
        r"([^{}]*?sentenceMeaningEn: null)"
        r"([^{}]*?\})",
        re.DOTALL
    )
    def replacer(m):
        return (m.group(1)
                + f"sentence: '{esc(sent)}'"
                + m.group(2).replace('sentenceMeaning: null', f"sentenceMeaning: '{esc(meaning)}'")
                + m.group(3).replace('sentenceMeaningEn: null', f"sentenceMeaningEn: '{esc(meaning_en)}'")
                + m.group(4))
    new_js, n = pat.subn(replacer, js, count=1)
    if n:
        js = new_js
        print(f'  ✓ {word}')
        patched += 1
    else:
        print(f'  - {word}: not found or already has sentence')

with open(cards_path, 'w', encoding='utf-8') as f:
    f.write(js)
shutil.copy2(cards_path, os.path.join(REPO_DIR, 'cards_data.js'))

remaining = js.count('sentence: null')
print(f'\nPatched {patched}. Remaining nulls: {remaining}')
