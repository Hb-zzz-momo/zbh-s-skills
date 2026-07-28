#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initialize or check a three-layer project memory entry."""
from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED_HEADINGS = ["尝试方法", "计划", "脚本/命令", "结果", "经验"]
THIRD_DIRS = ["计划", "尝试方法", "脚本", "结果", "经验"]
TEMPLATE = """# 项目记忆总览

> 第二层记忆桥：只写当前有效事实、第三层跳转和下一步判断；不要写完整流水。

## 尝试方法

- 当前可继续路线：
- 只保留为参考的路线：
- 禁止重试路线：
- 第三层跳转：`docs/project-entry/尝试方法/`

## 计划

- 当前主目标：
- 当前阶段：
- 下一步优先级：
- 本轮 gate / 止损条件：
- 暂不做：
- 第三层跳转：`docs/project-entry/计划/`

## 脚本/命令

- 启动命令：
- 测试/验证命令：
- 常用检查命令：
- 废弃命令与原因：
- 第三层跳转：`docs/project-entry/脚本/`

## 结果

- 当前正式结果：
- 当前最优结果：
- 稳定中位/常态表现：
- 负例和解释规则：
- 第三层跳转：`docs/project-entry/结果/`

## 经验

- 已成立经验：
- 歧义词表：
- 禁止误解：
- 下一轮必须继承：
- 第三层跳转：`docs/project-entry/经验/`
"""
AGENTS_BLOCK = """

## AI 启动读取顺序

1. 先读本文件，确认硬规则、禁止事项和项目边界。
2. 再读 `docs/project-entry/项目记忆总览.md`，获取当前有效事实和第三层跳转。
3. 只读取本轮相关的第三层原文：`docs/project-entry/计划/`、`尝试方法/`、`脚本/`、`结果/`、`经验/`。
4. 最后再读当前要修改的源码、测试和配置。

## 三层记忆维护规则

- `AGENTS.md` 只写启动顺序、硬边界、禁止事项和跳转入口，不写流水日志。
- 第二层总览只保留当前有效事实和跳转指针。
- 完整命令、raw 输出、失败细节和每轮记录写入第三层。
"""

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def write_if_missing(path: Path, text: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return True

def init(project: Path) -> int:
    project = project.resolve()
    entry = project / "docs" / "project-entry"
    created = []
    if write_if_missing(entry / "项目记忆总览.md", TEMPLATE):
        created.append(str((entry / "项目记忆总览.md").relative_to(project)))
    for name in THIRD_DIRS:
        d = entry / name
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d.relative_to(project)) + "/")
    agents = project / "AGENTS.md"
    if not agents.exists():
        agents.write_text("# AGENTS.md\n" + AGENTS_BLOCK.lstrip(), encoding="utf-8")
        created.append("AGENTS.md")
    else:
        text = read_text(agents)
        if "docs/project-entry/项目记忆总览.md" not in text:
            agents.write_text(text.rstrip() + AGENTS_BLOCK, encoding="utf-8")
            created.append("AGENTS.md updated")
    print("INIT_DONE")
    for item in created:
        print(f"CREATED_OR_UPDATED: {item}")
    if not created:
        print("NO_CHANGES")
    return check(project)

def check(project: Path) -> int:
    project = project.resolve()
    issues = []
    warnings = []
    agents = project / "AGENTS.md"
    claude = project / "CLAUDE.md"
    root_text = read_text(agents) + "\n" + read_text(claude)
    if not agents.exists() and not claude.exists():
        issues.append("缺少 AGENTS.md 或 CLAUDE.md 根规则入口。")
    if "docs/project-entry" not in root_text:
        warnings.append("根规则文件未明确指向 docs/project-entry 第二层入口。")
    overview = project / "docs" / "project-entry" / "项目记忆总览.md"
    if not overview.exists():
        issues.append("缺少 docs/project-entry/项目记忆总览.md 第二层入口。")
    else:
        text = read_text(overview)
        for heading in REQUIRED_HEADINGS:
            if f"## {heading}" not in text:
                issues.append(f"第二层缺少栏目：{heading}")
        line_count = len(text.splitlines())
        if line_count > 500:
            warnings.append(f"第二层总览超过 500 行（当前 {line_count} 行），建议拆分总览。")
    for name in THIRD_DIRS:
        if not (project / "docs" / "project-entry" / name).is_dir():
            issues.append(f"缺少第三层目录：docs/project-entry/{name}/")
    if issues:
        print("STATUS: BLOCK")
    elif warnings:
        print("STATUS: CAUTION")
    else:
        print("STATUS: PASS")
    for item in issues:
        print(f"ISSUE: {item}")
    for item in warnings:
        print(f"WARNING: {item}")
    return 2 if issues else 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init", "check"])
    parser.add_argument("--project", default=".")
    args = parser.parse_args()
    project = Path(args.project)
    if args.command == "init":
        return init(project)
    return check(project)

if __name__ == "__main__":
    raise SystemExit(main())