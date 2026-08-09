# -*- coding: utf-8 -*-
"""標準日本語 初級上：PDF 座標抽取（課文句 + 假名對位）。

頁面座標統一補償 rotation=180；假名(<7pt)以字元 bbox 的 x 重疊對回漢字。
輸出:std_extracted.json  {lesson: {"basic": [...], "applied": [...], "vocab": [...]}}
"""
import io, json, re, sys, unicodedata
import fitz

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\Users\user\我的雲端硬碟\07_程式專案\02_個人工具App\Japanese-tutor\paper md"
PDF = ROOT + r"\中日交流標準日本語.pdf"

# 課次 → 書頁起點（每課 10 頁）；PDF頁 = 書頁 + 16
LESSON_BOOK_PAGE = {1:22,2:32,3:42,4:52,5:68,6:78,7:88,8:98,9:114,10:124,11:134,12:144,
                    13:160,14:170,15:180,16:190,17:206,18:216,19:226,20:236,21:252,22:262,23:272,24:282}
PAGE_OFFSET = 16

KANA = re.compile(r'^[\u3040-\u309f\u30a0-\u30ffー〜、。・\s]+$')
HAS_KANJI = re.compile(r'[\u4e00-\u9fff]')

def norm_chars(page):
    """回傳 [(size, x0, y0, x1, y1, ch)]，已補償旋轉。"""
    W, H = page.rect.width, page.rect.height
    rot = page.rotation
    out = []
    d = page.get_text("rawdict")
    for b in d["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                size = s["size"]
                for c in s["chars"]:
                    x0, y0, x1, y1 = c["bbox"]
                    if rot == 180:
                        x0, y0, x1, y1 = W - x1, H - y1, W - x0, H - y0
                    ch = c["c"]
                    if ch.strip() == "":
                        continue
                    out.append((size, x0, y0, x1, y1, ch))
    return out

def cluster_lines(chars, ytol=4.0):
    """依 y0 分行；回傳 [[char,...] 按 x 排序]（保持全部字級混在同行判斷前先分開）"""
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
    lines.sort(key=lambda ln: ln[0][2])
    return lines

def build_ruby(text_chars, furi_chars):
    """text_chars/furi_chars: [(size,x0,y0,x1,y1,ch)]。回傳 (plain, ruby, reading_ok)
    ruby 格式：漢字連段後接 |かな ，段間以空白分隔（沿用 App 既有格式）。"""
    # 對每個假名字元，找 x 重疊最大的 text 字元索引
    assign = {}   # text_idx -> [kana chars]
    for fc in sorted(furi_chars, key=lambda t: t[1]):
        fx0, fx1 = fc[1], fc[3]
        fmid = (fx0 + fx1) / 2
        best, best_ov = None, 0.0
        for i, tc in enumerate(text_chars):
            ov = min(fx1, tc[3]) - max(fx0, tc[1])
            if ov > best_ov:
                best, best_ov = i, ov
        if best is None:  # 沒重疊：掛到中心點最近的字
            best = min(range(len(text_chars)),
                       key=lambda i: abs((text_chars[i][1]+text_chars[i][3])/2 - fmid))
        assign.setdefault(best, []).append(fc[5])
    plain = "".join(c[5] for c in text_chars)
    # 組 ruby：連續的「有假名的漢字」併為一段
    out, i, n = [], 0, len(text_chars)
    while i < n:
        ch = text_chars[i][5]
        if HAS_KANJI.match(ch) and any(j in assign for j in range(i, n) if text_chars[j][5] == ch or True):
            pass
        i += 1
    # 簡化重寫：逐字掃描
    out = []
    i = 0
    while i < n:
        ch = text_chars[i][5]
        if HAS_KANJI.match(ch):
            j = i
            kana = []
            while j < n and HAS_KANJI.match(text_chars[j][5]):
                kana.extend(assign.get(j, []))
                j += 1
            seg = "".join(text_chars[k][5] for k in range(i, j))
            if kana:
                out.append(" %s|%s " % (seg, "".join(kana)))
            else:
                out.append(seg)
            i = j
        else:
            out.append(ch)
            i += 1
    ruby = re.sub(r"\s+", " ", "".join(out)).strip()
    return plain, ruby

VOCAB_SPLIT = re.compile(r'(?<=）)\s*')

def parse_lesson(doc, lesson):
    """課內頁結構（書頁偏移）：+0~1 基本課文/生词, +2~4 語法·講解, +5~6 應用課文/生词, +7~9 練習"""
    start = LESSON_BOOK_PAGE[lesson] + PAGE_OFFSET
    res = {"basic": [], "applied": [], "vocab": [], "grammar_lines": []}
    for off in range(10):
        p = start + off
        if p >= len(doc):
            break
        page = doc[p]
        H = page.rect.height
        chars = norm_chars(page)
        furi = [c for c in chars if c[0] < 7]
        # --- 課文句（>=9.3pt）行 + 上方假名（僅課文頁）
        if off in (0, 1, 5, 6):
            big = [c for c in chars if c[0] >= 9.3]
            for ln in cluster_lines(big, ytol=4.5):
                text_cs = sorted(ln, key=lambda t: t[1])
                y = min(c[2] for c in text_cs)
                if y > H - 120:   # 頁底單字區的 10pt 中文字，略過
                    continue
                fcs = [c for c in furi if 3 < y - c[2] < 20]
                plain, ruby = build_ruby(text_cs, fcs)
                if len(plain.strip()) < 2:
                    continue
                sec = "basic" if off <= 1 else "applied"
                res[sec].append({"book": p - PAGE_OFFSET, "y": round(y, 1),
                                 "text": plain, "ruby": ruby})
        # --- 語法解釋/講解頁：抽 9pt 級文字行（含例句►），供文法卡複核
        if off in (2, 3, 4):
            mid = [c for c in chars if 8.0 <= c[0] < 12.5]
            for ln in cluster_lines(mid, ytol=4.0):
                text_cs = sorted(ln, key=lambda t: t[1])
                plain = "".join(c[5] for c in text_cs)
                if len(plain.strip()) < 2:
                    continue
                res["grammar_lines"].append({"book": p - PAGE_OFFSET,
                                             "y": round(min(c[2] for c in text_cs), 1),
                                             "text": plain})
        # --- 生词表：課文頁底部 25% 區域；含 10pt 簡體釋義字
        if off in (0, 1, 5, 6):
            vs = [c for c in chars if 8.0 <= c[0] < 11.0 and c[2] > H * 0.75]
            for ln in cluster_lines(vs, ytol=5.0):
                tc = sorted(ln, key=lambda t: t[1])
                y = min(c[2] for c in tc)
                fcs = [c for c in furi if 2 < y - c[2] < 14]
                plain, ruby = build_ruby(tc, fcs)
                for ent in VOCAB_SPLIT.split(ruby):
                    ent = ent.strip()
                    if not ent or ent.isdigit() or len(ent) < 2:
                        continue
                    res["vocab"].append({"book": p - PAGE_OFFSET, "entry": ent})
    return res

if __name__ == "__main__":
    doc = fitz.open(PDF)
    only = [int(a) for a in sys.argv[1:]] or list(LESSON_BOOK_PAGE)
    data = {}
    for les in only:
        data[les] = parse_lesson(doc, les)
        n = len(data[les].get("_lines", []))
        print(f"lesson {les}: lines={n} vocab={len(data[les]['vocab'])}")
    with io.open(ROOT + r"\std_extracted.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
