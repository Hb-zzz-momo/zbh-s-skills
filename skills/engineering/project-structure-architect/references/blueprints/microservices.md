# 微服务蓝图

```json
{
  "id": "microservices",
  "classification": {
    "purpose": "multiple independently deployable services",
    "deployment": "multiple services",
    "repository": "polyglot or language monorepo",
    "workflow": "service APIs, events, and independent delivery",
    "stacks": ["containers", "service-specific runtimes", "infrastructure as code"]
  },
  "directories": [
    {"path": "services", "purpose": "Contain independently buildable, testable, and deployable services.", "required": true, "local_rules": ["Each service owns its source, tests, configuration, and migrations.", "Services communicate through versioned contracts, never private source imports."]},
    {"path": "services/api/src", "purpose": "Contain the API service implementation.", "required": true},
    {"path": "services/api/tests", "purpose": "Contain API service-local tests.", "required": true},
    {"path": "services/api/config", "purpose": "Contain non-secret API service configuration schemas and defaults.", "required": true},
    {"path": "services/worker/src", "purpose": "Contain the independently deployable worker implementation.", "required": true},
    {"path": "services/worker/tests", "purpose": "Contain worker service-local tests.", "required": true},
    {"path": "services/worker/config", "purpose": "Contain non-secret worker configuration schemas and defaults.", "required": true},
    {"path": "packages/contracts", "purpose": "Store versioned API, event, and data contracts shared across services.", "required": true, "local_rules": ["Contracts contain interfaces and compatibility tests, not service implementations."]},
    {"path": "packages/clients", "purpose": "Store generated or maintained clients consumed by multiple services.", "required": false, "conditional": "shared_clients"},
    {"path": "packages/observability", "purpose": "Store stable shared telemetry interfaces and bootstrap code.", "required": false, "conditional": "shared_observability"},
    {"path": "infra/docker", "purpose": "Store repository-level container composition and build support.", "required": true},
    {"path": "infra/kubernetes", "purpose": "Store Kubernetes manifests or charts when used.", "required": false, "conditional": "with_kubernetes"},
    {"path": "infra/terraform", "purpose": "Store Terraform infrastructure definitions when used.", "required": false, "conditional": "with_terraform"},
    {"path": "gateway", "purpose": "Store gateway routing and policy configuration when a gateway exists.", "required": false, "conditional": "with_gateway"},
    {"path": "tests/contract", "purpose": "Test service contract compatibility across deployables.", "required": true},
    {"path": "tests/system", "purpose": "Test representative multi-service business paths.", "required": true},
    {"path": "docs/architecture", "purpose": "Document service ownership, data boundaries, and dependency rules.", "required": true},
    {"path": "docs/runbooks", "purpose": "Document service operations, failure handling, and recovery.", "required": true},
    {"path": "scripts", "purpose": "Store repository-wide build, validation, and environment entry points.", "required": true}
  ]
}
```

## 依赖方向

`services/* -> packages/contracts|clients|observability`；共享包不得依赖具体服务。服务间通过 API 或事件通信，不跨目录导入。`infra/` 消费服务制品与部署接口，服务源码不依赖具体部署清单。

## 增量规则

- 只有能独立部署且有明确所有权/数据边界的单元才成为新服务。
- 新服务必须同时建立源码、测试、配置、构建入口、健康检查、契约和运行说明。
- 可复用代码只有在消费者明确且不会耦合服务内部模型时才进入 `packages/`。
- 若部署始终是一个单元，应选单体后端或 Monorepo，而不是为了目录美观拆微服务。
