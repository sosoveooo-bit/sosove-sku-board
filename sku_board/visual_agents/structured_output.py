"""Strict complete-object extraction for Agent contracts, without invented fields."""
import json
import re


class StructuredOutputError(ValueError):
    pass


class OutputTruncated(StructuredOutputError):
    """A length-limited response must be split, not retried at the same size."""


def _complete_values(data, depth=0):
    """Accept common envelopes only after their entire outer JSON decoded."""
    yield data
    if depth < 3 and isinstance(data, dict):
        for key in ('data', 'result', 'output', 'response', 'plan', 'answer'):
            if isinstance(data.get(key), (dict, list)):
                yield from _complete_values(data[key], depth + 1)


def parse(value, schema):
    source = str(value or '').strip().lstrip('\ufeff')
    if not source:
        raise StructuredOutputError('导演返回空正文，请检查模型输出或输出额度配置')
    # Some gateways JSON-encode the content string once more.
    try:
        decoded = json.loads(source)
        if isinstance(decoded, str):
            source = decoded.strip()
    except ValueError:
        pass
    decoder = json.JSONDecoder()
    missing = None
    position = 0
    while match := re.search(r'[\{\[]', source[position:]):
        start = position + match.start()
        try:
            data, end = decoder.raw_decode(source, start)
        except ValueError as exc:
            # Never promote a nested object/array inside a broken outer JSON
            # document into a supposedly complete stage result.
            raise StructuredOutputError('导演 JSON 内容不完整或格式异常；保留已有阶段，不使用截断方案') from exc
        position = end
        for candidate in _complete_values(data):
            if isinstance(candidate, list) and set(schema) == {'pages'} and candidate and all(isinstance(p, dict) and 'page' in p for p in candidate):
                candidate = {'pages': candidate}
            if not isinstance(candidate, dict):
                continue
            absent = [k for k in schema if k not in candidate or candidate[k] is None or candidate[k] == '']
            if not absent:
                return candidate
            if missing is None or len(absent) < len(missing):
                missing = absent
    if missing is not None:
        raise StructuredOutputError('导演 JSON 缺少阶段字段：' + ', '.join(missing[:8]))
    if '{' not in source and '[' not in source:
        raise StructuredOutputError('导演返回了说明文字而非 JSON 方案')
    raise StructuredOutputError('导演 JSON 内容不完整或格式异常；保留已有阶段，不使用截断方案')
