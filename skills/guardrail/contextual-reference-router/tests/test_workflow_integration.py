import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class WorkflowIntegrationTests(unittest.TestCase):
    def assert_between(self, text: str, marker: str, before: str, after: str):
        self.assertIn(marker, text)
        self.assertLess(text.index(before), text.index(marker))
        self.assertLess(text.index(marker), text.index(after))

    def test_web_gate_is_between_spec_and_design(self):
        text = read("engineering/web-design-workflow-zh/SKILL.md")
        self.assert_between(text, "contextual-reference-router:gate:v1:start", "## Phase 1: 规格化需求", "## Phase 2: DESIGN.md 与审美门")
        self.assertIn("reference-brief", text)
        self.assertIn("局部 UI Bug", text)
        for trigger in ("Web 用户流程", "信息层级", "响应式", "用户体验"):
            self.assertIn(trigger, text)

    def test_ppt_gate_precedes_visual_system(self):
        text = read("presentation/ppt-workflow-orchestrator-zh/SKILL.md")
        self.assertIn("contextual-reference-router:gate:v1:start", text)
        self.assertLess(text.index("contextual-reference-router:gate:v1:start"), text.index("## Phase 5：三页纵向切片"))
        self.assertIn("事实来源仍归 `info-evidence-chain-zh`", text)
        self.assertIn("ppt-reference-library-zh", text)
        self.assertIn("新建或重设计 PPT", text)
        self.assertIn("完整模板", text)
        self.assertIn("禁止外部参考", text)

    def test_research_figure_gate_follows_fact_lock(self):
        text = read("research-audit/research-figure-generation-zh/SKILL.md")
        self.assert_between(text, "contextual-reference-router:gate:v1:start", "### Step 2: 锁定科学事实", "### Step 3: 选择生成策略")
        self.assertIn("外部案例不得定义科学事实", text)

    def test_engineering_prompt_reference_gate_is_conditional(self):
        text = read("engineering/engineering-skill-flow-zh/SKILL.md")
        self.assert_between(text, "contextual-reference-router:gate:v1:start", "## 1. Project Intake", "## 2. Solution Gate")
        self.assertIn("Coding Prompt", text)
        self.assertIn("形成后退出", text)

    def test_workflow_forge_has_mode_specific_reference_gate(self):
        text = read("guardrail/workflow-forge-zh/SKILL.md")
        self.assertIn("contextual-reference-router:gate:v1:start", text)
        for mode in ("模式 A", "模式 B", "模式 C", "模式 D"):
            self.assertIn(mode, text)
        self.assertIn("忠实还原", text)

    def test_global_router_and_manual_register_skill(self):
        router = read("guardrail/skill-router-zh/SKILL.md")
        manual = read("SKILL_ROUTING.zh-CN.md")
        self.assertIn("contextual-reference-router", router)
        self.assertIn("动态外部案例", router)
        self.assertIn("contextual-reference-router", manual)
        self.assertIn("参考驱动设计", manual)

    def test_generated_registry_lists_skill(self):
        registry = read("README.md")
        self.assertIn("contextual-reference-router", registry)
        row = next(line for line in registry.splitlines() if "`contextual-reference-router`" in line)
        self.assertNotRegex(row, r"\|\s*\|$")
        guardrail_section = registry.split("### 计划约束与迭代守门", 1)[1].split("### ", 1)[0]
        self.assertIn("`contextual-reference-router`", guardrail_section)


if __name__ == "__main__":
    unittest.main()
