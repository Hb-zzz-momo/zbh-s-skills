---
name: database-competition-score-runner
description: Run an evidence-driven database competition workflow from official rules through reproducible score verification. Use when a competition has multiple code, performance, integration, or ecosystem tracks and the result must maximize verified points without confusing implementation, local tests, formal submissions, or receipts.
---

# Database Competition Score Runner

Turn a broad competition request into a score ledger backed by reproducible evidence.

## Establish the rules

1. Read the official rules, repository instructions, competition attachments, and pinned baseline commits.
2. Build a coverage matrix with columns: task ID, maximum score, required artifact, acceptance command, official submission field, current evidence, status, and next action.
3. Record exact repository URLs, branch names, full 40-character commit IDs, commands, exit codes, logs, and receipt paths.
4. Never infer a formal score from a passing unit test, a local benchmark, a pushed branch, or a submission attempt without a receipt.

## Resolve constraints early

- Verify account access, available operating systems, GPU access, database capabilities, disk, memory, and time limits before promising all tracks.
- Separate account-only actions, hardware-only actions, code actions, performance experiments, and external publication.
- Do not expose passwords, tokens, cookies, private keys, or other credentials in notes or logs.
- Keep judging scripts, hidden tests, baseline data, and official gates read-only.

## Run the implementation loop

1. Reproduce the first real failure against a fresh database or clean environment.
2. Capture the exact source revision and a minimal failing command.
3. Trace the failure to one root cause; distinguish application, parser, planner, storage, transaction, and test-fixture issues.
4. Make the smallest coherent fix and add or retain a regression that fails first and passes after the fix.
5. Rebuild once, start from a fresh state, and rerun both the targeted test and adjacent compatibility tests.
6. Repeat only while evidence identifies a concrete defect. Do not broaden the change to make a benchmark look better.

## Prove results

- Unit and parser checks prove only the executed layer.
- A full build proves compilation and linking, not SQL behavior.
- A fresh-catalog SQL run proves that source revision on that environment.
- Performance results require the official workload, matched configuration, multiple interleaved runs, correctness checks, and the unmodified scorer.
- Final submission evidence must identify the exact submitted commit and the official receipt or score page.

Use this status vocabulary:

| Status | Meaning |
| --- | --- |
| `idea` | Proposed only |
| `implemented` | Source changed |
| `static-pass` | Syntax, diff, or static checks passed |
| `local-pass` | Reproducible local tests passed |
| `formal-pending` | Submitted, no authoritative receipt yet |
| `verified` | Official receipt confirms the score |
| `blocked` | Missing hardware, account, access, or external state |

## Parallel work

- Parallelize only disjoint tasks or isolated worktrees.
- Keep shared parser, schema, configuration, scoring, and integration contracts under one owner.
- Serialize heavy compilers and database instances when resources are constrained.
- Require subagents to return source revisions, commands, outputs, limitations, and exact files touched.
- Integrate and verify subagent work centrally; their conclusions are evidence, not final acceptance.

## Finish

Report the verified score, maximum score, unverified candidates, blocked tracks, and the smallest next action for each gap. Preserve all raw evidence and state clearly when a result is not suitable for an official claim.

<!-- OB-S:rtdiGh_FUQeyPW-yJzdSSQ -->
