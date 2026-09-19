"""Reusable product understanding using the existing director/vision transport."""
from .contracts import PRODUCT_VERSION, digest, required

SCHEMA = {
    'productSummary': 'actual product, construction and correct use, not campaign design',
    'categories': ['category and functional attributes'],
    'facts': [{'id': 'F1', 'statement': 'observed or supplied fact', 'assetIds': [], 'status': 'observed / supplied / uncertain'}],
    'productVisualDNA': {'shape': 'physical form', 'colors': [], 'materials': [], 'identityLocks': []},
    'referenceBreakdown': [{'assetId': 'provided asset id', 'role': 'product / usage / packaging / style / evidence', 'observations': 'what is visible'}],
    'audienceProfiles': [{'id': 'A1', 'description': 'general use needs, distinguish hypotheses', 'purchaseBarriers': []}],
    'consumerPsychology': [{'motivation': 'why useful', 'basis': 'facts or hypothesis'}],
    'coreSellingPoints': [{'customerValue': 'source-backed value', 'factIds': []}],
    'prohibitedVisualDirections': ['product-specific errors to avoid'],
    'missingInformation': [],
}


def cache_key(assets, payload):
    product_assets = [a for a in assets if a['role'] != 'style']
    if not product_assets:
        raise ValueError('请上传至少一张产品或使用参考图；风格图不作为产品依据')
    return digest([PRODUCT_VERSION, str(payload.get('productId') or ''), str(payload.get('skuId') or ''),
                   sorted((a['assetId'], a['role']) for a in product_assets),
                   str(payload.get('productFacts') or '')])


def analyze(call, context, images):
    data = call('product',
        'Analyze the actual product and its correct use from the supplied product references. '
        'Preserve the existing product-identification, reference-breakdown and visual-DNA capabilities. '
        'Separate observed facts from supplied claims and hypotheses. Unknown internals, clinical results, '
        'certificates and numbers stay unknown. Do not design pages or infer campaign colors. '
        'Read the entire userBrief and explicit productFacts as seller declarations, not verified evidence. '
        'Explicit productFacts are the latest seller clarification of identity and delivery contents. '
        'Analyze images AND those declarations; never silently replace a declared living plant with decoration, '
        'or a declared cosmetic with an electrical device based on appearance alone. Record identity, '
        'delivery-form or specification ambiguities in missingInformation, not a separate confirmation workflow. '
        'Do not treat ambiguous facts as established, or commit a provisional alternative as the actual product. '
        'Unverified efficacy/awards also belong in missingInformation. Seller clarification '
        'establishes intended sellable identity, not efficacy, certification, biological performance or proof. '
        'Keep missing-information notes internal. Product names/form/specs matter; country, palette, layout '
        'and image count in userBrief are campaign instructions, not physical product facts. '
        'Do not inherit a reference model identity. Output reusable product intelligence, not country-specific strategy.',
        context, SCHEMA, images)
    required(data, SCHEMA, '产品分析')
    if not isinstance(data['facts'], list) or not data['facts'] or not isinstance(data['productVisualDNA'], dict):
        raise ValueError('产品事实或视觉 DNA 尚未完整')
    ids = [f.get('id') for f in data['facts'] if isinstance(f, dict)]
    if len(ids) != len(data['facts']) or not all(ids) or len(set(ids)) != len(ids):
        raise ValueError('产品事实编号不完整或重复')
    return data


def for_planning(product):
    """Read old caches without the removed confirmation gate; keep uncertainty.

    Do not rewrite product caches or their hashes: saved plans and product
    analysis stay reusable. This is a downstream view, not a new AI analysis.
    """
    result = dict(product)
    assessment = result.pop('identityAssessment', None)
    if isinstance(assessment, dict):
        notes = list(result.get('missingInformation') or [])
        conflicts = assessment.get('conflicts')
        for conflict in conflicts if isinstance(conflicts, list) else []:
            if isinstance(conflict, str) and conflict.strip() and conflict not in notes:
                notes.append(conflict)
        result['missingInformation'] = notes
    return result
