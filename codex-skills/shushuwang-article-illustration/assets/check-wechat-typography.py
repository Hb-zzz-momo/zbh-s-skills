"""公众号稿排版门禁。

为什么要有它：排版参数曾经只写进了本地预览（build_preview.py 的 <style>），
而真正发出去的公众号稿（build_wechat.py 的内联样式）里正文段落**一条样式都没有**，
落到编辑器默认值，整篇偏小偏紧。当时的验收断言全是「有没有」类（框数、图数、图注数、
有没有外链），对字号行高完全无感，所以这个洞一路没被发现。

用法：
    python -X utf8 check-wechat-typography.py <微信公众号-发布稿.html>
参数改动时必须同步改这里，否则门禁会拦住——这是故意的。
"""
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

BODY_P = "color:#333333;font-size:17px;line-height:1.85;margin:15px 0;overflow-wrap:anywhere;"
H2_SIZE = "font-size:23px"
CAP_SIZE = "font-size:15px"
MIN_BODY_PARAS = 5


def main(path):
    html = Path(path).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("title").get_text(strip=True) if soup.find("title") else ""
    paras = soup.find_all("p")
    prose = [p for p in paras if not p.find("img")]
    caps = [p for p in paras if re.match(r"^图\s*\d", p.get_text(strip=True))]
    h2s = soup.find_all("h2")
    fails = []

    if len(h2s) < 3:
        fails.append(f"小标题太少（{len(h2s)} 个），可能没解析到正文")
    bad_h2 = [h for h in h2s if H2_SIZE not in (h.get("style") or "")]
    if bad_h2:
        fails.append(f"有 {len(bad_h2)} 个小标题不是 {H2_SIZE}：{bad_h2[0].get_text(strip=True)[:16]}")
    unnumbered = [h for h in h2s if not re.match(r"^\d+[.、]\s", h.get_text(strip=True))]
    if unnumbered:
        fails.append(f"有 {len(unnumbered)} 个小标题没有「N. 」序号：{unnumbered[0].get_text(strip=True)[:16]}")

    styled = [p for p in prose if (p.get("style") or "") == BODY_P]
    if len(styled) < MIN_BODY_PARAS:
        fails.append(f"正文段落只有 {len(styled)} 段带了 {BODY_P!r}，至少 {MIN_BODY_PARAS} 段")
    naked = [p for p in prose if not (p.get("style") or "").strip()]
    if naked:
        fails.append(f"有 {len(naked)} 个段落完全没有样式（落到编辑器默认值）")

    if not caps:
        fails.append("没有识别到图注段落（应以「图 N」开头）")
    bad_cap = [p for p in caps if CAP_SIZE not in (p.get("style") or "")]
    if bad_cap:
        fails.append(f"有 {len(bad_cap)} 条图注不是 {CAP_SIZE}")

    rounded = [i for i in soup.find_all("img") if "border-radius" in (i.get("style") or "")]
    if rounded:
        fails.append(f"有 {len(rounded)} 张图带了圆角（公众号稿不要圆角）")

    toc = [a for a in soup.find_all("a", href=True) if a["href"].startswith("#")]
    if toc:
        fails.append(f"正文里残留 {len(toc)} 个页内锚点链接（公众号里全失效）")

    nested = [p for p in paras if p.find("p")]
    if nested:
        fails.append(f"有 {len(nested)} 处 <p> 套 <p>（非法结构，粘贴到编辑器时容易掉样式）")

    if title and title in soup.find("body").get_text():
        fails.append("正文重复了标题（标题是平台独立字段）")

    print(f"文件：{path}")
    print(f"  段落 {len(paras)}（正文 {len(prose)}，规范内 {len(styled)}）｜小标题 {len(h2s)}｜图注 {len(caps)}")
    if fails:
        for f in fails:
            print("  FAIL " + f)
        print(f"\n{len(fails)} 项不达标")
        return 1
    print("  排版门禁全部通过")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
