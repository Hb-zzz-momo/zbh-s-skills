from __future__ import annotations

from pathlib import Path
from urllib.parse import quote


OUT = Path(__file__).resolve().parent
SVG = OUT / "openrank_architecture_reproduction.svg"
DRAWIO = OUT / "openrank_architecture_reproduction.fixed-background.drawio"
DRAWIO_XML = OUT / "openrank_architecture_reproduction.fixed-background.drawio.xml"
W, H = 1690, 939


def main() -> None:
    svg_text = SVG.read_text(encoding="utf-8")
    data_uri = "data:image/svg+xml," + quote(svg_text, safe="")
    model = f'''<mxGraphModel dx="{W}" dy="{H}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{W}" pageHeight="{H}" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="figure" value="" style="shape=image;html=1;imageAspect=0;aspect=fixed;verticalLabelPosition=bottom;verticalAlign=top;image={data_uri};" vertex="1" parent="1">
      <mxGeometry x="0" y="0" width="{W}" height="{H}" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>'''
    mxfile = f'''<mxfile host="app.diagrams.net" modified="2026-06-26T00:00:00.000Z" agent="Codex" version="24.7.0">
  <diagram id="openrank-fixed-background" name="OpenRank fixed background">{model}</diagram>
</mxfile>
'''
    DRAWIO_XML.write_text(model, encoding="utf-8")
    DRAWIO.write_text(mxfile, encoding="utf-8")
    print(DRAWIO)


if __name__ == "__main__":
    main()
