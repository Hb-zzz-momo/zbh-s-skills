# 检查与验收说明

## 1. 检查范围

`validate.py` 是只读辅助工具，使用 Python 3.9 或更新版本及标准库；不联网、不运行实验命令、不修改文件。Skill 文本本身不依赖 Python；只有运行此检查工具需要 Python。

工具分别检查主文件元数据、本包 Markdown 相对链接，以及可选 JSON 证据台账的一致性。它不是通用 YAML 解析器，也不能验证截图真假、实验算法正确性、课程认可或 Word 视觉质量。

单元测试使用临时目录中的合成数据，不包含用户实验成绩或真实运行结论。[行为用例](../evals/cases.json)仅定义测试场景，必须另行在实际客户端执行，不能把“用例文件存在”算作行为测试通过。

## 2. 从包根目录运行

将终端当前目录切换为包含 `SKILL.md` 的 `course-lab-workflow-zh` 文件夹，然后执行：

```bash
python scripts/validate.py
```

输入为当前 Skill 文件夹；输出为终端 JSON。`ok: true` 且退出码为 `0` 仅表示本次结构检查未发现错误。存在错误时退出码为 `1`。`warnings` 需要结合文字理解，不能忽略它们后宣称实验通过。

运行自动化单元测试：

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

运行模板台账检查：

```bash
python scripts/validate.py --evidence assets/evidence-register.json
```

模板尚未填实验身份与结果，因此可以通过结构检查，但应出现身份待替换、必做项待完成等警告。这正是草稿状态，不能解读为实验完成。

以下是有意的反向检查；对空白模板应失败并返回退出码 `1`：

```bash
python scripts/validate.py --evidence assets/evidence-register.json --require-ready
```

## 3. 检查实际实验台账

先将[台账模板](../assets/evidence-register.json)复制到实验工作目录，再填写实际数据。不要把本包内的模板当作所有课程共享的唯一台账。

台账至少包含 `lab_id`（课程及实验标识）、`attempt_id`（运行批次或修订标识）、必做要求和证据索引。每条证据必须指向相同实验与批次。证据相对路径以**台账 JSON 所在目录**为基准，不是以终端当前目录或 Skill 目录为基准。

例如台账在 `lab-work/web/lab1/evidence-register.json`，证据位于 `lab-work/web/lab1/evidence/E01.png`，则 `path` 填 `evidence/E01.png`。跨平台统一使用 `/`；不允许绝对路径或跳出台账目录的 `../`。本包目录不必收纳实验文件。

仍在 Skill 包根目录时，运行下列命令，将示例路径替换为台账真实位置：

```bash
python scripts/validate.py --evidence "实际工作目录/evidence-register.json" --check-files
```

`--check-files` 仅验证被引用文件存在且非空，不会识别图中文字或判断图像真实性。需要检查所有必做项是否已经达到台账中的复核条件时，加上：

```bash
python scripts/validate.py --evidence "实际工作目录/evidence-register.json" --check-files --require-ready
```

`ready_for_review` 表示**具备进一步复核的台账条件**，不表示已获得教师认可、实验全正确或报告可直接提交。

## 4. 台账字段约定

执行状态 `execution_status`：

| 值 | 含义 |
|---|---|
| `not_started` | 尚未开始 |
| `attempted` | 已尝试但没有完成判定 |
| `passed` | 按记录中的验证条件判为通过，仍须结合证据状态 |
| `failed` | 按验证条件判为失败 |
| `blocked` | 因权限、输入或环境等原因阻塞 |
| `not_applicable` | 不在本次课程要求范围内，必须填写依据 |

证据状态 `evidence_status` / `verification`：`verified` 已核验、`user_reported` 用户自述未独立复核、`unverified` 已有材料待复核、`example` 示例、`missing` 缺失。

证据类别 `kind`：`screenshot`、`log`、`output`、`source`、`user_statement`、`example`。真实文件证据填写 `path`；用户自述填写可追溯的 `locator`。每条证据填写 `description`，说明能支持哪一项结论。

只有源代码不能证明“实际运行通过”；示例不能支持真实通过；用户自述可以保留通过陈述，但不能自动升级为“已核验”。不适用项的依据仍需人工核对，不是随意跳过必做任务的入口。

## 5. 行为验收方法

每个行为用例包括 `prompt`、`must`、`must_not` 和预期工作模式。实际测试时，准备相应真实材料或明确标注的测试夹具，在目标客户端调用 Skill，保存完整输出。

每项只判“满足 / 不满足 / 无法判断”，并记录对应输出位置。只要出现伪造结果、混用课程、越权修改或违反明确修改边界，当前用例就不能判为通过。未实际运行的用例保持 `not_executed`，不生成虚构通过率。

用户实验的最终验收另按[验收清单](../assets/acceptance-checklist.md)完成。结构检查、单元测试、模型行为评估与实际实验验收是四件不同的事。

## 6. 能力边界（不要混淆）

`validate.py` 只检查本包结构与台账逻辑：主文件元数据、包内相对链接、可选台账 JSON 的字段与状态一致性。它**不能**打开 docx、读取页数、量图片比例、判断表格宽度、检查文字是否越过版心或页面是否留白过多。

报告版式必须用[版式自检脚本](../assets/scripts/check_layout.ps1)在装有 Word 与 poppler 的机器上实测（输出页数、图片宽高比、表格宽度、文字边界、逐页墨迹）。「结构检查通过」与「版式检查通过」是两件事，任何一方通过都不能代替另一方。
