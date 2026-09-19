"""Bounded, durable page authoring. No model reviewer and no invented pages."""
from . import scene_planner
from .structured_output import StructuredOutputError


def summaries(pages):
    return [{k: p.get(k) for k in ('page', 'purpose', 'sourceIds', 'scene', 'composition', 'visualDesign')}
            for p in pages]


def _indexed(pages, count):
    if not isinstance(pages, list):
        return {}
    indexed, duplicates = {}, set()
    for page in pages:
        if not isinstance(page, dict) or type(page.get('page')) is not int or not 1 <= page['page'] <= count:
            continue
        number = page['page']
        if number in indexed:
            duplicates.add(number)
        indexed[number] = page
    # Incomplete/unindexable drafts remain available for diagnostics, but are
    # not mistaken for authored pages on resume. Other valid pages survive.
    required = set(scene_planner.PAGE_SCHEMA) - {'visualDesign'}
    return {n: p for n, p in indexed.items() if n not in duplicates and required <= set(p)}


def _bounded(numbers, operation, batch_size, resize):
    pending = list(numbers)
    size = max(1, min(8, batch_size))
    while pending:
        batch = pending[:size]
        try:
            operation(batch)
        except StructuredOutputError:
            if len(batch) == 1:
                raise
            size = max(1, len(batch) // 2)
            resize(size)
            continue
        del pending[:len(batch)]


def create(call, context, draft, checkpoint, batch_size=8, resize=lambda size: None):
    count = context['pageCount']
    pages = _indexed(draft, count)

    def generate(numbers):
        existing = [pages[n] for n in sorted(pages)]
        covered = {s for p in existing for s in p.get('sourceIds', []) if isinstance(s, str)}
        candidates = scene_planner.create(call, {
            **context, 'requestedPageNumbers': numbers, 'existingPageSummaries': summaries(existing),
            'uncoveredSourceIds': [s['id'] for s in context['sources'] if s['id'] not in covered],
        })
        if not isinstance(candidates, list):
            raise ValueError('图片规划批次应为页面列表，已有批次已保留')
        ids = [p.get('page') if isinstance(p, dict) else None for p in candidates]
        if (any(type(n) is not int or n not in numbers for n in ids) or len(set(ids)) != len(ids)):
            raise ValueError('图片规划批次页码重复或超出本批范围，已有批次已保留')
        # Commit actual returned PageSpecs before validation; never synthesize a
        # missing page or discard an earlier successful batch.
        pages.update({p['page']: p for p in candidates})
        checkpoint([pages[n] for n in sorted(pages)])
        if set(ids) != set(numbers):
            raise StructuredOutputError('本批图片规划缺页，已保留完整页面；仅补齐本批缺失页')

    def generate_missing(numbers):
        missing = [n for n in numbers if n not in _indexed(list(pages.values()), count)]
        if missing:
            generate(missing)

    _bounded([n for n in range(1, count + 1) if n not in pages], generate_missing, batch_size, resize)
    return [pages[n] for n in sorted(pages)]


def repair(agent, call, context, pages, issues, checkpoint, batch_size=8, resize=lambda size: None):
    current = pages
    by_number = {i['page']: i for i in issues}

    def correct(numbers):
        nonlocal current
        current = agent(call, context, current, [by_number[n] for n in numbers])
        checkpoint(current)

    _bounded(sorted(by_number), correct, batch_size, resize)
    return current
