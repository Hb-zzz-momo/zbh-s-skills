"""Separate teaching context from candidate answers and pair rubric evidence."""
import hashlib
import json
from pathlib import Path
import re

from .documents import dump_json
from .engine import fingerprint
from .word_structure import normalized,read_structure

VERSION='word-first-1.3'
ROLES={'student_answer','question','instruction','example','metadata','ambiguous','page_context'}


def classify_blocks(structure,experiment_id):
    """Use structural boundaries, never answer-key similarity, to label provenance.

    Labels describe candidate submission content, not proof of authorship.
    Unknown boundaries stay ambiguous; no region is silently discarded.
    """
    profiles=json.loads(Path(__file__).with_name('evidence_profiles.json').read_text('utf-8'))
    profile=profiles[experiment_id]
    background={normalized(t) for t in profile['background_context']}
    in_answers=False;in_reflection=False;in_example=False;in_cover=True;in_background=False
    previous_question='';last_text='';classified=[]
    for block in structure['blocks']:
        text=block['text'].strip();compact=normalized(text)
        was_example=in_example
        role='ambiguous';basis='unclassified';question=previous_question
        if compact=='Linux命令格式':in_background=True
        if compact=='第一个C语言程序':in_background=False
        if re.match(r'实验(?:步骤|过程).*结果',compact):
            in_answers=True;in_cover=False;in_example=False
            role='question';basis='answer_region_boundary'
        elif re.match(r'(?:实验)?心得(?:与体会)?|实验总结',compact):
            in_reflection=True;in_answers=True;in_example=False
            value=re.split(r'[:：]',text,maxsplit=1)
            if len(value)==2 and value[1].strip():
                text=value[1].strip();role='student_answer';basis='explicit_reflection_value'
            else:role='question';basis='reflection_heading'
        elif re.match(r'评定成绩|教师评语|指导教师',compact):
            in_answers=False;in_reflection=False;role='metadata';basis='teacher_field'
        elif not in_answers:
            if '实验目的' in compact or '实验内容' in compact:in_cover=False
            if '示例' in compact or '例如' in compact:in_example=True
            role='metadata' if in_cover else 'example' if in_example else 'instruction'
            basis='before_answer_region'
        elif in_reflection:
            role='student_answer';basis='reflection_response'
        elif compact in background or (in_background and block['container']=='table_cell'):
            role='instruction';basis='known_teaching_background_region'
        elif re.search(r'给出|解释.{0,8}(?:作用|含义)|按顺序操作|记录下输出|输入如下',text):
            role='question';basis='explicit_task_instruction'
            if '输入以下代码' in text:in_example=True
            # Split appended answers only after an explicit closing task marker.
            closing=max(text.rfind('）'),text.rfind(')'))
            if closing>=0 and text[closing+1:].strip():
                question=text[:closing+1]
                text=text[closing+1:].strip();role='student_answer';basis='answer_after_task_marker'
        elif in_example and text:
            role='example';basis='code_explicitly_supplied_by_task'
            if compact=='}':in_example=False
        elif text.startswith('$'):
            if re.search(r'解释.{0,8}(?:作用|含义)',previous_question) and re.search(r'(?:作用|含义)\s*[:：]\s*\S',text):
                role='student_answer';basis='command_with_requested_student_explanation'
            else:
                role='ambiguous';basis='bare_command_could_be_task_or_response'
        elif re.match(r'^(?:[一二三四五六七八九十]+[、.．]|\d+[)）]\s*(?:使用|编写|编译|运行|查看|观察|完成|计算|分析|调试))',text) or compact in ('登录Linux','熟悉常用Linux命令','使用Linux的联机帮助man','Linux命令格式','Linux下文本编辑vi或者vim','第一个C语言程序','退出Linux'):
            role='question';basis='task_or_supplied_command'
        elif re.search(r'用自己设置|拷贝到Linux|通过VirtualBox|命令行模式下输入init',text):
            role='instruction';basis='operating_instructions'
        else:
            role='student_answer';basis='content_in_answer_region'
        if role=='question':previous_question=text;question=text
        if not text and block['image_ids']:
            role='example' if in_example else 'student_answer' if in_answers else 'example' if not in_cover else 'ambiguous'
            basis='image_anchor_in_answer_region' if in_answers else 'image_before_answer_region'
        # Word can anchor an answer screenshot to the same paragraph as its
        # question (or a prefilled command). Classify media separately; never
        # promote the surrounding task text to student evidence.
        image_role=role;image_basis=basis
        if block['image_ids']:
            supplied_image=re.search(r'示例截图|截图示例|参考截图|参考图|如下图所示|示例如下',block['text'])
            output_request=r'给出[^。\n]*(?:截图|运行结果|输出结果|输入代码后的结果)|记录[^。\n]*输出'
            if supplied_image:
                image_role='example';image_basis='explicitly_supplied_example_image'
            elif in_answers and role not in ('metadata','instruction') and re.search(output_request,block['text']):
                image_role='student_answer';image_basis='image_at_requested_output_anchor'
            elif was_example or in_example:
                image_role='example';image_basis='image_in_supplied_example_region'
            elif in_answers and role=='ambiguous' and text.startswith('$') and re.search(output_request,question or previous_question):
                image_role='student_answer';image_basis='image_after_requested_output_command'
        classified.append({**block,'text':text,'role':role,'role_basis':basis,
                           'image_role':image_role,'image_role_basis':image_basis,
                           'question_context':question or previous_question,'neighbor_context':last_text})
        if text:last_text=text
    return classified


def _terms(text):
    """Lexical retrieval proposes candidates only; it never awards points."""
    tokens=set(re.findall(r'[A-Za-z_][A-Za-z0-9_.-]*|--?[A-Za-z]+',text.lower()))
    for word in re.findall(r'[\u4e00-\u9fff]+',text):
        tokens.update(word[i:i+2] for i in range(len(word)-1))
    return tokens-{'截图','正确','内容','命令','展示','解释','对应','程序','结果'}


def pair_criteria(rubric,evidence):
    """Keep full evidence accessible; a candidate shortlist is not absence proof."""
    plan=[]
    for section in rubric['sections']:
        for criterion in section['criteria']:
            query=_terms(criterion['full_credit']+' '+criterion['partial_credit']+' '+section['title'])
            ranked=[]
            for e in evidence:
                if e.get('role')!='student_answer':continue
                content=e.get('text','')+' '+e.get('question_context','')+' '+e.get('neighbor_context','')
                score=len(query&_terms(content))
                if score:ranked.append((score,e['id']))
            selected=[eid for _,eid in sorted(ranked,key=lambda r:(-r[0],r[1]))[:12]]
            requirements={}
            # These gates express existing anchors, never new deductions. When
            # facts do not prove an anchor, hold for review rather than invent zero.
            if criterion['id']=='exp02.S03.C02':requirements['student_explanation_required']=True
            if criterion['id'] in ('exp03.S02.C01','exp03.S02.C03','exp03.S02.C05','exp03.S02.C07'):
                requirements['command_pattern']={'exp03.S02.C01':r'(?:\s-E\b|\bcpp\b)','exp03.S02.C03':r'\s-S\b','exp03.S02.C05':r'\s-c\b','exp03.S02.C07':r'\b(?:gcc|cc|clang|ld)\b.*hello\.o'}[criterion['id']]
            if criterion['id']=='exp03.S03.C04':requirements['full_command_patterns']=[r'^(?:\(gdb\)\s*)?(?:n|next)(?:\s|$)',r'^(?:\(gdb\)\s*)?(?:s|step)(?:\s|$)']
            plan.append({'criterion_id':criterion['id'],'candidate_evidence_ids':selected,'verification_requirements':requirements,
                         'search_scope_complete':False,'method':'heading-and-neighbor-lexical-candidates',
                         'instruction':'候选不是完整检索范围，不得据此判缺答；可查阅全部目录。逐条核对满分条件。'})
    return plan


def prepare_word_evidence(folder,manifest,rubric,identity_tokens=()):
    """Build structured evidence, original media, and independent page checks.

    Page images are context only: they cannot bypass a missing student-answer
    classification. Unsupported objects/coverage gaps become explicit blockers.
    """
    folder=Path(folder)
    structure=read_structure(folder/'structure.docx',folder/'media',folder/'paragraph-pages.json')
    blocks=classify_blocks(structure,rubric['experiment_id'])
    lookup={b['id']:b for b in blocks}
    raw_text=(folder/'local-text.txt').read_text('utf-8')
    pdf_text=normalized(raw_text)
    page_catalog=manifest['evidence']
    evidence=[];mismatch=[]
    def cleaned(value):
        for token in sorted((str(t) for t in identity_tokens if t),key=len,reverse=True):value=value.replace(token,'[身份已遮盖]')
        return value
    for block in blocks:
        original=structure['blocks'][block['index']]['text']
        # Minor line spacing changes are harmless; unmatched substantial text
        # is recorded for review rather than silently marked fully extracted.
        if len(normalized(original))>=12 and normalized(original) not in pdf_text:
            mismatch.append(block['id'])
        if not block['text'].strip() or block['role']=='metadata':continue
        text=cleaned(block['text'])
        evidence.append(dict(id=block['id']+'-text',kind='text',origin='student',role=block['role'],role_basis=block['role_basis'],
                             locator=f"Word {block['container']} {block['id']}，页{block['page_start']}—{block['page_end']}",
                             text=text,sha256=hashlib.sha256(text.encode()).hexdigest(),readable=True,block_id=block['id'],
                             page_start=block['page_start'],page_end=block['page_end'],
                             question_context=cleaned(block['question_context']),neighbor_context=cleaned(block['neighbor_context'])))
    for media in structure['images']:
        block=lookup[media['block_id']]
        evidence.append(dict(id=media['id'],kind='image',origin='student',role=block['image_role'],role_basis=block['image_role_basis'],
                             locator=f"Word原始图片 {media['package_part']}，锚点{block['id']}，页{block['page_start']}—{block['page_end']}",
                             sha256=media['sha256'],readable=media['readable'],file=str(Path(media['file']).relative_to(folder)),
                             original_file=str(Path(media['original_file']).relative_to(folder)),original_sha256=media['source_sha256'],
                             block_id=block['id'],page_start=block['page_start'],page_end=block['page_end'],
                             floating=media['floating'],question_context=cleaned(block['question_context']),neighbor_context=cleaned(block['neighbor_context'])))
    # Retain every rendered page for cross-check, labelled so prefilled text
    # on a page cannot stand in for an answer block.
    for e in page_catalog:
        if e['kind']=='image':evidence.append({**e,'role':'page_context','role_basis':'rendered_cross_check_only'})
    coverage={'word_paragraphs':len(blocks),'original_image_occurrences':len(structure['images']),
              'structure_docx_sha256':structure['docx_sha256'],
              'page_count':manifest['page_count'],'unmapped_blocks':structure['unmapped_blocks'],
              'text_not_matched_in_page_layer':mismatch,'object_issues':structure['issues'],
              'page_images_cross_check_required':True,
              'meaning':'结构与页面覆盖核对，不是图片内容已被正确理解或原创证明'}
    plan={'pipeline_version':VERSION,'classification_policy':'structural-labels-not-authorship-proof',
          'coverage':coverage,'criteria':pair_criteria(rubric,evidence)}
    dump_json(folder/'classified-blocks.json',blocks)
    dump_json(folder/'evidence-plan.json',plan)
    flags=[]
    if structure['unmapped_blocks']:flags.append('word_page_mapping_needs_review')
    if structure['issues']:flags.append('word_objects_need_review')
    if mismatch:flags.append('word_page_text_mismatch')
    return evidence,plan,flags
