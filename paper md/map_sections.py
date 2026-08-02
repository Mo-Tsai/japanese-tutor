# -*- coding: utf-8 -*-
"""把 COURSE_CARDS 的每張卡對回講義的「章 → 節 → 任務/主題」三層分類。"""
import re, json, io, sys, os, unicodedata
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r"C:\Users\user\我的雲端硬碟\07_程式專案\Japanese-tutor"
HANDOUT = os.path.join(ROOT, "paper md", "講義全文_解碼後.md")
REVIEW  = os.path.join(ROOT, "paper md", "講義抽取卡片_複核用.md")
HTML    = os.path.join(ROOT, "japanese-tutor.html")
HERE    = os.path.dirname(os.path.abspath(__file__))

lines = io.open(HANDOUT, encoding="utf-8").read().split("\n")

# ---------- 1. 節標題 ----------
sec_re = re.compile(r"^(\d{1,2})-(\d{1,2})[．.](.+)$")
sections, seen = [], set()
for i, ln in enumerate(lines):
    m = sec_re.match(ln.strip())
    if m and (int(m.group(1)), int(m.group(2))) not in seen:
        seen.add((int(m.group(1)), int(m.group(2))))
        sections.append((i, int(m.group(1)), int(m.group(2)), m.group(3).strip()))

# ---------- 2. 第三層：任務標題 + 主題單字 ----------
def tidy(t, n=16):
    t = re.split(r"[。：:！？]", t.strip(), 1)[0].strip()
    head = t.split(" ", 1)[0]
    if len(head) >= 4: t = head          # 短開頭（如「3」）通常是被拆斷的句子，保留整句
    t = t.strip("－—-·、 ")
    return t[:n] + ("…" if len(t) > n else "")

task_re = re.compile(r"^【([^】]+)】(.*)$")
TASK_NO = re.compile(r"^任務\s*(\d+)")
marks = []   # (line, kind, name, short)  kind: 'task' | 'topic'
caps  = []   # (line, 主題單字的主題名)
for i, ln in enumerate(lines):
    s = ln.strip()
    m = task_re.match(s)
    if m:
        label, title = m.group(1).strip(), m.group(2).strip()
        if not title:
            for j in range(i + 1, min(i + 4, len(lines))):
                t = lines[j].strip()
                if t and not t.startswith("###") and not t.startswith("【"):
                    title = t
                    break
        tno = TASK_NO.match(label)
        if tno:
            short = "任務%s" % tno.group(1)
            name = "%s %s" % (short, tidy(title))
        else:
            short = tidy(label, 12)
            name = short
        marks.append((i, "task", name.strip(), short))
        continue
    if s.startswith("主題單字"):
        SKIP = {"中文", "日文", "備註", "例句", "實用例句", "讀音"}
        topic = s[4:].strip()
        if topic in SKIP: topic = ""
        if not topic:
            for j in range(i + 1, min(i + 6, len(lines))):
                t = lines[j].strip()
                if t and not t.startswith("###") and t not in SKIP:
                    topic = t
                    break
        if topic in SKIP: topic = ""
        topic = tidy(topic, 14)
        if topic:
            caps.append((i, topic))
marks.sort()

# ---------- 3. 頁碼 -> 行範圍 ----------
page_start, pg_re = {}, re.compile(r"^### p\.(\d+)$")
for i, ln in enumerate(lines):
    m = pg_re.match(ln.strip())
    if m:
        page_start[int(m.group(1))] = i
pages_sorted = sorted(page_start)
def page_range(p):
    if p not in page_start: return None
    i = pages_sorted.index(p)
    end = page_start[pages_sorted[i + 1]] if i + 1 < len(pages_sorted) else len(lines)
    return (page_start[p], end)

# ---------- 3b. 主題單字標題 ←→ 表格配對 ----------
# PDF 抽出來的文字，標題有時在表格上方、有時在下方（同一份講義兩種都有）。
# 一頁之內標題數通常等於表格數，所以看「這一頁第一個出現的是標題還是表頭」
# 就能判定方向，再照順序一對一配。配不上的就丟掉，寧可少一層也不要標錯。
page_bounds = [(page_start[p], page_start[pages_sorted[k + 1]] if k + 1 < len(pages_sorted) else len(lines))
               for k, p in enumerate(pages_sorted)]
# 主題單字：改用 pdf_topics.py 從 PDF 座標抽出來的對照表（見該檔說明）。
# markdown 的文字順序會把標題和表格顛倒，只有 PDF 的幾何位置可信。
# 這裡靠「卡片的中文意思」對回該詞出現在哪張表，再取那張表的主題。
pdf_blocks = json.load(io.open(os.path.join(HERE, "pdf_topics.json"), encoding="utf-8"))

# PDF 內文混用了「康熙部首」區的字，NFKC 蓋不到 U+2E80 這一段，手動補掉
RADICAL = {"⻄": "西", "⺠": "民", "⻑": "長", "⻤": "鬼", "⻘": "青", "⻟": "食", "⻝": "食",
           "⻩": "黃", "⻢": "馬", "⻥": "魚", "⻦": "鳥", "⻧": "鹵", "⻮": "齒",
           "⻯": "龍", "⻲": "龜", "⻈": "言", "⻋": "車", "⻎": "辵", "⻏": "邑"}
def clean(s):
    s = re.sub(r"\s+", "", unicodedata.normalize("NFKC", s or ""))
    return "".join(RADICAL.get(ch, ch) for ch in s)

TERM2TOPIC = defaultdict(list)     # 中文詞 -> [(頁, 主題)]
for pg, topic, terms in pdf_blocks:
    topic = clean(topic)
    for t in terms:
        t = clean(t)
        if len(t) >= 2:
            TERM2TOPIC[t].append((pg, topic))

def page_of(pos):
    """md 行號 -> 講義頁碼"""
    best = None
    for p in pages_sorted:
        if page_start[p] <= pos: best = p
        else: break
    return best

def topic_by_meaning(meaning, page):
    """用中文意思查主題；同一個詞出現在多張表時，取離這張卡所在頁最近的。"""
    m = clean(meaning)
    if len(m) < 2: return None
    hits = TERM2TOPIC.get(m)
    if not hits and page is not None:
        # 卡片的中文有時被改寫過（多了括號、換了說法）→ 只在同一頁附近做包含比對
        near = [(pg, tp, t) for t, v in TERM2TOPIC.items() for pg, tp in v
                if abs(pg - page) <= 1 and (t in m or m in t)]
        if near:
            hits = [(pg, tp) for pg, tp, _ in near]
    if not hits or page is None: return None
    best = min(hits, key=lambda h: abs(h[0] - page))
    # 同一個中文詞可能在別章也出現（睡衣＝服飾店／飯店備品）→ 離太遠就不算
    return best[1] if abs(best[0] - page) <= 2 else None


# ---------- 4. 章 ----------
CH_NAME = {2:"基礎句型",3:"禮儀篇",4:"餐廳篇",5:"購物篇",6:"住宿篇",7:"交通篇",
           8:"觀光篇",9:"狀況篇",10:"交友篇",11:"看病篇",12:"生活篇"}
NAME_CH = {v: k for k, v in CH_NAME.items()}
ch_range = {}
for ch in CH_NAME:
    start = [s for s in sections if s[1] == ch][0][0]
    later = [s for s in sections if s[1] > ch]
    ch_range[ch] = (start, later[0][0] if later else len(lines))

# ---------- 5. 複核檔頁碼 ----------
CH_TITLE_RE = re.compile(r"^## 第(.+?)章(.*)$")
CN = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10,"十一":11,"十二":12}
review_pages, cur_ch = {}, None
for ln in io.open(REVIEW, encoding="utf-8"):
    m = CH_TITLE_RE.match(ln.rstrip("\n"))
    if m:
        cur_ch = CN.get(m.group(1).strip()); continue
    if ln.startswith("|") and cur_ch:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] in ("日文", "---"): continue
        try: pg = int(cells[-1])
        except ValueError: continue
        review_pages.setdefault((cur_ch, cells[0].replace("\\", "")), pg)

# ---------- 6. 讀 HTML 卡片 ----------
html = io.open(HTML, encoding="utf-8").read().split("\n")
start = next(i for i, l in enumerate(html) if l.startswith("const COURSE_CARDS"))
end   = next(i for i in range(start, len(html)) if html[i].strip() == "];")
cards = []
for i in range(start + 1, end):
    l = html[i]
    if not l.strip().startswith("{id:"): continue
    def f(name):
        m = re.search(r'\b%s:"((?:[^"\\]|\\.)*)"' % name, l)
        return m.group(1) if m else ""
    cards.append({"line": i, "id": f("id"), "jp": f("jp"), "chapter": f("chapter"),
                  "meaning": f("meaning")})
print("卡片數:", len(cards), "／節:", len(sections), "／第三層標記:", len(marks))

# ---------- 7. 定位 ----------
def occ(text, lo, hi):
    return [i for i in range(lo, hi) if text and text in lines[i]]

stat = Counter()
by_ch = defaultdict(list)
for c in cards: by_ch[c["chapter"]].append(c)

for chname, group in by_ch.items():
    ch = NAME_CH.get(chname)
    if ch is None:
        for c in group: c["pos"] = None
        continue
    lo, hi = ch_range[ch]
    prev = lo
    for c in group:
        jp, cand = c["jp"], []
        pg = review_pages.get((ch, jp))
        if pg and page_range(pg):
            a, b = page_range(pg)
            cand = occ(jp, a, b)
            if not cand:
                for k in (10, 6, 4):
                    cand = occ(jp[:k], a, b)
                    if cand: break
            if not cand: cand = [a]
            stat["review"] += 1
        if not cand:
            cand = occ(jp, lo, hi)
            if not cand:
                for k in (12, 8, 5):
                    if len(jp) <= k: break
                    cand = occ(jp[:k], lo, hi)
                    if cand: break
            if cand: stat["search"] += 1
        if not cand:
            c["pos"] = prev; stat["inherit"] += 1; continue
        fwd = [x for x in cand if x >= prev]
        c["pos"] = fwd[0] if fwd else cand[-1]
        prev = c["pos"]

print("定位來源:", dict(stat))

# ---------- 8. pos -> 節 / 細分類 ----------
def last_le(seq, pos):
    best = None
    for it in seq:
        if it[0] <= pos: best = it
        else: break
    return best

# 只有「中文意思剛好等於表格詞條」的卡查得到主題，中間常有漏網的。
# 卡片依講義順序排好後，若某張卡前後最近的兩張錨點卡屬於同一個主題，
# 那它夾在中間也一定是同一張表 → 補上。前後主題不同就不猜。
anchors = {}
for c in cards:
    if c["pos"] is not None:
        anchors[c["id"]] = topic_by_meaning(c["meaning"], page_of(c["pos"]))
filled = 0
for chname, group in by_ch.items():
    seq = sorted([c for c in group if c["pos"] is not None], key=lambda c: c["pos"])
    for idx, c in enumerate(seq):
        if anchors.get(c["id"]): continue
        before = next((seq[j] for j in range(idx - 1, -1, -1) if anchors.get(seq[j]["id"])), None)
        after  = next((seq[j] for j in range(idx + 1, len(seq)) if anchors.get(seq[j]["id"])), None)
        if before and after and anchors[before["id"]] == anchors[after["id"]]:
            anchors[c["id"]] = anchors[before["id"]]
            filled += 1
print("主題內插補上:", filled)

out = {}
for c in cards:
    if c["pos"] is None: continue
    ch = NAME_CH.get(c["chapter"])
    s = last_le(sections, c["pos"])
    if not s or s[1] != ch:
        cands = [x for x in sections if x[1] == ch]
        s = cands[0] if cands else None
    sec = "%d-%d %s" % (s[1], s[2], s[3]) if s else ""
    # 第三層：節內最後一個 task，若其後還有更近的 topic 就接上
    sub, subpos = "", c["pos"]
    if s:
        task = [m for m in marks if m[1] == "task" and s[0] <= m[0] <= c["pos"]]
        t = task[-1] if task else None
        topic = anchors.get(c["id"])
        if t and topic:
            sub, subpos = "%s · %s" % (t[3], topic), c["pos"]
        elif t:
            sub, subpos = t[2], t[0]
        elif topic:
            sub, subpos = topic, c["pos"]
    out[c["id"]] = {"sec": sec, "sub": sub, "secPos": s[0] if s else 0, "subPos": subpos}

# ---------- 9. 依講義順序整理出目錄樹 ----------
tree = defaultdict(lambda: defaultdict(Counter))
pos_sec, pos_sub = {}, {}
for c in cards:
    d = out.get(c["id"])
    if not d: continue
    sb = d["sub"] or "（未分節）"
    tree[c["chapter"]][d["sec"]][sb] += 1
    pos_sec.setdefault((c["chapter"], d["sec"]), d["secPos"])
    pos_sub[(c["chapter"], d["sec"], sb)] = min(pos_sub.get((c["chapter"], d["sec"], sb), 10**9), d["subPos"])

CH_ORDER = ['基礎句型','禮儀篇','餐廳篇','購物篇','住宿篇','交通篇',
            '觀光篇','狀況篇','交友篇','看病篇','生活篇']
js_tree, tot_sec, tot_sub = [], 0, 0
report = io.open(os.path.join(HERE, "tree.txt"), "w", encoding="utf-8")
for chn in sorted(tree, key=lambda x: CH_ORDER.index(x) if x in CH_ORDER else 99):
    report.write("\n■ %s（%d）\n" % (chn, sum(sum(v.values()) for v in tree[chn].values())))
    node = {"ch": chn, "secs": []}
    for sec in sorted(tree[chn], key=lambda x: pos_sec[(chn, x)]):
        tot_sec += 1
        report.write("  ▸ %s（%d）\n" % (sec, sum(tree[chn][sec].values())))
        subs = sorted(tree[chn][sec], key=lambda x: pos_sub[(chn, sec, x)])
        for sb in subs:
            tot_sub += 1
            report.write("      · %s（%d）\n" % (sb, tree[chn][sec][sb]))
        node["secs"].append({"sec": sec, "subs": subs})
    js_tree.append(node)
report.close()
print("節數:", tot_sec, " 細分類數:", tot_sub)

for v in out.values():
    v.pop("secPos", None); v.pop("subPos", None)
json.dump(out, io.open(os.path.join(HERE, "card_sections.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)
json.dump(js_tree, io.open(os.path.join(HERE, "course_tree.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
