"""Local COD shot allocation and text-only repetition checks; no model calls.

Axes are composition constraints, not ready-made prompts or new product claims.
User-provided geometry/people requirements outrank these automatic choices.
"""
from collections import Counter
from itertools import product
import json
import re

from . import cod_visual_routes

VERSION = 'cod-shot-diversity-v1'
SCALES = {
    'product-proof': ('context-wide', 'evidence-close', 'product-medium'),
    'macro': ('surface-macro', 'contact-close', 'edge-detail'),
    'process': ('operation-close', 'process-medium', 'result-detail'),
    'comparison': ('matched-medium', 'matched-detail', 'matched-wide'),
    'color': ('collection-wide', 'variant-detail', 'collection-medium'),
    'mechanism': ('connection-close', 'structure-medium', 'component-detail'),
    'application': ('use-context-wide', 'contact-close', 'use-medium'),
    'lifestyle': ('interaction-wide', 'interaction-medium', 'interaction-detail'),
    'specification': ('inventory-wide', 'measurement-detail', 'inventory-medium'),
}
VIEWS = ('eye-level-oblique', 'elevated-three-quarter', 'low-product-level')
COPY_ZONES = ('upper-negative-space', 'lower-negative-space', 'lateral-negative-space', 'distributed-proof-labels')


def _visual(page):
    visual = page.get('visualEnhancement')
    return visual if isinstance(visual, dict) else {}


def _canonical(value):
    # Headline, color and typography changes alone are not photographic diversity.
    value = re.sub(r'[“「"].*?[”」"]', '', str(value or '').lower())
    value = re.sub(r'#[0-9a-f]{6}\b|\b(?:red|green|blue|purple|gold|white|yellow)\b', '', value)
    return re.sub(r'\W+', ' ', value).strip()[:2400]


def repeated_designs(pages):
    """Conservative text similarity, not a visual-image similarity score."""
    previous, repeats = [], {}
    for page in pages:
        visual = _visual(page)
        layers = visual.get('companyPromptLayers') or {}
        if not isinstance(layers, dict):
            layers = {}
        fields = [
            _canonical(layers.get('visualNarrative')),
            _canonical(visual.get('camera')),
            _canonical(visual.get('composition') or visual.get('spatialPlan')),
            _canonical(visual.get('actionDirection')),
        ]
        # Linear-size character trigrams also handle CJK text. Avoid quadratic
        # string-diff work when many long cached briefs share repetitive prose.
        grams = [set(value[i:i+3] for i in range(max(0, len(value)-2))) for value in fields]
        for number, other, other_grams in previous:
            similarities = [len(a & b) / max(1, len(a | b)) for a, b in zip(grams, other_grams)]
            same = sum(len(a) >= 16 and len(b) >= 16 and similarity >= .82
                       for a, b, similarity in zip(fields, other, similarities))
            narrative_match = (len(fields[0]) >= 70 and len(other[0]) >= 70 and similarities[0] >= .88)
            if same >= 2 or narrative_match:
                repeats.setdefault(page.get('page'), []).append(number)
        previous.append((page.get('page'), fields, grams))
    return repeats


def contracts(pages):
    """Stable whole-suite allocations, also recomputed for saved plans on dispatch."""
    routes = cod_visual_routes.assignments(pages)
    repeats = repeated_designs(pages)
    used, scale_counts, view_counts, copy_counts = Counter(), Counter(), Counter(), Counter()
    recent = []
    result = []
    for page, route in zip(pages, routes):
        family = route['evidenceFamily']
        choices = list(product(SCALES.get(family, SCALES['product-proof']), VIEWS, COPY_ZONES))

        def penalty(choice):
            scale, view, copy = choice
            return (used[choice] * 200
                    + sum(25 * (scale == old[0]) + 12 * (view == old[1]) + 15 * (copy == old[2])
                          for old in recent[-2:])
                    + scale_counts[scale] * 4 + view_counts[view] + copy_counts[copy])

        selected = min(choices, key=penalty)
        scale, view, copy = selected
        people = ('interaction-required-by-source' if family == 'lifestyle'
                  else 'operation-only' if family in {'process', 'application'}
                  else 'product-led-no-decorative-portrait')
        result.append({
            'version': VERSION, 'page': page.get('page'), 'evidenceFamily': family,
            'shotScale': scale, 'viewpoint': view, 'copyPlacement': copy,
            'peopleIntent': people,
            'differentFromPages': [item.get('page') for item in pages[max(0, len(result)-2):len(result)]],
            'repeatedDesignPages': repeats.get(page.get('page'), [])[:5],
        })
        used[selected] += 1
        scale_counts[scale] += 1
        view_counts[view] += 1
        copy_counts[copy] += 1
        recent.append(selected)
    return result


RULES = (
    'These are per-page composition constraints, not fixed poster templates. '
    'Preserve every assigned source benefit, verified product/variant and approved local-language copy. '
    'Explicit user camera, scene, layout and people instructions take priority; vary only remaining free axes. '
    'Inherited generic scene/pose/layout defaults are editable, not user requirements. '
    'Use the assigned scale to prove THIS source point: close views show its real detail, wide views its actual context. '
    'Choose a plausible setting for the documented use. Keep correct use and product anatomy; '
    'never invent a capability, result, variant, mechanism or before/after proof. '
    'A changed headline, product color or mirrored arrangement alone does not count as a different picture. '
    'Derive foreground/midground/background and believable depth from the subject where relevant; '
    'for macro or flat evidence keep the needed detail sharp instead of adding scenery. '
    'Reserve the assigned copy area naturally, without a forced card, rail or banner; '
    'when text-free ignore copy placement entirely. Preserve supporting benefits without repeating one icon-column layout. '
    'Share product identity, palette and photographic grade, not the same portrait, pot-on-table setup or framing. '
    'Product-led pages exclude decorative full-person portraits; use hands/body contact only if needed to prove correct use. '
    'Do not remove source-required people, apparel wearers or explicit user casting for variety.'
)


def planner_instruction(records, page_numbers):
    wanted = set(page_numbers)
    # Only compact allocations are repeated across batches, not previous prose prompts.
    matrix = [{key: record[key] for key in ('page', 'evidenceFamily', 'shotScale', 'viewpoint', 'copyPlacement', 'peopleIntent')}
              for record in records]
    current = [record for record in records if record['page'] in wanted]
    return ('[COD WHOLE-SUITE SHOT ALLOCATION]\n' + json.dumps(matrix, ensure_ascii=False, separators=(',', ':'))
            + '\n[CURRENT BATCH DIVERSITY CONTRACTS]\n' + json.dumps(current, ensure_ascii=False, separators=(',', ':'))
            + '\n' + RULES
            + ' Realize these choices inside visualNarrative, camera, spatialPlan and layoutAndCopy, not just in page names.')


def render_instruction(contract):
    if not contract:
        return ''
    return ('[COD PAGE VISUAL DIVERSITY — camera/layout correction before rendering]\n'
            + json.dumps(contract, ensure_ascii=False, separators=(',', ':')) + '\n' + RULES
            + ' If the seven-layer draft repeats earlier execution, recompose its camera/framing/copy geometry '
              'to this allocation in this same render. Keep its source meaning and all user locks. '
              'Do not return an explanation or another planning step.')
