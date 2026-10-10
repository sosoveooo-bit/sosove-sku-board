"""Default JP25 photographic craft applied at planning AND final image execution."""
import json
import re

VERSION = "jp25-editorial-craft-v1"
PLAN_VERSION = "director-v35-editorial-craft-source-complete"
BRIEF_VERSION = "jp25-page-reference-brief-v7-editorial-craft"
DEFAULT_BIBLE = {
    "typography": "One Japanese type pairing for the set: restrained Mincho headline and clean Gothic annotations; two weights, disciplined alignment and optical spacing.",
    "layoutSystem": "Photography leads. A consistent inset alignment grid; compact titles and at most two useful supporting labels. Alternate full product, intimate detail and purposeful use images.",
    "materialTreatment": "Reference-true color, fine physical texture, gentle directional key light and retained local shadow. Control highlights separately on cloth, skin, metal and glass.",
}


def planning_instruction():
    return (
        f"[JP25 EDITORIAL CRAFT {VERSION} — default art direction]\n"
        "Explicit user requirements and source/product truth take precedence over these creative defaults. "
        "Design a coordinated Japanese product campaign with the precision of a carefully art-directed catalogue. "
        "High quality must be expressed as concrete production choices, not quality adjectives. "
        "MAIN 1-10: make the product and the benefit understandable immediately. Mix an establishing hero, proportion/use evidence, "
        "a meaningful construction close-up and alternate reference-supported views; do not make every main page a standing model beside a title. "
        "DETAIL 11-25: spend more of the frame on the exact part, material, mechanism, drape, styling combination or use evidence of that page. "
        "Use a full-body shot only when full-body evidence is needed. A fabric/stitching claim requires a readable tactile close-up, "
        "a proportion claim requires seeing the real garment proportions, and versatility requires the named styling/use change. "
        "State the precise source feature the viewer should be able to point to. Changing the backdrop or adding a slogan is not proof. "
        "Preserve exact full source meaning; a headline is the reading entry point, not a substitute for the source contract. "
        "LIGHT: one physically plausible shaped key, restrained fill or negative fill, controlled highlights, readable contact shadows, "
        "separation between subject and background, and enough depth of field to inspect the featured product. "
        "Keep real weave, seam relief, drape and metal edge highlights without coarse fake texture, crunchy sharpening or plastic skin. "
        "A grey/white palette means real light-toned surfaces with depth, not a white fog overlay or an erased background. "
        "LAYOUT: use fewer, better placed elements. Photograph/evidence normally occupies 80-90% of visual attention; "
        "copy stays secondary in a calm, physically plausible area. Do not allocate an empty 40% text column by habit. "
        "Choose one Japanese type system for the entire suite, at most two families and two weights. "
        "Default headline size about 4.5-6.5% of canvas width, short labels about 2-3%, with a coherent 5-7% safe inset and "
        "natural Japanese phrase breaks. These are defaults, not overrides of an explicit user layout or long mandatory copy. "
        "Prefer understated, aligned text over repeated pill badges, stacked tag boxes, enormous vertical slogans or ornate separators. "
        "Keep approved Japanese wording and textPolicy; do not invent labels, names, testimonials or decoration to fill space. "
        "RHYTHM: coordinate tight/medium/wide evidence scale and composition across all 25 pages. Do not merely mirror the same layout. "
        "Keep the shared palette, casting and tonal response; change framing for a reason supplied by the product or source point. "
        "Integrate a detail crop or matched comparison only when that page needs it and references support it; do not add unrelated collages. "
        "Record the selected typography, layoutSystem and materialTreatment in visualBible; express each page's concrete result in its six photography fields."
    )


def evidence_direction(page):
    # Prefer the actual claim's title. Supporting paragraphs can mention shoes
    # or accessories without making the page a styling-variation claim.
    source = str(page.get("focusTitle") or "").strip() or " ".join(str(page.get(k) or "") for k in (
        "focusDescription", "sourcePointVerbatim", "objective", "directorSellingPointEvidence"))
    if re.search(r"ステッチ|縫製|織り|织|肌理|面料|素材|fabric|weave|stitch|texture", source, re.I):
        return "Make the named weave/seam/material directly inspectable at a useful close scale with gentle raking light; a distant outfit photograph alone cannot prove this point. Keep true fiber scale and actual construction."
    if re.search(r"ポケット|ファスナー|ボタン|口袋|拉链|纽扣|结构|机制|機構|pocket|zip|button|mechanism", source, re.I):
        return "Frame the exact named part and enough surrounding product to locate it; resolve its edges, attachment and scale. Show an opening or internal view only when source references support it."
    if re.search(r"単品|合わせ|着回|着まわ|搭配|拆分|versatil|styling", source, re.I):
        return "Show the actual named styling combination or separate-use variation, keeping the current item unchanged; a new background with the same outfit is not the claimed styling evidence."
    if re.search(r"ハイウエスト|フレア|比例|比率|シルエット|腰|脚|裤|丈|silhouette|proportion|fit", source, re.I):
        return "Let the viewer inspect the real silhouette, waist/hem relationship and drape in one coherent camera view; keep body proportions natural and do not simulate a benefit by body warping."
    return "Make the current page's complete source point visible through its specific product feature or credible use moment, with a deliberate crop; scene decoration or a generic slogan alone is insufficient."


def execution_instruction(page):
    shared = str(page.get("jp25ArtDirection") or "").strip()
    if not shared:
        shared = json.dumps(DEFAULT_BIBLE, ensure_ascii=False)
    return (
        f"[JP25 EDITORIAL FINISH {VERSION}]\n"
        "Execute the online page's chosen scene, lens, action and source meaning; this finish layer refines craft, not a second camera recipe. "
        "The user's explicit framing, palette, identity and saved edits take priority. "
        + evidence_direction(page) + " "
        "Use controlled highlights, natural contact shadow, dimensional midtones and physically legible material texture. "
        "Keep the featured construction sharp without oversharpening or plastic smoothing. Preserve environmental depth and true product color. "
        "A light palette is not white haze: never wash away the photographed product or background just to make room for text. "
        "Make the photograph the main visual; keep exact approved Japanese type compact, precisely aligned and secondary. "
        "Do not enlarge it into a half-page slogan or add pill badges by habit. Maintain one consistent type system and measured safe spacing. "
        "Honor text-free pages and every explicitly authored layout. Never print planning labels, source IDs or these instructions. "
        "[SHARED EDITORIAL SYSTEM] " + shared
    )
