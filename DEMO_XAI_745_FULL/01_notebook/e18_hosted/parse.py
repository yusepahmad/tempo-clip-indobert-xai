"""Label-blind fixed rules for explicit final codes; no inference from prose."""
import re

def parse_answer(text, classes):
    assert len(classes) == 7 and len(set(classes)) == 7
    text = (text or '').strip()
    atom = r'(?:\*\*([A-G])\*\*|`([A-G])`|([A-G]))[.!]?'
    single = re.fullmatch(atom, text)
    if single:
        return next(x for x in single.groups() if x), 'single_code_with_optional_markup'
    final = re.search(r'(?:^|\n)Jawab satu kode A sampai G:\s*' + atom + r'\s*$', text)
    if final:
        return next(x for x in final.groups() if x), 'explicit_final_prompt_prefix'
    pair = re.fullmatch(r'([A-G]):\s*([A-Z_]+)[.!]?', text)
    if pair and classes[ord(pair[1])-ord('A')] == pair[2]:
        return pair[1], 'code_and_matching_class'
    return 'INVALID', 'unrecognized_or_ambiguous'
