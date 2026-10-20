# 收尾清理验证（2026-10-21）

本批次为用户明确要求的实验结束磁盘/内存收尾优化，不删除现有课程材料。保留原只读扫描与legacy迁移；新增精确清单清理器，接入课程、独立报告复核、科研实验和监控终态。提交ZIP只含用户要求的文件，内部复现材料另留单一来源。

## 实际验证

- 创建者先写行为测试再实现；最终21项unittest通过，Windows真实symlink及junction用例均执行，0跳过。主执行者已运行前版19项及四个Skill的quick_validate；最终21项由实现者及真实独立B分别运行，B最终8.963秒、native exit 0。
- 覆盖真实CLI dry-run/apply、混合无效项整体零删除、越界/受保护目录、过期指纹、keeper在删除集合/循环/内容不同、工作进程未停/验收未通过、日志独占、运行中变更partial及重跑不误删。
- 独立B `/root/cleanup_policy_review` 逐段审查策略/代码，另实测运行中计划变化与验收JSON重复字段均拒绝；最终PASS，无阻断。8.3短路径别名本机不能生成；代码拒绝非规范路径，模拟系统canonical解析不一致用例验证零删除，未宣称8.3原生实测。
- 独立C `/root/cleanup_forward_test` 用新TemporaryDirectory按实际用户情境构造计划并运行CLI；最终正确删除6个验证副本/临时文件、442逻辑字节，日志与独立统计一致。当前IPYNB/HTML及仅两成员ZIP、数据/模型/源码、关键失败证据和来源均保持hash，未知模型及其他任务不动；临时fixture已销毁。测试输入是假想材料，不冒充课程实测或真实磁盘回收量。
- C发现未知`.cache`被拒但文档不列后缀、错误不定位的问题；已补9后缀枚举和路径帮助，新CLI用例通过。B建议已合并：必要旧版本可用可复原差异保存，SHA只去重同字节副本；protected依赖闭包由领域执行者建立。
- 已补WPS/OneDrive本地删除可能被同步的边界；不调用云服务清理API，不把unlink说成只释放本机缓存。进程结束与磁盘逻辑字节分别报告。

## 最终冻结与复跑入口

- `scripts/closeout_artifacts.py` SHA256（本机Windows工作树字节）：`5dd61b2c6ee7bc177735bd19c78640797ed29161c1f08aa4dcccaacc06e2cf7a`
- `tests/test_closeout_artifacts.py` SHA256：`f63964bceba4a234a584756fb190b2bdd021726fa4443e06820a191deb17c2c8`
- `references/experiment-closeout.md` SHA256：`4b1a25140d43847e2e76cc3b8fb1c5b78b930541cf167cae369ed92284f59d2d`

```text
python -B -m unittest discover -s <skill>/tests -p test_closeout_artifacts.py -v
python <skill-creator>/scripts/quick_validate.py <skill>
```

默认干跑不写文件。apply只在已有授权和已停用消费者范围内使用；检查不提供对恶意并发写入的原子删除保证。当前课程目录没有在本批次执行清理；不声称已释放用户磁盘空间或RAM。

## 来源

实际读取[DVC gc](https://doc.dvc.org/command-reference/gc)、[Snakemake temp/protected](https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#protected-and-temporary-files)、[MLflow gc](https://mlflow.org/docs/latest/api_reference/cli.html#mlflow-gc)。采用引用保留集合、消费者完成后释放临时输出、不能凭生命周期猜可删；未安装新框架或替换本项目实验。
