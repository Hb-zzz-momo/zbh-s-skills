# Python 单体后端蓝图

```json
{
  "id": "python-backend",
  "classification": {
    "purpose": "Python API or backend service",
    "deployment": "single deployable",
    "repository": "single project",
    "workflow": "request-response application",
    "stacks": ["Python", "FastAPI, Django, Flask, or equivalent"]
  },
  "directories": [
    {"path": "app", "purpose": "Contain the importable backend application.", "required": true, "local_rules": ["Keep transport, business, and persistence responsibilities separate.", "Lower layers must not import HTTP routes."]},
    {"path": "app/api/routes", "purpose": "Define HTTP routes and transport translation.", "required": true},
    {"path": "app/api/dependencies", "purpose": "Provide request-scoped API dependencies.", "required": true},
    {"path": "app/core", "purpose": "Own configuration, security, logging, and lifecycle concerns.", "required": true},
    {"path": "app/services", "purpose": "Implement use cases and business orchestration.", "required": true},
    {"path": "app/repositories", "purpose": "Encapsulate persistence access.", "required": true},
    {"path": "app/models", "purpose": "Define persistence or domain models.", "required": true},
    {"path": "app/schemas", "purpose": "Define validated API and service-boundary data shapes.", "required": true},
    {"path": "app/db/migrations", "purpose": "Store versioned database migrations.", "required": true},
    {"path": "tests/unit", "purpose": "Test pure services, models, and helpers in isolation.", "required": true},
    {"path": "tests/integration", "purpose": "Test persistence, API, and external integration boundaries.", "required": true},
    {"path": "scripts", "purpose": "Store bounded maintenance entry points that call application modules.", "required": true},
    {"path": "docs/api", "purpose": "Document API contracts and usage.", "required": true},
    {"path": "docs/architecture", "purpose": "Document layers, dependency directions, and decisions.", "required": true}
  ]
}
```

## 依赖方向

`api -> services -> repositories -> db/models`。API 和服务可以使用 schemas；repositories 不得导入 API，models 不应持有 HTTP 语义。框架要求不同目录名时保留同样的职责边界。

## 文件路由示例

- 计费 HTTP 入口：`app/api/routes/billing.py`。
- 计费用例：`app/services/billing.py`。
- 账单持久化：`app/repositories/billing.py`。
- 运维脚本只做参数解析并调用 `app.services`，不复制业务逻辑。
