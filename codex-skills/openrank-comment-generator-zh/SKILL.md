---
name: openrank-comment-generator-zh
description: 为 openrank2 / OpenRank 可视化平台生成或补齐项目风格的中文代码注释。Use when Codex needs to add, rewrite, audit, or standardize Chinese module comments, function docstrings, route comments, Vue component comments, composable/state comments, chart lifecycle comments, API wrapper comments, Pinia store comments, or CSS section comments for this Flask + Vue3 + OpenDigger + LLM codebase.
---

# OpenRank 中文注释生成

## 工作流

1. 先确认当前目录是 `openrank2` 项目，读取 `backend/`、`frontend/src/` 中要处理的文件；不要只按文件名猜业务。
2. 运行注释清单脚本定位模块、函数、路由、Vue 组件逻辑和 CSS 分区：

```powershell
python C:\Users\zbh\.codex\skills\openrank-comment-generator-zh\scripts\comment_inventory.py --root .
```

3. 读取 `references/comment-style.md`，按模块类型选择注释模板。
4. 补注释时保持本项目口吻：中文、短句、解释“为什么这段逻辑存在”和“数据从哪里来/到哪里去”，不要写空泛的语法复述。
5. 编辑后再次运行清单脚本，确认新增模块和函数都有对应中文注释；必要时运行项目已有测试或启动命令做语法检查。

## 注释边界

- 优先补：文件头模块职责、Flask route 函数、数据同步/缓存/兜底函数、认证和收藏接口、Vue 图表渲染函数、异步数据加载函数、复杂 computed、watch、store action、CSS 大分区。
- 保持已有注释风格，不批量删除原注释；如遇乱码注释，先按代码真实行为重写成正常中文。
- 不给每一行机械加注释。变量名已经清楚时不注释，业务规则、兼容逻辑、安全限制、性能优化、降级路径必须注释。
- 对 OpenRank/OpenDigger/LLM/健康度/贡献者风险等项目术语保持原名，不强行翻译。

## 资源

- `references/comment-style.md`：项目注释风格、模块模板和常用句式。
- `scripts/comment_inventory.py`：扫描当前项目中模块、函数和注释覆盖情况，生成后续补注释清单。
