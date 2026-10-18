# 数据科学蓝图

```json
{
  "id": "data-science",
  "classification": {
    "purpose": "exploratory and reproducible data analysis",
    "deployment": "analysis workflow",
    "repository": "single data project",
    "workflow": "data lifecycle and reporting",
    "stacks": ["Python or R", "notebooks", "statistical analysis"]
  },
  "directories": [
    {"path": "configs", "purpose": "Store analysis parameters and data source configuration.", "required": true},
    {"path": "data", "purpose": "Own data by lifecycle stage and provenance.", "required": true, "local_rules": ["Treat raw data as immutable.", "Every interim and processed artifact must have a reproducible producer."]},
    {"path": "data/external", "purpose": "Store or reference third-party data and its provenance.", "required": true},
    {"path": "data/raw", "purpose": "Store immutable source data.", "required": true},
    {"path": "data/interim", "purpose": "Store reproducible intermediate transformations.", "required": true},
    {"path": "data/processed", "purpose": "Store validated analysis and modeling inputs.", "required": true},
    {"path": "notebooks", "purpose": "Store numbered exploration, prototyping, and communication notebooks.", "required": true, "local_rules": ["Number notebooks by analysis order.", "Promote reusable logic to src/{package_name} and keep notebooks thin."]},
    {"path": "notebooks/01_exploration", "purpose": "Store initial profiling and question-forming work.", "required": true},
    {"path": "notebooks/02_analysis", "purpose": "Store traceable statistical or model analysis.", "required": true},
    {"path": "notebooks/03_communication", "purpose": "Store presentation-focused notebooks derived from saved results.", "required": true},
    {"path": "src/{package_name}/data", "purpose": "Implement reusable loading, validation, and transformation.", "required": true},
    {"path": "src/{package_name}/features", "purpose": "Implement reusable feature and variable construction.", "required": true},
    {"path": "src/{package_name}/analysis", "purpose": "Implement reusable statistical and modeling procedures.", "required": true},
    {"path": "src/{package_name}/visualization", "purpose": "Implement reproducible chart and table generation.", "required": true},
    {"path": "models", "purpose": "Store generated models or artifact-store pointers.", "required": true},
    {"path": "reports/figures", "purpose": "Store generated reporting figures.", "required": true},
    {"path": "reports/tables", "purpose": "Store generated reporting tables.", "required": true},
    {"path": "reports/briefs", "purpose": "Store report source and concise findings tied to data versions.", "required": true},
    {"path": "tests", "purpose": "Test data contracts, transformations, metrics, and report producers.", "required": true},
    {"path": "scripts", "purpose": "Store reproducible batch entry points that call src code.", "required": true},
    {"path": "docs", "purpose": "Document data provenance, definitions, methodology, and reproducibility.", "required": true}
  ]
}
```

## 数据方向

`external/raw -> interim -> processed -> models/reports`。转换代码位于 `src/{package_name}`；Notebook 消费数据和可复用函数，但不成为唯一生产者。生成结果不得回写 `raw`。

## 增量规则

- 新数据源先登记来源、许可证、获取日期和完整性校验。
- 新 Notebook 按所在阶段编号；稳定的清洗、指标或绘图逻辑同步进入 `src/` 并测试。
- 若工作重点变成可组合训练节点与模型制品，迁移决策应评估 `machine-learning-pipeline`，但不自动改树。
