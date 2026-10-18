# 机器学习 Pipeline 蓝图

```json
{
  "id": "machine-learning-pipeline",
  "classification": {
    "purpose": "modular machine-learning training and evaluation pipeline",
    "deployment": "pipeline with generated model artifacts",
    "repository": "single machine-learning project",
    "workflow": "dependency-driven pipeline and experiments",
    "stacks": ["Python", "ML framework", "Kedro, Snakemake, or equivalent orchestration"]
  },
  "directories": [
    {"path": "configs/base", "purpose": "Store shared pipeline, dataset, and model defaults.", "required": true},
    {"path": "configs/local", "purpose": "Store ignored machine-local overrides without secrets in version control.", "required": true},
    {"path": "data/raw", "purpose": "Store immutable source training data or controlled references.", "required": true},
    {"path": "data/interim", "purpose": "Store reproducible intermediate datasets.", "required": true},
    {"path": "data/processed", "purpose": "Store validated model-ready datasets.", "required": true},
    {"path": "src/{package_name}/pipelines", "purpose": "Own registered pipeline boundaries and composition.", "required": true, "local_rules": ["Each pipeline owns node definitions and execution wiring.", "Keep parameters in configs and reusable primitives in domain modules."]},
    {"path": "src/{package_name}/pipelines/data_processing", "purpose": "Define data-processing nodes and their execution relationships.", "required": true},
    {"path": "src/{package_name}/pipelines/feature_engineering", "purpose": "Define feature-generation nodes and contracts.", "required": true},
    {"path": "src/{package_name}/pipelines/training", "purpose": "Define model-training nodes and artifact outputs.", "required": true},
    {"path": "src/{package_name}/pipelines/evaluation", "purpose": "Define metric, validation, and comparison nodes.", "required": true},
    {"path": "src/{package_name}/data", "purpose": "Implement reusable dataset schemas, loaders, and validation.", "required": true},
    {"path": "src/{package_name}/models", "purpose": "Implement reusable model definitions and inference interfaces.", "required": true},
    {"path": "src/{package_name}/metrics", "purpose": "Implement tested evaluation metrics.", "required": true},
    {"path": "experiments", "purpose": "Store immutable run configurations, notes, and metric summaries.", "required": true, "local_rules": ["Use stable experiment IDs and record code, data, config, seed, and environment lineage."]},
    {"path": "checkpoints", "purpose": "Store ignored local checkpoints or pointers to managed artifact storage.", "required": true},
    {"path": "outputs/metrics", "purpose": "Store machine-readable generated metrics.", "required": true},
    {"path": "outputs/figures", "purpose": "Store reproducibly generated evaluation figures.", "required": true},
    {"path": "outputs/predictions", "purpose": "Store generated validation or inference predictions.", "required": true},
    {"path": "notebooks", "purpose": "Store exploration and diagnostics that consume pipeline artifacts.", "required": true},
    {"path": "tests/unit", "purpose": "Test nodes, metrics, data contracts, and models in isolation.", "required": true},
    {"path": "tests/pipeline", "purpose": "Test pipeline wiring and small-fixture end-to-end execution.", "required": true},
    {"path": "scripts", "purpose": "Store launch, validation, and artifact-management entry points.", "required": true},
    {"path": "docs/reproducibility", "purpose": "Document environments, commands, seeds, and artifact lineage.", "required": true},
    {"path": "docs/model-cards", "purpose": "Document intended use, limits, data, and evaluation for released models.", "required": false, "conditional": "publish_models"}
  ]
}
```

## 依赖方向

配置和数据契约输入 Pipeline，Pipeline 编排可复用节点，节点调用 data/models/metrics，最终写入 checkpoints/outputs。Notebook 只能消费或调试这些边界，不得成为正式训练链的唯一入口。

## 增量规则

- Pipeline 子目录应把计算节点与执行关系分开表达；框架无固定文件名时仍保留此职责分离。
- 每次实验记录代码提交、数据版本、配置、随机种子、环境和制品位置。
- `checkpoints/` 默认本地忽略或外置，不把体积巨大等同于结构不规范。
- 若项目以人工可读的固定研究阶段为主，优先 `research-step-based`。
