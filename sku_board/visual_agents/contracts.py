"""Versioned data contracts; these are not image-layout templates."""
import hashlib
import json
import re

VERSION = 'cod-visual-agents-v1'
PRODUCT_VERSION = 'product-intelligence-v2-declared-identity'
SUITES = {'cod-country-landing-30', 'cod-country-detail-12'}
STAGES = ('product', 'strategy', 'direction', 'planning', 'prompts')
LABELS = dict(zip(STAGES, ('产品分析', '商品策略', '视觉导演', '图片规划', '动态 Prompt')))


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(dump(value).encode('utf-8')).hexdigest()


def raw_brief(payload):
    # Upload wrappers add filename-based routing prose; it is not a product fact.
    value = str(payload.get('suiteBrief') or payload.get('prompt') or '')
    return re.sub(r'(?m)^\[Reference role map\].*$', '', value).strip()


def request_fingerprint(payload):
    values = [VERSION, raw_brief(payload), str(payload.get('suiteKey')),
                   str(payload.get('suiteCountry') or 'KR'), int(payload['suiteCount']),
                   str(payload['size']), str(payload.get('platform') or ''),
                   payload.get('productFacts') or '']
    # Keep old saved-plan hashes valid when no new market fields were supplied.
    extras = {k: payload[k] for k in ('marketKnowledge', 'marketFeedback') if payload.get(k)}
    if extras:
        values.append(extras)
    return digest(values)


def required(data, fields, label):
    if not isinstance(data, dict):
        raise ValueError(f'{label} 返回格式应为对象')
    missing = [field for field in fields if field not in data or data[field] is None or data[field] == '']
    if missing:
        raise ValueError(f'{label} 缺少字段：' + ', '.join(missing))
    return data


def is_agent(pages):
    return isinstance(pages, list) and any(isinstance(p, dict) and p.get('visualPipelineVersion') == VERSION for p in pages)
