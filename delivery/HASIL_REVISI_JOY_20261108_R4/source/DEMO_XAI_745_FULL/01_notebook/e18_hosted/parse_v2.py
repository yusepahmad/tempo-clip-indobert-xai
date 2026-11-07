"""Explicit answer formats only; conflicting codes fail closed; never infer from reasons."""
import json
import re

def parse_answer(text,classes):
    assert len(classes)==len(set(classes))==7
    text=(text or '').strip()
    if text.startswith('{'):
        try:obj=json.loads(text)
        except (ValueError,TypeError):return 'INVALID','invalid_json'
        if not isinstance(obj,dict) or not {'code'}<=set(obj)<={'code','label'}:
            return 'INVALID','ambiguous_json'
        code=obj.get('code')
        if not isinstance(code,str) or len(code)!=1 or code not in 'ABCDEFG':
            return 'INVALID','invalid_json_code'
        if 'label' in obj and obj['label']!=classes[ord(code)-65]:
            return 'INVALID','json_code_label_mismatch'
        return code,'explicit_json_code'
    lines=[line.strip().replace('**','').replace('`','').strip(' \t\"\u201c\u201d')
           for line in text.splitlines() if line.strip()]
    if not lines:return 'INVALID','empty_response'
    candidates=[];mismatch=False
    for i,line in enumerate(lines):
        prefix=re.fullmatch(r'(?:Jawab(?:an)?(?: akhir)?(?: satu kode(?: A sampai G)?)?|Kode)\s*[:：]\s*(.+)',
                            line,flags=re.IGNORECASE)
        boundary=i in (0,len(lines)-1)
        if not prefix and not boundary:continue
        value=(prefix[1] if prefix else line).strip().strip(' \t\"\u201c\u201d')
        code=re.fullmatch(r'([A-G])[.!]?',value)
        if code:
            candidates.append((code[1],'explicit_prefix_code' if prefix else 'boundary_single_code'))
            continue
        pair=re.fullmatch(r'([A-G])(?:\s*[:\-\u2013]\s*|\s+|\s*(?=\())(?:\(([A-Z_]+)\)|([A-Z_]+))[.!]?',value)
        if pair:
            label=pair[2] or pair[3]
            if label==classes[ord(pair[1])-65]:candidates.append((pair[1],'explicit_matching_code_label'))
            else:mismatch=True
            continue
        label=value.rstrip('.!')
        if label in classes and (prefix or i==len(lines)-1):
            candidates.append(('ABCDEFG'[classes.index(label)],'explicit_class_name'))
    unique={code for code,_ in candidates}
    if mismatch:return 'INVALID','code_label_mismatch'
    if len(unique)>1:return 'INVALID','conflicting_explicit_codes'
    if len(unique)==1:return candidates[0]
    return 'INVALID','unrecognized_no_explicit_answer'
