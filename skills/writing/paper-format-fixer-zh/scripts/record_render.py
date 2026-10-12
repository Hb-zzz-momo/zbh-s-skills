"""Bind a real renderer receipt, PDF, and all page images to a DOCX version."""
import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pdfplumber
from docx import Document
from pypdf import PdfReader
from journal_profile import sha256, write_json, story_parts, load_profile


def text_coverage(source, rendered):
    def tokens(value):
        value = unicodedata.normalize('NFKC', value).lower()
        # Separate Chinese characters so wrapping does not destroy coverage.
        return Counter(re.findall(r'[\u3400-\u9fff]|[^\W\u3400-\u9fff]+', value, re.UNICODE))
    expected = tokens(source); observed = tokens(rendered)
    return sum((expected & observed).values()) / max(1, sum(expected.values()))


def record_render(docx, profile_path, export_path, images_dir):
    profile = load_profile(profile_path)
    export = json.loads(Path(export_path).read_text(encoding='utf-8-sig'))
    current = sha256(docx)
    if export.get('docx_sha256') != current or export.get('copy_sha256') != current:
        raise ValueError('Renderer receipt does not match the current input or its read-only copy')
    if export.get('read_only') is not True:
        raise ValueError('Renderer did not confirm opening a read-only copy')
    pdf = Path(export['pdf'])
    if sha256(pdf) != export.get('pdf_sha256'): raise ValueError('Export PDF changed after rendering')
    with pdfplumber.open(pdf) as rendered:
        page_count = len(rendered.pages)
        pdf_text = '\n'.join(page.extract_text() or '' for page in rendered.pages)
        fonts = sorted({c['fontname'] for page in rendered.pages for c in page.chars})
    doc = Document(docx)
    source_text = '\n'.join(' '.join(element.xpath('.//w:t/text()')) for _, element in story_parts(doc))
    coverage = text_coverage(source_text, pdf_text)
    unknown_fonts = [font for font in fonts if not any(font.split('+')[-1].startswith(prefix)
        for prefix in profile['render']['allowed_pdf_font_prefixes'])]
    files = sorted(Path(images_dir).glob('page-*.png'), key=lambda p:int(p.stem.split('-')[-1]))
    if len(files) != page_count or [int(p.stem.split('-')[-1]) for p in files] != list(range(1,page_count+1)):
        raise ValueError('Page PNG sequence is incomplete or contains stale extra pages; use a fresh render folder')
    if page_count != export['page_count']: raise ValueError('Renderer page count and PDF disagree')
    problems = []
    if coverage < profile['render']['minimum_text_coverage']: problems.append('render_text_coverage')
    if unknown_fonts: problems.append('render_font_fallback')
    return {'status':'BLOCK' if problems else 'PASS', 'problems':problems,
        'docx':str(Path(docx).resolve()),'docx_sha256':current,'profile_sha256':sha256(profile_path),
        'pdf':str(pdf.resolve()),'pdf_sha256':sha256(pdf),'renderer':export['renderer'],
        'renderer_version':export.get('renderer_version'),'read_only_copy':True,
        'page_count':page_count,'text_coverage':round(coverage,5),'pdf_fonts':fonts,'unknown_fonts':unknown_fonts,
        'pages':[{'number':i,'path':str(p.resolve()),'sha256':sha256(p)} for i,p in enumerate(files,1)]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ('docx','profile','export','images','out'): parser.add_argument('--'+arg,required=True)
    args=parser.parse_args()
    result=record_render(args.docx,args.profile,args.export,args.images)
    write_json(args.out,result)
    return 1 if result['status']=='BLOCK' else 0


if __name__=='__main__': raise SystemExit(main())
