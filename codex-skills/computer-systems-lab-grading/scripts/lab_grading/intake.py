"""File-first intake: inspect locally, then commit an explicitly confirmed ticket."""
import json
from pathlib import Path
import re
import shutil
import unicodedata
import uuid
import zipfile
from xml.etree import ElementTree as ET

from .documents import dump_json, sha256_file, to_pdf, validate_document
from .engine import load_rubric, require
from .storage import now


def normalized(text):
    return unicodedata.normalize('NFKC', str(text or ''))


def cover_header(cover):
    text=normalized(cover)
    body=re.search(r'(?:^|\n)\s*(?:[一二三四五六七八九十]+\s*[、.．]\s*)?实验\s*(?:目的|内容|步骤|要求|过程|任务)',text)
    return text[:body.start()] if body else text[:1800]


def identity_candidate(filename,cover=''):
    """Prefill fields for teacher confirmation; never create a roster identity."""
    stem=normalized(Path(filename).stem);header=cover_header(cover)
    file_numbers=list(dict.fromkeys(re.findall(r'(?<!\d)\d{5,16}(?!\d)',stem)))
    cover_numbers=list(dict.fromkeys(re.findall(r'学号\s*[:：]?\s*(\d{5,16})(?!\d)',header)))
    names={};sources=[];conflicts=[]
    if len(file_numbers)==1:
        tail=stem[stem.index(file_numbers[0])+len(file_numbers[0]):]
        name=re.match(r'[\s+_\-—]*([\u4e00-\u9fff·]{2,20})(?=(?:-\d+)?[\s+_\-—]*(?:实验|$))',tail)
        if name:names['文件名']=name[1]
    cover_name=re.search(r'(?:学生姓名|姓名)\s*[:：]?\s*([\u4e00-\u9fff·]{2,20})(?=\s|$|学号|班级|实验)',header)
    if cover_name:names['封面']=cover_name[1]
    numbers=set(file_numbers+cover_numbers)
    if len(numbers)>1:conflicts.append('文件名与封面学号不一致或包含多个学号，请手工核对')
    if len(set(names.values()))>1:conflicts.append('文件名与封面姓名不一致，请手工核对')
    if file_numbers or names.get('文件名'):sources.append('文件名')
    if cover_numbers or names.get('封面'):sources.append('封面身份字段')
    return dict(number=next(iter(numbers)) if len(numbers)==1 else '',
                name=next(iter(names.values())) if len(set(names.values()))==1 else '',
                sources=sources,conflicts=conflicts)


def new_version_hint(filename,cover='',student_name=''):
    """Only explicit submission markers, excluding names and lab instructions."""
    stem=normalized(Path(filename).stem)
    if student_name:stem=stem.replace(normalized(student_name),'')
    marker=r'最新(?:版|稿)?|新版(?:本)?|更新(?:版|稿)|修订(?:版|稿)|(?<![\u4e00-\u9fff])新(?![\u4e00-\u9fff])|新(?=实验)|实验(?:报告)?\s*[\d一二三四五六七八九十]+\s*新'
    match=re.search(marker,stem)
    if match:return dict(is_new=True,source='文件名',text=match[0],filename=filename)
    for line in cover_header(cover).splitlines():
        line=line.strip()
        field=re.match(r'(?:提交版本|报告版本|版本|提交说明)\s*[:：]\s*(.+)',line)
        if field and re.search(marker,field[1]):
            return dict(is_new=True,source='封面版本字段',text=line[:120],filename=filename)
        if re.match(r'实验(?:报告|\s*[\d一二三四五六七八九十])',line) and re.search(marker,line):
            return dict(is_new=True,source='封面报告标题',text=line[:120],filename=filename)
    return dict(is_new=False,source='',text='')


def experiment_numbers(text):
    result = set()
    chinese = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,
               '九':9,'十':10,'十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16}
    for m in re.finditer(r'实验(?:报告)?\s*[（(]?\s*(\d{1,2}|十[一二三四五六]?|[一二三四五六七八九])(?!\d)', normalized(text)):
        value = int(m[1]) if m[1].isdigit() else chinese.get(m[1], 0)
        if 1 <= value <= 16:result.add(f'exp{value:02}')
    return result


def docx_cover(path):
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo('word/document.xml')
        require(info.file_size <= 16*1024*1024, 'Word正文过大，请拆分报告')
        root = ET.fromstring(archive.read(info))
    ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    paragraphs = [''.join(p.itertext()) if not p.findall('.//w:t',ns) else
                  ''.join(t.text or '' for t in p.findall('.//w:t',ns))
                  for p in root.findall('.//w:p',ns)]
    # Cover fields precede experimental instructions. Do not search student examples.
    return '\n'.join(paragraphs)[:3000]


def pdf_cover(path):
    import pypdfium2 as pdfium
    document=pdfium.PdfDocument(path)
    try:
        if not len(document):return ''
        page=document[0]
        try:
            text=page.get_textpage()
            try:return text.get_text_range()[:3000]
            finally:text.close()
        finally:page.close()
    finally:document.close()


def read_cover(path, folder):
    if path.suffix.lower()=='.docx':return docx_cover(path), 'Word原始封面'
    if path.suffix.lower()=='.pdf':return pdf_cover(path), 'PDF首页'
    # Legacy Word is opened read-only using the same protected converter as grading.
    target=folder/'cover.pdf';structure=folder/'cover.docx'
    to_pdf(path,target,timeout=60,structure_docx=structure)
    return docx_cover(structure), '旧版Word封面'


def predict(filename, cover, catalog):
    """Deterministic, auditable cross-check. Conflicts never silently choose a side."""
    stem=normalized(Path(filename).stem);cover=cover_header(cover)
    students=[s for s in catalog['students'] if not s.get('demo')]
    groups=[g for g in catalog['groups'] if not g.get('demo') and not g.get('sourceGroupIds')]
    reasons=[];conflicts=[]
    def identify(text, source, limited=False):
        text=text[:1800] if limited else text
        numbers=set(re.findall(r'(?<!\d)\d{5,16}(?!\d)',text))
        matched=[s for s in students if normalized(s['number']) in numbers]
        if numbers and not matched:
            conflicts.append(source+'学号不在名单中');return None
        if len(matched)>1:
            conflicts.append(source+'包含多个学生学号');return None
        names=[s for s in students if s['name'] and normalized(s['name']) in text]
        if matched:
            student=matched[0]
            if names and student['id'] not in {s['id'] for s in names}:
                conflicts.append(source+'学号与姓名不一致');return None
            reasons.append(source+'完整学号匹配');return student['id']
        if len(names)==1:
            reasons.append(source+'唯一姓名匹配');return names[0]['id']
        if names:conflicts.append(source+'姓名重名，需核对学号')
        return None
    sid_file=identify(stem,'文件名')
    sid_cover=identify(cover,'封面',True) if cover.strip() else None
    sid=sid_file or sid_cover
    if sid_file and sid_cover and sid_file!=sid_cover:
        conflicts.append('文件名与封面对应不同学生');sid=None
    if any('学号' in c or '重名' in c for c in conflicts):sid=None
    exp_file=experiment_numbers(stem);exp_cover=experiment_numbers(cover[:1000])
    if not exp_cover:
        compact=re.sub(r'\s+','',cover[:1000]).lower()
        exp_cover={f'exp{i:02}' for i in range(1,17)
                   if re.sub(r'\s+','',load_rubric(f'exp{i:02}')['title']).lower() in compact}
    experiments=exp_file|exp_cover
    exp=next(iter(experiments)) if len(experiments)==1 else None
    if len(experiments)>1:conflicts.append('文件名或封面实验信息冲突，请确认所属实验')
    if exp_file:reasons.append('文件名实验编号')
    if exp_cover:reasons.append('封面实验编号或标题')
    owners=[g for g in groups if {'groupId':g['id'],'studentId':sid} in catalog['memberships']] if sid else []
    def compact(value):return re.sub(r'[\s·班]','',normalized(value)).lower()
    group_cover=[g for g in groups if compact(g['name']) and compact(g['name']) in compact(cover[:1800])]
    # Avoid choosing the shorter class name when one name contains another.
    group_cover=[g for g in group_cover if not any(g['name']!=h['name'] and compact(g['name']) in compact(h['name']) for h in group_cover)]
    group_id=None
    if len(owners)==1:
        group_id=owners[0]['id'];reasons.append('按花名册归入原班级')
        if group_cover and group_id not in {g['id'] for g in group_cover}:
            conflicts.append('封面班级与学生名单归属不一致');group_id=None
    elif owners:
        candidates=[g for g in owners if g['id'] in {h['id'] for h in group_cover}]
        if len(candidates)==1:group_id=candidates[0]['id'];reasons.append('封面区分多个班级归属')
        else:conflicts.append('学生属于多个班级，请选择本次所属班级')
    elif len(group_cover)==1:group_id=group_cover[0]['id'];reasons.append('封面班级名称')
    return dict(student_id=sid,group_id=group_id,experiment_id=exp,reasons=reasons,
                conflicts=conflicts,needs_confirmation=not(sid and group_id and exp) or bool(conflicts),
                candidate_student=identity_candidate(filename,cover) if not sid else None)


def inspect_file(service,path,filename,ticket_id):
    validate_document(path)
    folder=path.parent
    warnings=[]
    try:cover,source=read_cover(path,folder)
    except (OSError,ValueError,ET.ParseError,RuntimeError,zipfile.BadZipFile,KeyError) as exc:
        cover='';source='文件名与名单';warnings.append('封面暂未读到，仍可按文件名检查；批阅时会重新提取原件。')
    catalog=service.store.catalog()
    prediction=predict(filename,cover,catalog)
    student=next((s for s in catalog['students'] if s['id']==prediction['student_id']),None)
    name=student['name'] if student else (prediction.get('candidate_student') or {}).get('name','')
    if cover:prediction['reasons'].append(source+'交叉核对')
    else:warnings.append('封面未识别到文字，请检查识别结果。')
    ticket=dict(ticket_id=ticket_id,filename=filename,sha256=sha256_file(path),
                created_at=now(),catalog_revision=catalog['revision'],prediction=prediction,
                version_hint=new_version_hint(filename,cover,name),
                warnings=list(dict.fromkeys(warnings)))
    dump_json(folder/'ticket.json',ticket)
    return ticket


def confirm_file(service,ticket_id,group_id,experiment_id,student_id=None,*,reason='',actor='本地教师',defer_match=False):
    require(bool(re.fullmatch(r'[0-9a-f]{32}',ticket_id)),'导入凭证无效')
    folder=service.store.path('intake/'+ticket_id)
    require((folder/'ticket.json').is_file(),'识别记录不存在，请重新选择文件')
    with service.lock:
        ticket=json.loads((folder/'ticket.json').read_text('utf-8'))
        choice=dict(group_id=group_id,experiment_id=experiment_id,student_id=student_id,defer_match=defer_match)
        if ticket.get('committed'):
            require(ticket['committed']['choice']==choice,'已导入的文件不能改换归属，请重新导入')
            return dict(report=service.detail(ticket['committed']['report_id']),duplicate=True)
        prediction=ticket['prediction']
        require(group_id and experiment_id,'请检查并补全班级与实验')
        require(not (student_id and defer_match),'暂不匹配时不能指定学生')
        changed=any(choice[k]!=prediction.get(k) for k in ('group_id','experiment_id','student_id'))
        require(not changed or reason.strip(),'修正识别结果时请填写核对依据')
        path=folder/ticket['filename']
        require(path.is_file() and sha256_file(path)==ticket['sha256'],'待导入原件已改变，请重新选择文件')
        destination=service.store.path('originals/'+ticket_id)
        destination.mkdir(exist_ok=True,parents=True);original=destination/ticket['filename']
        if not original.exists():shutil.copyfile(path,original)
        require(sha256_file(original)==ticket['sha256'],'原件复制校验失败')
        try:
            result=service.ingest(original,ticket['filename'],group_id,experiment_id,student_id,
                reason or '教师检查并确认自动识别结果',actor,defer_match=defer_match,
                allow_experiment_override=True,version_hint=ticket.get('version_hint'))
        except BaseException:
            with service.store.connect() as db:
                used=db.execute('SELECT 1 FROM reports WHERE stored_file=?',(str(original.relative_to(service.store.root)),)).fetchone()
            if not used:original.unlink(missing_ok=True);destination.rmdir()
            raise
        ticket['committed']=dict(choice=choice,report_id=result['report']['id'],actor=actor,reason=reason,confirmed_at=now())
        dump_json(folder/'ticket.json',ticket)
        if result['duplicate']:
            with service.store.connect() as db:
                used=db.execute('SELECT 1 FROM reports WHERE stored_file=?',(str(original.relative_to(service.store.root)),)).fetchone()
            if not used:original.unlink(missing_ok=True);destination.rmdir()
        return result
