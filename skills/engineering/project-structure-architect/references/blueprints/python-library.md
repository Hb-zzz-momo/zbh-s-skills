# Python 库蓝图

```json
{
  "id": "python-library",
  "classification": {
    "purpose": "reusable and publishable Python library",
    "deployment": "package distribution",
    "repository": "single project",
    "workflow": "library build, test, and release",
    "stacks": ["Python", "pyproject.toml", "src layout"]
  },
  "directories": [
    {"path": "src/{package_name}", "purpose": "Contain the importable public library and its private modules.", "required": true, "local_rules": ["Expose supported APIs deliberately and keep imports independent of repository root.", "Do not put test-only or example-only code in the package."]},
    {"path": "tests/unit", "purpose": "Test public behavior and internal pure logic in isolation.", "required": true},
    {"path": "tests/integration", "purpose": "Test external services, file formats, and installed-package behavior.", "required": true},
    {"path": "docs/reference", "purpose": "Document the supported public API.", "required": true},
    {"path": "docs/guides", "purpose": "Store task-oriented user guides.", "required": true},
    {"path": "docs/development", "purpose": "Document contribution, testing, and release workflows.", "required": true},
    {"path": "examples", "purpose": "Store runnable examples that use the public package interface.", "required": false, "conditional": "with_examples"},
    {"path": "scripts", "purpose": "Store release and maintenance entry points that are not library APIs.", "required": false, "conditional": "with_maintenance_scripts"}
  ]
}
```

## 依赖方向

`tests/docs/examples -> installed src/{package_name}`。包源码不得导入 tests、docs 或 examples。构建与发布配置保留根级 `pyproject.toml`，不把根目录加入导入路径来掩盖缺失安装。

## 增量规则

- 新公共能力先确定公开模块和兼容性，再添加测试与 API 文档。
- 私有模块命名遵循项目约定；不要为一个函数创建无作用域 `utils/`。
- 示例必须通过公开 API 运行，并纳入至少一个自动验证路径。
