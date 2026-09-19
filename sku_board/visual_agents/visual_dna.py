"""Compile shared campaign style, not shared scene/pose/layout, without an AI call."""
from .contracts import digest


def lock(direction, country):
    dna = {
        'version': 'visual-dna-v1', 'market': country,
        'palette': direction['colorDirection'],
        'typography': direction['typographyDirection'],
        'castingPolicy': direction['modelStrategy'],
        'photographicLanguage': direction['photographyStyle'],
        'variationPolicy': direction['pageVariationPolicy'],
        'layoutGrammar': 'Consistent typographic hierarchy and readable margins; independently choose each page spatial structure.',
        'scope': 'Shared art direction, not a bitmap master. Casting applies only when a page needs humans. Camera, action, setting, subject scale and composition vary by PageSpec. Preserve physical product colors over campaign colors.',
    }
    dna['id'] = digest(dna)
    return dna
