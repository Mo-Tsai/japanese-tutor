# -*- coding: utf-8 -*-
"""標準日本語 初級下（L25-L48）：PDF 座標抽取。

跟上冊 extract_std.py 的差異（下冊是另一份掃描檔，參數完全不同）：
  * rotation = 0（上冊是 180，不需要補償）
  * PDF頁 = 書頁 + 15（上冊是 +16）
  * 每課 10 頁的內部結構也不一樣：
      +0 基本課文   +1~2 語法解釋   +3~4 表達及詞語講解
      +5 應用課文   +6~8 練習       +9 生詞表
  * 最關鍵：這份 OCR 會把句中的數字與英文拆成「另一個字級的獨立 span」，
    例如「中国で買ったCDを友達に貸しました」被拆成 12pt 的
    『中国で買ったを友達に貸しました。』加上 11pt 的『CD』。
    所以分行時**不能先依字級過濾**，要把同一 y 帶內的所有字級混在一起、
    再依 x 排序串接，數字與英文才會落回句子裡原本的位置。

輸出：std_extracted_shita.json
  {lesson: {"basic":[], "applied":[], "grammar_lines":[], "vocab_lines":[], "drill_lines":[]}}
"""
import io, json, os, re, sys
import fitz

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "新版标日第二版初级 下册(高清无水印) (2).pdf")
OUT = os.path.join(HERE, "std_extracted_shita.json")

# 課次 → 書頁起點（取自卷首目錄）。每課 10 頁；單元末另有 6 頁，所以單元交界會跳號。
LESSON_BOOK_PAGE = {
    25: 4,   26: 14,  27: 24,  28: 34,     # 第7單元 森赴北京
    29: 50,  30: 60,  31: 70,  32: 80,     # 第8單元 余暇
    33: 96,  34: 106, 35: 116, 36: 126,    # 第9單元 小野赴北京
    37: 142, 38: 152, 39: 162, 40: 172,    # 第10單元 遊覽北京
    41: 188, 42: 198, 43: 208, 44: 218,    # 第11單元 在北京的工作情況
    45: 234, 46: 244, 47: 254, 48: 264,    # 第12單元 新的拓展
}
PAGE_OFFSET = 15

FURI_MAX = 7.0          # 小於此字級視為假名注音層
HAS_KANJI = re.compile(r'[一-鿿]')


def norm_chars(page):
    """回傳 [(size, x0, y0, x1, y1, ch)]。

    下冊絕大多數頁面 rotation=0，但 PDF 第 132、133 頁（書頁 117、118，
    正好是第35課的語法解釋）是 180。不補償的話那兩頁抽出來的字是反的
    （『小句1たら,小句2』會變成『2句小,らた1句小』），所以照頁補。"""
    W, H = page.rect.width, page.rect.height
    rot = page.rotation
    out = []
    for b in page.get_text("rawdict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                size = s["size"]
                for c in s["chars"]:
                    if c["c"].strip() == "":
                        continue
                    x0, y0, x1, y1 = c["bbox"]
                    if rot == 180:
                        x0, y0, x1, y1 = W - x1, H - y1, W - x0, H - y0
                    out.append((size, x0, y0, x1, y1, c["c"]))
    return out


def cluster_lines(chars, ytol=6.0):
    """依 y0 分行（不分字級），行內依 x 排序。ytol 要略大於上冊，
    因為被拆出來的數字 span 基線常跟本文差 4px。"""
    lines = []
    for c in sorted(chars, key=lambda t: (t[2], t[1])):
        for ln in lines:
            if abs(ln[0][2] - c[2]) <= ytol:
                ln.append(c)
                break
        else:
            lines.append([c])
    for ln in lines:
        ln.sort(key=lambda t: t[1])
    lines.sort(key=lambda ln: min(c[2] for c in ln))
    return lines


def build_ruby(text_chars, furi_chars):
    """假名依 x 重疊掛回漢字；ruby 格式沿用 App 既有的『漢字|かな』空白分隔。"""
    assign = {}
    for fc in sorted(furi_chars, key=lambda t: t[1]):
        fx0, fx1 = fc[1], fc[3]
        fmid = (fx0 + fx1) / 2
        best, best_ov = None, 0.0
        for i, tc in enumerate(text_chars):
            ov = min(fx1, tc[3]) - max(fx0, tc[1])
            if ov > best_ov:
                best, best_ov = i, ov
        if best is None:
            if not text_chars:
                continue
            best = min(range(len(text_chars)),
                       key=lambda i: abs((text_chars[i][1] + text_chars[i][3]) / 2 - fmid))
        assign.setdefault(best, []).append(fc[5])

    plain = "".join(c[5] for c in text_chars)
    out, i, n = [], 0, len(text_chars)
    while i < n:
        if HAS_KANJI.match(text_chars[i][5]):
            j, kana = i, []
            while j < n and HAS_KANJI.match(text_chars[j][5]):
                kana.extend(assign.get(j, []))
                j += 1
            seg = "".join(text_chars[k][5] for k in range(i, j))
            out.append(" %s|%s " % (seg, "".join(kana)) if kana else seg)
            i = j
        else:
            out.append(text_chars[i][5])
            i += 1
    return plain, re.sub(r"\s+", " ", "".join(out)).strip()


VOCAB_COL_X = 258.0     # 生詞表雙欄的分界（左欄 59-255，右欄 260-455）


def page_lines(page, lo=7.0, hi=99.0, ymin=0.0, ymax=1.0, xlo=None, xhi=None):
    """抽出 [ymin,ymax] 比例區間內、字級在 [lo,hi) 的行；假名層另外對位。
    xlo/xhi 用來切生詞表的左右欄——不切的話兩欄會被併成同一行。"""
    H = page.rect.height
    chars = norm_chars(page)
    furi = [c for c in chars if c[0] < FURI_MAX]
    if xlo is not None:
        furi = [c for c in furi if xlo <= c[1] < (xhi if xhi is not None else 1e9)]
    body = [c for c in chars if lo <= c[0] < hi and ymin * H <= c[2] <= ymax * H
            and (xlo is None or xlo <= c[1] < (xhi if xhi is not None else 1e9))]
    res = []
    for ln in cluster_lines(body):
        y = min(c[2] for c in ln)
        fcs = [c for c in furi if 3 < y - c[2] < 22]
        plain, ruby = build_ruby(ln, fcs)
        if len(plain.strip()) < 2:
            continue
        res.append({"y": round(y, 1), "text": plain, "ruby": ruby})
    return res


def parse_lesson(doc, lesson):
    start = LESSON_BOOK_PAGE[lesson] + PAGE_OFFSET
    res = {"book_start": LESSON_BOOK_PAGE[lesson], "basic": [], "applied": [],
           "grammar_lines": [], "vocab_lines": [], "drill_lines": []}
    for off in range(10):
        p = start + off
        if p >= len(doc):
            break
        page = doc[p]
        bp = p - PAGE_OFFSET

        if off == 0:      # 基本課文（本文 11-12pt）＋頁底零星生詞
            for r in page_lines(page, lo=10.5, ymax=0.86):
                res["basic"].append({"book": bp, **r})
            for r in page_lines(page, lo=7.5, hi=10.5, ymin=0.86):
                res["vocab_lines"].append({"book": bp, "src": "基本課文頁", **r})
        elif off in (1, 2):   # 語法解釋
            for r in page_lines(page, lo=8.0, hi=13.0):
                res["grammar_lines"].append({"book": bp, "src": "語法解釋", **r})
        elif off in (3, 4):   # 表達及詞語講解
            for r in page_lines(page, lo=8.0, hi=13.0):
                res["grammar_lines"].append({"book": bp, "src": "表達講解", **r})
        elif off == 5:    # 應用課文（本文 10pt，場景說明 9pt）＋頁底生詞
            for r in page_lines(page, lo=8.5, ymax=0.86):
                res["applied"].append({"book": bp, **r})
            for r in page_lines(page, lo=7.5, hi=10.5, ymin=0.86):
                res["vocab_lines"].append({"book": bp, "src": "應用課文頁", **r})
        elif off in (6, 7, 8):   # 練習（例句可再利用，但多為填空指示）
            for r in page_lines(page, lo=8.0, hi=13.0):
                res["drill_lines"].append({"book": bp, **r})
        elif off == 9:    # 生詞表（雙欄；左右分開抽，否則兩欄會被併成同一行）
            for col, (xlo, xhi) in (("L", (0.0, VOCAB_COL_X)), ("R", (VOCAB_COL_X, 1e9))):
                for r in page_lines(page, lo=7.5, hi=11.0, ymax=0.60, xlo=xlo, xhi=xhi):
                    res["vocab_lines"].append({"book": bp, "src": "生詞表" + col, **r})
    return res


if __name__ == "__main__":
    doc = fitz.open(PDF)
    only = [int(a) for a in sys.argv[1:]] or sorted(LESSON_BOOK_PAGE)
    data = {}
    for les in only:
        d = parse_lesson(doc, les)
        data[les] = d
        print(f"L{les}: basic={len(d['basic'])} applied={len(d['applied'])} "
              f"grammar={len(d['grammar_lines'])} vocab={len(d['vocab_lines'])} drill={len(d['drill_lines'])}")
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("->", OUT)
