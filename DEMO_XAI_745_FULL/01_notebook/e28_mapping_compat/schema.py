"""Strict structural validation, without selecting outputs using target labels."""
import json

FIELDS = ('source_object', 'source_properties', 'target_situation', 'mapping', 'uncertainty')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def decode_json(content, finish):
    if not isinstance(content, str) or len(content.strip()) < 40 or finish != 'stop':
        raise ValueError('Incomplete response')
    fields = json.loads(content, object_pairs_hook=unique_object)
    if not isinstance(fields, dict) or set(fields) != set(FIELDS):
        raise ValueError('Incorrect fields')
    if not all(isinstance(fields[key], str) and fields[key].strip() for key in FIELDS):
        raise ValueError('Expected nonempty strings')
    explanation = '\n'.join(key + ': ' + fields[key].strip() for key in FIELDS)
    return fields, explanation


def transport_text(content):
    if not isinstance(content, str):
        raise ValueError('Expected text content')
    text = content.strip()
    if not text.startswith('```'):
        return text
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() not in ('```json', '```') or lines[-1].strip() != '```':
        raise ValueError('Unsupported outer wrapper')
    return '\n'.join(lines[1:-1]).strip()


def decode(content, finish):
    return decode_json(transport_text(content), finish)
