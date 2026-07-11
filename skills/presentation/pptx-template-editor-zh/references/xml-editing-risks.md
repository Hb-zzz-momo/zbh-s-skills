# PPTX XML 编辑风险

PPTX 是 OOXML ZIP 包。直接编辑可能破坏：

- `[Content_Types].xml` 部件类型。
- `.rels` 关系 ID 和相对路径。
- slide → layout → master → theme 链路。
- charts、embeddings、notes、comments、animations 与 customXml。

安全边界：

1. 解包时阻止路径穿越。
2. 修改前保留原 ZIP 和哈希。
3. 不批量重写 XML 格式。
4. 删除部件前同时审计所有关系文件。
5. 打包后验证必要部件，再用 Office 打开和渲染。

