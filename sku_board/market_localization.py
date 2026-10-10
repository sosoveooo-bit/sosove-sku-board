"""Selected-market art direction shared by COD analysis and image compilation."""
VERSION = 'selected-market-v1-20260912'

# Production suggestions, not mandatory landmarks, ethnic attributes or product facts.
SCENES = {
    'CN': ('a contemporary apartment kitchen in mainland China', 'a neighborhood cafe in mainland China', 'an everyday workplace in mainland China'),
    'KR': ('a contemporary Korean apartment kitchen', 'a Korean neighborhood cafe', 'a Korean everyday workplace'),
    'JP': ('a Japanese apartment with practical compact storage', 'a Japanese neighborhood cafe', 'a Japanese everyday office'),
    'US': ('a US home kitchen with everyday household storage', 'a US neighborhood cafe', 'a US everyday workplace'),
    'GB': ('a UK home with a compact kitchen and ordinary furnishings', 'a UK neighborhood cafe', 'a UK everyday workplace'),
    'DE': ('a German apartment kitchen with practical storage', 'a German neighborhood cafe', 'a German everyday workplace'),
    'HU': ('a Hungarian apartment kitchen with everyday furnishings', 'a Hungarian neighborhood cafe', 'a Hungarian everyday workplace'),
    'PL': ('a Polish apartment kitchen with practical storage', 'a Polish neighborhood cafe', 'a Polish everyday workplace'),
    'ES': ('a Spanish home kitchen in soft daylight', 'a Spanish neighborhood cafe', 'a Spanish everyday workplace'),
    'MX': ('a Mexican home kitchen with everyday furnishings', 'a Mexican neighborhood cafe', 'a Mexican everyday workplace'),
    'FR': ('a French apartment kitchen with practical storage', 'a French neighborhood cafe', 'a French everyday workplace'),
    'CZ': ('a Czech apartment kitchen with everyday furnishings', 'a Czech neighborhood cafe', 'a Czech everyday workplace'),
    'TW': ('a Taiwan apartment kitchen with practical compact storage', 'a Taiwan neighborhood cafe', 'a Taiwan everyday workplace'),
    'HK': ('a Hong Kong apartment with compact everyday storage', 'a Hong Kong neighborhood cafe', 'a Hong Kong everyday workplace'),
    'TH': ('a contemporary Thai home with shaded daylight and practical household furnishings', 'a Thai neighborhood cafe with light everyday furniture', 'a Thai everyday workplace with climate-appropriate casual styling'),
    'VN': ('a contemporary Vietnamese home with practical household storage', 'a Vietnamese neighborhood cafe', 'a Vietnamese everyday workplace'),
    'MY': ('a contemporary Malaysian home with practical household furnishings', 'a Malaysian neighborhood cafe', 'a Malaysian everyday workplace'),
    'SG': ('a Singapore apartment with space-efficient storage', 'a Singapore neighborhood cafe', 'a Singapore everyday workplace'),
    'PH': ('a contemporary Philippine home with practical everyday furnishings', 'a Philippine neighborhood cafe', 'a Philippine everyday workplace'),
    'ID': ('a contemporary Indonesian home with practical everyday furnishings', 'an Indonesian neighborhood cafe', 'an Indonesian everyday workplace'),
}
COPY = {
    'CN': 'Natural Simplified Chinese with vocabulary for mainland China; do not use Traditional Chinese, Japanese or Korean marketing copy.',
    'KR': 'Natural Korean copy with correct Hangul.', 'JP': 'Natural Japanese copy with correct kana and kanji.',
    'US': 'US English spelling and phrasing.', 'GB': 'UK English spelling and phrasing.',
    'DE': 'Natural German with correct umlauts and capitalization.', 'HU': 'Natural Hungarian with correct accents.',
    'PL': 'Natural Polish with correct diacritics.', 'ES': 'Spanish phrasing for Spain, not Mexico.',
    'MX': 'Mexican Spanish phrasing, not Spain-specific usage.', 'FR': 'Natural French with correct accents.',
    'CZ': 'Natural Czech with correct diacritics.', 'TW': 'Traditional Chinese and vocabulary for Taiwan.',
    'HK': 'Hong Kong Traditional Chinese and local written vocabulary, not Taiwan-default copy.',
    'TH': 'Natural Thai script with correct tone marks and vowel placement, no Hangul or Japanese copy.',
    'VN': 'Natural Vietnamese with correct tone marks.', 'MY': 'Malaysian Malay, not Indonesian.',
    'SG': 'Natural English for Singapore, not a US or UK setting.',
    'PH': 'Natural English for Philippine shoppers, not a US or UK setting.',
    'ID': 'Natural Indonesian, not Malaysian Malay.',
}


def direction(profile, page=1):
    code = profile['code']
    index = max(0, int(page or 1) - 1)
    scenes = profile.get('sceneRoster') or SCENES[code]
    scene = scenes[index % len(scenes)]
    roles = ('an individual demonstrating the product naturally', 'an everyday user in a candid practical moment',
             'an adult showing one simple product-specific action')
    roster = profile.get('castingRoster')
    casting = roster[index % len(roster)] if roster else f"{profile['model']}; {roles[index % len(roles)]}"
    instruction = ' '.join([
        f"[Selected-market identity lock — {VERSION}] Selected market={code} ({profile['label']}); added copy language={profile['language']}.",
        'The market selector governs localization. Other countries mentioned as product origins or style references do not change the destination.',
        COPY[code],
        profile.get('copyConvention', ''),
        f'Casting suggestion when a person is needed and no explicit person was supplied: {casting}.',
        f'Scene suggestion: {scene}; adapt to the product and assigned page, vary locations and camera routes across pages.',
        'If people are needed, use locally plausible everyday grooming, clothing and gestures; preserve explicitly supplied person identity and audience age. Do not infer nationality from face shape, impose one ethnicity or skin tone, or add people to product-only pages.',
        'Style references guide composition and lighting, not default casting, foreign signage or domestic settings. Do not default to Korean beauty-editorial or K-pop styling outside KR unless explicitly requested.',
        'Keep exact product, packaging inscriptions, source claims, numbers and use method unchanged. No invented flags, landmarks, costumes, local badges or prices; respect text-free requests.',
        profile.get('avoidCues', ''),
    ])
    return {'casting': casting, 'scene': scene, 'instruction': instruction}


def compact(profile):
    """Short lock for a single hook prompt; full pages use direction()."""
    code=profile['code']; scene=SCENES[code][0]
    return (f'[Selected-market identity lock] Selected market={code} ({profile["label"]}); language={profile["language"]}. '
            f'Use {scene} when needed. Other-country references are style/product context only. '
            f'{COPY[code]} Keep exact product, values and supplied copy; add no flags, landmarks or invented claims.')
