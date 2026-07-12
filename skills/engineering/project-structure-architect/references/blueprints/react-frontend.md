# React 单前端蓝图

```json
{
  "id": "react-frontend",
  "classification": {
    "purpose": "single React frontend application",
    "deployment": "single deployable",
    "repository": "single project",
    "workflow": "browser request-response application",
    "stacks": ["React", "TypeScript", "Vite, Next.js, or equivalent"]
  },
  "directories": [
    {"path": "public", "purpose": "Store assets served unchanged at stable public paths.", "required": true},
    {"path": "src/app", "purpose": "Compose application startup, routes, providers, and layouts.", "required": true, "local_rules": ["Keep feature implementation out of app; app only composes the product."]},
    {"path": "src/app/routes", "purpose": "Define top-level route composition.", "required": true},
    {"path": "src/app/providers", "purpose": "Compose application-wide providers.", "required": true},
    {"path": "src/app/layouts", "purpose": "Define top-level visual layouts.", "required": true},
    {"path": "src/features", "purpose": "Own business features including their private components, API, state, and types.", "required": true, "local_rules": ["Create one directory per business capability, not per file type.", "Keep feature-private code inside its owner feature."]},
    {"path": "src/components/ui", "purpose": "Store reusable business-agnostic UI primitives.", "required": true},
    {"path": "src/components/common", "purpose": "Store composed components shared by multiple features.", "required": false, "conditional": "shared_common_components"},
    {"path": "src/services", "purpose": "Store shared HTTP clients and cross-feature service adapters.", "required": true},
    {"path": "src/hooks", "purpose": "Store hooks used across multiple features.", "required": true},
    {"path": "src/stores", "purpose": "Store truly application-wide state.", "required": true},
    {"path": "src/lib", "purpose": "Wrap third-party libraries and framework integrations.", "required": true},
    {"path": "src/assets", "purpose": "Store assets transformed by the build.", "required": true},
    {"path": "src/styles", "purpose": "Store global styles, tokens, and themes.", "required": true},
    {"path": "tests", "purpose": "Store cross-feature integration and end-to-end support tests.", "required": true},
    {"path": "docs", "purpose": "Document frontend architecture, accessibility, and testing conventions.", "required": true}
  ]
}
```

## 依赖方向

`app -> features -> components/ui, services, lib`。共享组件、services 和 lib 不得反向依赖具体功能；功能间优先通过公开入口或应用层编排，不跨目录深层导入。

## 文件路由示例

- 登录表单：`src/features/authentication/components/LoginForm.tsx`。
- 仅认证使用的用户请求：`src/features/authentication/api/users.ts`。
- 多功能共享 HTTP 客户端：`src/services/http-client.ts`。
- 无业务语义的按钮：`src/components/ui/Button.tsx`。
