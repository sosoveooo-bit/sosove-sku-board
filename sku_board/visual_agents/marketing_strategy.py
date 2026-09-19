from .contracts import required

SCHEMA = {
    'positioning': 'product-specific commercial positioning with brief rationale',
    'purchaseReasons': [{'id': 'R1', 'reason': 'actual buyer motivation', 'sourceIds': []}],
    'conversionPriorities': [{'objective': 'what must be understood', 'sourceIds': []}],
    'emotionalTriggers': [{'emotion': 'desired feeling', 'expression': 'contextual expression'}],
    'objectionResponses': [{'objection': 'purchase concern', 'response': 'source-backed response', 'sourceIds': []}],
    'salesNarrative': [{'objective': 'stage purpose', 'reason': 'why this order for this product'}],
    'assumptions': [],
}


def create(call, context):
    return required(call('strategy',
        'Act as the marketing strategist. Decide why this audience buys THIS product in the selected market/platform. '
        'Use the original source ledger and product facts; do not invent offers, shipping, COD inspection rights, '
        'Read explicit marketKnowledge as dated, scoped, user-supplied evidence, not verified research. '
        'If it is empty state market assumptions rather than claiming a search was performed. '
        'reviews, medical proof or market research. Mark uncertain audience/platform beliefs as assumptions. '
        'Choose conversion priorities and emotions, not a preset sales funnel or image sequence. '
        'This is a sales communication plan, not an evidence-audit report. Missing data and uncertain '
        'claims remain INTERNAL in assumptions; do not make a sales page about "not documented", '
        '"not proven", evidence ledgers or everything the photos fail to establish. Select other useful '
        'supported buying reasons instead. Preserve necessary real consumer warnings, instructions and '
        'delivery limitations. Do not turn a provisional identity hypothesis into the product being sold. '
        'For each buying reason explain how an actual customer would understand or experience its value. '
        'Return concise structured decisions, not repeated product analysis.', context, SCHEMA), SCHEMA, '商品策略')
