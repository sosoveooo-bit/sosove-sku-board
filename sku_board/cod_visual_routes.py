"""Source-driven evidence assignments, not prewritten photography templates."""
import json
import re
from collections import Counter

FAMILIES = (
    ("specification", r"规格|参数|尺寸|包装清单|product.info|specification", "Product inventory and readable specification composition."),
    ("macro", r"触感|柔软|纹理|材质|面料|texture|tactile|fabric", "A dominant material/contact macro; show people only when the assigned evidence needs them."),
    ("process", r"步骤|加热|操作|使用方法|清洗|水洗|洗涤|heat|wash|step", "A correct operation sequence or close action-to-result study."),
    ("comparison", r"对比|前后|before|after|compar", "A matched-condition comparison focused only on the documented difference."),
    ("color", r"颜色|色彩|六色|配色|color|colour", "A color/variant collection with actual product and result colors as the dominant subject."),
    ("mechanism", r"原理|结构|机制|微球|mechanism|structure", "A source-supported structural or mechanism explanation; no invented anatomy or technology."),
    ("application", r"多材质|适用|兼容|场合|application|compatible", "A set of genuinely different supported applications, not repeated tabletop portraits."),
    ("lifestyle", r"亲子|家庭|陪伴|儿童互动|family|together", "A human interaction scene that proves this particular source benefit."),
)


def assignments(pages):
    counts = Counter()
    records = []
    for page in pages:
        # Do not select an evidence family from inherited generic scene text.
        source = " ".join(str(page.get(key) or "") for key in (
            "sourcePointVerbatim", "focusTitle", "focusDescription", "sellingPoint",
            "localizedSellingPointTitle", "directorSellingPointEvidence"))
        family, direction = "product-proof", "Choose the clearest product-specific proof; a decorative person is not mandatory."
        for name, pattern, candidate in FAMILIES:
            if re.search(pattern, source, re.I):
                family, direction = name, candidate
                break
        counts[family] += 1
        records.append({"page": page.get("page"), "sourcePointIndex": page.get("sourcePointIndex"),
                        "evidenceFamily": family, "occurrence": counts[family], "direction": direction})
    return records


def instruction(routes):
    return (
        "[WHOLE-SUITE SOURCE-DRIVEN EVIDENCE MAP]\n" + json.dumps(routes, ensure_ascii=False) +
        "\nThese are planning suggestions, not new product facts or fixed layouts. Explicit user scene/people/copy requirements win. "
        "Author independent photography for each page's actual source point. For repeated families, change the proof object, "
        "camera scale and layout topology, not just wording or left/right position. Keep only palette, typography and product identity shared. "
        "Do not impose a person, tabletop, package packshot, circular inset or bottom icon rail on every page. "
        "If the source supports only one setup, prefer a distinct informative detail over invented use or unsupported claims. "
        "Return visualEnhancement.localizedHeadline in the selected language derived from this page's source; "
        "retain explicit supplied headlines verbatim and honor text-free requests. Never use a generic placeholder slogan."
    )
