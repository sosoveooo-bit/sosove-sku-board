# COD Prompt Fidelity and Density Fix

## Problem

COD country and COD detail outputs were visually overloaded and sometimes
replaced an explicitly supplied per-image scene, action, composition, effect or
headline with generic director styling.

## Cause

- The generic company-style prompt encouraged rich callouts and multiple labels.
- The director was allowed to rewrite scene, mood, action, composition, effects
  and copy even when the user had supplied those fields for a specific image.
- Per-image `场景 / 氛围 / 特效 / 文案 / 卖点` blocks were treated as one long
  global brief, so one page could inherit another page's scene.

## Fix

- Parse numbered `主图` and `详情图` blocks into page contracts.
- Persist `userPromptContract` and `userLockedFields` through plan review,
  generation, retries and result metadata.
- Keep the per-image execution card at the start of the remote prompt so it
  survives the 7000-character provider limit.
- Keep user-locked fields verbatim while the director fills only missing fields.
- Default to one headline and zero or one support label; explicit page contracts
  add no microcopy unless supplied.
- Reserve at least 75% of the canvas for photography and keep visible text under
  15%, with narrow exceptions for comparison, overview and feedback pages.
- Reject generated pages that change locked fields or add paragraphs, benefit
  walls, icon rows, badge clusters, decorative English or unrequested inset cards.

## Protected Configuration

This change does not edit image-provider endpoints, credentials, account pools,
node weights or the Giikin Acore provider configuration.

## 2026-07-29 Company-output parity findings

- The company task submits the complete `sale_image` material set, separate
  `reference_images`, target country/language, 3:4 counts and the selected image
  model into one landing-page task. The local per-page router was reducing later
  pages to two original references before adding the generated page-1 anchor.
- The observed company task used `generate_image_gpt_image_2_low`; the local COD
  run was forcing `gpt-image-2` high even when the full-review profile was chosen.
- Both remote paths cap each page prompt at 7000 characters. Local COD prompts
  were 14k-17k characters, so the company-art-direction block occurred after the
  transport cutoff even though the page execution card survived at the front.
- Company output uses full-bleed lifestyle photography, large Mincho headlines,
  warm paper-like zones, restrained gold/caramel callouts, asymmetrical magazine
  rhythm and stronger conversion packaging. Local output was therefore cleaner
  but noticeably flatter and closer to a sparse catalogue.

## 2026-07-29 parity changes

- Every COD page now receives all eight original uploads in stable order; the
  director's `referenceIndexes` act as priority hints instead of deleting the
  remaining product/color/model evidence. The generated page-1 anchor is still
  appended after those originals.
- COD provider quality is fixed to `low` to match the company GPT Image 2 task,
  while the `quality` generation profile still controls full-suite review,
  concurrency and retry behavior.
- A compact company visual-DNA block is inserted immediately after the per-page
  execution contract, before the 7000-character cutoff.
- Page-level apparel phrases such as `米白色款长裙`, `藏青色长裙` and `咖色长裙`
  now participate in color-range extraction.
- `codDetail` now uses the same generic-product, target-country and multi-reference
  prompt compiler as `codKorea` instead of falling through to garment boilerplate.
