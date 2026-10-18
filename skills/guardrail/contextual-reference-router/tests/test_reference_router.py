import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "reference_router.py"
CASES = json.loads((ROOT / "tests" / "cases.json").read_text(encoding="utf-8"))


def load_module():
    spec = importlib.util.spec_from_file_location("reference_router", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.router = load_module()

    def test_plan_acceptance_cases(self):
        for case in CASES:
            with self.subTest(case=case["id"]):
                result = self.router.route_task(case["task"])
                self.assertEqual(case["should_trigger"], result["should_trigger"])
                self.assertEqual(case["route"], result["primary_route"])
                source_names = [item["name"] for item in result["sources"]]
                for expected in case["must_include"]:
                    self.assertIn(expected, source_names)
                for forbidden in case["must_exclude"]:
                    self.assertNotIn(forbidden, source_names)

    def test_positive_routes_respect_research_limits(self):
        for case in CASES:
            result = self.router.route_task(case["task"])
            if not result["should_trigger"]:
                continue
            self.assertGreaterEqual(len(result["sources"]), 2)
            self.assertLessEqual(len(result["sources"]), 5)
            self.assertEqual({"min": 3, "max": 8}, result["case_target"])
            self.assertEqual({"min": 2, "max": 4}, result["core_reference_target"])
            self.assertEqual({"min": 3, "max": 7}, result["rule_target"])
            self.assertGreaterEqual(len(result["dimensions"]), 2)
            self.assertTrue(all(query.strip() for query in result["search_queries"]))

    def test_route_catalog_covers_plan_matrix_and_extensions(self):
        expected = {
            "web-visual", "landing-page", "web-app", "web-flow", "dashboard",
            "ppt-structure", "ppt-visual", "research-presentation", "coding-prompt",
            "agent-rules", "data-visualization", "scientific-mechanism",
            "system-architecture", "color-system", "typography", "visual-assets",
            "report-template",
        }
        self.assertEqual(expected, set(self.router.ROUTES))
        for route, config in self.router.ROUTES.items():
            with self.subTest(route=route):
                self.assertGreaterEqual(len(config["sources"]), 2)
                self.assertLessEqual(len(config["sources"]), 5)
                self.assertTrue(all(source in self.router.SOURCE_CATALOG for source in config["sources"]))

    def test_negative_route_has_no_sources(self):
        result = self.router.route_task("修复 Python 函数中的数组越界问题。")
        self.assertFalse(result["should_trigger"])
        self.assertEqual([], result["sources"])
        self.assertIn("普通代码报错修复", result["reason"])

    def test_extended_routing_matrix_categories(self):
        cases = [
            ("设计一个 AI SaaS Landing Page 的首屏、定价和 CTA。", "landing-page", {"Land-book", "Lapa Ninja", "Awwwards"}),
            ("设计 Web App 后台的设置、订阅和空状态。", "web-app", {"Mobbin", "Refero", "Page Flows"}),
            ("设计一套具有高端科技视觉的融资路演 PPT。", "ppt-visual", {"Behance", "Deck.gallery", "Dribbble"}),
            ("为开源数据平台设计无障碍品牌配色系统。", "color-system", {"Awwwards", "Coolors"}),
            ("为技术产品设计可部署的中英文字体层级。", "typography", {"Typewolf", "Land-book"}),
            ("为跨工具项目编写 AGENTS.md、CLAUDE.md 和 Cursor Rules。", "agent-rules", {"OpenAI 官方文档", "Anthropic 官方文档", "Cursor Directory", "高质量开源仓库实例"}),
            ("改进产品的信息层级、用户体验和展示逻辑。", "web-visual", {"Awwwards", "Land-book"}),
            ("设计产品图标系统和空状态插画风格。", "visual-assets", {"Iconify", "unDraw", "Behance"}),
            ("查找专业的数据分析报告模板。", "report-template", {"Behance", "SlideShare", "Pitch"}),
        ]
        for task, expected_route, expected_sources in cases:
            with self.subTest(task=task):
                result = self.router.route_task(task)
                self.assertEqual(expected_route, result["primary_route"])
                self.assertTrue(expected_sources.issubset({item["name"] for item in result["sources"]}))

    def test_explicit_exclusion_boundaries_do_not_trigger(self):
        tasks = [
            "不要联网，也不要参考外部案例，只修改现有网站文案。",
            "已经提供完整参考图，请严格按照参考图做局部修改，不要探索新风格。",
            "实现快速排序算法并解释复杂度。",
            "翻译这段英文。",
            "修复 Dashboard 数据加载 bug。",
        ]
        for task in tasks:
            with self.subTest(task=task):
                result = self.router.route_task(task)
                self.assertFalse(result["should_trigger"])
                self.assertEqual("none", result["primary_route"])

    def test_plan_specific_dimensions_are_exposed(self):
        expected = {
            "web-visual": {"information architecture", "color system", "type hierarchy", "data presentation"},
            "web-flow": {"user flow", "error state", "empty state", "feedback"},
            "dashboard": {"metric cards", "filters", "trend", "relationship network", "risk state"},
            "research-presentation": {"research storyline", "data visualization", "multi-slide rhythm"},
            "coding-prompt": {"official technical guidance", "tool rules", "acceptance criteria"},
            "scientific-mechanism": {"scientific accuracy", "algorithm relationships", "arrow semantics"},
        }
        for case in CASES:
            route = case["route"]
            if route not in expected:
                continue
            with self.subTest(route=route):
                actual = set(self.router.route_task(case["task"])["dimensions"])
                self.assertTrue(expected[route].issubset(actual))


class BriefValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.router = load_module()

    def test_valid_reference_brief_passes(self):
        brief = {
            "task": {"deliverable": "developer analytics homepage", "audience": "developers", "industry": "open source analytics"},
            "design_goal": "Create a credible analytics homepage with clear product proof.",
            "reference_dimensions": ["information architecture", "visual hierarchy", "data presentation"],
            "live_access": True,
            "reviewed_case_count": 3,
            "reviewed_website_count": 3,
            "sources": [
                {"name": "Awwwards", "url": "https://www.awwwards.com/sites/example", "case": "Example project", "relevance": "visual hierarchy", "facts": ["The page is a published project entry."], "observations": ["large left-aligned heading"], "inferences": ["The heading can shorten time to orientation."], "adopt": ["clear hierarchy"], "reject": ["heavy motion"], "translation": ["use repository graph as hero proof"], "license_checked": True},
                {"name": "Land-book", "url": "https://land-book.com/websites/example", "case": "Analytics landing page", "relevance": "page structure", "facts": ["The entry contains a full landing page."], "observations": ["single narrative flow"], "inferences": ["One narrative can reduce scanning ambiguity."], "adopt": ["one primary CTA"], "reject": ["generic testimonials"], "translation": ["show real project metrics"], "license_checked": True},
                {"name": "Typewolf", "url": "https://www.typewolf.com/site-of-the-day/example", "case": "Technology typography case", "relevance": "type hierarchy", "facts": ["The case identifies the font pairing."], "observations": ["two-weight sans-serif hierarchy"], "inferences": ["A restrained weight range supports data density."], "adopt": ["two-weight hierarchy"], "reject": ["display face in body copy"], "translation": ["use deployable local sans-serif fonts"], "license_checked": True}
            ],
            "rules": ["one primary action", "real product proof in hero", "restrained motion"],
            "rejected_patterns": ["generic testimonials", "motion without product value"],
            "applied_to_final": ["hero", "navigation", "metrics section"],
            "limitations": [],
            "fact_observation_inference_separated": True
        }
        result = self.router.validate_brief(brief)
        self.assertEqual("PASS", result["status"])
        self.assertEqual([], result["issues"])

    def test_homepage_only_brief_is_blocked(self):
        brief = {
            "task": {"deliverable": "homepage", "audience": "developers", "industry": "analytics"},
            "design_goal": "Create a homepage.",
            "reference_dimensions": ["visual hierarchy"],
            "live_access": True,
            "reviewed_case_count": 1,
            "reviewed_website_count": 1,
            "sources": [
                {"name": "Awwwards", "url": "https://www.awwwards.com", "case": "", "relevance": "looks good", "observations": [], "adopt": [], "reject": [], "translation": [], "license_checked": False}
            ],
            "rules": ["modern"],
            "rejected_patterns": [],
            "applied_to_final": [],
            "limitations": [],
            "fact_observation_inference_separated": False
        }
        result = self.router.validate_brief(brief)
        self.assertEqual("BLOCK", result["status"])
        messages = " ".join(issue["message"] for issue in result["issues"])
        self.assertIn("至少两个互补来源", messages)
        self.assertIn("具体案例", messages)
        self.assertIn("落实", messages)

    def test_reference_brief_contract_fields_are_required(self):
        brief = {
            "task": {"deliverable": "dashboard", "audience": "maintainers", "industry": "open source"},
            "design_goal": "",
            "reference_dimensions": [],
            "live_access": True,
            "reviewed_case_count": 2,
            "reviewed_website_count": 2,
            "sources": [
                {"name": "Mobbin", "url": "https://mobbin.com/screens/example", "case": "Analytics dashboard", "relevance": "product states", "observations": ["dense table"], "adopt": ["clear filters"], "reject": ["hidden labels"], "translation": ["label every risk filter"], "license_checked": True},
                {"name": "From Data to Viz", "url": "https://www.data-to-viz.com/graph/line.html", "case": "Line chart guidance", "relevance": "trend selection", "observations": ["ordered variables"], "adopt": ["line trend"], "reject": ["radar chart"], "translation": ["show repository health over time"], "license_checked": True},
            ],
            "rules": ["label filters", "show time range", "include risk state"],
            "rejected_patterns": [],
            "applied_to_final": ["filters", "trend panel"],
            "limitations": [],
            "fact_observation_inference_separated": True,
        }
        result = self.router.validate_brief(brief)
        self.assertEqual("BLOCK", result["status"])
        messages = " ".join(issue["message"] for issue in result["issues"])
        self.assertIn("设计目标", messages)
        self.assertIn("参考维度", messages)
        self.assertIn("不采用", messages)

    def test_offline_brief_requires_explicit_limitation(self):
        brief = {
            "task": {"deliverable": "scientific diagram", "audience": "reviewers", "industry": "machine learning"},
            "design_goal": "Create an accurate mechanism diagram.",
            "reference_dimensions": ["scientific hierarchy"],
            "live_access": False,
            "reviewed_case_count": 0,
            "reviewed_website_count": 0,
            "sources": [],
            "rules": [],
            "rejected_patterns": [],
            "applied_to_final": [],
            "limitations": ["实时参考检索未完成；仅使用用户提供的本地论文图。"],
            "fact_observation_inference_separated": True
        }
        result = self.router.validate_brief(brief)
        self.assertEqual("BLOCK", result["status"])

    def test_complete_offline_brief_is_caution_not_pass(self):
        brief = {
            "task": {"deliverable": "scientific diagram", "audience": "reviewers", "industry": "machine learning"},
            "design_goal": "Create an accurate mechanism diagram from supplied local figures.",
            "reference_dimensions": ["scientific hierarchy", "arrow semantics"],
            "live_access": False,
            "reviewed_case_count": 1,
            "reviewed_website_count": 0,
            "sources": [
                {"name": "User-supplied paper figure", "path": "materials/paper-figure-3.png", "case": "Paper Figure 3", "relevance": "domain mechanism", "facts": ["The supplied figure labels three stages."], "observations": ["left-to-right flow"], "inferences": ["The stage order should remain stable."], "adopt": ["three-stage order"], "reject": ["dense legend"], "translation": ["redraw as editable modules"], "license_checked": True}
            ],
            "rules": ["preserve stage order", "label every arrow", "use one legend"],
            "rejected_patterns": ["decorative arrows without meaning"],
            "applied_to_final": ["mechanism canvas"],
            "limitations": ["实时参考检索未完成；仅使用用户提供的本地论文图。"],
            "fact_observation_inference_separated": True,
        }
        result = self.router.validate_brief(brief)
        self.assertEqual("CAUTION", result["status"])

    def test_live_brief_rejects_non_http_case_location(self):
        brief = {
            "task": {"deliverable": "dashboard", "audience": "maintainers", "industry": "open source"},
            "design_goal": "Create an actionable health dashboard.",
            "reference_dimensions": ["product states", "chart selection"],
            "live_access": True,
            "reviewed_case_count": 3,
            "reviewed_website_count": 3,
            "sources": [
                {"name": f"Source {index}", "url": f"not-a-url/case-{index}", "case": f"Case {index}", "relevance": "relevant", "facts": ["fact"], "observations": ["observation"], "inferences": ["inference"], "adopt": ["rule"], "reject": ["pattern"], "translation": ["module"], "license_checked": True}
                for index in range(1, 4)
            ],
            "rules": ["rule one", "rule two", "rule three"],
            "rejected_patterns": ["pattern"],
            "applied_to_final": ["dashboard"],
            "limitations": [],
            "fact_observation_inference_separated": True,
        }
        result = self.router.validate_brief(brief)
        self.assertEqual("BLOCK", result["status"])
        self.assertIn("HTTP", " ".join(issue["message"] for issue in result["issues"]))

    def test_five_reviewed_cases_with_two_core_references_passes(self):
        brief = {
            "task": {"deliverable": "dashboard", "audience": "maintainers", "industry": "open source"},
            "design_goal": "Create an actionable health dashboard.",
            "reference_dimensions": ["product states", "chart selection"],
            "live_access": True,
            "reviewed_case_count": 5,
            "reviewed_website_count": 3,
            "sources": [
                {"name": "GitHub", "url": "https://github.com/example/project/community", "case": "Community profile", "relevance": "actionable checklist", "facts": ["The page exposes governance checks."], "observations": ["status rows"], "inferences": ["Risks should link to actions."], "adopt": ["action rows"], "reject": ["brand chrome"], "translation": ["governance module"], "license_checked": True},
                {"name": "From Data to Viz", "url": "https://www.data-to-viz.com/graph/line.html", "case": "Line chart guidance", "relevance": "trend choice", "facts": ["Line charts encode ordered variables."], "observations": ["axis-first guidance"], "inferences": ["Health trends need explicit ranges."], "adopt": ["line trend"], "reject": ["dual axis"], "translation": ["trend module"], "license_checked": True},
            ],
            "rules": ["link risks to actions", "show time range", "separate missing from zero"],
            "rejected_patterns": ["opaque composite score"],
            "applied_to_final": ["risk list", "trend module"],
            "limitations": [],
            "fact_observation_inference_separated": True,
        }
        result = self.router.validate_brief(brief)
        self.assertEqual("PASS", result["status"])


if __name__ == "__main__":
    unittest.main()
