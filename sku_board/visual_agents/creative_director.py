from .contracts import required

SCHEMA = {
    'visualTheme': 'distinct concept with commercial rationale',
    'colorDirection': {'palette': [], 'rationale': '', 'tonalRange': ''},
    'typographyDirection': 'native-language hierarchy and readability',
    'modelStrategy': 'whether/where people help; audience, actions, realistic skin; not mandatory portraits',
    'sceneStrategy': 'product-specific settings, activities and evidence',
    'photographyStyle': 'light, material and camera intentions',
    'representationStrategy': [{'method': 'free-form expressive method', 'appropriateFor': '', 'requiredEvidence': ''}],
    'campaignInvariants': [],
    'pageVariationPolicy': 'what must differ versus what must stay consistent',
}


def create(call, context, images=None):
    return required(call('direction',
        'Act as an ecommerce creative director. Make new visual decisions from this product and strategy. '
        'Do not choose a fixed category template or page-number rotation. Follow designKnowledge.richnessRule: '
        'unless explicitly requesting minimal or catalog photography, design finished layered sales artwork. '
        'Build a dominant benefit visual plus meaningful supporting detail and a clear reading path. Choose '
        'scene depth, use/evidence panels, macro photography or diagrams for actual buying questions; never a decorative quota. '
        'Keep physical product identity and explicit user requirements. Share typography/palette, not scene/pose/layout. '
        'Use designKnowledge as optional category expertise and reference observations as factual material. '
        'For each representationStrategy explain the buying question it answers and when it would be unsuitable. '
        'Design a hierarchy with a strong focal idea and useful supporting detail, not isolated product-plus-portrait '
        'repeated throughout. A focused macro still needs visible material/functional detail and scale context, '
        'not an empty background. Vary scene-led, action-led and explanatory pages without a prescribed order. '
        'Choose color from the campaign, not automatic blue-white or black-gold. Localize context without national stereotypes. '
        'Design sales communication, not a catalog of unknown information. Translate a buying reason into '
        'an observable action, contextual benefit, useful detail or supported comparison. Vary camera distance, '
        'subject scale and information hierarchy, not just backgrounds. Keep operator-only audit notes out '
        'of visible art. Necessary instructions and real limitations remain legible. '
        'Reference craft is not evidence of claims. No generated first-image bitmap anchor.', context, SCHEMA, images), SCHEMA, '视觉导演')
