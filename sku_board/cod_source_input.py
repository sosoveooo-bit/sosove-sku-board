"""Conservative unnumbered heading/paragraph intake for country suites."""
import re

CONTROL = re.compile(r'^(?:依据|根据|请|要求|需要|输出|尺寸|文案|背景|配色|字体|风格|目标|模特|人物|禁止|不要|不出现|不能|权威背书|认证|设计要求|全局要求|主图|详情图|轮播图|图片|\[|【|\d+\s*[.、)）])')


def unnumbered_points(value):
    lines = [line.strip() for line in str(value or '').replace('\r\n','\n').split('\n') if line.strip()]
    def heading(line):
        return 2 <= len(line) <= 60 and not CONTROL.search(line) and not re.search(r'[。！？.!?；;：:]$',line)
    records=[];i=0
    while i+1<len(lines):
        title=lines[i];description=lines[i+1]
        if not heading(title) or CONTROL.search(description) or not (len(description)>len(title) and re.search(r'[。.!！?？]$',description)):
            i+=1;continue
        body=[description];i+=2
        while i<len(lines) and not CONTROL.search(lines[i]) and not heading(lines[i]):
            body.append(lines[i]);i+=1
        detail='\n'.join(body)
        records.append({'kind':'main' if len(records)<5 else 'detail','title':title,'description':detail,
                        'sourceVerbatim':title+'\n'+detail,'sourceType':'selling_point','unnumberedPair':True})
    # Require repeated structure, not a random short line followed by prose.
    return records if len(records)>=2 else []


def localized_copy(value, country):
    value=str(value or '').strip()
    if not value or re.search(r'本土化\s*[·:：]|SOURCE_HEADLINE|PRIMARY_PROOF|VISUAL_EVIDENCE|待翻译|待生成',value,re.I):return False
    if country not in {'CN','JP','TW','HK'} and re.search(r'[\u3400-\u9fff\u3040-\u30ff]',value):return False
    if country=='CN' and re.search(r'[\u3040-\u30ff]',value):return False
    if country!='KR' and re.search(r'[\uac00-\ud7af]',value):return False
    if country!='TH' and re.search(r'[\u0e00-\u0e7f]',value):return False
    required={'TH':r'[\u0e00-\u0e7f]','KR':r'[\uac00-\ud7af]','JP':r'[\u3040-\u30ff\u3400-\u9fff]',
              'CN':r'[\u3400-\u9fff]','TW':r'[\u3400-\u9fff]','HK':r'[\u3400-\u9fff]'}
    return bool(re.search(required.get(country,r'[^\W\d_]'),value))


def headline(page, country):
    visual=page.get('visualEnhancement') or {}
    layers=visual.get('companyPromptLayers') or {}
    candidates=[page.get('localizedSellingPointTitle'),visual.get('localizedHeadline'),page.get('headline')]
    # The online director sometimes puts the approved title only in layoutAndCopy.
    candidates+=re.findall(r'[“「"]([^”」"\n]{2,220})[”」"]',str(layers.get('layoutAndCopy') or ''))
    return next((str(value).strip() for value in candidates if localized_copy(value,country)), '')
