# -*- coding: utf-8 -*-
"""把 std_cards/L*.json 合併、驗證，注入 japanese-tutor.html 的
//__STD_CARDS__ 與 //__STD_GRAMMAR__ 標記。可重複執行（每次整段重寫）。"""
import io, json, os, re, sys, glob

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "..", "japanese-tutor.html")

KANA_OK = re.compile(r'^[぀-ゟ゠-ヿー〜]+$')

def js_str(s):
    return json.dumps(s, ensure_ascii=False)

def validate(card, errs):
    cid = card.get("id", "?")
    if card.get("type") == "grammar":
        if not card.get("pattern"): errs.append(f"{cid}: grammar 缺 pattern")
        for ex in card.get("examples", []):
            r = ex.get("ruby", ex.get("jp", ""))
            plain = "".join(t.split("|")[0] if "|" in t else t for t in r.split(" "))
            if plain.replace(" ", "") != ex.get("jp", "").replace(" ", ""):
                errs.append(f"{cid}: 例句 ruby 還原不符: {ex.get('jp','')[:20]}")
        return
    jp, ruby, reading = card.get("jp", ""), card.get("ruby", ""), card.get("reading", "")
    plain = "".join(t.split("|")[0] if "|" in t else t for t in ruby.split(" "))
    if plain.replace(" ", "") != jp.replace(" ", ""):
        errs.append(f"{cid}: ruby 還原不符 jp={jp[:24]}")
    rd = reading.replace("、", "").replace("。", "").replace("，", "").replace(",", "").replace(" ", "")
    rd = re.sub(r'[A-Za-zＡ-Ｚａ-ｚ0-9０-９？?！!・]', '', rd)
    if rd and not KANA_OK.match(rd):
        errs.append(f"{cid}: reading 含非假名: {reading[:24]}")

def main():
    files = sorted(glob.glob(os.path.join(HERE, "std_cards", "L*.json")),
                   key=lambda p: int(re.search(r"L(\d+)", os.path.basename(p)).group(1)))
    cards, grammar, errs, ids = [], [], [], set()
    for fp in files:
        data = json.load(io.open(fp, encoding="utf-8"))
        for c in data:
            if c["id"] in ids:
                errs.append(f"{c['id']}: id 重複（{os.path.basename(fp)}）")
                continue
            ids.add(c["id"])
            # 標準化 sub
            if c.get("sub", "").startswith("生词"):
                c["sub"] = "生词"
            validate(c, errs)
            (grammar if c.get("type") == "grammar" else cards).append(c)
    print(f"cards={len(cards)} grammar={len(grammar)} errors={len(errs)}")
    for e in errs[:40]:
        print(" !", e)
    if errs:
        print("驗證未過，不注入。")
        sys.exit(1)

    def card_js(c):
        keys = ["id","jp","ruby","reading","meaning","type","chapter","sec","sub","note","sentence","sentenceMeaning","grammar"]
        parts = []
        for k in keys:
            if k in c and c[k] not in (None, "", []):
                v = json.dumps(c[k], ensure_ascii=False) if isinstance(c[k], list) else js_str(c[k])
                parts.append(f"{k}:{v}")
        return "{" + ",".join(parts) + "}"

    def gram_js(g):
        parts = [f"id:{js_str(g['id'])}", f"pattern:{js_str(g['pattern'])}"]
        for k in ["title", "explain", "chapter", "sec"]:
            if g.get(k): parts.append(f"{k}:{js_str(g[k])}")
        exs = ",".join("{jp:%s,ruby:%s,cn:%s}" % (js_str(e.get("jp","")), js_str(e.get("ruby", e.get("jp",""))), js_str(e.get("cn","")))
                       for e in g.get("examples", []))
        parts.append("examples:[" + exs + "]")
        return "{" + ",".join(parts) + "}"

    cards_block = "\n".join(card_js(c) + "," for c in cards)
    gram_block = "\n".join(gram_js(g) + "," for g in grammar)

    html = io.open(HTML, encoding="utf-8").read()
    # 每次重寫「起始標記〜結束標記」之間的內容；兩個標記都保留，可重複執行
    for mark, block in [("STD_CARDS", cards_block), ("STD_GRAMMAR", gram_block)]:
        pat = re.compile(r"(//__%s__\n)(.*?)(//__END_%s__)" % (mark, mark), re.S)
        if not pat.search(html):
            print(f"找不到 {mark} 標記，中止（不寫檔）"); sys.exit(1)
        html = pat.sub(lambda m: m.group(1) + block + "\n" + m.group(3), html, count=1)
    io.open(HTML, "w", encoding="utf-8", newline="\n").write(html)
    print("injected into japanese-tutor.html")

if __name__ == "__main__":
    main()
