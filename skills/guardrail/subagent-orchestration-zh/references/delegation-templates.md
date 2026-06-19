# Delegation Templates

## Subagent 路由声明

```text
Subagent 路由：
- 授权：是/否，依据是...
- 本地主 skill：...
- 子代理计划：explorer/worker/reviewer，数量...
- 写范围：...
- 等待策略：...
- 回收审计：...
```

## Explorer Brief

```markdown
# Explorer Brief

- role: explorer
- mode: read-only
- objective:
- parent skill:
- input context:
- read-first files:
- do-not-read / do-not-touch:

## Task

Answer this one bounded question:

...

## Return Contract

- scope inspected:
- evidence with file/path/source anchors:
- confirmed facts:
- inferred facts:
- unresolved unknowns:
- fastest next check:
- confidence: high / medium / low

## Stop Condition

Stop after answering the bounded question. Do not propose edits unless asked.
```

## Worker Brief

```markdown
# Worker Brief

- role: worker
- mode: write
- parent skill:
- mission:
- minimum change:
- writable scope:
- forbidden scope:
- validation command:
- integration gate:

## Shared Rules

- You are not alone in the codebase.
- Do not revert or overwrite changes made by others.
- Only edit files inside writable scope.
- If the task requires touching forbidden scope, stop and report.
- Leave a merge-ready summary for the parent.

## Task

...

## Return Contract

- files changed:
- behavior changed:
- commands run:
- results:
- risks:
- parent integration notes:

## Stop Condition

Stop after the scoped change and validation. Do not expand scope.
```

## Reviewer Brief

```markdown
# Reviewer Brief

- role: reviewer
- mode: read-only
- parent skill:
- review scope:
- evidence to inspect:
- acceptance criteria:

## Task

Review for defects, regressions, missing tests, scope drift, and integration risk.

## Return Contract

- verdict: PASS / CAUTION / BLOCK
- findings ordered by severity:
- evidence anchors:
- missing verification:
- residual risk:
- smallest recommended fix:

## Stop Condition

Do not edit files. Do not broaden review outside scope unless a blocker requires it.
```

## Research Candidate Audit Brief

```markdown
# Research Candidate Audit Brief

- role: research explorer
- mode: read-only
- candidate id:
- parent flow: research-skill-flow-zh
- stage: Memory Intake / Gap Gate / Research Design / Smoke / Dev / Formal / Paper

## Candidate

- pain point:
- hypothesis:
- innovation:
- expected mechanism:
- claimed evidence:

## Task

Check whether the candidate has enough evidence and a clear failure condition for the current stage.

## Return Contract

- evidence supporting gap:
- evidence against gap:
- local feasibility:
- smoke design:
- failure condition:
- risk level: low / medium / high
- suggested action: PASS / CAUTION / BLOCK
- claim boundary:

## Stop Condition

Do not upgrade this candidate to a paper contribution. Formal and claim decisions return to local audit skills.
```

## Engineering Parallel Review Brief

```markdown
# Engineering Parallel Review Brief

- role: engineering reviewer
- mode: read-only
- parent lifecycle stage:
- changed scope:
- commands already run:

## Task

Review only the changed behavior boundary. Prioritize user-visible defects, missing regression coverage, unsafe coupling, and rollback risk.

## Return Contract

- verdict: PASS / CAUTION / BLOCK
- top findings:
- tests or checks missing:
- scope drift:
- rollback risk:
- recommended next action:
```

## Orchestration Plan

```markdown
# Orchestration Plan

- run id:
- request summary:
- user constraints:
- authorized for subagents: yes / no
- local primary skill:
- delegation justification:
- worker count:
- execution mode: serial / parallel / mixed
- review policy:

## Agents

| id | type | mode | mission | writable scope | wait rule | integration gate |
|---|---|---|---|---|---|---|

## Evidence Paths

- worker briefs:
- results:
- review verdict:
- acceptance:

## Fallback

- no subagent tools:
- partial result:
- conflict:
```

## Status

```markdown
# Subagent Status

- run id:
- current stage:
- active agents:
- waiting agents:
- completed agents:
- failed agents:
- current blocker:
- next parent action:
```

## Acceptance

```markdown
# Acceptance

- accepted: yes / no
- parent verification:
- subagent results used:
- landed changes:
- audit skill triggered:
- residual risks:
- cleanup decision: keep evidence / remove transient artifacts
```
