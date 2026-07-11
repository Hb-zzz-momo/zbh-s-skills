# local-python-figure-mcp

本地科研数据图 MCP。它只从用户给定的 CSV/TSV/XLSX 表格生成图，不执行任意 Python 脚本，不推断 P 值、样本量、显著性或统计结论。

## Tools

- `inspect_table`: 查看表格列名、类型、缺失值和少量预览。
- `plot_table`: 从表格生成 `png/svg/pdf`，并保存 `plot_spec.json` 和 `caption.md`。

## Codex 配置

```toml
[mcp_servers.local_python_figure]
command = "uv"
args = ["run", "--directory", "C:\\Users\\zbh\\.agents\\mcp-servers\\local-python-figure-mcp", "python", "server.py"]
startup_timeout_sec = 60
tool_timeout_sec = 180
default_tools_approval_mode = "prompt"

[mcp_servers.local_python_figure.env]
FIGURE_ALLOWED_ROOTS = "C:\\Users\\zbh;D:\\;E:\\"
```

首次使用前在本目录运行：

```powershell
uv sync
```

## 示例提示词

```text
用 local_python_figure 的 inspect_table 检查 D:\project\paper\data\result.csv。
然后用 plot_table 生成 x=method, y=accuracy 的 bar 图，输出 SVG/PDF/PNG。
不要添加显著性星号，不要推断 P 值。
```
