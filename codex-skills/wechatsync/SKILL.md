---
name: wechatsync
description: "Multi-platform article publisher and content distribution tool. Sync and cross-post Markdown/HTML articles to 29+ platforms including Zhihu (知乎), Juejin (掘金), CSDN, Toutiao (头条), Weibo (微博), Xiaohongshu (小红书), Bilibili (B站), WordPress, Typecho, WeChat (微信公众号), and more. Use when the user wants to publish, sync, cross-post, or distribute articles (文章同步/多平台发布/一键发布) to Chinese content platforms, tech communities, blogging sites, or self-hosted blogs. Also use when checking platform login status or extracting articles from web pages. Keywords: content syndication, blog distribution, multi-platform publishing, self-media (自媒体), content creator tools."
metadata:
  openclaw:
    requires:
      env:
        - WECHATSYNC_TOKEN
      bins:
        - wechatsync
    primaryEnv: WECHATSYNC_TOKEN
    emoji: "\U0001F4DD"
    homepage: https://github.com/wechatsync/Wechatsync
    install:
      - kind: node
        package: "@wechatsync/cli"
        bins: [wechatsync]
---

# WechatSync

Publish and sync Markdown/HTML articles to 29+ content platforms via CLI.

## 本用户内容偏好：炒技鼠鼠王

为“炒技鼠鼠王”账号或 `E:/project/自媒体` 项目准备、修改或同步内容时，先读取 [文章与模块配图规则](../shushuwang-article-illustration/SKILL.md)。以文章为主，必要配图基于用户指定的鼠鼠与尖叫鸡 Logo，辅助解释或轻松氛围；不要自动转成海报式图卡。该偏好只决定内容与配图风格，账号连接、同步和发布仍按本技能及当前用户授权执行。

## Prerequisites

This skill requires external tools that the user must install themselves:

1. **CLI tool** (`@wechatsync/cli`): Open-source npm package ([source code](https://github.com/wechatsync/Wechatsync/tree/v2/packages/cli)). Install with `npm install -g @wechatsync/cli`
2. **Chrome extension**: Open-source browser extension ([source code](https://github.com/wechatsync/Wechatsync/tree/v2/packages/extension)). Install from [Chrome Web Store](https://chrome.google.com/webstore/detail/hchobocdmclopcbnibdnoafilagadion) or [download ZIP](https://www.wechatsync.com/#install)
3. **Token**: User-generated token set in extension settings. The token is created locally by the user and used only for localhost communication between CLI and extension. Set via `export WECHATSYNC_TOKEN="your-token"`
4. **Platform logins**: Log in to target platforms in browser (extension uses existing browser cookies, no credentials are stored or transmitted)

**Security model**: All data stays local. The CLI communicates with the Chrome extension over localhost. The extension calls platform APIs directly from the browser using existing login sessions. No third-party server involved. Full source code is open and auditable.

Before running any command, confirm the user has completed the prerequisites. Do not install packages on the user's behalf without explicit consent.

## Commands

### Sync

```bash
wechatsync sync article.md -p juejin              # single platform
wechatsync sync article.md -p juejin,zhihu,csdn   # multiple platforms
wechatsync sync article.md -p juejin -t "Title"   # custom title
wechatsync sync article.md -p juejin --cover ./cover.png  # cover image
wechatsync sync article.md -p juejin --dry-run     # preview only
```

### Platforms & Auth

```bash
wechatsync platforms          # list all platforms
wechatsync platforms --auth   # show login status
wechatsync auth zhihu         # check single platform
```

### Extract

```bash
wechatsync extract              # extract from current browser page
wechatsync extract -o article.md  # save to file
```

## Platform IDs

## 平台清单按账号走，别按"上次发过哪几个"走（2026-09-26 用户纠正）

| 账号 | 平台 |
| --- | --- |
| 炒技鼠鼠王（技术） | 微信公众号、CSDN、掘金、知乎 |
| 炒基鼠鼠王（基金） | 微信公众号、知乎、雪球、东方财富 |

- 雪球是投资社区，技术文不要发；CSDN / 掘金是技术社区，基金文不要发。
- **`-p` 一次只传一个平台**：`-p csdn,juejin` 会报 `Platform not found: csdn juejin` 并让全部图片上传失败；要发两个就调两次。

zhihu, juejin, csdn, jianshu, toutiao, douyin, weibo, bilibili, xiaohongshu, baijiahao, weixin, yuque, douban, sohu, xueqiu, woshipm, dayu, yidian, 51cto, sohufocus, imooc, oschina, segmentfault, cnblogs, x, eastmoney, smzdm, netease, wordpress, typecho

## Notes

- Images auto-uploaded to target platform CDN (PNG, JPG, GIF, WebP, SVG)
- Markdown title extracted from front matter `title` or first `# heading`
- Articles sync as **drafts** by default — user reviews before publishing

## 本机已复现的转换缺陷与公众号验收

2026-09-24，本机 CLI 的简易 `markdownToHtml` 使用只匹配 LF 的围栏正则；Windows CRLF 原稿的 20 个代码块被转成 0 个 `pre`，仅统一换行后才识别到 20 个。不要直接将 Windows Markdown 多平台同步结果当作保留了代码结构。技术文章要使用可靠渲染流程，核对转换前后每个代码块的完整文本、缩进和换行；不能只数反引号或看草稿保存成功。

该 CLI 将本地图片先上传到平台列表中的第一个平台，随后依赖其他平台转存。因此“3 张上传成功”不能代表微信公众号已有 3 张素材。公众号适配需分别确认图片转存、带内联样式的命令框、标题层级、外部资料链接和原生目录；若使用 WechatSync 的 HTML 输入，先提供经过核对的公众号专用 HTML。若改用 baoyu-post-to-wechat，则按其自身渲染和上传流程，不混用两种转换结果。

资料链接除保留可用链接外，应有完整 URL 的文字兜底；本地页内锚点不可代替公众号原生目录验收。未进入后台核验或用户反馈图片、链接、代码缺失时，标为“草稿格式未通过”，不能继续以“草稿已同步”掩盖问题。

用户当前编辑器已实际提示“请勿插入非 mp.weixin.qq.com 域名的链接”。遇到这一明确提示，应提供无超链接导入稿：资料保留完整 URL 纯文字，去掉受拒绝的 href；未经后台验证的 # 页内目录改为普通阅读导航。不能仅在文末补地址却继续保留会触发报错的正文外链，也不能据此泛化为所有公众号永远不能插外链。

2026-09-24 用户定稿的公众号两条常规：① 公众号固定使用无超链接版本，资料以完整 URL 纯文字附在文末，不再尝试正文外链；② 代码块和 ASCII 流程图必须带框，`<pre>` 的底色会被公众号编辑器丢弃（用户实测只剩普通文字），需改成外层 `section` 负责底色/圆角/内边距、内层 `section` 负责等宽字体与 `white-space:pre-wrap`，换行用 `<br>`、行首缩进用 `&nbsp;`。可复用脚本示例：`E:\project\自媒体\2026-09-24-Harness与向量数据库\编辑记录\build_wechat_code_boxes.py`（含转换前后代码文本一致性的断言）。

2026-09-26 用户定稿的第三条常规：**一个平台的排版改进必须同轮落到所有会发的平台**。只把知乎之类的单个平台调好看、其它平台留旧样式，用户会直接指出“其他不修改是什么意思”。逐平台核对图注落位、分隔线、表格、引用块、字号层级，并记录平台丢弃了什么。

第四条常规：**自检之后必须迭代**——每次用户说“不行”、或某条脚本检查失败，都要写成“现象 + 证据 → 根因 → 改法 → 重跑全部检查 → 把这类问题加进断言”。只修一次不补断言，下一篇文章会重犯；完整循环与交付门禁见 `shushuwang-article-illustration` 技能的 SKILL.md「自检之后必须迭代」与 `references/readability-and-traffic.md` 第七节。

## 平台版式差异（本机实测，出稿前照这张表处理）

| 平台 | 保留 | 丢弃/不可靠 | 出稿做法 |
| --- | --- | --- | --- |
| 知乎 | 表格、引用块、分隔线、图片、目录锚点 | 段首缩进（只丢首段，段落不齐） | 不用缩进、不用 `---`；靠小标题分层；图注填“图片注释”字段（同步写不进去，须在编辑器补：点 `figcaption` → 对出现的 `.Image-captionInput textarea` 用 `pressSequentially` 键入 → **点正文标题让它失焦才算提交**；`fill()` 无效、Esc 是取消。**改完必须刷新页面复核**，完整动作链见 `shushuwang-article-illustration/references/readability-and-traffic.md` 第六节） |
| 雪球 | 标题、段落、图片 | Markdown 表格、列表排版、段首全角空格、分隔线（实测 `tables=0` / `indented=0` / `hr=0`） | 表格与自测题转图片；图注在图片下另起一行；目录直接删；按《社区规则》发帖时勾选 AI 生成内容标识。核对草稿要借扩展所在的 Edge（Codex in-app 浏览器未登录雪球，AX 快照可能早于正文加载，需等几秒后读 `[contenteditable="true"]`） |
| 微信公众号 | 内联样式的 section 框、行内样式表格、图片 | 正文外链、`<pre>` 底色、`<style>` 块 | section 框画公式/结论；图注用 13px 灰字；资料以完整网址纯文字附文末 |

**`--cover` 不等于封面已设好（2026-09-26 实测）**：本机用 `sync --cover 本地图` 之后，知乎草稿的发布设置仍显示「添加文章封面」、雪球草稿刷新后仍显示「上传封面」，也就是封面没写进去。发布前逐个平台打开编辑器确认封面区；另外基金主题的图片与正文署名一律用「炒基鼠鼠王」，技术主题才用「炒技鼠鼠王」。
| 东方财富 | 同雪球（同源编辑器） | 同雪球 | 用雪球那套；本机未登录，未做平台内复核 |

平台内核对方法、样本与排版参数见 `shushuwang-article-illustration` 技能的 `references/readability-and-traffic.md`（第六、七节）。

## Workflow

1. Confirm prerequisites are installed (ask user if unsure)
2. Check login: `wechatsync platforms --auth`
3. Sync: `wechatsync sync <file> -p <platform1>,<platform2>`
4. Report results with draft URLs

Example prompts:
- "Sync this article to Juejin and Zhihu"
- "Which platforms am I logged into?"
- "Extract the article from browser and save it"
- "把这篇文章同步到掘金和知乎"
