<!-- Slide number: 1 -->
01
VIBE CODING PLAYBOOK
VIBE CODING
从一句想法到可验证产品

AI CODING SESSION
> goal: filter unfinished tasks
read src/TodoList.tsx
edit query: status=open
用 AI 加速构建，
用证据守住质量
run npm test -- TodoList
✓ open / done / empty
review diff: 18 lines
ready for human approval
BEGINNER PLAYBOOK
快速反馈，不放弃判断
VIBE / CODE

来源：SRC-GH-BEST

### Notes:
先问学员：你希望 AI 替你写多少代码，还是希望它帮你更快得到可验证结果？本课选择后者。

<!-- Slide number: 2 -->
02
COURSE MAP
TABLE OF
CONTENT
重新定义
提示与上下文
01
04

三个常见误区
质量与安全
02
05

小步闭环
十分钟练习
03
06

从定义到发布门禁，
建立可迁移的协作方法。

来源：SRC-LOCAL

### Notes:
告诉学员这不是工具功能介绍，而是一套可以迁移到不同 AI 编程工具的工作方法。

<!-- Slide number: 3 -->
03
DEFINITION
WHAT MAKES
VIBE CODING DIFFERENT
自然语言只是入口，
反馈闭环才是差异
↘
↘
↘
自然语言起步
高频反馈
人类负责
different
先表达意图，再进入实现细节
生成、运行、观察、修正
目标、边界、验证、发布

INTENT
FEEDBACK
JUDGMENT
goal: unfinished filter
run → observe
review diff
context: existing TodoList
test failed: empty state
check permissions
constraint: no DB change
fix component branch
verify acceptance criteria
done: tests + screenshot
rerun → 3 tests pass
human approves release

来源：SRC-GH-BEST · SRC-GH-PROMPT

### Notes:
把它定义为一种交互节奏：自然语言让启动更快，反馈循环让方向不断收敛，人类仍负责判断。

<!-- Slide number: 4 -->
04
BOUNDARY
WHERE VIBE CODING
CREATES VALUE

FAST
FEEDBACK
适用 / FIT
慎用 / CAUTION
原型与交互验证
认证、支付与权限
01
01
内部工具与重复脚本
隐私、核心数据与秘密
02
02

速度优势只在反馈可观察、
修改可回滚时成立。
低风险、可撤销界面
不可逆操作与关键基础设施
03
03

来源：SRC-GH-BEST · SRC-OWASP

### Notes:
快速反馈适合可观察、可回滚的任务。高风险领域不是不能用 AI，而是必须增加设计审查、安全验证和权限边界。

<!-- Slide number: 5 -->
05
FAILURE MODES
THREE WAYS
VIBE CODING FAILS
01
愿望式提示
只说做什么，
不说完成标准
02
上下文断裂
↘
模型不知道项目约定
和真实接口
03
跳过验证
↘
能运行，
就当成可以发布
↘

多数失败不是模型不会写，而是目标、上下文、验证缺了一环。

来源：SRC-GH-BEST · SRC-OWASP

### Notes:
三个问题分别对应目标、上下文、验证。后面的工作流就是逐一补上这三个缺口。

<!-- Slide number: 6 -->
06
METHOD
THE VIBE CODING
FEEDBACK LOOP
每次只推进一个可观察切片

01
03
05

02
04
定义
生成
修复

给上下文
验证
目标 + Done
一个薄切片
回源再复验

文件 + 约束
运行 + 测试

DEFINE
VERIFY
FIX
Goal / Context
npm test -- TodoList
failure → source file
Constraints / Done
✓ open ✓ done ✓ empty
small diff → rerun
one behavior only
capture evidence
approve only with proof

来源：SRC-GH-BEST · SRC-ANTHROPIC

### Notes:
强调薄切片：不要让 AI 一次生成整个系统。每一轮都要有可以运行、观察和否定的结果。

<!-- Slide number: 7 -->
07
PROMPTING
PROMPT LIKE
A PRODUCT BRIEF
好提示 = 一个可执行的产品简报

用户最终能做什么
GOAL
01

PROMPT CONTRACT
Goal:
为待办页增加“未完成”筛选
现有文件、接口、约定
CONTEXT
02

Context:
复用现有 TodoList 与查询 API
不能改什么、技术边界
CONSTRAINTS
03

Constraints:
不改数据库，不新增依赖
Done:
3 条测试通过 + 运行截图 + 小 Diff
如何证明完成
DONE
04

可验证

来源：SRC-GH-PROMPT · SRC-ANTHROPIC

### Notes:
这四项是课程归纳框架。示例：为现有待办页增加筛选；复用当前 API；不改数据库；用三条测试和截图证明完成。

<!-- Slide number: 8 -->
08
DEMO
FROM VAGUE IDEA
TO WORKING SLICE
逐轮收窄，不赌一句万能提示

01 / PROMPT

Goal: unfinished filter
02 / BUILD

Context: TodoList.tsx
edit TodoList.tsx
03 / VERIFY
Constraint: no DB change
+ status query parameter
✓ open tasks
Done: tests + screenshot
+ empty-state branch
✓ completed tasks
scope locked
18 lines changed

✕ empty state spacing
run local preview
fix → rerun

✓ 3/3 + screenshot

来源：SRC-GH-PROMPT · SRC-LOCAL

### Notes:
演示三轮：第一轮锁定范围，第二轮生成薄切片，第三轮根据测试失败修复。不要把失败藏起来。

<!-- Slide number: 9 -->
09
CONTEXT
CONTEXT IS
YOUR REAL LEVERAGE
项目文件比更长的提示
更有复用价值
把重复规则写进仓库，
让每一轮对话都从同一事实出发。
↘

README
TESTS

AGENTS.md
EXAMPLES
install
happy
scope
pattern
start
edge
rules
naming
verify
failure
deliver
output
怎么运行
什么叫正确
怎么协作
项目真实风格

来源：SRC-GH-BEST · SRC-LOCAL

### Notes:
当规则会重复出现时，不要每次重新描述，把它写进项目文件、测试和示例。这就是可复用上下文。

<!-- Slide number: 10 -->
10
QUALITY
QUALITY GATES
BEFORE YOU SHIP
必须验证
必须守住
能运行
输入
真实入口可启动
外部内容不可信
01
01

有测试
权限
正常与失败路径
最小授权与确认
02
02

可审查
秘密与依赖
Diff 小且可解释
不泄露、不盲装
03
03

模型输出 = 未验证候选实现
发布决定始终由人负责

来源：SRC-GH-BEST · SRC-OWASP

### Notes:
把模型输出当成未经验证的候选实现。发布决定必须由人负责，尤其是输入、权限、秘密和外部依赖。

<!-- Slide number: 11 -->
11
LAB
10-MINUTE
VIBE CODING LAB

10:00
TASK

为静态待办页增加
“未完成”筛选
DELIVER
1 段结构化提示
1 个可运行切片
3 条验证证据
只完成一个小闭环，
不比赛谁写得多。

RULE
一次只改一个行为；
失败必须保留并修复。
START SMALL

来源：SRC-GH-PROMPT · SRC-LOCAL

### Notes:
让学员两人一组：一人扮演产品负责人，写 Goal/Context/Constraints/Done；另一人操作 AI 并记录每轮证据。

<!-- Slide number: 12 -->
12
CLOSING
LET AI MOVE FAST.
KEEP HUMAN JUDGMENT.

生成候选实现
加速探索与修改
AI
Vibe Coding 的价值来自更短反馈；
它的安全来自人类保留判断。

定义目标与边界
审查证据
批准发布
HUMAN
下一次编码，从一个
可验证的薄切片开始。

VIBE / CODE

来源：SRC-GH-BEST · SRC-OWASP

### Notes:
最后复述：Vibe Coding 的价值来自更短反馈；它的安全来自人类始终保留目标、边界、验证和发布责任。