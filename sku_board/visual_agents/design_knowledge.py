"""Local design choices, not fixed page templates or market research claims."""
REVISION = 'commercial-design-v5-rich-visual-execution'
GUIDES = {
    'beauty': (('beauty', 'skincare', 'cosmetic', '美妆', '护肤'), ['texture macro', 'application sequence', 'care routine', 'applicator detail']),
    'supplements': (('supplement', 'nutrition', '保健', '营养'), ['verified ingredients', 'label and serving information', 'daily routine', 'packaging detail']),
    'apparel': (('apparel', 'clothing', 'fashion', '服装', '服饰'), ['fit in motion', 'fabric macro', 'construction details', 'styling', 'verified sizing']),
    'home': (('home', 'household', 'furniture', '家居', '家具'), ['spatial use demonstration', 'installation steps', 'storage', 'material detail', 'verified dimensions']),
    'electronics': (('electronics', 'digital', '3c', '数码', '电子'), ['connection diagram', 'controls close-up', 'use sequence', 'compatibility', 'verified specifications']),
}


def for_product(product):
    categories = product.get('categories') or []
    text = ' '.join(str(x).lower() for x in categories) if isinstance(categories, list) else str(categories).lower()
    return {
        'revision': REVISION,
        'categoryChoices': [{'category': key, 'possibleMethods': methods} for key, (aliases, methods) in GUIDES.items()
                            if any(alias in text for alias in aliases)],
        'selectionRule': 'Choose only methods justified by this product and request, not required pages. For unknown categories reason from actual function and buyer questions.',
        'campaignRule': 'Allocate different buying questions and visual explanations before prompts. No fixed page order, palette or portrait quota. Preserve accurate scale and product structure.',
        'richnessRule': 'Default to finished, visually layered sales artwork, not an isolated catalog cutout with a new heading. Build a dominant benefit scene, a useful supporting demonstration/detail and a clear reading path; these can coexist in one photograph or an independently chosen layout. Specify actual objects, actions, depth, relative scale and positions. Richness means more useful visual explanation, not more repeated products, words, badges or decorative panels. Explicit white-background, minimal or text-free requests take precedence.',
        'marketRule': 'Use selected locale and supplied facts. Distinguish assumptions from research. No invented certifications, reviews, prices, endorsements, mechanisms, tests or result metrics.',
    }


def reference_catalog(product, assets):
    """Reuse cached observations; explicit upload roles win over inferred roles."""
    observed = {r.get('assetId'): r for r in product.get('referenceBreakdown', []) if isinstance(r, dict)}
    result = []
    for asset in assets:
        if asset['role'] == 'style':
            continue
        detail = observed.get(asset['assetId'], {})
        result.append({'assetId': asset['assetId'],
                       'role': detail.get('role', 'product') if asset['role'] == 'auto' else asset['role'],
                       'observations': str(detail.get('observations', ''))[:700]})
    return result
