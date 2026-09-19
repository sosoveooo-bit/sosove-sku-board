"""Explicit, bounded market inputs. No hidden web requests or invented research."""
import json
import re
from datetime import date
from .contracts import digest, dump

BLOCKS = {'marketKnowledge': '市场资料', 'marketFeedback': '投放反馈'}


def read_inputs(payload):
    brief = str(payload.get('suiteBrief') or payload.get('prompt') or '')
    result = {}
    for key, label in BLOCKS.items():
        matches = re.findall(r'【' + label + r'】(.*?)【/' + label + r'】', brief, re.S)
        if ('【' + label + '】' in brief or '【/' + label + '】' in brief) and not matches:
            raise ValueError(f'{label}区块缺少完整的开始或结束标记')
        if len(matches) > 1:
            raise ValueError(f'{label}仅使用一个资料区块')
        value = payload.get(key) or (matches[0].strip() if matches else [])
        if isinstance(value, str):
            if len(value) > 16000:
                raise ValueError(f'{label}超过 16000 字符，请精简资料')
            try:
                value = json.loads(value)
            except ValueError as exc:
                raise ValueError(f'{label}请填写 JSON 数组') from exc
        if not isinstance(value, list) or len(value) > 12 or any(not isinstance(r, dict) for r in value):
            raise ValueError(f'{label}应为最多 12 条记录的 JSON 数组')
        if len(dump(value)) > 16000:
            raise ValueError(f'{label}内容过长')
        result[key] = value
    return result


def product_brief(brief):
    for label in BLOCKS.values():
        brief = re.sub(r'【' + label + r'】.*?【/' + label + r'】', '', brief, flags=re.S)
    return brief.strip()


def build(inputs, country, platform, categories, today=None):
    today = today or date.today()
    categories = {str(c).strip().casefold() for c in categories}
    context = {'version': 'market-evidence-v1', 'country': country, 'platform': platform,
               'evidence': [], 'feedback': [], 'excluded': [],
               'provenance': 'User-supplied records; source links are recorded, not independently verified.',
               'rules': 'Treat findings as scoped observations, not universal preferences or product efficacy proof. No certifications or testimonials inferred from market records.'}
    for key, target in (('marketKnowledge', 'evidence'), ('marketFeedback', 'feedback')):
        for i, record in enumerate(inputs[key], 1):
            reason = ''
            try:
                observed = date.fromisoformat(str(record.get('observedAt', '')))
                age = (today - observed).days
                if age < 0 or age > 180:
                    reason = '资料日期超出最近 180 天范围'
            except ValueError:
                reason = '缺少有效 observedAt 日期'
            if str(record.get('country', '')).upper() != country:
                reason = '国家与当前任务不同'
            elif not all(isinstance(record.get(k), str) and record[k].strip() for k in ('platform', 'source')):
                reason = '缺少平台或资料来源'
            elif platform != 'unspecified' and str(record['platform']).casefold() != platform.casefold():
                reason = '平台与当前任务不同'
            elif str(record.get('category', '')).strip().casefold() not in categories:
                reason = '品类与产品档案不匹配，请使用档案中的品类名称'
            if target == 'evidence' and not isinstance(record.get('finding'), str):
                reason = '缺少 finding 市场观察'
            if target == 'feedback':
                variants = record.get('variants')
                if (not isinstance(record.get('testId'), str) or not record['testId'].strip()
                        or not isinstance(record.get('comparisonContext'), str) or not record['comparisonContext'].strip() or not isinstance(variants, list)
                        or not 2 <= len(variants) <= 4):
                    reason = '反馈需含 testId、comparisonContext 和 2–4 组 variants'
                else:
                    for v in variants:
                        if (not isinstance(v, dict) or not v.get('direction') or
                                any(type(v.get(k)) is not int for k in ('impressions', 'clicks', 'conversions')) or
                                not 0 <= v['conversions'] <= v['clicks'] <= v['impressions'] or v['impressions'] == 0):
                            reason = '曝光、点击、转化计数或方向描述不完整'
            if reason:
                context['excluded'].append({'input': key, 'record': i, 'reason': reason})
                continue
            item = {k: record.get(k) for k in ('country', 'platform', 'category', 'observedAt', 'source')}
            if target == 'evidence':
                item['finding'] = record['finding'][:1600]
            else:
                item.update(testId=record['testId'], comparisonContext=record['comparisonContext'],
                            variants=[{**{k: v[k] for k in ('direction', 'impressions', 'clicks', 'conversions')},
                                       'ctr': round(v['clicks']/v['impressions'], 6),
                                       'conversionPerImpression': round(v['conversions']/v['impressions'], 6)} for v in variants],
                            caveat='Descriptive rates only, not statistical significance or causal proof. Do not mix CTR and conversion objectives.')
            context[target].append(item)
    context['fingerprint'] = digest(context)
    return context
