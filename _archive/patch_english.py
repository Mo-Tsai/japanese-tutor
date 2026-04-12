#!/usr/bin/env python3
import re, sys, shutil
sys.stdout.reconfigure(encoding='utf-8')

path = 'C:/Users/Mo_Tsai/Desktop/Google Drive/自動化測試資料夾/Japanese-tutor/cards_data.js'
with open(path, encoding='utf-8') as f:
    js = f.read()

ENGLISH = {
    # N5
    '奥さん':           "someone else's wife; your wife",
    'お兄さん':         "older brother (polite/general term)",
    # N4 - from JLPT_N4.csv (a-row)
    'あ':              "ah; oh (exclamation)",
    'アフリカ':         "Africa",
    '上がる':           "to rise; to go up",
    '挨拶':            "greeting; salutation",
    'アジア':           "Asia",
    '赤ちゃん':         "baby; infant",
    '赤ん坊':          "baby; infant",
    'アクセサリー':      "accessories; jewelry",
    'アメリカ':         "America; United States",
    'アナウンサー':      "announcer; newscaster",
    'あんな':           "that kind of; like that",
    '案内':            "guide; information; to show around",
    '安心':            "peace of mind; relief",
    'アルバイト':       "part-time job",
    'アルコール':       "alcohol",
    '浅い':            "shallow; superficial",
    '遊び':            "play; game; fun",
    '集まる':          "to gather; to collect",
    '謝る':            "to apologize",
    '倍':              "twice; double",
    '番組':            "program (TV/radio)",
    '場所':            "place; location",
    'ベル':            "bell; doorbell",
    '美術館':          "art museum",
    'びっくり':         "surprised; startled",
    'ビル':            "building; office building",
    '僕':              "I; me (male, casual)",
    '貿易':            "trade; commerce",
    'ぶどう':          "grape",
    '文学':            "literature",
    '文化':            "culture",
    '文法':            "grammar",
    'ちゃん':          "-chan (affectionate name suffix)",
    'チェック':         "check; checkered pattern",
    '血':              "blood",
    '力':              "strength; power; ability",
    '地理':            "geography",
    '中学校':          "middle school; junior high school",
    '注意':            "attention; caution; warning",
    '注射':            "injection; shot",
    '大学生':          "university student",
    '大事':            "important; precious",
    # Additional N4 words from other sources
    '暖房':            "heating; heater",
    '男性':            "male; man",
    'できるだけ':       "as much as possible",
    '電報':            "telegram",
    '電灯':            "electric light",
    'どんどん':         "rapidly; steadily; one after another",
    '泥棒':            "thief; burglar",
    '道具':            "tool; instrument",
    '枝':              "branch; twig",
    '選ぶ':            "to choose; to select",
    'ファックス':       "fax; fax machine",
    '増える':          "to increase; to multiply",
    '深い':            "deep; profound",
    '復習':            "review; revision",
    '複雑':            "complicated; complex",
    '踏む':            "to step on; to tread on",
    '降り出す':        "to begin to rain/snow",
    '布団':            "futon; Japanese bedding",
    '太る':            "to gain weight; to become fat",
    '普通':            "normal; ordinary; usually",
    'ガラス':          "glass (material)",
    'ガソリン':         "gasoline; petrol",
    'ガソリンスタンド':  "gas station; petrol station",
    'ガス':            "gas",
    '原因':            "cause; origin; reason",
    '下宿':            "boarding house; lodging",
    '技術':            "technology; skill; technique",
    'ごちそう':         "feast; treat; delicious food",
    'ごみ':            "garbage; trash; rubbish",
    'ご覧になる':       "to look; to see; to watch (honorific)",
    'ご主人':          "husband (someone else's); master",
    'ご存じ':          "knowing (honorific); are you aware",
    '具合':            "condition; state; health",
    '拝見':            "to look; to see (humble)",
    '歯医者':          "dentist",
    'はっきり':         "clearly; distinctly",
    '運ぶ':            "to carry; to transport",
    '花見':            "cherry blossom viewing",
    'ハンドバッグ':      "handbag; purse",
    '反対':            "opposition; opposite; against",
    '払う':            "to pay",
    '発音':            "pronunciation",
    '林':              "forest; woods",
    '恥ずかしい':       "embarrassing; ashamed; shy",
}

patched = 0
not_found = []

for word, en in ENGLISH.items():
    en_esc = en.replace("'", "\\'")
    # Find card with this word that has meaningEn: ''
    pat = re.compile(
        r"(word: '" + re.escape(word) + r"'[^}]*?meaningEn: )'([^}]*?\})",
        re.DOTALL
    )
    def make_repl(en_val):
        def repl(m):
            # Only replace if currently empty
            if m.group(2).startswith("'"):
                return m.group(0)  # already has value
            return m.group(1) + "'" + en_val + "'" + m.group(2)[1:]
        return repl

    # Simpler approach: replace meaningEn: '' for this word
    pat2 = re.compile(
        r"(word: '" + re.escape(word) + r"'(?:(?!level:).)*?meaningEn: )'(?='[^']*sentence:)",
        re.DOTALL
    )

    # Most direct: find the exact card block and replace meaningEn: '' with value
    pat3 = re.compile(
        r"(\{ level: 'N[45]', word: '" + re.escape(word) +
        r"'[^}]*?meaningEn: )''",
        re.DOTALL
    )
    new_js, n = pat3.subn(r"\g<1>'" + en_esc + "'", js, count=1)
    if n:
        js = new_js
        patched += 1
    else:
        not_found.append(word)

print(f'Patched: {patched}')
if not_found:
    print(f'Not found ({len(not_found)}):')
    for w in not_found:
        print(f'  {w}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(js)
shutil.copy2(path, r'C:/Users/Mo_Tsai/AppData/Local/Temp/japanese-flashcard-repo/cards_data.js')
print('Done.')
