"""Preserve the old submission API without rebuilding the old visual template."""
from copy import deepcopy
from .contracts import VERSION, SUITES, digest, dump, request_fingerprint, is_agent, raw_brief
from .validation import ready_status


def compile_prompt(authored, product, country, size, visual_dna=None, page_spec=None):
    # Only identity/copy/technical locks are deterministic. Art direction is AI-authored.
    dna_lock = ('[Shared visual DNA; style constraints, not visible copy] ' + dump(visual_dna)
                + '\nApply this palette, typography and photographic language across the series. '
                  'If page prose conflicts with shared style use this DNA, but retain its distinct scene and composition.\n\n') if visual_dna else ''
    # Forward the actual per-page decisions, not a shared layout template. This keeps
    # supporting visuals from disappearing when the prompt author summarizes a plan.
    design = (page_spec or {}).get('visualDesign') or {}
    execution = {k: page_spec[k] for k in ('scene', 'composition') if page_spec and page_spec.get(k)}
    execution.update({k: design[k] for k in ('benefitVisualization', 'informationHierarchy') if design.get(k)})
    page_lock = ('[Page visual execution; internal art direction, not visible copy] ' + dump(execution)
                 + '\nPreserve these page-specific visual relationships and supporting detail. '
                   'Render the exact visible copy only; do not print these instructions.\n\n') if execution else ''
    return page_lock + dna_lock + '\n\n'.join((authored['creativeInstruction'],
        '[Product identity only; do not inherit reference layout] ' + dump(product['productVisualDNA']),
        f'[Delivery] One finished {size} image. Selected market={country}. No outer mockup or page-1 bitmap reference.',
        '[Exact visible copy] ' + dump(authored['exactCopy']),
        '[Text boundary] Render only the exact visible copy above (plus original product markings). '
        'The exact-copy list is authoritative if scene prose paraphrases a caption; do not render alternative wording. '
        'All other context, uncertainty notes, reference IDs and validation instructions are internal, not image text.',
        '[Page-specific exclusions] ' + dump(authored['negativeInstructions'])))


def pages_from_state(state, payload):
    ledger = {s['id']: s for s in state.get('sources', [])}
    result = []
    for spec in state.get('planning', []):
        authored = state.get('prompts', {}).get(str(spec['page'])) or {}
        source_text = '\n\n'.join(ledger[s]['text'] for s in spec['sourceIds'])
        page = {
            'page': spec['page'], 'visualPipelineVersion': VERSION, 'agentPlanId': state['planId'],
            'agentInputHash': state['requestHash'], 'agentProductKey': state['productKey'],
            'agentSpec': deepcopy(spec), 'agentPrompt': deepcopy(authored),
            'country': payload['suiteCountry'], 'size': payload['size'],
            'role': spec['purpose'], 'title': spec['purpose'], 'focus': source_text,
            'focusTitle': spec['purpose'], 'focusDescription': source_text,
            'sourcePointVerbatim': source_text, 'sourcePointType': 'agent-ledger',
            'composition': spec['composition'], 'scene': spec['scene'], 'objective': spec['purpose'],
            'section': 'main' if spec['page'] <= state['mainCount'] else 'detail',
            'sectionIndex': spec['page'],
            'headline': next((c['text'] for c in authored.get('exactCopy', []) if c['role'] == 'headline'), ''),
        }
        if state.get('designRevision'):
            page['agentDesignRevision'] = state['designRevision']
        result.append(page)
    return result


def normalize_pages(pages, count):
    if not isinstance(pages, list) or len(pages) != count:
        return []
    if any(not isinstance(p, dict) or p.get('visualPipelineVersion') != VERSION for p in pages):
        return []
    if any(type(p.get('page')) is not int for p in pages) or {p['page'] for p in pages} != set(range(1, count + 1)):
        return []
    return sorted(deepcopy(pages), key=lambda p: p['page'])


def compile_pages(pages, base_prompt, brief, suite_key, country, size, count):
    pages = normalize_pages(pages, count)
    if suite_key not in SUITES or not ready_status(pages, count, VERSION)['ready']:
        raise ValueError('动态方案尚未完整，请继续缺页创作')
    # Older clients do not transmit platform; stored input hash is additionally checked by verify_submission.
    for p in pages:
        if p['country'] != country or p['size'] != size:
            raise ValueError('动态方案市场或尺寸已变化，请重新策划')
    return [p['agentPrompt']['resolvedPrompt'] for p in pages], pages


def saved_submission(store, owner, plan_id, payload):
    """Read an owner-scoped checkpoint, without any model calls or new planning."""
    if not isinstance(plan_id, str) or not plan_id:
        raise ValueError('动态方案编号缺失，请重新同步方案')
    state = store.get(owner, 'plan', plan_id)
    if not state:
        raise ValueError('动态方案不属于当前账号或已缺失，请重新策划')
    check_payload = {**payload, 'platform': state['payload'].get('platform', '')}
    check_payload.setdefault('productFacts', state['payload'].get('productFacts', ''))
    for key in ('marketKnowledge', 'marketFeedback'):
        check_payload.setdefault(key, state['payload'].get(key, []))
    from .market_context import read_inputs
    check_payload.update(read_inputs(check_payload))
    # Browser FormData serializes textarea newlines as CRLF; JSON preflight keeps LF.
    # Preserve existing cache hashes, but compare equivalent wire encodings fairly.
    def wire_fingerprint(value):
        brief = raw_brief(value).replace('\r\n', '\n').replace('\r', '\n')
        facts = str(value.get('productFacts') or '').replace('\r\n', '\n').replace('\r', '\n')
        return request_fingerprint({**value, 'suiteBrief': brief, 'prompt': brief, 'productFacts': facts})
    if (state['requestHash'] != request_fingerprint(check_payload)
            and wire_fingerprint(state['payload']) != wire_fingerprint(check_payload)):
        raise ValueError('原始需求、国家或尺寸已变化，请重新策划；产品分析仍可复用')
    return state, pages_from_state(state, state['payload'])


def submission_differences(pages, expected):
    """Only page numbers and field names; never put product prose in error logs."""
    by_page = {p['page']: p for p in expected}
    differences = []
    for page in pages:
        saved = by_page.get(page.get('page'))
        fields = [k for k in ('agentSpec', 'agentPrompt', 'agentInputHash', 'country', 'size')
                  if saved is None or page.get(k) != saved.get(k)]
        if fields:
            differences.append({'page': page.get('page'), 'fields': fields})
    return differences


def verify_submission(store, owner, pages, payload, assets=None):
    if not is_agent(pages):
        return
    plan_ids = {p.get('agentPlanId') for p in pages}
    if len(plan_ids) != 1:
        raise ValueError('动态方案版本混用，请重新同步方案')
    state, expected = saved_submission(store, owner, next(iter(plan_ids)), payload)
    if len(pages) != len(expected):
        raise ValueError('动态页面数量不匹配')
    differences = submission_differences(pages, expected)
    if differences:
        first = differences[0]
        raise ValueError(f"动态页面内容与已保存版本不同：第 {first['page']} 页 {'/'.join(first['fields'])}；请同步已保存方案后重试，本页修改请使用补充要求")
    if assets is not None and sorted(a['assetId'] for a in assets) != sorted(a['assetId'] for a in state['assets']):
        raise ValueError('产品参考图已变化，请先更新产品方案')
