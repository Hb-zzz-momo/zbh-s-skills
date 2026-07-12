#!/usr/bin/env python3
"""Deterministic helper for contextual reference routing and brief validation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SOURCE_CATALOG: dict[str, dict[str, str]] = {
    "Awwwards": {"domain": "awwwards.com", "role": "creative web visual direction"},
    "Land-book": {"domain": "land-book.com", "role": "landing-page and homepage structure"},
    "Lapa Ninja": {"domain": "lapa.ninja", "role": "full landing-page narrative and CTA rhythm"},
    "SiteInspire": {"domain": "siteinspire.com", "role": "minimal editorial web design"},
    "Recent.design": {"domain": "recent.design", "role": "current web visual patterns"},
    "Mobbin": {"domain": "mobbin.com", "role": "real product UI and states"},
    "Page Flows": {"domain": "pageflows.com", "role": "end-to-end user flows"},
    "Refero": {"domain": "refero.design", "role": "page and component patterns"},
    "Coolors": {"domain": "coolors.co", "role": "palette and contrast"},
    "Typewolf": {"domain": "typewolf.com", "role": "font pairing and hierarchy"},
    "Deck.gallery": {"domain": "deck.gallery", "role": "complete deck narrative and rhythm"},
    "Behance": {"domain": "behance.net", "role": "presentation and brand visual systems"},
    "SlideShare": {"domain": "slideshare.net", "role": "real presentation structure"},
    "Pitch": {"domain": "pitch.com", "role": "editable business presentation patterns"},
    "Dribbble": {"domain": "dribbble.com", "role": "single-slide visual inspiration"},
    "From Data to Viz": {"domain": "data-to-viz.com", "role": "chart selection by data relationship"},
    "Apache ECharts Examples": {"domain": "echarts.apache.org", "role": "production chart implementation examples"},
    "Observable": {"domain": "observablehq.com", "role": "advanced interactive visualization"},
    "Data Viz Project": {"domain": "datavizproject.com", "role": "visualization type taxonomy"},
    "OpenAI 官方文档": {"domain": "developers.openai.com", "role": "authoritative Codex and prompt guidance"},
    "Anthropic 官方文档": {"domain": "docs.anthropic.com", "role": "authoritative Claude and agent guidance"},
    "官方 Cookbook": {"domain": "cookbook.openai.com", "role": "official implementation examples"},
    "Cursor Directory": {"domain": "cursor.directory", "role": "community project-rule examples"},
    "Fabric": {"domain": "github.com/danielmiessler/fabric", "role": "reusable prompt patterns"},
    "高质量开源仓库实例": {"domain": "github.com", "role": "maintained project-rule and agent-instruction examples"},
    "BioRender": {"domain": "biorender.com", "role": "scientific mechanism information organization"},
    "Behance 科研图案例": {"domain": "behance.net", "role": "scientific visual composition"},
    "相关论文真实机制图": {"domain": "publisher or paper repository", "role": "domain-accurate mechanism evidence"},
    "AWS Architecture Center": {"domain": "aws.amazon.com", "role": "cloud reference architectures"},
    "Azure Architecture Center": {"domain": "learn.microsoft.com", "role": "enterprise architecture patterns"},
    "Google Cloud Architecture Center": {"domain": "cloud.google.com", "role": "data and AI architecture patterns"},
    "Excalidraw Libraries": {"domain": "libraries.excalidraw.com", "role": "editable architecture icon libraries"},
    "Iconify": {"domain": "iconify.design", "role": "open icon systems with per-set licensing"},
    "unDraw": {"domain": "undraw.co", "role": "editable illustration patterns and empty states"},
}


ROUTES: dict[str, dict[str, Any]] = {
    "web-visual": {
        "dimensions": ["information architecture", "visual style", "color system", "type hierarchy", "data presentation", "responsive layout"],
        "sources": ["Awwwards", "Land-book", "Coolors", "Typewolf", "SiteInspire"],
        "query": "developer tools analytics homepage clean visual system product proof",
    },
    "web-flow": {
        "dimensions": ["user flow", "interaction states", "error state", "empty state", "feedback"],
        "sources": ["Mobbin", "Page Flows", "Refero"],
        "query": "web app registration login save export report user flow states",
    },
    "dashboard": {
        "dimensions": ["product UI", "metric cards", "filters", "trend", "relationship network", "risk state", "chart selection", "chart implementation", "empty and loading states"],
        "sources": ["Mobbin", "From Data to Viz", "Apache ECharts Examples", "Observable"],
        "query": "open source repository health analytics dashboard filters trends network risk states",
    },
    "ppt-structure": {
        "dimensions": ["storyline", "slide rhythm", "information density", "visual hierarchy"],
        "sources": ["Deck.gallery", "SlideShare", "Pitch", "Behance"],
        "query": "professional technology presentation complete deck narrative",
    },
    "research-presentation": {
        "dimensions": ["research storyline", "multi-slide rhythm", "scientific visual language", "data visualization", "cover and closing"],
        "sources": ["Deck.gallery", "Behance", "SlideShare", "From Data to Viz"],
        "query": "university data science defense presentation machine learning research deck",
    },
    "coding-prompt": {
        "dimensions": ["official technical guidance", "instruction hierarchy", "tool rules", "constraints", "acceptance criteria", "failure handling"],
        "sources": ["OpenAI 官方文档", "Anthropic 官方文档", "官方 Cookbook", "Cursor Directory", "Fabric"],
        "query": "Flask Vue 3 Codex reusable skill project instructions tool rules acceptance criteria",
    },
    "agent-rules": {
        "dimensions": ["product-specific authority", "instruction hierarchy", "project context", "tool boundaries", "failure handling"],
        "sources": ["OpenAI 官方文档", "Anthropic 官方文档", "Cursor Directory", "高质量开源仓库实例"],
        "query": "official AGENTS.md CLAUDE.md Cursor Rules project instructions maintained repository examples",
    },
    "data-visualization": {
        "dimensions": ["data relationship", "chart type", "labels", "implementation"],
        "sources": ["From Data to Viz", "Data Viz Project", "Apache ECharts Examples", "Observable"],
        "query": "data relationship chart selection labels accessible implementation",
    },
    "scientific-mechanism": {
        "dimensions": ["scientific accuracy", "information hierarchy", "algorithm relationships", "arrow semantics", "model boundary"],
        "sources": ["BioRender", "Behance 科研图案例", "相关论文真实机制图"],
        "query": "multi-objective feature selection algorithm mechanism diagram paper schematic",
    },
    "system-architecture": {
        "dimensions": ["system boundary", "data flow", "service relationships", "editable symbols"],
        "sources": ["AWS Architecture Center", "Azure Architecture Center", "Google Cloud Architecture Center", "Excalidraw Libraries"],
        "query": "AI data platform reference architecture data flow security deployment",
    },
    "landing-page": {
        "dimensions": ["hero", "content rhythm", "CTA", "social proof", "pricing"],
        "sources": ["Land-book", "Lapa Ninja", "Awwwards"],
        "query": "AI SaaS landing page hero pricing CTA social proof full page",
    },
    "web-app": {
        "dimensions": ["product structure", "components", "interaction states", "empty state", "error state"],
        "sources": ["Mobbin", "Refero", "Page Flows"],
        "query": "web app admin settings subscription empty error state product UI",
    },
    "ppt-visual": {
        "dimensions": ["visual system", "slide continuity", "cover", "data slides", "type hierarchy"],
        "sources": ["Behance", "Deck.gallery", "Dribbble"],
        "query": "premium technology investor presentation complete deck visual system",
    },
    "color-system": {
        "dimensions": ["industry fit", "brand color", "semantic color", "contrast", "accessibility"],
        "sources": ["Awwwards", "Coolors", "SiteInspire"],
        "query": "data platform brand color system accessible contrast technology",
    },
    "typography": {
        "dimensions": ["font pairing", "type hierarchy", "multilingual readability", "deployment availability", "font license"],
        "sources": ["Typewolf", "Land-book", "SiteInspire"],
        "query": "technology product bilingual typography hierarchy deployable web fonts",
    },
    "visual-assets": {
        "dimensions": ["icon semantics", "illustration style", "empty states", "brand fit", "asset license"],
        "sources": ["Iconify", "unDraw", "Behance"],
        "query": "developer product icon system empty state illustration consistent visual language",
    },
    "report-template": {
        "dimensions": ["report narrative", "section structure", "data pages", "type hierarchy", "editable template"],
        "sources": ["Behance", "SlideShare", "Pitch"],
        "query": "professional data analytics report presentation template full document",
    },
}


NEGATIVE_PATTERNS = (
    "数组越界", "普通代码报错", "修复 bug", "修复bug", "变量名", "一行代码", "翻译", "事实问答"
)

EXPLICIT_SKIP_PATTERNS = (
    "不要联网", "禁止联网", "不参考外部", "跳过外部参考", "不要探索新风格",
    "严格按照参考图做局部修改", "严格按参考图局部修改",
)


def _contains(text: str, words: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(word.lower() in lower for word in words)


def _select_route(task: str) -> str:
    if _contains(task, EXPLICIT_SKIP_PATTERNS):
        return "none"
    is_bugfix = _contains(task, ("修复", "排查", "debug", "fix")) and _contains(task, ("bug", "报错", "故障", "加载失败", "运行错误"))
    has_design_intent = _contains(task, ("设计", "视觉", "布局", "交互", "体验", "样式", "信息层级", "状态设计"))
    if is_bugfix and not has_design_intent:
        return "none"
    if _contains(task, NEGATIVE_PATTERNS) and not _contains(task, ("界面", "视觉", "交互", "布局", "prompt", "skill")):
        return "none"
    if _contains(task, ("cursor rules", "agents.md", "claude.md")):
        return "agent-rules"
    if _contains(task, ("coding prompt", "agent prompt", "codex", "开发 skill", "开发skill", "编写可长期复用", "提示词")):
        return "coding-prompt"
    if _contains(task, ("科研机制图", "算法机制图", "特征选择算法", "graphical abstract", "机制图", "通路图")):
        return "scientific-mechanism"
    if _contains(task, ("系统架构图", "架构图", "数据流图", "cloud architecture", "部署架构")):
        return "system-architecture"
    if _contains(task, ("dashboard", "数据大屏", "指标卡片", "健康度分析")):
        return "dashboard"
    if _contains(task, ("完整交互流程", "用户流程", "交互流程", "onboarding", "注册", "登录", "收藏", "导出报告")):
        return "web-flow"
    if _contains(task, ("web app", "后台系统", "后台管理", "管理系统", "产品内部", "设置页", "订阅和空状态")):
        return "web-app"
    if _contains(task, ("ppt", "答辩", "演示文稿", "路演", "presentation")):
        if _contains(task, ("科研", "课程答辩", "数据科学", "机器学习", "论文", "研究")):
            return "research-presentation"
        if _contains(task, ("高端", "高级", "科技视觉", "视觉系统", "品牌视觉")):
            return "ppt-visual"
        return "ppt-structure"
    if _contains(task, ("数据可视化", "图表选型", "折线图", "关系图", "可视化图表")):
        return "data-visualization"
    if _contains(task, ("报告模板", "汇报模板", "report template")):
        return "report-template"
    if _contains(task, ("图标系统", "图标风格", "插画系统", "插画风格", "空状态插画")):
        return "visual-assets"
    if _contains(task, ("配色", "色板", "颜色系统", "色彩系统", "品牌色")):
        return "color-system"
    if _contains(task, ("字体", "字型", "排版层级", "typography")):
        return "typography"
    if _contains(task, ("landing page", "落地页", "活动页面")):
        return "landing-page"
    if _contains(task, ("信息层级", "用户体验", "产品展示逻辑", "展示逻辑", "响应式设计")):
        return "web-visual"
    if _contains(task, ("网站", "官网", "首页", "landing page", "saas", "web", "页面视觉", "设计页面")):
        return "web-visual"
    if _contains(task, ("参考案例", "行业标杆", "设计感", "配色", "字体", "模板", "视觉")):
        return "web-visual"
    return "none"


def route_task(task: str) -> dict[str, Any]:
    task = task.strip()
    route = _select_route(task)
    if route == "none":
        reason = "普通代码报错修复、纯文本或非设计任务不触发参考路由。"
        return {
            "should_trigger": False,
            "primary_route": "none",
            "reason": reason,
            "dimensions": [],
            "sources": [],
            "search_queries": [],
            "case_target": {"min": 0, "max": 0},
            "core_reference_target": {"min": 0, "max": 0},
            "rule_target": {"min": 0, "max": 0},
        }

    config = ROUTES[route]
    sources = [
        {"name": name, **SOURCE_CATALOG[name]}
        for name in config["sources"][:5]
    ]
    search_queries = [
        config["query"],
        f"{task} concrete case study full project",
    ]
    return {
        "should_trigger": True,
        "primary_route": route,
        "reason": "任务包含设计、交互、展示、可视化或提示系统，需要外部参考提高决策质量。",
        "dimensions": config["dimensions"],
        "sources": sources,
        "search_queries": search_queries,
        "case_target": {"min": 3, "max": 8},
        "core_reference_target": {"min": 2, "max": 4},
        "rule_target": {"min": 3, "max": 7},
    }


def _is_homepage_only(url: str) -> bool:
    cleaned = re.sub(r"^https?://", "", url.strip()).rstrip("/")
    return "/" not in cleaned


def _is_concrete_http_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and not _is_homepage_only(url)


def validate_brief(brief: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    live_access = bool(brief.get("live_access"))
    limitations = brief.get("limitations") or []
    if not live_access:
        limitation_text = " ".join(str(item) for item in limitations)
        if "实时参考检索未完成" not in limitation_text:
            issues.append({"severity": "ERROR", "message": "无法联网时必须明确‘实时参考检索未完成’及替代证据。"})

    task = brief.get("task") or {}
    for field, label in (("deliverable", "交付物"), ("audience", "目标受众"), ("industry", "行业或主题")):
        if not str(task.get(field, "")).strip():
            issues.append({"severity": "ERROR", "message": f"当前任务缺少{label}。"})
    if not str(brief.get("design_goal", "")).strip():
        issues.append({"severity": "ERROR", "message": "Reference Brief 必须声明当前设计目标。"})
    if not brief.get("reference_dimensions"):
        issues.append({"severity": "ERROR", "message": "Reference Brief 必须记录选取的参考维度。"})

    reviewed_case_count = brief.get("reviewed_case_count")
    reviewed_website_count = brief.get("reviewed_website_count")
    if not isinstance(reviewed_case_count, int):
        issues.append({"severity": "ERROR", "message": "必须记录 reviewed_case_count。"})
    elif live_access and not 3 <= reviewed_case_count <= 8:
        issues.append({"severity": "ERROR", "message": "联网普通任务必须查看 3–8 个具体案例。"})
    elif not live_access and not 1 <= reviewed_case_count <= 8:
        issues.append({"severity": "ERROR", "message": "离线降级仍须检查 1–8 个本地可靠案例。"})
    if live_access:
        if not isinstance(reviewed_website_count, int) or not 2 <= reviewed_website_count <= 5:
            issues.append({"severity": "ERROR", "message": "联网普通任务必须记录 2–5 个已检查网站。"})
        elif isinstance(reviewed_case_count, int) and reviewed_website_count > reviewed_case_count:
            issues.append({"severity": "ERROR", "message": "已检查网站数不能大于具体案例数。"})
    elif reviewed_website_count not in (None, 0):
        issues.append({"severity": "ERROR", "message": "离线降级的 reviewed_website_count 应为 0 或省略。"})

    sources = brief.get("sources") or []
    if live_access and not 2 <= len(sources) <= 4:
        issues.append({"severity": "ERROR", "message": "必须最终保留 2–4 个核心参考，即至少两个互补来源。"})
    if not live_access and not 1 <= len(sources) <= 4:
        issues.append({"severity": "ERROR", "message": "离线降级仍须保留 1–4 个本地可靠核心参考。"})
    if isinstance(reviewed_case_count, int) and len(sources) > reviewed_case_count:
        issues.append({"severity": "ERROR", "message": "核心参考数不能大于已检查案例数。"})
    distinct_sources = {
        (urlparse(str(source.get("url", ""))).netloc.lower().removeprefix("www.") or str(source.get("name", "")).lower())
        for source in sources
    }
    if live_access and len(sources) >= 2 and len(distinct_sources) < 2:
        issues.append({"severity": "ERROR", "message": "至少两个案例必须来自两个互补来源，不能全部来自同一网站。"})
    if live_access and isinstance(reviewed_website_count, int) and len(distinct_sources) > reviewed_website_count:
        issues.append({"severity": "ERROR", "message": "核心参考网站数不能大于已检查网站数。"})
    for index, source in enumerate(sources, start=1):
        prefix = f"来源 {index}"
        if not source.get("case"):
            issues.append({"severity": "ERROR", "message": f"{prefix} 必须记录具体案例或页面名称。"})
        if live_access and not _is_concrete_http_url(str(source.get("url", ""))):
            issues.append({"severity": "ERROR", "message": f"{prefix} 必须记录具体案例的有效 HTTP(S) URL，不能写首页或伪路径。"})
        if not live_access and not str(source.get("path") or source.get("url") or "").strip():
            issues.append({"severity": "ERROR", "message": f"{prefix} 必须记录本地参考材料路径。"})
        for field, label in (
            ("relevance", "相关性"), ("facts", "事实"), ("observations", "观察"),
            ("inferences", "推断"), ("adopt", "采用元素"), ("reject", "放弃元素"),
            ("translation", "项目转译"),
        ):
            if not source.get(field):
                issues.append({"severity": "ERROR", "message": f"{prefix} 缺少{label}。"})
        if source.get("license_checked") is not True:
            issues.append({"severity": "ERROR", "message": f"{prefix} 未记录素材或模板许可证检查。"})

    rules = brief.get("rules") or []
    if not 3 <= len(rules) <= 7:
        issues.append({"severity": "ERROR", "message": "必须提炼 3–7 条可执行设计规律。"})
    if not brief.get("rejected_patterns"):
        issues.append({"severity": "ERROR", "message": "必须明确记录不采用的设计模式及原因。"})
    if not brief.get("applied_to_final"):
        issues.append({"severity": "ERROR", "message": "必须记录参考规律在最终产物中的落实位置。"})
    if brief.get("fact_observation_inference_separated") is not True:
        issues.append({"severity": "ERROR", "message": "必须区分事实、观察、推断和设计建议。"})

    if issues:
        status = "BLOCK"
    else:
        status = "PASS" if live_access else "CAUTION"
    return {"status": status, "issues": issues, "limitations": limitations}


def run_batch(cases: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    failures = []
    for case in cases:
        actual = route_task(case["task"])
        source_names = [item["name"] for item in actual["sources"]]
        checks = {
            "trigger": actual["should_trigger"] == case["should_trigger"],
            "route": actual["primary_route"] == case["route"],
            "must_include": all(name in source_names for name in case.get("must_include", [])),
            "must_exclude": all(name not in source_names for name in case.get("must_exclude", [])),
        }
        passed = all(checks.values())
        results.append({"id": case["id"], "passed": passed, "checks": checks, "actual": actual})
        if not passed:
            failures.append(case["id"])
    return {"status": "PASS" if not failures else "BLOCK", "case_count": len(cases), "failures": failures, "results": results}


def _write_result(result: dict[str, Any], output: str | None) -> None:
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(payload, encoding="utf-8")
    print(payload, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Route reference sources and validate Reference Briefs.")
    sub = parser.add_subparsers(dest="command", required=True)
    route_parser = sub.add_parser("route")
    route_parser.add_argument("--task", required=True)
    route_parser.add_argument("--output")
    brief_parser = sub.add_parser("validate-brief")
    brief_parser.add_argument("--input", required=True)
    brief_parser.add_argument("--output")
    batch_parser = sub.add_parser("batch-test")
    batch_parser.add_argument("--cases", required=True)
    batch_parser.add_argument("--output")
    args = parser.parse_args(argv)

    if args.command == "route":
        result = route_task(args.task)
        _write_result(result, args.output)
        return 0
    if args.command == "validate-brief":
        brief = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = validate_brief(brief)
        _write_result(result, args.output)
        return {"PASS": 0, "CAUTION": 1, "BLOCK": 2}[result["status"]]
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    result = run_batch(cases)
    _write_result(result, args.output)
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
