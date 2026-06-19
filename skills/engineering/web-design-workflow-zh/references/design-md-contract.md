# DESIGN.md Contract

`DESIGN.md` 是设计和代码之间的契约。除局部 UI bug 修复外，新网站、新页面、Landing Page、Portfolio、产品页和大改版都应先生成或更新它。

## Required Sections

1. **Visual Theme & Atmosphere**
   - 页面类型、受众、调性、设计关键词、反面关键词。
   - 明确交互档位：L1 精致静态 / L2 流畅交互 / L3 沉浸体验。

2. **Color Palette & Roles**
   - 用 CSS 变量定义背景、表面、边框、文本、强调色、语义色。
   - 提供 RGB variants，方便 `rgba()`。
   - 禁止组件里散落硬编码颜色。

3. **Typography Rules**
   - 字体来源、fallback、字号层级、行高、字重。
   - 中文页面必须显式配置中文字体。
   - 标题、正文、标签、代码分别定义，不混用。

4. **Component Stylings**
   - 按钮、卡片、导航、链接、标签、表单等关键组件。
   - 每类组件必须覆盖 default / hover / active / focus / disabled 或不可用策略。

5. **Layout Principles**
   - 容器宽度、网格、断点、间距刻度、section padding。
   - 说明哪些布局适合密集信息，哪些用于品牌展示。

6. **Depth & Elevation**
   - 阴影、边框、层级、悬浮关系。
   - 说明何时不用卡片，避免卡片套卡片。

7. **Animation & Interaction**
   - 入场、滚动、hover/focus、特殊效果和 reduced motion 降级。
   - L2+ 必须说明滚动 reveal、导航变化或视差策略。
   - L3 必须说明 pin/3D/转场等重动效的性能边界。

8. **Do's and Don'ts**
   - Do 至少 5 条，Don't 至少 8 条。
   - Don't 要明确禁止 AI 默认风格、无意义装饰、颜色漂移、过度动效、文字溢出等。

9. **Responsive Behavior**
   - 至少覆盖 Desktop / Tablet / Mobile。
   - 说明折叠策略、触摸目标、移动端动效降级和横向溢出防线。

## Minimum Quality Bar

- 每章都有实质内容，不只写标题。
- 色彩、字体、间距、圆角、动效都能映射到代码实现。
- 能解释为什么该风格适合这个项目。
- 有一个 signature moment，但不把每个区块都做成特效展示。
- 不用纯色块假装图片素材；缺素材时要用真实可替换占位图或明确请求用户提供。
- 写完代码后逐项核对 `DESIGN.md`，不符合就改代码或回改规范。
