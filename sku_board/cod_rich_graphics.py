"""Rich photographic ecommerce layouts, not borrowed product claims."""
import re
from . import cod_campaign_art

VERSION='cod-country-v33-rich-graphic-types'
TYPES={
    'overview':('综合卖点主图','Exact-product hero with use context, a readable benefit inventory and supporting product details',
        [('HERO','Exact complete product and a relevant user/context if requested','48-56%','DOMINANT'),
         ('SUPPORT','Distinct approved benefits or directly observable features; do not duplicate the headline','14-18%','SUPPORTING'),
         ('PROOF','Two relevant detail/use panels tied to the core and approved support','18-24%','SUPPORTING')]),
    'comparison':('对比矩阵图','Matched comparisons explained through product and use evidence',
        [('PRODUCT','Exact product locator and current difference','18-24%','SUPPORTING'),
         ('MATRIX','One to three matched-condition comparison rows, only for separately supported contexts; if only one is supported use one large pair','48-58%','DOMINANT'),
         ('EXPLAIN','Concise labels explaining the observed difference; chart only with verified comparable values','12-18%','SUPPORTING')]),
    'scenes':('多场景应用图','Different supported uses, not repeated poses in the same room',
        [('PRODUCT','Complete product and concise application overview','18-24%','SUPPORTING'),
         ('SCENES','Three to six distinctly useful local scenes when supported; reduce to the actual number. Each panel must change activity/context, not merely face or angle','50-60%','DOMINANT'),
         ('LABELS','One native-language use label per panel; no invented capability or testimony','10-16%','SUPPORTING')]),
    'material':('材质细节图','Photographic material and construction evidence with useful scale/context',
        [('HERO','Large exact-product or material macro with realistic texture','40-50%','DOMINANT'),
         ('DETAILS','Two or three distinct supplied construction/contact details; no repeat crops passed off as new evidence','24-32%','SUPPORTING'),
         ('LABELS','Part/function annotations or source-backed material comparison; no invented grade, test or numbers','12-18%','SUPPORTING')]),
    'mechanism':('结构原理图','Real product with a clearly subordinate explanatory diagram',
        [('PRODUCT','Exact product photograph preserving physical topology','24-32%','SUPPORTING'),
         ('DIAGRAM','Clearly labelled conceptual mechanism/structure explanation grounded in supplied information; if internals are unknown use an external part/action diagram, not an invented exploded view','34-44%','DOMINANT'),
         ('DETAILS','One or two verified part/contact crops with short explanations','18-24%','SUPPORTING')]),
    'steps':('步骤流程图','Correct operation shown at distinct useful stages',
        [('CONTEXT','Exact product and the actual use setting','24-32%','SUPPORTING'),
         ('STEPS','Two to four real steps supported by usage references; product orientation/contact remain correct in each','38-48%','DOMINANT'),
         ('DETAIL','Important contact/action close-up and a source-backed use condition','18-24%','SUPPORTING')]),
    'parameters':('参数适配图','Readable product information, options and selection guidance',
        [('PRODUCT','Exact product/verified variant inventory at comparable scale','28-36%','SUPPORTING'),
         ('TABLE','Only supplied measurements/specifications/compatibility rows. No age-based prescription, inferred medical advice or invented values','34-44%','DOMINANT'),
         ('DETAIL','Verified fit/part locator or care/contents explanation; omit unknown fields','16-22%','SUPPORTING')]),
}


def select(page):
    source=' '.join(str(page.get(k) or '') for k in ('sourcePointVerbatim','focusTitle','focusDescription','sellingPoint'))
    number=max(1,int(page.get('page') or 1))
    if re.search(r'产品信息|参数表|尺寸表|规格|包装清单|specification',source,re.I):return 'parameters'
    if number==1:return 'overview'
    if re.search(r'对比|前后|before|after|compar',source,re.I):return 'comparison'
    if re.search(r'早晚|日夜|多场景|不同场景|多效|多用|适用人群|morning|night|multi.?use',source,re.I):return 'scenes'
    family=cod_campaign_art.routes([page])[0]['family']
    if re.search(r'原理|结构|机制|胶原|弹力纤维|mechanism|structure|collagen',source,re.I):return 'mechanism'
    if family in {'procedure','routine'}:return 'steps'
    if family in {'texture','durability','lines','tone'}:return 'material'
    if family in {'information','fit','capacity'}:return 'parameters' if family=='information' else 'material'
    if family in {'audience','application'}:return 'scenes'
    # A varied explanation of the assigned point, never a demand to invent comparisons.
    return ('overview','material','steps')[(number-1)%3]


def modules(page):
    kind=select(page);label,description,regions=TYPES[kind]
    source=str(page.get('sourcePointVerbatim') or page.get('focus') or page.get('focusTitle') or '')
    support=page.get('codMainSupportingPoints') or []
    heading={'id':'RICH_HEADLINE','visual':'One strong native-language headline and a short source-backed explanatory line',
        'content':'Current source meaning only; exact supplied native copy wins. Internal Chinese titles are not image text.',
        'position':'10-14%, chosen around visual hierarchy','weight':'SUPPORTING','container':'Integrated full-bleed graphic'}
    result=[heading]
    for name,visual,position,weight in regions:
        result.append({'id':'RICH_'+name,'visual':visual,'position':position,'weight':weight,
            'content':f'Prove the assigned source: {source}. '+
                ('Use only the separate approved supporting inventory.' if support else 'No unlisted additional benefits; use distinct real details of this same source.'),
            'container':f'{label}: {description}. Designed panels may share a background; not a poster mockup.'})
    return result


def guidance(page):
    key=select(page);label,description,_=TYPES[key]
    return (f'[RICH COD GRAPHIC TYPE — {key} / {label}] {description}. '
        'This is one finished ecommerce graphic containing coordinated photographic/diagram panels, not necessarily one photographic exposure. '
        'Follow the listed RICH_* regions; normalize their suggested areas to 100% without overlap. Use native-language headline/subheadline and concise evidence labels, not tiny paragraphs. '
        'Panels of the same claim may show different real contexts, details or conditions. No decorative panel quota: when evidence is limited enlarge the useful material rather than inventing more. '
        'Typography and palette are shared, but not a universal bottom icon rail. Product identity and every source number/condition remain intact. '
        'Explicit text-free, title-only, minimal, single-scene, no-diagram or no-collage instructions override this default. '
        'Technical drawings, arrows and conceptual diagrams are permitted when supported and clearly distinguishable from photographs; product and people remain photorealistic. '
        'Do not borrow the example glasses, Korean copy, 12g/0.03s values, ratings, awards or certification badges. No fabricated clinical results or test data.')
