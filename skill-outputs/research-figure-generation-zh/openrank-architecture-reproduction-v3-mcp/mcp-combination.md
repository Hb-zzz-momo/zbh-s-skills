# MCP Combination

## Selected Route

Best route for this architecture reproduction:

```text
draw.io MCP + Lucide vector icons + Inkscape MCP
```

## Why This Combination

- `drawio`: keeps an editable structure source through `open_drawio_xml` and `.drawio` / `.drawio.xml` files.
- Lucide SVG icons: provides real vector icons instead of letter placeholders.
- `inkscape`: validates, cleans, and exports the final SVG to PNG/PDF.

## Excluded From Main Route

- `wps-office`: useful for inserting this figure into Word/PPT or exporting WPS pages, but not optimal for precise vector architecture drawing.
- `local_python_figure`: intended for real data charts; this figure is a system architecture diagram, not a data plot.
- `biorender`: intended for biomedical mechanism/pathway icons; not relevant to this software architecture.

## Practical Boundary

The final high-fidelity figure is produced as SVG and exported through Inkscape MCP. The `.drawio` source is provided for editable structure work, but draw.io MCP itself is not a headless high-fidelity renderer/exporter.
