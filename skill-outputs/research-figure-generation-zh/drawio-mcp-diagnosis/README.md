# draw.io MCP 诊断记录

## 结论

`drawio` 不是安装失败。本机配置、npm 包和 MCP 协议探测均可用；当前聊天里“不可直接调用”的主要原因是现有 Codex 会话没有热加载新增 MCP 工具。

## 已验证

```powershell
codex mcp get drawio
npx -y @drawio/mcp --help
uv run --directory C:\Users\zbh\.agents\mcp-servers\local-python-figure-mcp python C:\Users\zbh\.agents\skill-outputs\research-figure-generation-zh\drawio-mcp-diagnosis\probe_drawio_mcp.py
```

探测到的本地工具：

- `open_drawio_xml`
- `open_drawio_csv`
- `open_drawio_mermaid`

工具清单已保存到：

```text
C:\Users\zbh\.agents\skill-outputs\research-figure-generation-zh\drawio-mcp-diagnosis\drawio_mcp_tools.json
```

## 为什么看起来不可用

1. `drawio` 是后来写入 `C:\Users\zbh\.codex\config.toml` 的，当前 Codex 会话通常不会自动热加载新 MCP。
2. 这轮会话的直接工具列表中没有暴露 `mcp__drawio__...` 工具名，所以我不能像调用 Inkscape MCP 那样直接调用它。
3. 官方 `@drawio/mcp` 是打开 draw.io 编辑器的工具服务器，不是无头 PNG/SVG/PDF 导出器。
4. 本地 `@drawio/mcp` 不暴露 `search_shapes`；该能力属于 draw.io MCP App Server 场景。

## 让它可用的步骤

1. 重启 Codex/IDE 会话。
2. 在新会话里执行：

```powershell
codex mcp list
codex mcp get drawio
```

3. 在 Codex TUI 中输入 `/mcp`，确认 `drawio` 已加载。
4. 新会话中可请求：

```text
调用 drawio 的 open_drawio_mermaid 打开这段 Mermaid。
调用 drawio 的 open_drawio_xml 打开这个 mxGraph XML，并使用 routing=libavoid。
```

## 对科研图复现的实际建议

对于 OpenRank 这类系统架构图，正确链路应是：

```text
参考图 -> 生成 draw.io XML / Mermaid 草图 -> draw.io 中使用真实图标库精修 -> 导出 .drawio/SVG/PDF -> Inkscape 最终清理
```

不要把 `@drawio/mcp` 当作从截图自动生成高保真矢量图的工具。它能解决“可编辑结构图入口”，不能自动补齐所有真实小图标和版式细节。
