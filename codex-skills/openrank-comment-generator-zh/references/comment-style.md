# openrank2 中文注释风格

## 项目定位

本项目是 OpenRank / OpenDigger 可视化平台，后端是 Flask + SQLAlchemy + JWT + OpenDigger 数据缓存，前端是 Vue3 + Pinia + ECharts。注释要服务于比赛答辩、后续维护和代码阅读，重点说明业务链路，而不是解释语言语法。

## 通用风格

- 使用简体中文，句子短，直接说明职责。
- 可以保留少量项目中已有的强调符号，如 `✅`、`🔥`、`====` 分区线；不要为了装饰滥用。
- 注释贴近代码块：文件头说明模块，函数上方或 docstring 说明函数职责，复杂步骤前用编号注释。
- 优先回答三件事：这段代码做什么、为什么需要、和上下游怎么衔接。
- 不写“定义变量”“调用函数”这类无信息注释。

## 后端模块模板

文件头适合使用：

```python
# backend/data_fetcher.py
"""
OpenDigger 数据同步模块
负责从 OpenDigger API 拉取指标序列，清洗为统一格式后写入本地 SQLite。
同步完成后生成 LLM 生态汇总，供排行榜、雷达图和智能报告复用。
"""
```

接口蓝图适合使用：

```python
"""
本文档 = 后端接口蓝图
所有路径统一以 /api 开头，负责平台元数据、指标序列、LLM 汇总、智能报告和贡献者风险接口。
"""
```

普通函数 docstring：

```python
def compute_llm_summary_from_db():
    """
    从数据库计算 LLM 生态汇总数据。
    使用批量查询替代 N+1 查询，并将 openrank/activity 归一化后计算 health_score。
    """
```

复杂流程内部注释：

```python
# 1) 命中缓存且未过期：直接返回本地数据，避免频繁请求 OpenDigger
# 2) 缓存不存在或过期：请求上游，并把 HTTP/网络错误统一转成 ApiException
# 3) 写回 MetricSeries，保证后续图表和汇总接口复用同一份数据
```

后端重点补注释位置：

- `main.py`：`.env` 加载顺序、密钥来源、生产环境强制检查、CORS 白名单、后台同步线程。
- `data_fetcher.py`：配置读取、OpenDigger 请求、404 处理、DB upsert、无效项目清理、LLM 汇总生成。
- `api/opendigger.py`：Blueprint 分区、ApiException、缓存策略、元数据接口、指标接口、LLM 报告兜底、贡献者风险计算。
- `api/auth.py`：注册校验、唯一性检查、密码哈希、JWT claims、登录身份判断。
- `api/favorites.py`：single/plan 两类收藏、去重键、登录用户隔离。
- `models.py`：User/Favorite/MetricSeries 三张表的用途和关键字段。
- `metric_utils.py`：统计函数、最近 N 个月提取、健康度权重。
- `rate_limiter.py`：限流键、窗口清理、响应头、登录用户降级到 IP。

## 前端 Vue 模板

组件文件头或 `<script setup>` 前适合使用：

```js
/**
 * 这个组件只做一件事：
 * 给定 org/repo/metric，去后端拉 OpenDigger 指标数据，然后用 ECharts 画趋势折线图。
 */
```

异步加载函数：

```js
async function loadData() {
  // 防御：缺少 org/repo 时不请求后端，直接显示可读错误
  // 请求成功后统一 normalize，兼容后端返回的对象数组和二维数组
  // 等 DOM 稳定后再渲染图表，避免 ECharts 容器尺寸为 0
}
```

复杂 computed：

```js
const autoConclusion = computed(() => {
  // 1. 找出各维度领先者
  // 2. 计算各项目加权总分
  // 3. 生成场景化建议和差异化洞察
})
```

watch / 生命周期：

```js
// 当用户切换 metric/org/repo 时自动刷新图表
watch(() => [props.platform, props.org, props.repo, props.metric], () => loadData())

// 组件销毁时释放 ECharts 实例和窗口监听，避免重复初始化和内存泄漏
onBeforeUnmount(() => { ... })
```

前端重点补注释位置：

- `api/api.js`：HTTP 实例、Token 注入、OpenDigger/LLM/Auth/Favorites 分组。
- `stores/*.js`：持久化状态、登录恢复、收藏兼容逻辑、plan/single 区分。
- `components/*Chart.vue`：ECharts 初始化、数据归一化、resize、空态/错误态。
- `components/ContributorRiskCard.vue`：项目校验、风险接口、趋势/等级展示。
- `views/HomeView.vue`：项目树加载、选择限制、雷达指标映射、智能结论、报告弹窗、打字机。
- `views/LLMSummaryView.vue`：榜单排序、收藏榜单、分类渲染、图表同步。
- `views/FavoritesView.vue`：收藏类型解析、旧数据兼容、删除流程。

## CSS 注释模板

CSS 使用大分区，避免给每个选择器加注释：

```css
/* ========== 状态提示 ========== */

/* ========== 股票风格数据面板 ========== */

/* ========== 图表区域 ========== */
```

对复杂覆盖规则可以补一句原因：

```css
/* 全屏阅读模式：只显示右侧报告，让答辩时投屏阅读更清楚 */
```

## 质量检查

- 每个 Python 文件应有文件头或模块 docstring。
- 每个 Flask route 函数应有一句中文 docstring 或上方中文注释。
- 每个复杂 helper 函数应说明输入、输出或业务约束。
- 每个 Vue 组件至少有组件职责注释；复杂 `computed`、`async function`、`watch`、生命周期清理要有中文注释。
- CSS 至少按页面区域分区。
- 注释必须和当前代码一致；如果发现注释描述了不存在的接口、字段或参数，先改注释，不改业务。
