# -*- coding: utf-8 -*-
"""掃描 COURSE_CARDS（講義卡）文字，對映到標日文法卡 id，
注入 japanese-tutor.html 的 //__COURSE_GRAMMAR_MAP__ 標記。
規則刻意保守：只對「特徵明確」的句型做對映，寧缺勿錯。"""
import io, json, os, re, sys, glob

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "..", "japanese-tutor.html")

# (文法卡 pattern 的辨識子串, 講義卡文字的觸發 regex)
RULES = [
    ("たことがあります", r"たことがあります|たことはありません"),
    ("ことができます",   r"ことができます"),
    ("ないでください",   r"ないでください"),
    ("なくてもいいです", r"なくてもいい"),
    ("なければなりません", r"なければなりません|なければいけません"),
    ("てもいいです",     r"(?<!なく)てもいいです|(?<!なく)でもいいです"),
    ("てはいけません",   r"てはいけません"),
    ("てください",       r"てください"),
    ("ています",         r"ています|でいます"),
    ("たいです",         r"たいです|たいんです"),
    ("欲しいです",       r"欲しい|ほしいです"),
    ("ませんか",         r"(?<![えれ])ませんか"),
    ("ましょうか",       r"ましょうか"),
    ("ましょう",         r"ましょう(?!か)"),
    ("をください",       r"をください|を下さい"),
    ("から〜まで",       r"から.{0,12}まで"),
    ("と思います",       r"と思います|とおもいます"),
    ("のです",           r"んです|のですか"),
    ("たり〜たり",       r"たり.+たり"),
    ("たほうがいいです", r"たほうがいい"),
    ("ほうがいいです",   r"(?<!た)ほうがいい"),
    ("になります",       r"[にく]なりま(す|した)"),
    ("にします",         r"にします|にしてください"),
    ("より",             r"より"),
    ("いちばん",         r"いちばん|一番"),
    ("好きです",         r"が好き|が 好|がすき"),
    ("上手です",         r"が上手|が下手|が 上手|が 下手"),
    ("分かります",       r"が分かります|(?<!こと)ができます"),
    ("てから",           r"てから"),
]

def main():
    # 1. 文法卡 pattern → gid
    files = sorted(glob.glob(os.path.join(HERE, "std_cards", "L*.json")),
                   key=lambda p: int(re.search(r"L(\d+)", os.path.basename(p)).group(1)))
    pat2gid = []
    for fp in files:
        for c in json.load(io.open(fp, encoding="utf-8")):
            if c.get("type") == "grammar":
                pat2gid.append((c["pattern"], c["id"]))
    rules = []
    for key, rx in RULES:
        gid = next((g for p, g in pat2gid if key in p), None)
        if gid:
            rules.append((re.compile(rx), gid))
        else:
            print(f"  (略過規則 {key}：找不到對應文法卡)")

    # 2. 掃 COURSE_CARDS
    html = io.open(HTML, encoding="utf-8").read()
    m = re.search(r"const COURSE_CARDS = \[\n(.*?)\n\];", html, re.S)
    body = m.group(1)
    n_mapped, mapping = 0, {}
    for line in body.split("\n"):
        idm = re.search(r'id:"(c_\d+)"', line)
        if not idm:
            continue
        jp = re.search(r'jp:"((?:[^"\\]|\\.)*)"', line)
        se = re.search(r'sentence:"((?:[^"\\]|\\.)*)"', line)
        text = (jp.group(1) if jp else "") + "␟" + (se.group(1) if se else "")
        gids = []
        for rx, gid in rules:
            if rx.search(text) and gid not in gids:
                gids.append(gid)
        if gids:
            mapping[idm.group(1)] = gids[:3]
            n_mapped += 1
    print(f"mapped {n_mapped} course cards")

    block = "\n".join(f'{k}:{json.dumps(v)},' for k, v in mapping.items())
    pat = re.compile(r"(//__COURSE_GRAMMAR_MAP__\n)(.*?)(//__END_COURSE_GRAMMAR_MAP__)", re.S)
    if not pat.search(html):
        print("找不到 COURSE_GRAMMAR_MAP 標記，中止（不寫檔）"); sys.exit(1)
    html = pat.sub(lambda mm: mm.group(1) + block + "\n" + mm.group(3), html, count=1)
    io.open(HTML, "w", encoding="utf-8", newline="\n").write(html)
    print("injected COURSE_GRAMMAR_MAP")

if __name__ == "__main__":
    main()
