# 前后端分离 Web 蓝图

```json
{
  "id": "web-fullstack-separated",
  "classification": {
    "purpose": "polyglot full-stack web application",
    "deployment": "frontend and backend independently deployable",
    "repository": "polyglot monorepo",
    "workflow": "request-response application",
    "stacks": ["React or Vue", "FastAPI, Django, Spring, or equivalent"]
  },
  "directories": [
    {"path": "frontend", "purpose": "Own the browser application, its build, dependencies, tests, and local documentation.", "required": true, "local_rules": ["Keep browser code and frontend dependencies inside frontend.", "Organize business code by feature; keep shared UI free of feature state."]},
    {"path": "frontend/public", "purpose": "Store assets served without bundler transformation.", "required": true},
    {"path": "frontend/src/app", "purpose": "Compose routes, providers, layouts, and application startup.", "required": true},
    {"path": "frontend/src/app/routes", "purpose": "Define application route composition.", "required": true},
    {"path": "frontend/src/app/providers", "purpose": "Compose global providers and application-wide context.", "required": true},
    {"path": "frontend/src/app/layouts", "purpose": "Define application-level layouts.", "required": true},
    {"path": "frontend/src/features", "purpose": "Own complete business features and their private UI, API, state, and types.", "required": true},
    {"path": "frontend/src/components/ui", "purpose": "Store business-agnostic reusable UI primitives.", "required": true},
    {"path": "frontend/src/components/common", "purpose": "Store cross-feature composed components with explicit consumers.", "required": false, "conditional": "shared_common_components"},
    {"path": "frontend/src/services", "purpose": "Provide shared HTTP clients and cross-feature service adapters.", "required": true},
    {"path": "frontend/src/hooks", "purpose": "Store genuinely global reusable hooks.", "required": true},
    {"path": "frontend/src/stores", "purpose": "Store application-wide state only.", "required": true},
    {"path": "frontend/src/lib", "purpose": "Wrap third-party libraries behind project-owned interfaces.", "required": true},
    {"path": "frontend/src/assets", "purpose": "Store assets processed by the frontend build.", "required": true},
    {"path": "frontend/src/styles", "purpose": "Store global design tokens and style foundations.", "required": true},
    {"path": "frontend/tests", "purpose": "Store frontend integration and end-to-end support tests.", "required": true},
    {"path": "backend", "purpose": "Own the server application, its build, dependencies, tests, and local documentation.", "required": true, "local_rules": ["Keep HTTP adapters thin and place business behavior in services.", "Use repositories for persistence and do not import API modules from lower layers."]},
    {"path": "backend/app/api/routes", "purpose": "Expose HTTP routes and translate transport inputs and outputs.", "required": true},
    {"path": "backend/app/api/dependencies", "purpose": "Provide request-scoped dependencies for the API layer.", "required": true},
    {"path": "backend/app/core", "purpose": "Own cross-cutting configuration, security, and lifecycle concerns.", "required": true},
    {"path": "backend/app/services", "purpose": "Implement application use cases and business orchestration.", "required": true},
    {"path": "backend/app/repositories", "purpose": "Encapsulate persistence access behind domain-oriented interfaces.", "required": true},
    {"path": "backend/app/models", "purpose": "Define persistence or domain models according to the selected framework.", "required": true},
    {"path": "backend/app/schemas", "purpose": "Define validated API and service-boundary data shapes.", "required": true},
    {"path": "backend/app/db/migrations", "purpose": "Store versioned database schema migrations.", "required": true},
    {"path": "backend/tests", "purpose": "Store backend unit, integration, and API tests.", "required": true},
    {"path": "backend/scripts", "purpose": "Store bounded operational entry points that call backend code.", "required": true},
    {"path": "contracts", "purpose": "Store shared OpenAPI, event, or schema contracts between deployables.", "required": false, "conditional": "shared_contracts", "local_rules": ["Treat contracts as versioned interfaces; do not place application implementations here."]},
    {"path": "infrastructure", "purpose": "Store repository-level container, gateway, and deployment configuration.", "required": false, "conditional": "with_infrastructure"},
    {"path": "docs/architecture", "purpose": "Document cross-deployable architecture and decisions.", "required": true},
    {"path": "docs/api", "purpose": "Document public and integration-facing APIs.", "required": true},
    {"path": "docs/adr", "purpose": "Store architecture decision records.", "required": true}
  ]
}
```

## 依赖方向

`frontend -> contracts <- backend`；部署配置依赖可构建制品，不被应用源码导入。后端内部遵循 `api -> services -> repositories -> db/models`。前端功能可依赖共享 UI、services 和 lib，共享层不得反向依赖具体功能。

## 增量规则

- 新功能放 `frontend/src/features/<feature>/`，仅该功能使用的请求封装放其 `api/`。
- 新后端用例放 `backend/app/services/`，HTTP 入口放 `backend/app/api/routes/`。
- 只有共享契约真实存在时启用 `contracts/`；只有存在部署配置时启用 `infrastructure/`。
- 若现有仓库已稳定使用 `apps/web` 和 `apps/api`，不要套用本蓝图进行迁移。
