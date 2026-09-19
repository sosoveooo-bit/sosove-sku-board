"""Reference-informed evidence art direction for COD country suites only.

Learn layout relationships, not the reference campaign's claims or product.
"""
import json
import re
from collections import Counter

KEY = 'cod-country-landing-30'
VERSION = 'cod-country-v33-rich-graphic-types'
PRODUCT_FIELDS = ('productSummary', 'productCategory')
CATEGORIES = (
    ('pet', r'宠物|猫粮|狗粮|狗狗|猫咪|\b(?:pet|dog|cat)\b', 'Show correct pet-product scale and a calm supervised interaction only if relevant; no animal health outcomes or human-use substitution.'),
    ('baby', r'婴儿|婴幼儿|奶瓶|婴童|\b(?:baby|infant|stroller)\b', 'Show verified construction, caregiver handling and age-appropriate context; no unsupported safety/development promises or unsafe use.'),
    ('apparel', r'服装|衣服|连衣裙|连体裤|衬衫|西装|外套|文胸|裤子|内衣|袜子|鞋子|\b(?:dress|blazer|shirt|jumpsuit|trousers|garment|apparel|shoes|bra)\b', 'Show the exact garment fit, seams, closures, drape and fabric response through worn full/medium shots and construction macros. Preserve body proportions and all garment topology.'),
    ('kitchen', r'厨房|厨具|拧盖器|开瓶器|锅具|炒锅|刀具|切菜|餐具|保鲜盒|\b(?:kitchen|cookware|jar opener|bottle opener|pan|cutlery)\b', 'Show correct grip, contact geometry, supported food/container and the practical action. Use structure and material close-ups; no invented leverage ratios or impossible operation.'),
    ('beauty', r'护肤|精华|护理棒|面霜|化妆|美容|卸妆|润肤|肌肤|皮肤|ครีม|บำรุงผิว|スキンケア|美容液|\b(?:skincare|serum|cosmetic|moisturizer|skin cream|cream stick)\b', 'Show the exact applicator, texture, correct contact/application and realistic skin. Preserve natural pores and tone; do not turn a cosmetic into an electrical or medical device.'),
    ('wellness', r'按摩器|护腰|护膝|矫姿|保健品|营养补充|\b(?:massager|supplement|knee brace|posture corrector)\b', 'Show ergonomic fit, exact contact/use position and observable comfort context; no invented medical anatomy, cure, certification or recovery timeline.'),
    ('electronics', r'耳机|充电器|音箱|摄像头|手机支架|智能手表|数据线|电池|\b(?:earbuds|headphones|charger|speaker|camera|smartwatch|electronics)\b', 'Show exact controls, ports, connectors and real supported interaction; explain functions using supplied specifications, not invented displays, compatibility or battery life.'),
    ('household', r'家居|收纳|清洁|拖把|床品|枕头|窗帘|家具|除尘|\b(?:storage|mop|bedding|pillow|curtain|furniture|cleaning)\b', 'Show the actual room/use zone, scale, arrangement and material or cleaning contact; comparisons use the same scene and only documented results.'),
    ('outdoor', r'户外|露营|帐篷|登山|运动器材|健身|骑行|\b(?:camping|tent|outdoor|fitness|cycling)\b', 'Show supported outdoor/fitness use, handling and construction details; no unverified weather extremes, impact ratings or performance outcomes.'),
    ('accessory', r'饰品|项链|戒指|手链|耳环|手提包|背包|\b(?:jewelry|necklace|ring|bracelet|handbag|backpack)\b', 'Show actual proportions, finish, clasp, compartments and on-body scale as relevant; preserve verified material and color, no invented precious-metal grading.'),
    ('food', r'食品|零食|咖啡豆|茶叶|饼干|\b(?:snack|coffee beans|tea leaves|biscuits|food)\b', 'Show verified packaging, portion, texture and serving context; ingredients, nutrition and origin come only from supplied facts.'),
)
GENERIC_RULES = (
    ('information', r'产品信息|规格|参数|尺寸表|包装清单|specification', 'A readable source-backed specification or inventory layout; omit unknown values.'),
    ('procedure', r'使用方法|步骤|安装|操作|搭配|流程|\b(?:step|installation|operation)\b', 'A close correct-use sequence with exact contact, orientation and scale.'),
    ('comparison', r'对比|前后|\b(?:before|after|comparison)\b', 'A matched-condition comparison of the supported difference; no invented outcomes or altered body/scene.'),
    ('mechanism', r'原理|结构|机制|杠杆|\b(?:mechanism|structure|lever)\b', 'A product-led structural explanation tied to visible parts; use cutaways only when supported, never invented internals.'),
    ('texture', r'材质|面料|触感|纹理|柔软|弹力|弹性|\b(?:fabric|texture|material|stretch|elastic)\b', 'A real material/contact macro and controlled handling demonstration; preserve weave, texture and realistic deformation.'),
    ('fit', r'版型|显瘦|垂坠|落肩|腰线|穿着|\b(?:fit|drape|silhouette)\b', 'Show actual product fit and silhouette at useful full and detail scales; no body reshaping or false size improvement.'),
    ('handling', r'省力|省时|防滑|握持|便捷|\b(?:grip|effort|convenient|non-slip)\b', 'One clear correct-use action emphasizing grip, force direction or fewer verified steps, plus a contact detail.'),
    ('capacity', r'收纳|容量|空间|便携|\b(?:capacity|portable|compact)\b', 'Show verified objects fitting, folding or storage in a real-scale arrangement; no invented capacity or dimensions.'),
    ('durability', r'耐用|耐磨|防水|防摔|\b(?:durable|waterproof|resistant)\b', 'Show construction and the supported use condition; no destructive/extreme test, rating or test count without evidence.'),
    ('function', r'功能|充电|续航|连接|兼容|\b(?:function|charging|battery|compatible)\b', 'Show the exact supported function through real interfaces or connectors; no invented specification or decorative fake UI.'),
    ('simplification', r'多效|合一|精简|多用|\bmultifunction\b', 'A complete product with distinct verified uses/benefits; the exact item, not several invented variants.'),
    ('routine', r'早晚|日夜|晨间|夜间|\b(?:morning|night)\b', 'Two supported time-of-day use contexts with different lighting and actions; no implied new performance.'),
    ('audience', r'适用|人群|年龄|友好|\b(?:audience|suitable)\b', 'A plausible selected-market use context for the stated audience; add people only when useful to this evidence.'),
)
RULES = (
    ('information', r'产品信息|规格|参数|净含量|包装清单|specification', 'A readable verified-information panel with an exact product inventory; omit unknown values.'),
    ('routine', r'早晚|日夜|晨间|夜间|morning|night', 'A matched morning/evening routine diptych; distinct light and action, same product. Do not imply SPF or UV protection without evidence.'),
    ('procedure', r'使用方法|步骤|涂抹|搭配|流程|step|routine', 'A correct-use sequence with action close-ups; applicator orientation and contact match usage references.'),
    ('texture', r'清爽|吸收|黏|质地|触感|texture|absorb', 'A dominant product-texture/contact macro with a practical application view; preserve realistic surface texture, no invented absorption seconds.'),
    ('contour', r'紧致|提拉|松垮|下颌|轮廓|firm|lift', 'A face-contour close-up and correct application crop when this is skincare; otherwise the actual product-specific contour proof. Never reshape anatomy to simulate measured results.'),
    ('tone', r'焕亮|匀肤|暗沉|肤色|bright|skin.tone', 'Matched-light surface or complexion detail plus application context. Preserve natural skin tone, no whitening filter or fabricated progress timeline.'),
    ('lines', r'细纹|干纹|皱纹|纹理|wrinkle', 'A tight target-area detail with realistic pores and a smaller exact-use crop; no airbrushed skin or invented treatment outcome.'),
    ('mechanism', r'胶原|弹性|弹力|原理|结构|机制|collagen|elastic|mechanism', 'Product-led explanation with a subordinate clearly labelled conceptual diagram only where the source supports it; distinguish illustration from measured clinical evidence.'),
    ('simplification', r'多效|合一|精简|替代|multi.function', 'One complete product hero surrounded by distinct supplied benefits or a source-supported routine comparison; no extra bottles or made-up functions.'),
    ('audience', r'温和|熟龄|人群|年龄|友好|sensitive', 'A credible local everyday user/application portrait with a concise suitability explanation; no invented safety certification, zero-irritation promise or user testimonial.'),
    ('comparison', r'对比|前后|before|after', 'A balanced two-panel comparison under matched light, camera and conditions; results require evidence and must not be simulated as clinical proof.'),
)
TOPOLOGIES = ('dominant evidence photograph with a narrow side detail',
              'large close-up with a restrained lower explanation strip',
              'asymmetric hero and two small supporting evidence crops')
EVIDENCE_LAYOUTS = {
    'procedure': ('large active-use frame with sequential close-up steps', 'horizontal step sequence beneath the main operation view', 'vertical correct-use progression beside a complete product'),
    'comparison': ('matched side-by-side panels with one shared condition label', 'matched top/bottom panels at the same scale', 'one large evidence pair with a small reference-condition strip'),
    'information': ('complete product inventory beside a readable specification table', 'large product locator above grouped verified specification rows', 'verified contents lineup and clearly grouped care information'),
    'texture': ('dominant material macro with a smaller handling context', 'large contact-action crop with an exact texture detail alongside', 'complete product at supporting scale beside a large surface study'),
    'fit': ('full worn silhouette with one exact construction detail', 'matched front and side fit views with restrained labels', 'movement hero plus a fabric drape crop'),
    'mechanism': ('large actual structure close-up with source-supported part labels', 'exact product view and subordinate clearly marked explanatory diagram', 'action/contact frame with a supported structure detail'),
    'capacity': ('real-scale contents arrangement and full product opening', 'supported folded/open states shown at matched scale', 'actual storage scene with a close view of the relevant compartment'),
}


def category(pages, product_context='', analysis=None):
    analysis = analysis if isinstance(analysis, dict) else {}
    # Explicit online product summary takes precedence over advertising references.
    sources = [' '.join(str(analysis.get(k) or '') for k in PRODUCT_FIELDS), str(product_context or ''),
               ' '.join(str(p.get(k) or '') for p in pages for k in ('sourcePointVerbatim','focusTitle','focusDescription'))]
    for source in sources:
        matches = [(name, direction) for name,pattern,direction in CATEGORIES if re.search(pattern,source,re.I)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            # Ambiguous input should be resolved by the vision director, never first-match guessing.
            return 'mixed', 'Resolve the actual product from its reference-labelled facts; select evidence per product without blending categories or inventing functions.'
    return 'generic', 'Use directly observed product facts and the current source point; choose an informative actual use/material/detail proof, not a borrowed category template.'


def routes(pages, product_context='', analysis=None):
    product_category, _ = category(pages, product_context, analysis)
    counts = Counter()
    result = []
    for i, page in enumerate(pages):
        # Exclude inherited scene/role wording so a template cannot determine the benefit.
        source = ' '.join(str(page.get(k) or '') for k in ('sourcePointVerbatim','focusTitle','focusDescription','sellingPoint'))
        family, evidence = 'product-proof', 'Show the current benefit through its actual product/use detail, not a decorative held-product portrait.'
        for name, pattern, direction in (RULES if product_category=='beauty' else GENERIC_RULES):
            if re.search(pattern, source, re.I):
                family, evidence = name, direction
                break
        occurrence = counts[family]; counts[family] += 1
        result.append({'page':page.get('page',i+1),'sourcePointIndex':page.get('sourcePointIndex'),
            'productCategory':product_category,
            'family':family,'evidence':evidence,'variation':occurrence+1,
            'layoutSuggestion':EVIDENCE_LAYOUTS.get(family,TOPOLOGIES)[(max(1,int(page.get('page') or i+1))-1) % 3],
            'tonalRole':'deep product-derived explanatory background' if family=='mechanism' else
                        'calm high-contrast information background' if family=='information' else
                        'bright product-derived photographic background'})
    return result


def instruction(pages, suite_key, product_context='', analysis=None):
    if suite_key != KEY:
        return ''
    product_category, category_direction = category(pages,product_context,analysis)
    return '\n'.join((
        '[COD COUNTRY CAMPAIGN ART DIRECTION — '+VERSION+']',
        'Create a connected sales story in the existing page order and source-point assignments, not a repeated poster template. '
        'Each page must connect its exact source claim to a visible evidence subject and one clear headline. '
        'Use the following suggestions only when compatible with this actual product; the AI director still authors the photograph.',
        f'[Product-specific visual vocabulary] Category suggestion={product_category}. {category_direction}',
        json.dumps(routes(pages,product_context,analysis),ensure_ascii=False,separators=(',',':')),
        'First hero: strong product/application impression plus a concise benefit cluster. '
        'Other main images: follow the assigned rich-graphic modules. One dominant visual group may contain multiple related evidence panels; '
        'and 3–5 DISTINCT approved supporting labels only when that many exist. Never count the headline as a support label. '
        'Detail images: develop one source point using a close-up, correct-use sequence, matched comparison or explanation; not every page needs insets or icons. '
        'Choose the layout topology around the evidence instead of forcing a fixed top-title/bottom-icon grid. '
        'Write evidence placement into visualNarrative and layoutAndCopy; retain seven complete layers without adding a new analysis pass. '
        'When RICH_* modules are assigned, one finished image means one designed ecommerce page, not a single exposure. Scene mosaics, matched comparison matrices and supported explanatory diagrams are valid; do not collapse them into a portrait and headline.',
        'Keep product identity, package graphics, typography family and supplied HEX colors fixed. Vary light/dark tonal roles only within the permitted palette; '
        'explicit background or no-text requirements override these suggestions. Use a bold offer section only if an actual offer was supplied. '
        'Vary camera distance, use action, evidence scale and product location across adjacent pages; no page-1 bitmap anchor. '
        'No automatic blue/gold palette, mandatory faces, borrowed brand names, black censor blocks or empty poster bands.',
        'Reference images demonstrate graphic craft, not proof of claims. Never invent or copy doctor credentials, certificates, ratings, '
        'clinical percentages, before/after outcomes, effect durations or prices. Unsupported mechanism claims may be explained as claims, '
        'not fabricated scientific proof. Preserve the complete original product/benefit text for traceability; do not turn it into extra facts. '
        'Respect the selected market and explicit person references; use realistic skin and hands rather than changing ethnicity or anatomy to match an ad.'
    ))
