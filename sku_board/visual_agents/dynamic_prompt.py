from .contracts import required


def create(call, context):
    data = call('prompts',
        'Act as the dynamic image prompt author. Independently write an executable image-generation instruction '
        'for EACH supplied PageSpec, not one base prompt with substituted labels. Realize the actual purpose, '
        'evidence, action, spatial layout and copy hierarchy from that page. Preserve product identity and the '
        'shared visualDNA (palette, typography, casting policy and photographic language) exactly; do not '
        'invent a new campaign style per page. Casting is conditional on this page needing people. '
        'Never copy another page composition or render the DNA ID as text. Exact visible copy must be in the '
        'selected locale, concise, and supported by the referenced original claims. Literal Latin brand/product '
        'names explicitly documented in productIdentity may retain original spelling as role=label; all '
        'headlines and support sentences must use the selected language. If repairFeedback is supplied, '
        'correct only those validation errors in the supplied draft; preserve the page design. Put the exact visible '
        'wording in exactCopy; in creativeInstruction specify its placement and hierarchy by role (headline/support/label). '
        'The compiler appends exactCopy verbatim to the final image prompt; duplicating those strings in the scene '
        'description is unnecessary. Do not introduce alternate wording in creativeInstruction. '
        'Each exactCopy.sourceIds must be a subset of THAT page sourceIds, '
        'not factIds, page numbers or a neighboring page sourceIds. For an explicitly text-free page return an empty exactCopy array. '
        'No reference numbers, source IDs, planning labels, fake certificates, prices or unsupported metrics on '
        'the image. State concrete product-specific exclusions, not long generic prompt boilerplate. '
        'Start with the page visual hook and composition, then exact copy, reference use, shared style and exclusions. '
        'Realize visualDesign, not metadata labels. '
        'Start from buyingReason and benefitVisualization; implement the explicit informationHierarchy. '
        'Preserve the planned supporting visuals, actions and spatial layers, not just the hero object and '
        'headline. Describe each useful detail position, relative scale and relationship to the focal benefit. '
        'Do not collapse a rich scene, comparison or sequence into a single centered packshot. Richness is '
        'visual storytelling, not filler text, repeated products or invented proof badges. Honor explicit '
        'minimal, white-background and text-free decisions in the PageSpec. '
        'Do not render internal analysis, unknown-field lists or phrases such as "nicht dokumentiert", '
        '"Nicht belegt", "supported by images" or evidence-audit headings. Such notes are for the operator. '
        'Use buyer-facing supported value statements, not a poster explaining missing evidence. Keep actual '
        'consumer warnings, instructions and material purchase limitations when relevant. '
        'Aim for 1200-3500 characters per page, retaining essential page instructions but excluding unrelated '
        'campaign rules. Reserve readable text space at the requested size; '
        'never shrink the finished poster into an inset. Return only requested pages. Do not redesign strategy.', context,
        {'pages': [{'page': 'requested integer', 'creativeInstruction': 'complete independent image instruction',
                    'exactCopy': [{'text': 'exact native text', 'role': 'headline/support/label', 'sourceIds': []}],
                    'negativeInstructions': []}]})
    return required(data, ('pages',), '动态 Prompt')['pages']
