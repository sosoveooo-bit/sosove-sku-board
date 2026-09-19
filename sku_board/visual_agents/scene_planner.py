from .contracts import required

PAGE_SCHEMA = {
    'page': 'integer in requested range', 'purpose': 'specific question answered and expected takeaway',
    'userPsychology': 'current concern and desired understanding', 'sourceIds': ['original source ids'],
    'factIds': ['product fact ids'], 'scene': 'actual subject/activity/setting or product-led explanation',
    'composition': 'dominant visual, useful secondary detail, actual spatial positions and relative scale; independently designed',
    'copyDirection': 'native-language headline and supporting-message intent; obey explicit no-text instructions',
    'evidenceMethod': 'specific source-backed method, not generic proof',
    'referenceAssetIds': ['provided asset ids'], 'difference': 'concrete difference from neighboring pages',
    'visualDesign': {
        'primarySubject': 'product / person / detail / environment / diagram',
        'method': 'hero / demonstration / macro / comparison / sequence / diagram / montage / specification',
        'layoutFamily': 'single / split / grid / layered / editorial',
        'humanRole': 'none / hands / contextual / portrait',
        'visualHook': 'concrete visual idea explaining this benefit, not a heading',
        'referenceReason': 'why selected assets support this view',
        'buyingReason': 'specific purchase question or benefit this page addresses',
        'benefitVisualization': 'what action, relationship or visible detail explains that value',
        'informationHierarchy': ['specific focal scene and relative space', 'supporting detail/action and position', 'copy placement and reading order if text is allowed'],
    },
}


def create(call, context):
    data = call('planning',
        'Plan all requested page numbers for this batch ONLY as part of one connected but visually varied sales story. '
        'When requestedPageNumbers is supplied, return exactly those page numbers. pageCount is the total campaign '
        'length, NOT the number to output now. Use existingPageSummaries for continuity and avoid repeating them. '
        'Prioritize uncoveredSourceIds where relevant, especially in the final batch, while honoring the full story. '
        'Each page must have its own '
        'purpose, buyer psychology, scene, composition and copy direction. First imagine the finished page. '
        'Use visualDesign to record actual subject, method, layout and human role, not synonyms disguising '
        'the same portrait. Avoid three consecutive identical subject/method/layout combinations unless '
        'explicitly requested as a uniform series. Select minimum sufficient assets by their observations: '
        'detail for macros, usage for actions, packaging for packaging. Do not attach all by default. '
        'Respect visualDNA palette/typography/photographic language without duplicating a fixed layout. '
        'Do not fill a fixed page-role template. '
        'Cover every original selling-point source. Repeated benefits need a different useful explanation, not a new '
        'claim. Choose product-only pages when useful. Do not require a portrait or fixed panels on every page. '
        'Honor requested main/detail counts, language, size and text policy. Return concise complete PageSpecs; '
        'Use concise English for internal planning fields, reserving the selected language for copyDirection. '
        'Budget about 150-200 words per page overall; each decision is one short sentence and hierarchy '
        'is 2-4 short placement instructions, not repeated campaign rules. '
        'do not write long image prompts yet. Refer only to supplied source/fact/asset ids. '
        'For every visualDesign supply buyingReason, benefitVisualization and informationHierarchy. '
        'Use the existing scene/composition/hierarchy fields to make richness executable: name the foreground '
        'subject or action, useful context or detail, spatial placement and relative scale. Unless explicitly '
        'minimal, avoid empty product-on-background layouts. Support the focal benefit with an explanatory '
        'close-up, real use interaction, source-backed comparison or contextual relationship; select what '
        'actually helps, not a fixed panel count. One rich photographic scene can suffice. The main image '
        'must remain dominant and text readable; detail pages can focus on one topic without becoming empty. '
        'A change of hue, scenery or title around the same centered product is not sufficient variation. '
        'Explain how the image makes the value understandable; a static product shown again with a new '
        'heading is not a new idea. Choose a useful visual proof or experience without fabricated claims. '
        'Missing-information lists and internal evidence audits stay in the operator panel, never become '
        'page topics or public copy. Plan valuable supported topics instead; retain genuine usage warnings. '
        'referenceAssetIds are the actual image-generation inputs: use product/usage/detail/packaging assets, '
        'not style/layout/scene-only references. Style references inform text direction only. '
        'EVERY page must include at least one sourceIds entry and one referenceAssetIds entry. '
        'Copy ids exactly from the input; never leave either list empty, including hero or CTA pages. '
        'sourceIds means traceability to the user request, NOT proof that a user claim is true. '
        'When a supplied claim conflicts with observed facts, explain that limitation in evidenceMethod '
        'and use a grounded visual direction; do not present unsupported claims as verified facts.',
        context, {'pages': [PAGE_SCHEMA]})
    return required(data, ('pages',), '图片规划')['pages']


def repair_contract(call, context, pages, issues):
    """One bounded correction of malformed PageSpecs, not an extra review stage."""
    numbers = {i['page'] for i in issues}
    data = call('planning',
        'Repair ONLY the listed PageSpec contract errors. Return complete PageSpecs for requested page numbers only. '
        'Keep existing creative decisions and valid references unless the listed issue requires a change. '
        'Every page needs nonempty sourceIds and referenceAssetIds using exact supplied ids. '
        'factIds may be empty when no established fact applies. Select product images by their observations, '
        'never style-only references. Do not attach all images by default. '
        'A sourceId traces the user request; it does NOT certify its claims. Preserve this distinction in '
        'evidenceMethod and do not invent efficacy, certifications, product properties or source evidence. '
        'Address all listed issues, including missing text fields, with concise concrete decisions.',
        {**context, 'pagesToRepair': [p for p in pages if p['page'] in numbers], 'issues': issues,
         'otherPages': [{'page': p['page'], 'sourceIds': p.get('sourceIds'),
                         'purpose': p.get('purpose'), 'visualDesign': p.get('visualDesign')}
                        for p in pages if p['page'] not in numbers],
         'allowedReferences': {'sourceIds': [s['id'] for s in context['sources']],
                               'factIds': [f['id'] for f in context['product']['facts']],
                               'referenceAssetIds': [a['assetId'] for a in context['assets']
                                                     if a['role'] not in {'style', 'layout', 'scene'}]}},
        {'pages': [PAGE_SCHEMA]})
    replacements = required(data, ('pages',), '规划引用修正')['pages']
    if (not isinstance(replacements, list) or len(replacements) != len(numbers)
            or any(not isinstance(p, dict) or type(p.get('page')) is not int for p in replacements)
            or {p['page'] for p in replacements} != numbers):
        raise ValueError('引用修正页码不匹配，原规划草稿已保留')
    lookup = {p['page']: p for p in replacements}
    return [lookup.get(p['page'], p) for p in pages]


def repair(call, context, pages, issues):
    numbers = {issue['page'] for issue in issues}
    data = call('planning',
        'Repair ONLY listed page designs before rendering. Keep page numbers and sourceIds. '
        'Change actual visual explanations or spatial structures, not just labels. Avoid repeating other pages. '
        'No fixed page rotation. Return complete PageSpecs for requested pages only.',
        {**context, 'pagesToRepair': [p for p in pages if p['page'] in numbers], 'issues': issues,
         'otherPages': [{'page': p['page'], 'purpose': p['purpose'], 'visualDesign': p.get('visualDesign'),
                         'scene': p['scene'], 'composition': p['composition']}
                        for p in pages if p['page'] not in numbers]}, {'pages': [PAGE_SCHEMA]})
    replacements = required(data, ('pages',), '局部设计修正')['pages']
    if (not isinstance(replacements, list) or len(replacements) != len(numbers)
            or any(not isinstance(p, dict) or type(p.get('page')) is not int for p in replacements)
            or {p['page'] for p in replacements} != numbers):
        raise ValueError('局部修正页码不匹配，原规划已保留')
    lookup = {p['page']: p for p in replacements}
    for page in pages:
        if page['page'] in lookup and lookup[page['page']].get('sourceIds') != page['sourceIds']:
            raise ValueError('局部修正应保留原卖点引用')
    return [lookup.get(p['page'], p) for p in pages]
