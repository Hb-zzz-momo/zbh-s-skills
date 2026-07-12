# 有序科研步骤蓝图

```json
{
  "id": "research-step-based",
  "classification": {
    "purpose": "reproducible scientific research with ordered stages",
    "deployment": "research workflow",
    "repository": "single research project",
    "workflow": "ordered research steps and experiments",
    "stacks": ["Python", "scientific computing", "paper and artifact generation"]
  },
  "directories": [
    {"path": "configs", "purpose": "Store shared dataset, model, and workflow configuration.", "required": true},
    {"path": "configs/experiments", "purpose": "Store reusable experiment configurations referenced by runs.", "required": true},
    {"path": "data", "purpose": "Own the complete data lifecycle with provenance documentation.", "required": true, "local_rules": ["Never overwrite raw data.", "Generated data must move from interim to processed through reproducible code."]},
    {"path": "data/external", "purpose": "Store or reference third-party data with source and license metadata.", "required": true},
    {"path": "data/raw", "purpose": "Store immutable source observations.", "required": true},
    {"path": "data/interim", "purpose": "Store reproducible intermediate data products.", "required": true},
    {"path": "data/processed", "purpose": "Store validated inputs for modeling and final analysis.", "required": true},
    {"path": "steps", "purpose": "Express ordered workflow entry points and step-local contracts.", "required": true, "local_rules": ["Use NN_step_name directories with run.py, config.yaml, and README.md.", "Keep reusable algorithms in src/{package_name}, not in steps."]},
    {"path": "src/{package_name}/data", "purpose": "Implement reusable data access and validation logic.", "required": true},
    {"path": "src/{package_name}/preprocessing", "purpose": "Implement reusable cleaning and preprocessing logic.", "required": true},
    {"path": "src/{package_name}/features", "purpose": "Implement reusable feature engineering.", "required": true},
    {"path": "src/{package_name}/models", "purpose": "Implement model definitions, training, and inference.", "required": true},
    {"path": "src/{package_name}/evaluation", "purpose": "Implement metrics, validation, and statistical comparison.", "required": true},
    {"path": "src/{package_name}/visualization", "purpose": "Implement reproducible figure and table generation.", "required": true},
    {"path": "src/{package_name}/utils", "purpose": "Store small package-scoped primitives with explicit ownership.", "required": false, "conditional": "package_utilities"},
    {"path": "experiments", "purpose": "Store run-specific configurations, notes, metrics, and registry records.", "required": true, "local_rules": ["Give every experiment a stable ID and preserve its configuration and metrics.", "Do not commit bulky checkpoints unless explicitly required."]},
    {"path": "notebooks/01_exploration", "purpose": "Store ordered exploratory analysis notebooks.", "required": true},
    {"path": "notebooks/02_prototyping", "purpose": "Store disposable prototypes before reusable logic is promoted to src.", "required": true},
    {"path": "notebooks/03_result_analysis", "purpose": "Store traceable analysis of saved results.", "required": true},
    {"path": "outputs/models", "purpose": "Store generated model artifacts or pointers to artifact storage.", "required": true},
    {"path": "outputs/figures", "purpose": "Store reproducibly generated figures.", "required": true},
    {"path": "outputs/tables", "purpose": "Store reproducibly generated result tables.", "required": true},
    {"path": "outputs/predictions", "purpose": "Store generated prediction artifacts.", "required": true},
    {"path": "outputs/logs", "purpose": "Store runtime logs that are safe to regenerate or archive.", "required": true},
    {"path": "paper/manuscript", "purpose": "Store manuscript source.", "required": true},
    {"path": "paper/references", "purpose": "Store bibliography and paper-local reference records.", "required": true},
    {"path": "paper/supplementary", "purpose": "Store supplementary material source.", "required": true},
    {"path": "paper/submission", "purpose": "Store explicitly prepared submission bundles, not working files.", "required": true},
    {"path": "tests/unit", "purpose": "Test reusable scientific functions and metrics.", "required": true},
    {"path": "tests/integration", "purpose": "Test data, model, and external-tool boundaries.", "required": true},
    {"path": "tests/pipeline", "purpose": "Test step contracts and end-to-end reproducibility on small fixtures.", "required": true},
    {"path": "scripts", "purpose": "Store repository maintenance and batch-launch entry points.", "required": true},
    {"path": "docs/methodology", "purpose": "Document method definitions and implementation correspondence.", "required": true},
    {"path": "docs/experiment-design", "purpose": "Document comparison, ablation, and statistical plans.", "required": true},
    {"path": "docs/reproducibility", "purpose": "Document environments, commands, seeds, and artifact lineage.", "required": true}
  ]
}
```

## `steps/` 与 `src/`

`steps/` 表达工作流顺序，负责参数、输入输出和调用；`src/` 表达代码职责，负责算法、模型、指标和绘图。`steps/05_model_training/run.py` 应调用 `src/{package_name}/models/`，不得包含数百行训练实现。

## 增量规则

- 新步骤取当前最大编号加一，不重排已有编号，并同时创建 `run.py`、`config.yaml`、`README.md`。
- `README.md` 写明输入、输出、依赖步骤、运行命令和完成判据。
- `data/raw` 只读；`outputs/` 不放源码；实验目录保存配置与指标以形成证据链。
- 已使用成熟 Pipeline 框架的仓库应选择 `machine-learning-pipeline`，不要再叠加 `steps/`。
