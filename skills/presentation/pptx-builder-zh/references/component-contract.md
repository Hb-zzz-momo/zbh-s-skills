# PPT 组件契约

每个组件必须接收 slide、主题令牌、内容和几何框；只负责一种视觉职责；把 `slide_id`、组件名、`x/y/w/h` 和用途登记到构建清单；不得随机声明颜色、字体或间距；对空内容给出明确错误或跳过规则。

推荐组件：`title`, `sourceFooter`, `metric`, `processNode`, `comparisonColumn`, `evidenceItem`, `imageFrame`, `chartAnnotation`。

