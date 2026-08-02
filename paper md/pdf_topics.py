# -*- coding: utf-8 -*-
"""直接從 PDF 幾何位置抽出「主題單字XXX → 這張表的中文詞」對照表。

markdown 版的文字順序不可靠（標題有時跑到表格後面），但 PDF 裡標題永遠在表格
正上方。這裡用座標重排每一頁，就能拿到不會錯的主題歸屬。
"""
import pdfplumber, json, io, re, sys, unicodedata
sys.stdout.reconfigure(encoding='utf-8')
PDF = r"C:\Users\user\我的雲端硬碟\07_程式專案\Japanese-tutor\paper md\實用日文會話課｜課程講義｜完整版0515.pdf"
OUT = "pdf_topics.json"

CID = re.compile(r"\(cid:\d+\)")
HDR = {"中文", "日文", "備註", "中⽂", "⽇⽂"}

def page_lines(page):
    ws = page.extract_words()
    rows = {}
    for w in ws:
        rows.setdefault(round(w["top"] / 4), []).append(w)
    out = []
    for k in sorted(rows):
        g = sorted(rows[k], key=lambda w: w["x0"])
        txt = "".join(w["text"] for w in g)
        out.append((g[0]["top"], g[0]["x0"], txt))
    return out

def norm(s):
    # PDF 內文用的是康熙部首字（⽂ ⾁ ⼤…），NFKC 會統一還原成一般漢字
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", CID.sub("", s))).strip()

blocks = []          # (printed_page, caption, [terms])
with pdfplumber.open(PDF) as pdf:
    for idx, page in enumerate(pdf.pages):
        printed = idx + 1
        cur = None
        for top, x0, raw in page_lines(page):
            t = norm(raw)
            if not t: continue
            if t.startswith("主題單字"):
                name = t[4:].strip()
                cur = [printed, name, []]
                blocks.append(cur)
                continue
            if cur is None: continue
            if t in HDR or t == "中文日文備註": continue
            if re.fullmatch(r"\d{1,3}", t): continue
            # 表格左欄＝中文；右欄是被 CID 打壞的日文，用不上
            if x0 < 200 and len(t) <= 24:
                cur[2].append(t)
        if printed % 60 == 0:
            print("…已讀到第", printed, "頁", file=sys.stderr)

# 標題文字有時被拆成兩行（「主題單字」在一行、主題在下一行）→ 用第一個詞補
for b in blocks:
    if not b[1] and b[2]:
        b[1] = b[2].pop(0)

blocks = [b for b in blocks if b[1]]
json.dump(blocks, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
print("主題區塊:", len(blocks), " 收錄詞條:", sum(len(b[2]) for b in blocks))
print("範例:", blocks[40][:2], blocks[40][2][:6])
