#!/usr/bin/env python3
"""实验报告交付前强制校验。

硬性门禁（不通过则必须改后重跑，不得交付）：
  1. 一级章节阶梯（一、二、三…）与参考件逐字一致且顺序一致
  2. --require 指定的结构性子章节必须存在（如“（一）实验环境”“（二）实验总体逻辑链路”）
  3. AI Report 的字段结构与参考件一致（字段名与顺序、条目数不少于参考件）
  4. --forbidden 指定的禁用内容（他人姓名/学号、服务器 IP 等）出现 0 次
  5. 插图数量与尺寸合规（宽度 ≤ 6.3 in、高度 ≤ 7.5 in）
  6. 给了 --pdf 时：正文与插图不得超出页边距
  7. 根据 --code-presentation 与 --result-presentation 分别检查课程证据呈现规则。
     默认either，不把截图偏好泛化；检测不替代人工覆盖核查。
提示项（WARN，需人工确认）：
  - 二级章节与参考件不完全一致
  - 页尾空白过大、整页只有一张图

用法：
  python check_report.py --template 参考件.docx --report 成品.docx
         [--pdf 成品.pdf] [--forbidden "张三,20231234,10.0.0.1"]
         [--require "（一）实验环境,（二）实验总体逻辑链路"]
退出码：0 = 通过；1 = 有阻塞问题。
"""
import argparse
import json
import os
import re
import sys
import zipfile

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Emu
from docx.text.paragraph import Paragraph

L1 = re.compile(r"^[一二三四五六七八九十]+、")
L2 = re.compile(r"^（[一二三四五六七八九十]+）")
AI_ITEM = re.compile(r"^AI\s*Report\s*\d+")
FIELD = re.compile(r"^\d+\.\s*\S+")

# 正式报告里的代码与结果强特征；解释性正文中的单个术语不算代码段。
TEXT_EVIDENCE = [
    (re.compile(r"^\s*SELECT\s+.+\s+FROM\s+\w+", re.I), "正文粘贴SQL语句，应使用截图"),
    (re.compile(r"^\s*(?:public\s+)?(?:class|interface)\s+\w+\s*[{(]"), "正文粘贴源代码，应使用截图"),
    (re.compile(r"^\s*(?:function\s+\w+\s*\(|(?:const|let)\s+\w+\s*=)"), "正文粘贴JavaScript，应使用截图"),
    (re.compile(r"^\s*</?(?:html|div|table|select|project|dependency|mapper)\b[^>]*>"), "正文粘贴HTML或配置，应使用截图"),
    (re.compile(r"^\s*[>$#]\s*(curl|docker|mysql|wsl|python3?|pip|kubectl)\b"), "命令提示符后面跟着运行输出"),
    (re.compile(r"^\+-{3,}\+"), "数据库客户端的结果表"),
    (re.compile(r"^\s*mysql:\s*\[Warning\]"), "mysql 客户端输出"),
    (re.compile(r"^\s*(CONTAINER ID|NAMES)\s+(IMAGE|IMAGE)\b"), "docker ps 输出"),
    (re.compile(r"^\s*\d+\s+rows? in set\b"), "mysql 结果行数提示"),
    (re.compile(r"^\s*Empty set\b"), "mysql 空结果提示"),
    (re.compile(r"^\s*(?:#\s*)?\[\s*\d+\s*/\s*\d+\s*\]"), "脚本自己打印的进度行"),
    (re.compile(r"^\s*(?:#\s*)?共\s*(?:下载|抓取|保存|处理|生成|采集)\s*\d+"), "脚本自己打印的统计行"),
    (re.compile(r"\S+\.(?:jpg|jpeg|png|bmp)\s+\d{2,5}x\d{2,5}\b"), "脚本打印的逐张结果行"),
]

# 接口返回信封：整段里既出现 "code": 200 又出现 "data"/"count"，才算把返回体抄下来；
# 正文里顺口引用 {"code":"500"} 这种不算（那是引用报错，不是粘贴返回体）。
JSON_ENVELOPE = re.compile(r'(?s)(?=.*"code"\s*:\s*"?\d{3})(?=.*"(?:data|count)"\s*:)')


def all_paragraphs(doc):
    """按文档顺序读取正文及所有层级表格，避免漏掉课程模板内的内容。"""
    return [Paragraph(p, doc) for p in doc.element.body.iter(qn('w:p'))]


def text_evidence(doc, limit=4, code_presentation="either", result_presentation="either"):
    """找出疑似把运行结果直接粘成文字的段落/单元格。"""
    hits = []

    def scan(text):
        if result_presentation == "screenshot" and JSON_ENVELOPE.search(text):
            hits.append(("接口返回的 JSON 返回体", " ".join(text.split())[:70]))
            return
        for raw in text.split("\n"):
            line = raw.strip()
            if not line:
                continue
            for idx, (pat, kind) in enumerate(TEXT_EVIDENCE):
                if idx < 4 and code_presentation != "screenshot": continue
                if idx >= 4 and result_presentation != "screenshot": continue
                if pat.search(line):
                    hits.append((kind, line[:70]))
                    return

    for p in all_paragraphs(doc):
        if p.text.strip():
            if p.style and p.style.name == 'CodeBlock' and code_presentation == 'screenshot':
                hits.append(("正文CodeBlock应改为真实截图",p.text[:70]))
            else:
                scan(p.text)
    return hits[:limit], len(hits)


def outline(doc):
    """返回 (一级章节列表, 二级章节列表, AI 条目->字段列表)"""
    l1, l2, ai = [], [], []
    for par in all_paragraphs(doc):
        text = par.text.strip()
        if not text:
            continue
        runs = [r for r in par.runs if r.text.strip()]
        bold = bool(runs) and all(r.bold for r in runs)
        parent = par._p.getparent()
        cell_heading = parent.tag == qn('w:tc') and parent.find(qn('w:p')) is par._p
        auto_numbered = cell_heading and par._p.find('./' + qn('w:pPr') + '/' + qn('w:numPr')) is not None
        if (bold or cell_heading) and (L1.match(text) or auto_numbered):
            l1.append(text)
            ai.append(None)
        elif bold and L2.match(text):
            l2.append(text)
        elif bold and AI_ITEM.match(text):
            ai.append((text, []))
        elif FIELD.match(text) and ai and isinstance(ai[-1], tuple):
            ai[-1][1].append(re.sub(r"^\d+\.\s*", "", text).split("：")[0].strip())
    return l1, l2, [a for a in ai if a]


def pdf_bounds(path):
    """量出参考件实际渲染出的内容边界（左右以上下为绝对页边距）。"""
    import fitz

    pdf = fitz.open(path)
    left, right, top = 1e9, -1e9, 1e9
    max_gap = 0.0
    for page in pdf:
        boxes = [b[:4] for b in page.get_text("blocks") if b[6] == 0]
        boxes += [(r.x0, r.y0, r.x1, r.y1)
                  for r in (page.get_image_bbox(im) for im in page.get_images(full=True))]
        if not boxes:
            continue
        left = min(left, min(b[0] for b in boxes))
        right = max(right, max(b[2] for b in boxes))
        top = min(top, min(b[1] for b in boxes))
        gap = (page.rect.height - 72.0) - max(b[3] for b in boxes)
        max_gap = max(max_gap, gap / 72.0)
    return {"left_min": round(left, 1), "right_max": round(right, 1),
            "top_min": round(top, 1), "max_bottom_gap_in": round(max_gap, 2)}


def brief(items, n=3):
    """二级章节差异可能很多，只列前几项，避免刷屏。"""
    head = [x if len(x) <= 16 else x[:16] + "…" for x in items[:n]]
    return head + ([f"（共 {len(items)} 项）"] if len(items) > n else [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--pdf")
    ap.add_argument("--forbidden", default="")
    ap.add_argument("--require", default="")
    ap.add_argument("--bounds", help="参考件的版式边界 JSON（由 --emit-bounds 生成）")
    ap.add_argument("--emit-bounds", help="量出参考件边界并写入该 JSON 后退出")
    ap.add_argument("--allow-text-evidence", action="store_true",
                    help="仅在用户明确同意文字例外后使用，并在报告中说明原因")
    ap.add_argument("--code-presentation", choices=["text","screenshot","either"], default="either")
    ap.add_argument("--result-presentation", choices=["screenshot","either"], default="either")
    args = ap.parse_args()

    if args.emit_bounds:
        data = pdf_bounds(args.pdf or args.template)
        with open(args.emit_bounds, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        print("已写入版式边界:", data)
        return 0

    t_l1, t_l2, t_ai = outline(Document(args.template))
    r_l1, r_l2, r_ai = outline(Document(args.report))
    fails, warns = [], []

    if t_l1 != r_l1:
        fails.append("一级章节与参考件不一致")
        print("  参考件:", " / ".join(t_l1))
        print("  成品  :", " / ".join(r_l1))
    extra = [x for x in r_l2 if x not in t_l2]
    missing_l2 = [x for x in t_l2 if x not in r_l2]
    if missing_l2 or extra:
        warns.append(f"二级章节差异：参考件独有 {brief(missing_l2)}；成品独有 {brief(extra)}")

    for item in [x for x in args.require.split(",") if x.strip()]:
        if item.strip() not in r_l2:
            fails.append(f"缺少结构性子章节：{item.strip()}")

    if len(r_ai) < len(t_ai):
        fails.append(f"AI Report 条目 {len(r_ai)} 条，少于参考件的 {len(t_ai)} 条")
    else:
        want = t_ai[0][1] if t_ai else []
        for title, fields in r_ai:
            if want and fields[:len(want)] != want:
                fails.append(f"{title} 的字段结构与参考件不一致：{fields} != {want}")

    z = zipfile.ZipFile(args.report)
    body = re.sub(r"<[^>]+>", "", z.read("word/document.xml").decode("utf-8")
                  .replace("</w:p>", "\n"))
    for s in [x.strip() for x in args.forbidden.split(",") if x.strip()]:
        n = body.count(s)
        if n:
            fails.append(f"出现禁用内容“{s}”×{n}")

    doc = Document(args.report)
    hits, total = text_evidence(doc, code_presentation=args.code_presentation, result_presentation=args.result_presentation)
    if args.code_presentation == "text":
        code_hits, ncode = text_evidence(doc, code_presentation="screenshot", result_presentation="either")
        if not ncode: fails.append("课程要求文本核心代码，但未检测到；需人工核对代码标识与正文")
    if total:
        detail = "；".join(f"{k} → {s}" for k, s in hits)
        (warns if args.allow_text_evidence else fails).append(
            f"疑似违反本次代码或结果呈现规则（{total} 处）：{detail}")

    sizes = [(Emu(int(e.get("cx"))).inches, Emu(int(e.get("cy"))).inches)
             for p in all_paragraphs(doc) for e in p._p.findall(".//" + qn("wp:extent"))]
    bad = [s for s in sizes if s[0] > 6.3 or s[1] > 7.5]
    if bad:
        fails.append(f"插图尺寸超限：{bad}")

    if args.pdf:
        import fitz

        bounds = None
        if args.bounds and os.path.exists(args.bounds):
            bounds = json.load(open(args.bounds, encoding="utf-8"))
        pdf = fitz.open(args.pdf)
        L = bounds["left_min"] if bounds else 85.0
        R = bounds["right_max"] if bounds else 556.0
        sec = doc.sections[0]
        T, B = sec.top_margin.pt, sec.bottom_margin.pt
        if not bounds: L, R = sec.left_margin.pt, sec.page_width.pt - sec.right_margin.pt
        for i, page in enumerate(pdf, 1):
            W, H = page.rect.width, page.rect.height
            boxes = [b[:4] for b in page.get_text("blocks") if b[6] == 0]
            boxes += [(r.x0, r.y0, r.x1, r.y1)
                      for r in (page.get_image_bbox(im) for im in page.get_images(full=True))]
            for x0, y0, x1, y1 in boxes:
                if x0 < L - 6 or x1 > R + 6 or y0 < T - 14 or y1 > H - B + 14:
                    fails.append(f"第 {i} 页有内容超出页边距：({x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f})")
            bottom = max([b[3] for b in boxes], default=0)
            gap = (H - B) - bottom
            limit = max(4.5, (bounds or {}).get("max_bottom_gap_in", 0) + 0.8)
            if gap > limit * 72:
                fails.append(f"第 {i} 页页尾空白 {gap / 72:.1f} in（> {limit:.1f} in）")
            elif gap > 3.0 * 72 and i != pdf.page_count:
                warns.append(f"第 {i} 页页尾空白 {gap / 72:.1f} in")
            if i != 1 and len(page.get_images(full=True)) == 1 and len(page.get_text("blocks")) <= 1:
                warns.append(f"第 {i} 页整页只有一张图")

    print(f"一级章节 {len(r_l1)} 个，二级章节 {len(r_l2)} 个，AI Report {len(r_ai)} 条，插图 {len(sizes)} 张")
    for w in warns:
        print("  [warn]", w)
    for f in fails:
        print("  [FAIL]", f)
    print("交付门禁：" + ("通过" if not fails else f"不通过（{len(fails)} 项阻塞）"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
