"""Compile authenticated plan responses without calling a model or changing engine files."""
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
import sys
import json
import hashlib
import threading
import time
from collections import OrderedDict
from copy import deepcopy

COMPILE_VERSION = 'studio-compile-v1-market-lock'
_compiled = OrderedDict()
_compile_lock = threading.RLock()


def load_engine():
    root = str(Path(__file__).resolve().parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)
    from sku_board import backend
    if not callable(getattr(backend, 'build_ai_image_suite_prompts', None)):
        raise RuntimeError('提示词编译入口缺失')
    return backend


def compile_existing_plan(payload):
    engine = load_engine()
    key = payload.get('suiteKey')
    if key not in {engine.AI_IMAGE_COD_SUITE_KEY, engine.AI_IMAGE_COD_DETAIL_SUITE_KEY, engine.AI_IMAGE_LANDING_SUITE_KEY}:
        raise ValueError('创作模式不正确')
    count = payload.get('suiteCount')
    if not isinstance(count, int) or engine.normalize_ai_image_suite_count(key, count) != count:
        raise ValueError('方案页数不正确')
    pages = payload.get('suitePages')
    if not isinstance(pages, list) or len(pages) != count or not all(isinstance(page, dict) for page in pages):
        raise ValueError('逐页方案不完整，请先完成缺页策划')
    country = payload.get('suiteCountry', 'JP')
    if country not in engine.AI_IMAGE_COD_COUNTRY_PROFILES or (key == engine.AI_IMAGE_LANDING_SUITE_KEY and country != 'JP'):
        raise ValueError('目标市场不正确')
    if any(page.get('country') and page['country'] != country for page in pages):
        raise ValueError('方案市场与当前选择不一致，请先更新市场方案')
    fields = {name: payload.get(name, '') for name in ('prompt', 'suiteBrief')}
    if any(not isinstance(value, str) or len(value) > 64000 for value in fields.values()):
        raise ValueError('原始需求格式或长度不正确')
    result = {name: payload.get(name) for name in ('suiteKey','suiteCount','suitePages','suiteCountry','suitePlanVersion','size')}
    result['suiteCountry'] = country
    result['size'] = payload.get('size') or engine.ai_image_suite_config(key)['size']
    if result['size'] != engine.ai_image_suite_config(key)['size']:
        raise ValueError('画布尺寸与当前板块不一致')
    result['ok'] = True
    result['companyPromptStatus'] = engine.ai_image_company_prompt_status(pages, count, key)
    if not result['companyPromptStatus']['ready']:
        raise ValueError('线上七层提示词尚有缺页，请先完成缺页策划')
    return enrich_plan(result, fields)


def compile_key(result, fields):
    payload = [COMPILE_VERSION, fields.get('prompt', ''), fields.get('suiteBrief', ''),
               result['suiteKey'], result['suiteCount'], result.get('size', '750x1000'),
               result.get('suiteCountry', 'JP'), result.get('suitePlanVersion'), result['suitePages']]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def text_fields(content_type, body):
    message = BytesParser(policy=default).parsebytes(
        ('Content-Type: ' + content_type + '\r\nMIME-Version: 1.0\r\n\r\n').encode() + body)
    fields = {}
    for part in message.iter_parts():
        name = part.get_param('name', header='content-disposition')
        if name and not part.get_filename():
            fields[name] = (part.get_payload(decode=True) or b'').decode('utf-8')
    return fields


def enrich_plan(result, fields, engine=None):
    if not result.get('ok') or not result.get('companyPromptStatus', {}).get('ready'):
        return result
    started = time.perf_counter()
    # Do not share cache entries with injected test/custom compilers.
    cacheable = engine is None
    key = compile_key(result, fields) if cacheable else None
    with _compile_lock:
        cached = _compiled.get(key) if cacheable else None
        if cached is not None:
            _compiled.move_to_end(key)
            result.update(deepcopy(cached))
            result['studioCompileCacheHit'] = True
            result['studioCompileMs'] = round((time.perf_counter() - started) * 1000)
            return result
    if engine is None:
        engine = load_engine()
    prompts, pages = engine.build_ai_image_suite_prompts(
        fields.get('prompt', ''), fields.get('suiteBrief', ''), result.get('size', '750x1000'),
        suite_key=result['suiteKey'], plan=result['suitePages'], has_style_anchor=False,
        country=result.get('suiteCountry', 'JP'), suite_count=result['suiteCount'])
    ready = engine.ai_image_company_prompt_status(pages, result['suiteCount'], result['suiteKey'])
    if not ready['ready'] or len(prompts) != len(pages):
        raise ValueError('完整方案编译后出现缺页，请续写方案后重试。')
    result['studioPromptPreview'] = [
        {'page': page['page'], 'prompt': prompt} for page, prompt in zip(pages, prompts)]
    result['studioCompiledReady'] = True
    result['studioPromptNote'] = '实际编译的逐页基础提示词；节点提交时仍会追加模型适配和参考图约束。'
    result['studioCompileCacheHit'] = False
    result['studioCompileMs'] = round((time.perf_counter() - started) * 1000)
    if cacheable:
        with _compile_lock:
            _compiled[key] = deepcopy({name: result[name] for name in
                ('studioPromptPreview', 'studioCompiledReady', 'studioPromptNote')})
            _compiled.move_to_end(key)
            while len(_compiled) > 8:
                _compiled.popitem(last=False)
    return result
