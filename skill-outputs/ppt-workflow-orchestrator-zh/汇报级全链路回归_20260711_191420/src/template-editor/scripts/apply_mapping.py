"""Conservative OOXML text/image mapping editor that never mutates its source."""
from __future__ import annotations
import argparse, hashlib, json, tempfile, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS={"a":"http://schemas.openxmlformats.org/drawingml/2006/main","p":"http://schemas.openxmlformats.org/presentationml/2006/main","r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
for k,v in NS.items(): ET.register_namespace(k,v)
REL_NS="http://schemas.openxmlformats.org/package/2006/relationships"; ET.register_namespace("",REL_NS)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def safe_extract(archive: zipfile.ZipFile, target: Path):
    total=0; root=target.resolve()
    for info in archive.infolist():
        parts=Path(info.filename.replace("\\","/")).parts
        if Path(info.filename).is_absolute() or ".." in parts: raise SystemExit(f"unsafe ZIP member: {info.filename}")
        total+=info.file_size
        if info.file_size>100*1024*1024 or total>500*1024*1024: raise SystemExit("PPTX archive exceeds safe extraction limits")
        dest=(root/info.filename).resolve()
        if not dest.is_relative_to(root): raise SystemExit(f"unsafe ZIP destination: {info.filename}")
    archive.extractall(root)
def replace_text(root,expected,replacement):
    hits=0
    for node in root.findall(".//a:t",NS):
        if node.text==expected: node.text=replacement; hits+=1
    return hits
def replace_image(td: Path, slide: int, root, shape_name: str, replacement: Path):
    parent={c:p for p in root.iter() for c in p}
    embed=None
    for node in root.findall(".//p:cNvPr",NS):
        if node.get("name")==shape_name:
            cur=node
            while cur is not None and cur.tag!=f"{{{NS['p']}}}pic": cur=parent.get(cur)
            if cur is not None:
                blip=cur.find(".//a:blip",NS); embed=blip.get(f"{{{NS['r']}}}embed") if blip is not None else None
            break
    if not embed: raise SystemExit(f"picture shape not found: {shape_name}")
    rel_file=td/f"ppt/slides/_rels/slide{slide}.xml.rels"; rel=ET.parse(rel_file); target=None
    for item in rel.getroot():
        if item.get("Id")==embed: target=item.get("Target"); break
    if not target: raise SystemExit(f"image relationship not found: {embed}")
    media=(rel_file.parent.parent/target).resolve()
    if not media.is_relative_to(td.resolve()): raise SystemExit("image relationship escapes unpacked package")
    if media.suffix.lower()!=replacement.suffix.lower(): raise SystemExit("replacement image extension must match existing media extension")
    media.write_bytes(replacement.read_bytes()); return str(media.relative_to(td))
def main():
    p=argparse.ArgumentParser(); p.add_argument("source",type=Path); p.add_argument("--mapping",type=Path,required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--report",type=Path,required=True); a=p.parse_args()
    source=a.source.resolve(); output=a.output.resolve()
    if source==output: raise SystemExit("source and output must differ")
    before=sha(source); mapping=json.loads(a.mapping.read_text(encoding="utf-8")); applied=[]
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        with zipfile.ZipFile(source) as z: safe_extract(z,td)
        for op in mapping.get("operations",[]):
            slide=int(op["slide"]); xml=td/f"ppt/slides/slide{slide}.xml"
            if not xml.is_file(): raise SystemExit(f"slide not found: {slide}")
            root=ET.parse(xml)
            if op["type"]=="replace_text":
                hits=replace_text(root.getroot(),str(op["expected"]),str(op["replacement"]))
                expected_hits=int(op.get("expected_hits",1))
                if hits!=expected_hits: raise SystemExit(f"replace_text expected {expected_hits} hits but got {hits}: {op['expected']}")
                root.write(xml,encoding="utf-8",xml_declaration=True); applied.append({"type":"replace_text","slide":slide,"hits":hits})
            elif op["type"]=="replace_image":
                media=replace_image(td,slide,root.getroot(),str(op["shape_name"]),Path(op["replacement"]).resolve()); applied.append({"type":"replace_image","slide":slide,"media":media})
            else: raise SystemExit(f"unsupported operation: {op['type']}")
        output.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED) as z:
            for f in sorted(td.rglob("*")):
                if f.is_file(): z.write(f,f.relative_to(td).as_posix())
    if sha(source)!=before: raise SystemExit("source changed unexpectedly")
    result={"status":"PASS","source":str(source),"output":str(output),"source_sha256":before,"output_sha256":sha(output),"operations":applied}
    a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(result,ensure_ascii=False)); return 0
if __name__=="__main__": raise SystemExit(main())
