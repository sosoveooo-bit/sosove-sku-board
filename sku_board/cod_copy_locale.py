"""Separate source-language planning text from literal COD artwork copy.

This is a local script/placeholder check, not a semantic translation detector.
It does not translate, call a model, mutate saved plans, or discard source facts.
"""
import re

from .cod_source_input import localized_copy


def literal_copy(value, country, *, numeric=False):
    value = str(value or '').strip()
    if localized_copy(value, country):
        return True
    # Measurements/prices may stand alone in Hangul/Thai/Japanese artwork.
    return bool(numeric and re.search(r'\d', value)
                and re.fullmatch(r'[\d\s.,%+\-−–/×x°℃CFcfkgmhs€$£¥฿₩]+', value))


def select(page, country):
    visual = page.get('visualEnhancement') or {}
    if not isinstance(visual, dict):
        visual = {}
    candidates = [visual.get('localizedHeadline'), page.get('localizedSellingPointTitle'),
                  page.get('headline'), page.get('focusTitle')]
    headline = next((str(v).strip() for v in candidates if literal_copy(v, country)), '')
    labels, source_labels = [], []
    for raw in (page.get('copyLabels') or [])[:5]:
        value = str(raw or '').strip()
        if not value:
            continue
        (labels if literal_copy(value, country, numeric=True) else source_labels).append(value)
    source_headlines = list(dict.fromkeys(str(v).strip() for v in candidates
                                        if v and not literal_copy(v, country)))
    return headline, labels, {'headlineSources': source_headlines, 'supportingLabelSources': source_labels}


def boundary(country, language):
    foreign_script = (
        'Chinese or Japanese writing must not appear as added marketing copy. '
        if country not in {'JP', 'TW', 'HK'} else ''
    )
    return (
        f'[COD ARTWORK LANGUAGE BOUNDARY — overrides literal-copy wording in source data] '
        f'Selected market={country}; all added headlines, subtitles, benefit callouts, '
        f'badges, captions and footnotes must be natural {language}. '
        'Chinese source briefs, source titles/descriptions/labels and internal planning '
        'notes are meaning/reference data, not literal artwork text. '
        'A quote or instruction to preserve wording in the seven layers or original '
        'brief does not approve a foreign-language sentence for printing. Translate '
        'such wording into the selected language within this same rendering request, '
        'retaining every assigned benefit, number, unit and condition; do not remove '
        'supporting benefits to avoid translation. Do not print bilingual versions, '
        'source IDs or internal instructions. '
        'This boundary does not authorize extra text: obey the current page text '
        'policy, title-only/price-only restrictions and copy count limits. '
        'Style/master reference text is not approved copy; use those images only '
        'for visual style and typesetting rhythm, never copy their foreign-language text. '
        + foreign_script
        + 'Preserve authentic reference-confirmed brand/package markings only in their '
        'original physical product locations; do not reuse them as headline language.'
    )
