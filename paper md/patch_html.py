# -*- coding: utf-8 -*-
"""把 sec / sub 欄位寫進 COURSE_CARDS，並插入 COURSE_TREE 目錄樹。"""
import json, io, re, os, sys
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r"C:\Users\user\我的雲端硬碟\07_程式專案\Japanese-tutor"
HTML = os.path.join(ROOT, "japanese-tutor.html")
HERE = os.path.dirname(os.path.abspath(__file__))

secs = json.load(io.open(os.path.join(HERE, "card_sections.json"), encoding="utf-8"))
tree = json.load(io.open(os.path.join(HERE, "course_tree.json"), encoding="utf-8"))

for d in secs.values():
    for v in (d["sec"], d["sub"]):
        assert '"' not in v and "\\" not in v, v

src = io.open(HTML, encoding="utf-8").read()
lines = src.split("\n")
start = next(i for i, l in enumerate(lines) if l.startswith("const COURSE_CARDS"))
end   = next(i for i in range(start, len(lines)) if lines[i].strip() == "];")

patched = skipped = 0
for i in range(start + 1, end):
    l = lines[i]
    if not l.strip().startswith("{id:"): continue
    l = re.sub(r',sec:"[^"]*",sub:"[^"]*"', "", l)   # 舊的先拆掉，重跑時才不會疊加
    cid = re.search(r'id:"([^"]+)"', l).group(1)
    d = secs.get(cid)
    if not d:
        skipped += 1; continue
    ins = ',sec:"%s",sub:"%s"' % (d["sec"], d["sub"])
    new = re.sub(r'(chapter:"[^"]*")', lambda m: m.group(1) + ins, l, count=1)
    if new == l:                          # 沒有 chapter 欄位 → 加在 id 後面
        new = re.sub(r'(id:"[^"]*")', lambda m: m.group(1) + ins, l, count=1)
    lines[i] = new
    patched += 1

print("已加欄位:", patched, " 跳過:", skipped)

# ---- 插入 COURSE_TREE ----
tree_js = "COURSE_TREE = [\n" + ",\n".join(
    '{ch:"%s",secs:[%s]}' % (
        n["ch"],
        ",".join('{sec:"%s",subs:[%s]}' % (s["sec"], ",".join('"%s"' % b for b in s["subs"]))
                 for s in n["secs"])
    ) for n in tree) + "\n];"

block = ("\n// ===== 講義目錄樹：章 → 節 → 任務／主題（依課本順序）=====\n"
         "// 由 PDF 講義的節標題（X-Y．…）與【任務N】／主題單字標題自動對出來的三層目錄，\n"
         "// 讓分類選單可以往下鑽，不用再從一大袋卡片裡翻。\n"
         "const " + tree_js + "\n")

marker = "// ===== 分類軸：章節（新）"
assert marker in src
if "const COURSE_TREE" not in src:
    out = "\n".join(lines).replace(marker, block.lstrip("\n") + "\n" + marker, 1)
else:
    out = "\n".join(lines)
    out = re.sub(r"const COURSE_TREE = \[[\s\S]*?\n\];", tree_js.replace("COURSE_TREE", "const COURSE_TREE", 1), out, count=1)

io.open(HTML, "w", encoding="utf-8", newline="").write(out)
print("寫入完成，檔案大小:", len(out))
