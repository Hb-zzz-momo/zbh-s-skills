"""Convert Word to PDF and retain visible page coverage for multimodal grading."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading

from .engine import require

VERSION = 'pdfium-pages-1.1'
SUPPORTED = {'.doc', '.docx', '.pdf'}
_WORD_CONVERSION_LOCK = threading.Lock()


def validate_document(path):
    """Reject mislabeled or damaged input before launching the Word converter."""
    import zipfile
    path = Path(path)
    require(path.is_file() and path.suffix.lower() in SUPPORTED, 'unsupported or missing report')
    require(0 < path.stat().st_size <= 64*1024*1024, 'document empty or exceeds 64 MiB')
    with path.open('rb') as stream:
        header = stream.read(1024)
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        require(b'%PDF-' in header, 'invalid PDF header')
    elif suffix == '.doc':
        require(header.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1') or header.lstrip().startswith(b'{\\rtf'), f'不是有效的Word报告（文件大小{path.stat().st_size}字节）。可能选中了临时文件、未下载完整或文件格式不正确；请重新下载完整报告，确认能用Word/WPS打开，再另存为.docx后上传。此文件未导入，也不会记零分。')
    else:
        require(zipfile.is_zipfile(path), 'invalid DOCX archive')
        with zipfile.ZipFile(path) as archive:
            require('word/document.xml' in archive.namelist(), 'DOCX document part missing')


def sha256_file(path):
    """Hash bytes instead of filenames so replacement versions cannot be confused."""
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def dump_json(path, value):
    """Atomic replacement prevents a stopped process leaving apparently valid JSON."""
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', 'utf-8')
    temp.replace(path)


def to_pdf(source, destination, *, timeout=180, structure_docx=None, paragraph_map=None):
    """Preserve visible OLE/floating content through Word, never save the original.

    PDF input is copied. A Word timeout is a failed extraction, never an empty
    student answer. The command receives literal arguments, not constructed code.
    """
    source, destination = Path(source).resolve(), Path(destination).resolve()
    validate_document(source)
    require(source.suffix.lower() in SUPPORTED, 'only .doc, .docx and .pdf are supported')
    require(0 < source.stat().st_size <= 64 * 1024 * 1024, 'document empty or exceeds 64 MiB')
    require(not destination.exists(), 'conversion output already exists')
    destination.parent.mkdir(parents=True, exist_ok=True)
    before = sha256_file(source)
    if source.suffix.lower() == '.pdf':
        shutil.copyfile(source, destination)
        info = {'converter': 'PDF passthrough'}
    else:
        require(os.name == 'nt', 'Word conversion requires Windows and Microsoft Word; provide PDF on other platforms')
        metadata = destination.with_suffix('.conversion.json')
        command=['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
                 '-File',str(Path(__file__).with_name('word_to_pdf.ps1'))]
        arguments=['-Source',str(source),'-Destination',str(destination),'-Metadata',str(metadata)]
        if structure_docx:arguments+=['-StructureDocx',str(structure_docx)]
        if paragraph_map:arguments+=['-ParagraphMap',str(paragraph_map)]
        def cleanup_owned():
            try:subprocess.run(command+['-Destination',str(destination),'-Cleanup'],capture_output=True,timeout=20)
            except (OSError,subprocess.TimeoutExpired):pass
        # Import inspection and the grading queue share Word automation.
        with _WORD_CONVERSION_LOCK:
            try:completed=subprocess.run(command+arguments,capture_output=True,timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                cleanup_owned()
                raise ValueError('Word conversion timed out; extraction failed, owned-process cleanup attempted') from exc
            if completed.returncode != 0 or not destination.exists() or not metadata.exists():
                dump_json(destination.with_suffix('.conversion-error.json'),{'returncode':completed.returncode,
                          'stderr':completed.stderr.decode('utf-8','replace')[-4000:]})
                cleanup_owned()
                raise ValueError('Word conversion failed; conversion diagnostics retained, source unchanged')
        info = json.loads(metadata.read_text('utf-8-sig'))
    require(sha256_file(source) == before, 'source changed during conversion')
    return info


def _matches(textpage, text):
    """Locate exact identity strings for image masking without changing body code."""
    searcher = textpage.search(text)
    try:
        while True:
            found = searcher.get_next()
            if found is None:
                break
            yield found
    finally:
        searcher.close()


def extract_document(source, output_dir, *, identity_tokens=(), max_pages=80):
    """Render every visible page and overlapping tiles, including image-only pages.

    Text-layer identity masking is best-effort; scanned names inside screenshots
    remain possible and are disclosed in the manifest. No OCR claim is made.
    """
    import pypdfium2 as pdfium
    from PIL import ImageDraw
    source, output = Path(source).resolve(), Path(output_dir).resolve()
    require(not output.exists(), 'extraction directory already exists; use a new version')
    output.mkdir(parents=True)
    conversion = to_pdf(source, output/'rendered.pdf',
                        structure_docx=output/'structure.docx' if source.suffix.lower()!='.pdf' else None,
                        paragraph_map=output/'paragraph-pages.json' if source.suffix.lower()!='.pdf' else None)
    document = pdfium.PdfDocument(output/'rendered.pdf')
    document.init_forms()
    require(0 < len(document) <= max_pages, 'page count empty or exceeds configured limit')
    require('pages' not in conversion or conversion['pages'] == len(document), 'Word/PDF page count mismatch')
    evidence, pages, raw_texts = [], [], []
    picture=None
    try:
        for index in range(len(document)):
            page = document[index]
            textpage = page.get_textpage()
            raw_text = textpage.get_text_bounded()
            raw_texts.append(raw_text)
            w, h = page.get_size()
            require(w > 0 and h > 0 and w * h <= 2_000_000, 'abnormal PDF page dimensions')
            scale = min(2.0, 2400/max(w, h))
            bitmap = page.render(scale=scale)
            picture = bitmap.to_pil().convert('RGB')
            bitmap.close()
            painter = ImageDraw.Draw(picture)
            tokens = set(str(x) for x in identity_tokens if str(x).strip())
            # Numeric constants such as 4294967295 are grading evidence, not IDs.
            tokens.update(re.findall(r'(?:学号|Student\s*ID)\s*[:：]?\s*(\d{9,13})(?!\d)', raw_text, re.I))
            cleaned = raw_text
            masked = 0
            for token in sorted(tokens, key=len, reverse=True):
                cleaned = cleaned.replace(token, '[身份已遮盖]')
                for start, count in _matches(textpage, token):
                    boxes = [textpage.get_charbox(i) for i in range(start, start+count)]
                    left=min(b[0] for b in boxes); bottom=min(b[1] for b in boxes)
                    right=max(b[2] for b in boxes); top=max(b[3] for b in boxes)
                    # PDF y runs upward; raster y runs downward. Rotated pages
                    # need explicit review instead of an unverified mask.
                    if page.get_rotation() == 0:
                        painter.rectangle((left*scale-2,(h-top)*scale-2,right*scale+2,(h-bottom)*scale+2),fill='white')
                        masked += 1
            pid = f'p{index+1:03}'
            page_path = output/f'{pid}.png'
            picture.save(page_path)
            if cleaned.strip():
                evidence.append(dict(id=pid+'-text', kind='text', origin='student', locator=f'第{index+1}页正文/表格文本层（含题面，须区分作答）',
                                     sha256=hashlib.sha256(cleaned.encode('utf-8')).hexdigest(), readable=True, text=cleaned))
            # Tiles keep small screenshot code readable after server-side resizing.
            tile_height = 1000
            starts = list(range(0, picture.height, tile_height-100))
            tile_ids = []
            for number, top in enumerate(starts, 1):
                if top and picture.height-top < 100:
                    break
                bottom = min(top+tile_height, picture.height)
                eid = f'{pid}-image{number}'
                path = output/(eid+'.jpg')
                with picture.crop((0,top,picture.width,bottom)) as tile:tile.save(path,quality=94)
                evidence.append(dict(id=eid, kind='image', origin='student', locator=f'第{index+1}页，像素区域0,{top},{picture.width},{bottom}，父页{pid}',
                                     sha256=sha256_file(path), readable=True, file=path.name,
                                     parent_sha256=sha256_file(page_path), bbox=[0,top,picture.width,bottom]))
                tile_ids.append(eid)
            pages.append(dict(page=index+1, page_file=page_path.name, sha256=sha256_file(page_path),
                              text_chars=len(raw_text), tiles=tile_ids, masked_text_occurrences=masked, rotation=page.get_rotation()))
            del painter
            picture.close();picture=None
            textpage.close(); page.close()
    finally:
        if picture is not None:picture.close()
        document.close()
    full_text = '\n'.join(raw_texts)
    cover = '\n'.join(raw_texts[:1])
    ids = sorted(set(re.findall(r'(?:学号|Student\s*ID)\s*[:：]?\s*(\d{9,13})(?!\d)', cover, re.I)))
    if not ids:
        ids = sorted({str(t) for t in identity_tokens if re.fullmatch(r'\d{9,13}',str(t)) and str(t) in cover})
    manifest = dict(extractor_version=VERSION, source_sha256=sha256_file(source), pdf_sha256=sha256_file(output/'rendered.pdf'),
                    conversion=conversion, page_count=len(pages), pages=pages, evidence=evidence,
                    extraction_complete=True, cover_id_candidates=ids,
                    privacy_note='遮盖文本层已知姓名/学号；图片内部身份文字不能保证全部识别。评分提示禁止按身份评分。',
                    scanned_pages=[p['page'] for p in pages if p['text_chars'] < 20],
                    rotation_review_required=any(p['rotation'] for p in pages))
    # Full text stays local for identity/version review, outside the model packet.
    (output/'local-text.txt').write_text(full_text, 'utf-8')
    dump_json(output/'manifest.json', manifest)
    return manifest
