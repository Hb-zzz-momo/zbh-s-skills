"""颜色轻重体检：统计每种颜色承载了多少文字，看整篇是不是"只有重、没有轻"。

用法：python -X utf8 check-color-weight.py <微信公众号-发布稿.html> [--ref]

判据来自同账号已发文章的实测（见 SKILL.md「颜色要分轻重」）：
    正文 #333 约 72%、标题 #184c50 约 4%、次级 #506665/#60706f 约 16%、
    浅底框约 7%、深底代码块约 5%。
次级（图注/来源/说明）低于 10% 会告警：整篇都是"重"的，读起来没有轻重。
"""
import collections
import re
import sys

from bs4 import BeautifulSoup

HEAVY_BODY = {"#333", "#333333", "rgb(51,51,51)", "rgb(51, 51, 51)"}
HEAVY_TITLE = {"#184c50"}
LIGHT = {"#506665", "#60706f", "#8a9693", "#666", "#666666"}
LIGHT_FLOOR = 10.0


def profile(path):
    soup = BeautifulSoup(open(path, encoding="utf-8", errors="ignore").read(), "html.parser")
    root = soup.find(id="js_content") or soup.find("body")
    text_by_color = collections.Counter()
    bg_text = collections.Counter()
    bg_tone = collections.Counter()
    for el in root.find_all(True):
        st = re.sub(r"\s+", "", el.get("style") or "")
        m = re.search(r"color:(#[0-9a-fA-F]{3,6}|rgb\([^)]*\))", st)
        if m and el.strings:
            own = "".join(el.strings)
            if own.strip():
                text_by_color[m.group(1).lower()] += len(re.sub(r"\s", "", own))
        b = re.search(r"background:(#[0-9a-fA-F]{3,6}|rgb\([^)]*\))", st)
        if b:
            tone = b.group(1).lower()
            bg_tone[tone] += 1
            bg_text[tone] += len(re.sub(r"\s", "", el.get_text("")))
    has_code = bool(soup.find(["code", "pre"])) or any(
        "172d33" in (e.get("style") or "") for e in soup.find_all(True))
    return text_by_color, bg_text, bg_tone, has_code


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    path = argv[1]
    text_by_color, bg_text, bg_tone, has_code = profile(path)
    total = sum(text_by_color.values()) or 1

    def share(pred):
        return sum(v for k, v in text_by_color.items() if pred(k)) / total * 100

    body = share(lambda c: c in HEAVY_BODY or c == "rgb(51,51,51)")
    title = share(lambda c: c in HEAVY_TITLE)
    light = share(lambda c: c in LIGHT)
    tinted = sum(bg_text.values()) / total * 100

    print(f"文件：{path}")
    print(f"  正文（重）      {body:5.1f}%")
    print(f"  标题（重）      {title:5.1f}%")
    print(f"  次级（轻）      {light:5.1f}%   ← 目标 ≥ {LIGHT_FLOOR}%")
    print(f"  底纹框文字      {tinted:5.1f}%   底纹层次 {len(bg_tone)} 种 {dict(bg_tone.most_common(4))}")
    print("  全部颜色占比：")
    for k, v in text_by_color.most_common(8):
        print(f"    {k:22s} {v / total * 100:5.1f}%")

    warns = []
    if light < LIGHT_FLOOR:
        warns.append(f"次级文字只有 {light:.1f}%，低于 {LIGHT_FLOOR}%：整篇偏重，没有轻重对比")
    if len(bg_tone) < 2 and has_code:
        warns.append(f"底纹只有 {len(bg_tone)} 种层次：有代码/命令却没给深底块，技术细节会失去重量")
    if warns:
        for w in warns:
            print("  WARN " + w)
        return 1
    print("  颜色轻重正常")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
