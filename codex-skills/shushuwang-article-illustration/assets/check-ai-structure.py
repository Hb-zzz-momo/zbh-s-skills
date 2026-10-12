"""结构级 AI 痕迹体检。

为什么单独做这个：早年那份「词表扫描」只能查禁用词（此外/赋能/抓手…），
而真正暴露"AI 在完成一篇完整科普"的是**结构**——讲义式编号、自测题、
术语连排定义、段落过于齐整、过渡胶水句。词表一条都扫不到。

用法：
    python -X utf8 check-ai-structure.py <文章.md> [--ref <参照文章.md>]

判据来自 2026-09-26 的一次外部审稿（ChatGPT 指出 9 处结构问题，
我们的词表扫描全部漏掉）与两篇已发布样本的实测。
"""
import re
import statistics
import sys
from pathlib import Path

# 过渡胶水句：宣布"接下来讲什么"或"这说明了什么"，本身不提供信息
GLUE = ["更麻烦的是", "它说明了一件事", "区分方法很简单", "同样形状的事还有很多",
        "同样的结构也出现在", "站在.*角度算一遍", "值得注意的是", "不难发现",
        "换句话说", "由此可以看出", "这也就意味着", "需要注意的是"]
# 教学模板件：出现在技术分享里就是"AI 微课"信号
TEACHING = ["自测", "先自己答一遍", "答案：", "练习", "小测验", "思考题"]


def load(path):
    t = Path(path).read_text(encoding="utf-8")
    t = re.sub(r"^---\n.*?\n---\n", "", t, flags=re.S)
    return t


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    path = argv[1]
    ref = argv[argv.index("--ref") + 1] if "--ref" in argv else None
    text = load(path)
    heads = re.findall(r"^##\s+(.+)$", text, re.M)
    paras = [l.strip() for l in text.split("\n")
             if l.strip() and not l.startswith(("#", "|", "!", ">"))]
    body = [p for p in paras if not p.startswith("-")]
    plain = re.sub(r"\*\*|\s", "", "".join(body))

    fails, warns = [], []

    # 先算两个"配料"，编号本身是不是问题要看它们
    # 教学模板件
    hits = [k for k in TEACHING if k in text]

    # 术语连排定义：「**中文（English）**：定义」连续出现
    runs = re.findall(r"\*\*[^*（）()]{2,12}[（(][A-Za-z][^）)]*[）)]\*\*[：:]", text)

    # 1. 讲义式编号：参照样本（已发的那篇）也用「N. 」序号，所以编号本身只算 WARN；
    #    只有跟教学件/连排定义同时出现，才判成"AI 微课"。
    numbered = [h for h in heads if re.match(r"^\d+[.、]\s", h)]
    all_numbered = bool(heads) and len(numbered) == len(heads) and len(heads) >= 6
    if all_numbered and (hits or len(runs) >= 2):
        fails.append(f"全部 {len(heads)} 个标题带「N. 」序号，且同时有教学模板件或连排定义，整体是「AI 微课」结构")
    elif all_numbered:
        warns.append(f"全部 {len(heads)} 个标题带「N. 」序号（参照那篇也用序号，本身不算问题；留意别和自测题同时出现）")

    # 2. 教学模板件
    if hits:
        fails.append(f"出现教学模板件 {hits}：课程类可以有，技术分享/信息分享里应删掉或改成开放式收尾")

    # 3. 术语连排定义：「**中文（English）**：定义」连续出现
    if len(runs) >= 2:
        fails.append(f"连续出现 {len(runs)} 个「术语（English）：定义」的百科式定义，应拆进叙述里一个个出现")

    # 4. 过渡胶水句
    glue = []
    for g in GLUE:
        n = len(re.findall(g, text))
        if n:
            glue.append(f"{g}×{n}")
    if len(glue) >= 3:
        fails.append("过渡胶水句偏多：" + "、".join(glue) + "。留 1–2 处，其余直接删")
    elif glue:
        warns.append("有过渡胶水句：" + "、".join(glue))

    # 5. 段落机械齐整：段长离散度太低
    PL = [len(p) for p in body if len(p) > 8]
    if len(PL) >= 8:
        cv = statistics.pstdev(PL) / max(1, statistics.mean(PL))
        if cv < 0.35:
            fails.append(f"段落长度过于齐整（离散系数 {cv:.2f}）：每段都像一个模块，应允许长短不一")
        else:
            warns.append(f"段落长度离散系数 {cv:.2f}（越大越自然）")

    # 6. 全文没有长段
    if PL and max(PL) < 90:
        warns.append(f"最长段只有 {max(PL)} 字：全文等长短段也显机械，允许有一两段展开")

    # 7. AI 免责声明 boilerplate
    if re.search(r"不构成任何?[^。]*建议", text):
        warns.append("有「不构成…建议」式免责声明：技术类内容通常不需要，由作者决定留不留")

    # 8. 文件核验口吻
    if re.search(r"故未采用|经.{0,12}条目回溯|尚待考证|不予采纳", text):
        warns.append("出现文献核验口吻（「……故未采用」这类公文腔）：通俗文里读起来割裂，改成人话")

    print(f"文件：{path}")
    print(f"  标题 {len(heads)} 个（带序号 {len(numbered)}）｜正文段落 {len(body)}｜正文 {len(plain)} 字")
    if ref:
        rt = load(ref)
        rheads = re.findall(r"^##\s+(.+)$", rt, re.M)
        rbody = [l.strip() for l in rt.split("\n")
                 if l.strip() and not l.startswith(("#", "|", "!", ">", "-"))]
        print(f"  参照：标题 {len(rheads)} 个（带序号 {sum(1 for h in rheads if re.match(r'^\\d+[.、]', h))}）"
              f"｜正文段落 {len(rbody)}｜正文 {len(re.sub(r'[* ]', '', ''.join(rbody)))} 字")
    for f in fails:
        print("  FAIL " + f)
    for w in warns:
        print("  WARN " + w)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
