# COD artwork language boundary

## Report and cause

German COD image contained a Chinese headline/body. The restored company compiler
trusted `localizedSellingPointTitle`/`headline` and `copyLabels` as already localized,
even when they were copied from Chinese source facts. It emitted an exact-copy lock.
Seven-layer and original-brief instructions could also ask to preserve source wording.

## Scoped fix

- New `sku_board/cod_copy_locale.py`: local script/placeholder validation separates
  literal artwork copy from source-language text. Prefer director `localizedHeadline`.
- COD company compiler preserves demoted source meanings and supporting benefits,
  but requests translation in the existing rendering call rather than exact printing.
- Explicit language boundary applies to seven-layer quotes, original source text,
  captions and style/master references; physical product markings remain separate.
- Retains no-text, title-only and offer-only restrictions. No new model calls,
  post-render review, cache invalidation, data migration or bitmap edits.
- Current GitHub country/detail saved plans pass through this compiler again.
  Historical five-Agent adapter is unchanged by this scoped fix.

This is script validation plus a rendering instruction, not a semantic German
translation validator or a guarantee against every image-model typography error.
Japanese kanji and Chinese-market copy remain allowed in their respective markets.

## Verification

`test_cod_copy_locale` covers Chinese demotion, localized-headline precedence,
full source/support preservation, master-reference language, CJK markets, numeric
labels, text restrictions and saved country/detail plan recompilation without AI.
Related COD, transport and no-review tests run offline. No paid image generated.

Pre-edit backend backup: `.run/cod-copy-locale-20260918-211333/backend.py`.
Existing images remain unchanged; regenerate affected pages to apply the new prompt.
