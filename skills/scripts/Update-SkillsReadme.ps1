# Skills README auto-generator
# Usage: powershell -File .\scripts\Update-SkillsReadme.ps1
# Or:    & "C:\Users\zbh\.agents\skills\scripts\Update-SkillsReadme.ps1"

$skillsRoot = Split-Path $PSScriptRoot -Parent
$readmePath = Join-Path $skillsRoot "README.md"

function Get-RelFromSkillsRoot([string]$Root, [string]$FullPath) {
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd([char[]]@('\', '/'))
    $dirFull   = [System.IO.Path]::GetFullPath($FullPath)
    $prefix    = $rootFull + [IO.Path]::DirectorySeparatorChar
    if ($dirFull.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        return $dirFull.Substring($prefix.Length)
    }
    if ($dirFull.Equals($rootFull, [StringComparison]::OrdinalIgnoreCase)) { return '' }
    return $dirFull
}
# addyosmani/agent-skills leaf folder names (also first-level dir under agent-skills-ao/)
$agentSkillsAo = @(
    'api-and-interface-design','browser-testing-with-devtools','ci-cd-and-automation',
    'code-review-and-quality','code-simplification','context-engineering','debugging-and-error-recovery',
    'deprecation-and-migration','documentation-and-adrs','doubt-driven-development','frontend-ui-engineering',
    'git-workflow-and-versioning','idea-refine','incremental-implementation','performance-optimization',
    'planning-and-task-breakdown','security-and-hardening','shipping-and-launch','source-driven-development',
    'spec-driven-development','test-driven-development','using-agent-skills'
)

$agentSkillsAoDescZh = @{
    'api-and-interface-design' = '指导稳定 API 与接口设计，适用于 REST/GraphQL 接口、模块边界、类型契约、前后端边界等公共接口设计。'
    'browser-testing-with-devtools' = '使用真实浏览器和 DevTools 验证页面行为，适用于 DOM 检查、控制台错误、网络请求、性能与渲染问题排查。'
    'ci-cd-and-automation' = '自动化 CI/CD 流水线配置，适用于构建、测试、质量门禁、部署流程和自动化脚本编排。'
    'code-review-and-quality' = '进行多维度代码审查，合并前优先检查缺陷风险、可维护性、测试覆盖、性能、安全和架构一致性。'
    'code-simplification' = '在不改变行为的前提下简化代码，适用于降低复杂度、去除重复、改善命名、拆分职责和提升可读性。'
    'context-engineering' = '优化 Agent 上下文配置，适用于项目启动、上下文退化、任务切换、规则文件整理和提示上下文设计。'
    'debugging-and-error-recovery' = '系统化定位根因并恢复错误，适用于测试失败、构建中断、异常行为、回归问题和未知报错排查。'
    'deprecation-and-migration' = '管理废弃与迁移流程，适用于移除旧系统/API/功能、兼容迁移、用户过渡和弃用策略设计。'
    'documentation-and-adrs' = '记录架构决策与项目文档，适用于 ADR、公共 API 变更、重要特性发布和未来维护上下文沉淀。'
    'doubt-driven-development' = '对非平凡决策进行怀疑式复核，适用于高风险代码、陌生系统、生产关键路径和需要反证审查的方案。'
    'frontend-ui-engineering' = '构建生产级前端界面，适用于组件、布局、状态、交互、响应式设计和用户可感知体验实现。'
    'git-workflow-and-versioning' = '规范 Git 工作流与版本管理，适用于分支、提交、变更组织、冲突处理、发布版本和协作流程。'
    'idea-refine' = '通过发散与收敛思考迭代打磨想法，适用于创意澄清、方案压力测试、MVP 范围收敛和一页纸产出。'
    'incremental-implementation' = '按小步可验证方式交付改动，适用于多文件功能、较大重构、风险分阶段落地和持续验证。'
    'performance-optimization' = '优化应用性能，适用于性能回归、加载速度、Core Web Vitals、热点剖析、资源瓶颈和响应时间问题。'
    'planning-and-task-breakdown' = '把需求拆解为有序任务，适用于规格明确但规模较大的功能、实施排期、范围评估和依赖梳理。'
    'security-and-hardening' = '加固代码安全性，适用于用户输入、认证授权、数据存储、外部集成、会话管理和漏洞风险面。'
    'shipping-and-launch' = '准备生产发布，适用于上线清单、监控告警、灰度发布、回滚策略、发布风险和发布后验证。'
    'source-driven-development' = '基于官方文档做实现决策，适用于框架/库版本易变、需要权威来源、避免过时模式的开发任务。'
    'spec-driven-development' = '先写规格再编码，适用于新项目、新功能、需求不清晰、边界模糊或需要明确验收标准的任务。'
    'test-driven-development' = '用测试驱动开发，适用于实现逻辑、修复缺陷、改变行为、证明正确性和防止回归。'
    'using-agent-skills' = '发现并调用合适的 Agent 技能，适用于会话开始、技能选择、技能组合和工作流路由。'
}

$agentSkillsAoTrigZh = @{
    'api-and-interface-design' = 'API设计、接口设计、REST、GraphQL、模块边界、类型契约、前后端边界、公共接口稳定性。'
    'browser-testing-with-devtools' = '浏览器测试、DevTools、DOM检查、控制台错误、网络请求、页面渲染、真实浏览器验证。'
    'ci-cd-and-automation' = 'CI/CD、GitHub Actions、流水线、自动化测试、质量门禁、构建部署、发布自动化。'
    'code-review-and-quality' = '代码审查、Code Review、合并前检查、质量审计、缺陷风险、可维护性、测试缺口。'
    'code-simplification' = '代码简化、重构、降低复杂度、去重复、改善命名、拆分职责、可读性提升。'
    'context-engineering' = '上下文工程、规则文件、AGENTS.md、提示上下文、项目启动上下文、任务切换。'
    'debugging-and-error-recovery' = '调试、报错恢复、根因分析、测试失败、构建失败、行为异常、回归定位。'
    'deprecation-and-migration' = '废弃、迁移、兼容策略、旧接口移除、用户迁移、弃用计划、系统替换。'
    'documentation-and-adrs' = '文档、ADR、架构决策记录、公共API变更、设计决策、维护上下文。'
    'doubt-driven-development' = '怀疑式开发、反证审查、高风险决策、生产关键路径、方案复核、正确性优先。'
    'frontend-ui-engineering' = '前端工程、组件、布局、状态管理、交互、响应式、UI体验、生产级界面。'
    'git-workflow-and-versioning' = 'Git工作流、分支、提交、冲突、版本管理、发布版本、协作变更。'
    'idea-refine' = '想法打磨、创意迭代、ideate、方案压力测试、MVP范围、一页纸。'
    'incremental-implementation' = '增量实现、小步交付、多文件改动、分阶段落地、持续验证、降低变更风险。'
    'performance-optimization' = '性能优化、性能回归、加载速度、Core Web Vitals、剖析、瓶颈、响应时间。'
    'planning-and-task-breakdown' = '任务拆解、实施计划、需求拆分、范围评估、依赖梳理、排期。'
    'security-and-hardening' = '安全加固、输入校验、认证授权、数据存储、外部集成、会话安全、漏洞风险。'
    'shipping-and-launch' = '上线、发布准备、发布清单、监控告警、灰度、回滚、发布验证。'
    'source-driven-development' = '官方文档、权威来源、框架版本、库用法、避免过时模式、文档驱动开发。'
    'spec-driven-development' = '规格驱动、先写规格、需求不清、验收标准、新功能边界、设计规格。'
    'test-driven-development' = '测试驱动、TDD、单元测试、回归测试、修复缺陷、行为变更、正确性证明。'
    'using-agent-skills' = '技能选择、调用技能、技能组合、工作流路由、会话启动、Agent技能发现。'
}

$scenarioBySkill = @{
    'agent-wait-monitor-zh'        = 'ops'
    'artifact-curator-zh'        = 'ops'
    'decisive-result-audit-zh'   = 'research-audit'
    'exam-answer-zh'             = 'course'
    'info-evidence-chain-zh'     = 'info'
    'iteration-reflection-guard-zh' = 'guardrail'
    'knowledge-digest-zh'        = 'learning'
    'lab-report-coach-zh'        = 'course'
    'paper-writing-zh'           = 'writing'
    'plan-faithful-execution-zh' = 'guardrail'
    'ppt-story-design-zh'        = 'presentation'
    'engineering-skill-flow-zh'  = 'engineering'
    'web-design-workflow-zh'     = 'engineering'
    'project-dev-zh'             = 'engineering'
    'project-handoff-zh'         = 'engineering'
    'project-kickoff-delivery-zh' = 'engineering'
    'research-coach-zh'          = 'research-audit'
    'research-experiment-ops-zh' = 'research-audit'
    'research-iteration-audit-zh' = 'research-audit'
    'research-skill-flow-zh'     = 'research-audit'
    'research-statistics-reporting-zh' = 'research-audit'
    'software-copyright-zh'      = 'presentation'
    'skill-router-zh'            = 'guardrail'
    'subagent-orchestration-zh'  = 'guardrail'
    'translation-zh'             = 'writing'
    'workflow-forge-zh'          = 'guardrail'
}

# Collect all skill info (type-first subfolders + shared references/ at repo root)
$skills = [System.Collections.ArrayList]::new()
$idx = 0
$skillDirs = @(
    Get-ChildItem $skillsRoot -Recurse -Filter 'SKILL.md' -File |
    Where-Object {
        $p = $_.FullName
        $p -notmatch '[\\/]scripts[\\/]' -and $p -notmatch '[\\/]references[\\/]'
    } |
    ForEach-Object { $_.Directory } |
    Sort-Object FullName -Unique
)
foreach ($dir in $skillDirs) {
    $md = Join-Path $dir.FullName "SKILL.md"
    if (-not (Test-Path $md)) { continue }
    $idx++
    $raw = [System.IO.File]::ReadAllText($md, [System.Text.Encoding]::UTF8)
    $lc  = ([System.IO.File]::ReadAllLines($md, [System.Text.Encoding]::UTF8)).Count

    $n = $dir.Name
    if ($raw -match '(?m)^name:\s*(.+)$') { $n = $Matches[1].Trim() }

    $frontDesc = ''
    if ($raw -match '(?m)^description:\s*(.+)$') {
        $frontDesc = $Matches[1].Trim().Trim([char[]]@("'", '"'))
    }

    $d = ''
    if ($frontDesc -and $frontDesc -match '(.+?)\s*Use when') {
        $d = $Matches[1].Trim().TrimEnd(':').TrimEnd('。').TrimEnd('.')
    }
    elseif ($raw -match '(?ms)^description:\s*[''"]?(.+?)Use when') {
        $d = $Matches[1].Trim().TrimEnd(':').TrimEnd('。').TrimEnd('.')
    }

    $t = ''
    if ($frontDesc -and $frontDesc -match 'Use when:\s*(.+)$') {
        $t = $Matches[1].Trim()
    }
    elseif ($raw -match 'Use when:\s*([^.''\"]+)') {
        $t = $Matches[1].Trim()
    }
    if ($t) {
        $t = ($t -replace '不适用于[:：].*$', '').Trim().TrimEnd('。').TrimEnd('.')
    }

    if ($agentSkillsAo -contains $dir.Name) {
        if ($agentSkillsAoDescZh.ContainsKey($dir.Name)) {
            $d = $agentSkillsAoDescZh[$dir.Name]
        }
        if ($agentSkillsAoTrigZh.ContainsKey($dir.Name)) {
            $t = $agentSkillsAoTrigZh[$dir.Name]
        }
    }

    $scenario = 'other'
    if ($agentSkillsAo -contains $dir.Name) {
        $scenario = 'agent-skills-ao'
    }
    if ($scenarioBySkill.ContainsKey($n)) {
        $scenario = $scenarioBySkill[$n]
    }

    $relDir = Get-RelFromSkillsRoot $skillsRoot $dir.FullName

    [void]$skills.Add([PSCustomObject]@{
        Idx = $idx; Name = $n; Scenario = $scenario; Lines = $lc; Desc = $d; Trig = $t; RelDir = $relDir
    })
}

# Scenario display names and stable order
$scenarioLabel = @{
    'research-audit'='科研实验与结果审计'
    'engineering'='项目工程开发'
    'guardrail'='计划约束与迭代守门'
    'writing'='论文写作与翻译'
    'course'='课程实验与考试'
    'info'='信息调研与证据链'
    'presentation'='汇报展示与软著'
    'ops'='长任务与产物管理'
    'learning'='全局学习复盘'
    'agent-skills-ao'='addyosmani / agent-skills 工程工作流'
    'other'='其他'
}
$scenarioOrder = @('research-audit','engineering','guardrail','writing','course','info','presentation','ops','learning','agent-skills-ao','other')

$date = Get-Date -Format 'yyyy-MM-dd'
$L = [System.Collections.ArrayList]::new()

# --- header ---
[void]$L.Add('# Skills Registry')
[void]$L.Add('')
[void]$L.Add("> Path: ``~/.agents/skills/``  ")
[void]$L.Add("> Layout: one type folder (e.g. ``research-audit/``, ``agent-skills-ao/``) then the skill dir; shared ``references/`` stays at repo root.  ")
[void]$L.Add("> Updated: $date  ")
[void]$L.Add('> Auto-generated by `scripts/Update-SkillsReadme.ps1`')
[void]$L.Add("> Routing: start with ``skill-router-zh`` or ``SKILL_ROUTING.zh-CN.md``; load only the necessary 1-3 skills for the current task.")
[void]$L.Add('')
[void]$L.Add('## Global Defaults')
[void]$L.Add('')
[void]$L.Add('- ``knowledge-digest-zh`` is a user-level global skill and is auto-invoked at task completion via ``~/.agents/.instructions.md``')
[void]$L.Add('')

# --- routing protocol ---
[void]$L.Add('## Skill Routing Protocol')
[void]$L.Add('')
[void]$L.Add('- For any "which skill should I use" or multi-skill orchestration task, start with ``skill-router-zh``.')
[void]$L.Add('- For engineering tasks, use the ``agent-skills-ao`` lifecycle: Define -> Plan -> Build -> Verify -> Review -> Ship; for complex engineering, multi-solution implementation, architecture changes, engineering Gate, or technical spike, start with ``engineering-skill-flow-zh``.')
[void]$L.Add('- For strict plans, contest prompts, fixed requirements, or user-specified boundaries, add ``plan-faithful-execution-zh`` before implementation.')
[void]$L.Add('- Load the minimum useful set: usually one primary skill plus one verification/review skill; avoid loading the whole library.')
[void]$L.Add('- Full routing handbook: ``SKILL_ROUTING.zh-CN.md``.')
[void]$L.Add('')

# --- overview table ---
[void]$L.Add('## Overview')
[void]$L.Add('')
$displayIdx = 0
foreach ($scenario in $scenarioOrder) {
    $group = @($skills | Where-Object { $_.Scenario -eq $scenario } | Sort-Object Name)
    if ($group.Count -eq 0) { continue }
    $label = if ($scenarioLabel.ContainsKey($scenario)) { $scenarioLabel[$scenario] } else { $scenario }
    [void]$L.Add("### $label")
    [void]$L.Add('')
    [void]$L.Add('| # | Skill | Lines | Description |')
    [void]$L.Add('|---|-------|-------|-------------|')
    foreach ($s in $group) {
        $displayIdx++
        [void]$L.Add("| $displayIdx | ``$($s.Name)`` | $($s.Lines) | $($s.Desc) |")
    }
    [void]$L.Add('')
}

# --- triggers ---
[void]$L.Add('## Trigger Keywords')
[void]$L.Add('')
foreach ($scenario in $scenarioOrder) {
    $group = @($skills | Where-Object { $_.Scenario -eq $scenario } | Sort-Object Name)
    if ($group.Count -eq 0) { continue }
    $label = if ($scenarioLabel.ContainsKey($scenario)) { $scenarioLabel[$scenario] } else { $scenario }
    [void]$L.Add("### $label")
    foreach ($s in $group) {
        if ($s.Trig) {
            [void]$L.Add("- **$($s.Trig)** -> ``$($s.Name)``")
        }
    }
    [void]$L.Add('')
}

# --- common features ---
[void]$L.Add('## Common Features')
[void]$L.Add('')
[void]$L.Add('All skills support:')
[void]$L.Add('')
[void]$L.Add('1. **Self-iteration mode** - give feedback after use to trigger optimization')
[void]$L.Add('2. **YAML frontmatter** - standard name / description fields')
[void]$L.Add('3. **Markdown deliverable** - substantial skill outputs must also be written to Markdown file(s) or a dedicated output folder in the current workspace')
[void]$L.Add('4. **Skill-output naming** - new outputs go under ``skill-outputs/<skill-name>/`` and use Chinese topic names with the date/time suffix, for example ``阶段审计报告_YYYYMMDD_HHMMSS.md``; do not repeat the skill name in the file or folder name')
[void]$L.Add('5. **Line limit** - every SKILL.md < 500 lines')
[void]$L.Add('')

# --- directory tree ---
[void]$L.Add('## Directory Structure')
[void]$L.Add('')
[void]$L.Add('```')
[void]$L.Add('~/.agents/skills/')
[void]$L.Add('  README.md')
[void]$L.Add('  .instructions.md')
if (Test-Path (Join-Path $skillsRoot 'SKILL_ROUTING.zh-CN.md')) {
    [void]$L.Add('  SKILL_ROUTING.zh-CN.md')
}
[void]$L.Add('  scripts/')
[void]$L.Add('    Update-SkillsReadme.ps1')
$refDir = Join-Path $skillsRoot 'references'
if (Test-Path $refDir) {
    [void]$L.Add('  references/')
    foreach ($item in (Get-ChildItem $refDir -File | Sort-Object Name)) {
        [void]$L.Add("    $($item.Name)")
    }
}
foreach ($s in ($skills | Sort-Object RelDir)) {
    $disp = ($s.RelDir -replace '\\','/') + '/'
    [void]$L.Add("  $disp")
    $items = Get-ChildItem (Join-Path $skillsRoot $s.RelDir) | Sort-Object { if($_.PSIsContainer){0}else{1} }, Name
    foreach ($item in $items) {
        $suf = if ($item.PSIsContainer) { '/' } else { '' }
        [void]$L.Add("    $($item.Name)$suf")
    }
}
[void]$L.Add('```')

# --- write ---
$output = $L -join "`n"
[System.IO.File]::WriteAllText($readmePath, $output, [System.Text.Encoding]::UTF8)
Write-Host "README.md updated: $($skills.Count) skills, $date"
