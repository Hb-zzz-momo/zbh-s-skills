"""Read OOXML structure/media first; page renders are independent cross-checks."""
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

from .documents import dump_json, sha256_file
from .engine import require

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
V='urn:schemas-microsoft-com:vml'


def normalized(text):
    """Ignore layout/control separators, preserving substantive text and numbers."""
    return re.sub(r'[\s\x00-\x1f]+','',text)


def _own_nodes(node):
    """Nested textbox paragraphs are separate blocks, never double-count their text."""
    yield node
    for child in node:
        if child.tag!=f'{{{W}}}p':
            yield from _own_nodes(child)


def read_structure(docx,output_dir,paragraph_map=()):
    """Extract only local related media with bounded ZIP/XML reads, no external fetch.

    Original media bytes remain unchanged. Legacy DOC images are those in Word's
    OOXML copy, explicitly identified rather than claimed binary-DOC byte-exact.
    """
    from PIL import Image
    docx,output=Path(docx),Path(output_dir)
    output.mkdir(parents=True,exist_ok=True)
    if isinstance(paragraph_map,(str,Path)):
        paragraph_map=json.loads(Path(paragraph_map).read_text('utf-8-sig'))
    by_text=defaultdict(deque)
    for position,entry in enumerate(paragraph_map):
        by_text[normalized(entry['text'])].append({**entry,'map_position':position})
    map_cursor=0
    blocks,images,issues=[],[],[]
    with zipfile.ZipFile(docx) as archive:
        require(sum(i.file_size for i in archive.infolist())<=128*1024*1024,'OOXML expanded size exceeds limit')
        def xml(name):
            raw=archive.read(name)
            require(len(raw)<=20*1024*1024 and b'<!DOCTYPE' not in raw.upper(),'unsafe/oversized XML')
            return ET.fromstring(raw)
        root=xml('word/document.xml')
        rels={e.attrib['Id']:e.attrib for e in xml('word/_rels/document.xml.rels')}
        parent={child:p for p in root.iter() for child in p}
        paragraphs=list(root.iter(f'{{{W}}}p'))
        require(len(paragraphs)<=10000,'too many Word paragraphs')
        for index,p in enumerate(paragraphs):
            nodes=list(_own_nodes(p))
            text=''.join(n.text or '' for n in nodes if n.tag==f'{{{W}}}t')
            candidates=by_text[normalized(text)]
            while candidates and candidates[0]['map_position']<map_cursor:candidates.popleft()
            mapping=candidates.popleft() if candidates else None
            if mapping:map_cursor=mapping['map_position']+1
            ancestors=[];cur=p
            while cur in parent:cur=parent[cur];ancestors.append(cur.tag.rsplit('}',1)[-1])
            location='textbox' if 'txbxContent' in ancestors else 'table_cell' if 'tc' in ancestors else 'paragraph'
            bid=f'w{index+1:04}'
            runs=[]
            for run in (n for n in nodes if n.tag==f'{{{W}}}r'):
                own=list(_own_nodes(run));value=''.join(n.text or '' for n in own if n.tag==f'{{{W}}}t')
                color=next((n.attrib.get(f'{{{W}}}val') for n in own if n.tag==f'{{{W}}}color'),None)
                if value:runs.append({'text':value,'color':color})
            block={'id':bid,'index':index,'container':location,'text':text,'runs':runs,
                   'page_start':mapping['page_start'] if mapping else None,'page_end':mapping['page_end'] if mapping else None,'image_ids':[]}
            for node in nodes:
                rid=(node.attrib.get(f'{{{R}}}embed') or node.attrib.get(f'{{{R}}}link')) if node.tag==f'{{{A}}}blip' else node.attrib.get(f'{{{R}}}id') if node.tag==f'{{{V}}}imagedata' else None
                if not rid:continue
                rel=rels.get(rid)
                if not rel or rel.get('TargetMode')=='External':
                    issues.append({'block_id':bid,'reason':'external_or_missing_image_relationship'});continue
                part=posixpath.normpath(posixpath.join('word',rel['Target']))
                require(part.startswith('word/') and not PurePosixPath(part).is_absolute(),'image relationship outside Word package')
                raw=archive.read(part);require(len(raw)<=32*1024*1024,'original image too large')
                digest=hashlib.sha256(raw).hexdigest()
                suffix=Path(part).suffix.lower()
                # Full SHA-256 stays in the evidence manifest. A shorter basename
                # keeps nested teaching/group/job paths within Windows limits.
                target=output/(digest[:24]+suffix)
                if not target.exists():target.write_bytes(raw)
                require(sha256_file(target)==digest,'original image filename collision or tampering')
                iid=f'{bid}-img{len(block["image_ids"])+1}'
                display=target;readable=True
                try:
                    with Image.open(target) as im:
                        width,height=im.size
                        require(0<width*height<=50_000_000,'abnormal original image dimensions')
                        im.load()
                        if suffix not in ('.png','.jpg','.jpeg','.gif','.webp'):
                            display=output/(digest[:24]+'.display.png');im.convert('RGB').save(display)
                except Exception:
                    width=height=None;readable=False
                    issues.append({'block_id':bid,'reason':'image_requires_page_render','part':part})
                ancestors_image=[];cursor=node
                while cursor in parent and cursor is not p:
                    cursor=parent[cursor];ancestors_image.append(cursor.tag.rsplit('}',1)[-1])
                floating='anchor' in ancestors_image or 'shape' in ancestors_image
                # Hidden cropped pixels are not part of the visible submission.
                # Retain original bytes locally; unsupported display transforms
                # must use page review, never silently send/grade hidden content.
                transformed=False
                scope=node
                while scope in parent and scope is not p and scope.tag.rsplit('}',1)[-1] not in ('pic','shape'):
                    scope=parent[scope]
                for setting in scope.iter():
                    name=setting.tag.rsplit('}',1)[-1]
                    if name=='srcRect' and any(v not in ('0','0.0') for v in setting.attrib.values()):transformed=True
                    if name=='xfrm' and any(setting.attrib.get(k,'0') not in ('0','false','0.0') for k in ('rot','flipH','flipV')):transformed=True
                    if name=='imagedata' and any(setting.attrib.get(k,'0') not in ('0','0f','0.0') for k in ('cropleft','cropright','croptop','cropbottom')):transformed=True
                if transformed:
                    readable=False
                    issues.append({'block_id':bid,'reason':'image_display_transform_requires_page_review','part':part})
                image={'id':iid,'block_id':bid,'relationship_id':rid,'package_part':part,'source_sha256':digest,
                       'original_file':str(target),'file':str(display),'sha256':sha256_file(display),
                       'readable':readable,'width':width,'height':height,'floating':floating,'display_transform_requires_review':transformed,
                       'page_start':block['page_start'],'page_end':block['page_end']}
                images.append(image);block['image_ids'].append(iid)
            blocks.append(block)
        other_parts=[n for n in archive.namelist() if re.fullmatch(r'word/(header\d+|footer\d+|footnotes|endnotes)\.xml',n)]
        for part in other_parts:
            if xml(part).find(f'.//{{{A}}}blip') is not None or xml(part).find(f'.//{{{V}}}imagedata') is not None:
                issues.append({'reason':'image_in_other_story_requires_review','part':part})
    unmapped=[b['id'] for b in blocks if (b['text'].strip() or b['image_ids']) and b['page_start'] is None]
    result={'version':'word-structure-1.0','docx_sha256':sha256_file(docx),'blocks':blocks,'images':images,
            'issues':issues,'unmapped_blocks':unmapped,'paragraph_count':len(blocks),'image_occurrences':len(images)}
    dump_json(output.parent/'word-structure.json',result)
    return result
