"""Pre-render contract checks only. Never invokes a vision/image-review model."""
import re
from difflib import SequenceMatcher
from .contracts import required, digest


DESIGN_VALUES = {
    'primarySubject': {'product', 'person', 'detail', 'environment', 'diagram'},
    'method': {'hero', 'demonstration', 'macro', 'comparison', 'sequence', 'diagram', 'montage', 'specification'},
    'layoutFamily': {'single', 'split', 'grid', 'layered', 'editorial'},
    'humanRole': {'none', 'hands', 'contextual', 'portrait'},
}


def internal_copy(text):
    """Narrow pre-render leakage checks, not a model-based content review."""
    return bool(re.search(
        r'\bnicht\s+(?:dokumentiert|belegt)\b|durch\s+die\s+bilder\s+gestützt|'
        r'\b(?:not documented|not evidenced|evidence ledger|supported by (?:the )?images)\b|'
        r'内部(?:分析|核查)|资料缺失|尚未核实|待核验|原文引用|素材引用|未记录|未证实|'
        r'画像から確認できる|資料未確認|未検証|ยังไม่ได้รับการยืนยัน', str(text), re.I))


def design_issues(pages, allow_uniform=False):
    """Cheap plan-only checks; no claim to recognize similarity in rendered images."""
    issues, groups, previous, signatures = {}, {}, [], []
    for page in sorted(pages, key=lambda p: p['page']):
        n, design = page['page'], page.get('visualDesign')
        signature = re.sub(r'\d+|\s+', '', page['scene'] + '|' + page['composition']).lower()
        if any(SequenceMatcher(None, signature, old, autojunk=False).ratio() > .94 for old in signatures):
            issues[n] = '场景和构图与已有页面过近，请改动实际内容'
        signatures.append(signature)
        if (not isinstance(design, dict)
                or any(design.get(k) not in values for k, values in DESIGN_VALUES.items())
                or any(not isinstance(design.get(k), str) or len(design[k].strip()) < 4
                       for k in ('visualHook', 'referenceReason'))):
            issues[n] = '补齐准确的视觉主角、表现方式、布局、人物角色、视觉创意与素材理由'
            continue
        if (any(not isinstance(design.get(k), str) or len(design[k].strip()) < 4
                for k in ('buyingReason', 'benefitVisualization'))
                or not isinstance(design.get('informationHierarchy'), list)
                or len(design['informationHierarchy']) < 2
                or any(not isinstance(x, str) or len(x.strip()) < 4 for x in design['informationHierarchy'])):
            issues[n] = '补齐购买理由、卖点的画面表达与信息层级；勿只换背景或标题'
        if internal_copy(page.get('copyDirection', '')):
            issues[n] = '内部核查备注混入文案方向；只改成有依据的消费者内容，保留必要使用提示'
        key = tuple(design[k] for k in ('primarySubject', 'method', 'layoutFamily'))
        groups.setdefault(key, []).append(n)
        if not allow_uniform and len(previous) >= 2 and previous[-2:] == [key, key]:
            issues[n] = '连续三页主角、表现方式和布局相同，请改变实际画面而非改名'
        previous.append(key)
    if not allow_uniform and len(pages) >= 6:
        limit = max(3, int(len(pages) * .6))
        for numbers in groups.values():
            for n in numbers[limit:]:
                issues[n] = '同一主角、表现方式和布局占比过高，请选择其他有依据的视觉解释'
    return [{'page': n, 'reason': reason} for n, reason in sorted(issues.items())]


def _validate_page(page, count, source_ids, fact_ids, asset_ids):
    required(page, ('page', 'purpose', 'userPsychology', 'sourceIds', 'factIds', 'scene',
                    'composition', 'copyDirection', 'evidenceMethod', 'referenceAssetIds', 'difference'), '单页设计')
    n = page['page']
    if type(n) is not int or not 1 <= n <= count:
        raise ValueError('页面编号重复或超出请求范围')
    for field, allowed in (('sourceIds', source_ids), ('factIds', fact_ids), ('referenceAssetIds', asset_ids)):
        if not isinstance(page[field], list) or any(not isinstance(x, str) or x not in allowed for x in page[field]):
            raise ValueError(f'第 {n} 页 {field} 含未知引用')
        if field != 'factIds' and not page[field]:
            raise ValueError(f'第 {n} 页缺少' + ('原文引用 sourceIds' if field == 'sourceIds' else '产品素材引用 referenceAssetIds'))
    for field in ('purpose', 'userPsychology', 'scene', 'composition', 'copyDirection', 'evidenceMethod', 'difference'):
        if not isinstance(page[field], str) or len(page[field].strip()) < 4:
            raise ValueError(f'第 {n} 页 {field} 尚未具体说明')


def has_page_index(pages, count):
    return (isinstance(pages, list) and len(pages) == count
            and all(isinstance(p, dict) and type(p.get('page')) is int for p in pages)
            and {p['page'] for p in pages} == set(range(1, count + 1)))


def plan_contract_issues(pages, count, source_ids, fact_ids, asset_ids):
    """Identify repairable page contracts without rewriting or inventing any references."""
    if not isinstance(pages, list) or len(pages) != count:
        raise ValueError(f'图片规划应包含 {count} 页')
    if not has_page_index(pages, count):
        raise ValueError('页面编号重复或超出请求范围')
    issues, covered = [], set()
    for page in pages:
        try:
            _validate_page(page, count, source_ids, fact_ids, asset_ids)
        except ValueError as exc:
            issues.append({'page': page['page'], 'reason': str(exc)})
        ids = page.get('sourceIds')
        if isinstance(ids, list):
            covered.update(x for x in ids if isinstance(x, str) and x in source_ids)
    missing = sorted(set(source_ids) - covered)
    if missing:
        # Let the planner choose a relevant page; do not arbitrarily assign missing claims.
        if not issues:
            issues = [{'page': p['page'], 'reason': '原始卖点未完整覆盖；选择合适页面说明或澄清，勿编造证据',
                       'uncoveredSourceIds': missing} for p in pages]
        else:
            issues[0]['uncoveredSourceIds'] = missing
    return issues


def validate_plan(pages, count, source_ids, fact_ids, asset_ids, check_similarity=True):
    if not isinstance(pages, list) or len(pages) != count:
        raise ValueError(f'图片规划应包含 {count} 页')
    covered, numbers, signatures = set(), set(), []
    for page in pages:
        _validate_page(page, count, source_ids, fact_ids, asset_ids)
        n = page['page']
        if n in numbers:
            raise ValueError('页面编号重复或超出请求范围')
        numbers.add(n)
        covered.update(page['sourceIds'])
        signature = re.sub(r'\d+|\s+', '', page['scene'] + '|' + page['composition']).lower()
        if check_similarity and any(SequenceMatcher(None, signature, previous, autojunk=False).ratio() > .94 for previous in signatures):
            raise ValueError(f'第 {n} 页场景与构图过近，请只修正相关页面设计')
        signatures.append(signature)
    if set(source_ids) - covered:
        raise ValueError('原始卖点未完整覆盖：' + ','.join(sorted(set(source_ids) - covered)))
    return sorted(pages, key=lambda p: p['page'])


def identity_label(value, role, identity):
    """Permit literal Latin package names, not arbitrary untranslated ad copy."""
    if role not in {'label', 'brand', 'product_name', 'productName'} or not isinstance(value, str):
        return False
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 .+&®™/()_-]{0,79}', value):
        return False
    def strings(node):
        if isinstance(node, str):
            yield node
        elif isinstance(node, dict):
            for child in node.values():
                yield from strings(child)
        elif isinstance(node, list):
            for child in node:
                yield from strings(child)
    return any(re.search(r'(?<![A-Za-z0-9])' + re.escape(value) + r'(?![A-Za-z0-9])', s, re.I)
               for s in strings(identity or {}))


def validate_prompt(value, spec, country, localized_copy, product_identity=None):
    required(value, ('page', 'creativeInstruction', 'exactCopy', 'negativeInstructions'), '单页 Prompt')
    if type(value['page']) is not int or value['page'] != spec['page']:
        raise ValueError('Prompt 页码与设计不一致')
    instruction = value['creativeInstruction']
    if not isinstance(instruction, str) or not 100 <= len(instruction) <= 16000:
        raise ValueError('单页 Prompt 长度异常或内容过短')
    if not isinstance(value['exactCopy'], list) or not isinstance(value['negativeInstructions'], list):
        raise ValueError('文案和排除方向应为列表')
    if any(not isinstance(v, str) for v in value['negativeInstructions']):
        raise ValueError('排除方向格式异常')
    for item in value['exactCopy']:
        required(item, ('text', 'role', 'sourceIds'), '可见文案')
        if not isinstance(item['role'], str) or not item['role'].strip():
            raise ValueError('可见文案角色格式异常')
        if internal_copy(item['text']):
            raise ValueError(f"第 {spec['page']} 页内部核查备注混入可见文案，请局部修正文案并保留必要使用提示")
        if not isinstance(item['text'], str) or not item['text'].strip() or not (localized_copy(item['text'], country)
                or identity_label(item['text'], item['role'], product_identity)):
            raise ValueError(f"第 {spec['page']} 页可见文案与目标语言不匹配（exactCopy 第 {value['exactCopy'].index(item) + 1} 项）")
        # exactCopy is the authoritative visible text. The compiler injects it
        # into the final prompt; repeating it in creativeInstruction is optional.
        # Requiring both fields to duplicate it wasted a model repair request.
        if (not isinstance(item['sourceIds'], list)
                or any(not isinstance(source, str) for source in item['sourceIds'])
                or set(item['sourceIds']) - set(spec['sourceIds'])):
            raise ValueError('文案引用超出本页原文范围')
    return value


def ready_status(pages, count, version):
    ready = []
    for page in pages if isinstance(pages, list) else []:
        prompt = page.get('agentPrompt') or {}
        if (page.get('visualPipelineVersion') == version and page.get('agentPlanId')
                and page.get('agentSpec') and prompt.get('resolvedPrompt')
                and prompt.get('promptHash') == digest(prompt['resolvedPrompt'])):
            ready.append(page.get('page'))
    valid = sorted({n for n in ready if type(n) is int and 1 <= n <= count})
    missing = [n for n in range(1, count + 1) if n not in valid]
    return {'ready': len(ready) == count and len(valid) == count, 'readyCount': len(valid),
            'readyPages': valid, 'missingPages': missing, 'promptSource': 'dynamic-agent',
            'expectedCount': count}
