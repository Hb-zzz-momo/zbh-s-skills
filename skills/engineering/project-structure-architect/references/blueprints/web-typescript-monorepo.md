# TypeScript Monorepo 蓝图

```json
{
  "id": "web-typescript-monorepo",
  "classification": {
    "purpose": "multiple TypeScript applications with shared packages",
    "deployment": "multiple applications",
    "repository": "language monorepo",
    "workflow": "workspace task graph",
    "stacks": ["TypeScript", "React or Node.js", "pnpm or equivalent", "Turborepo or equivalent"]
  },
  "directories": [
    {"path": "apps", "purpose": "Contain independently runnable or deployable applications.", "required": true, "local_rules": ["Every child is an application boundary with local dependencies and tests.", "Do not import another application's private source directly."]},
    {"path": "apps/web", "purpose": "Own the primary user-facing web application.", "required": true},
    {"path": "apps/admin", "purpose": "Own the independently runnable administration application.", "required": true},
    {"path": "apps/api", "purpose": "Own an independently runnable Node.js API when required.", "required": false, "conditional": "with_api"},
    {"path": "apps/docs", "purpose": "Own a separately built documentation application when required.", "required": false, "conditional": "with_docs_app"},
    {"path": "packages", "purpose": "Contain stable libraries consumed by multiple workspace applications.", "required": true, "local_rules": ["Packages must not contain application-specific routes, state, or deployment logic.", "Create a package only for an explicit boundary or known consumer."]},
    {"path": "packages/ui", "purpose": "Provide shared business-agnostic UI components for web and admin.", "required": true},
    {"path": "packages/types", "purpose": "Provide shared TypeScript types across applications.", "required": true},
    {"path": "packages/api-client", "purpose": "Provide a generated or maintained shared API client.", "required": false, "conditional": "shared_api_client"},
    {"path": "packages/validation", "purpose": "Provide shared boundary validation schemas.", "required": false, "conditional": "shared_validation"},
    {"path": "packages/config-eslint", "purpose": "Provide shared lint configuration.", "required": false, "conditional": "shared_tooling"},
    {"path": "packages/config-typescript", "purpose": "Provide shared TypeScript compiler configuration.", "required": false, "conditional": "shared_tooling"},
    {"path": "packages/testing", "purpose": "Provide shared test utilities without application fixtures.", "required": false, "conditional": "shared_testing"},
    {"path": "infrastructure", "purpose": "Store deployment and repository-level environment configuration.", "required": false, "conditional": "with_infrastructure"},
    {"path": "scripts", "purpose": "Store repository-wide maintenance entry points.", "required": true},
    {"path": "docs", "purpose": "Document workspace boundaries, package ownership, and cross-app decisions.", "required": true}
  ]
}
```

## 依赖方向

`apps/* -> packages/*`。包之间的依赖必须无环并通过公开入口；`packages/*` 不得依赖 `apps/*`。应用间通过 API、事件或共享契约通信，不直接导入彼此源码。

## 增量规则

- 能独立启动或部署的单元进入 `apps/`；仅一个应用使用的代码留在该应用内。
- 只有明确有多个消费者或代表稳定边界时才创建 `packages/<name>`。
- 包级任务和配置尽量与包同址，根级任务只编排工作区。
- 已有 `frontend/backend` 多语言结构时，不因添加共享类型就整体改为本蓝图。
