# Planning reference failure: preserve and repair PageSpecs

## Observed failure

The German 24-page campaign `1371beaabd994678becb11890300b0b7` repeatedly stopped at
`第 1 页缺少原文或产品素材引用`. The stored record contained a cached product analysis,
strategy and direction, twelve uploaded assets and one source entry, but no
`planningDraft`. Several completed planning responses (approximately 30,000
characters each) had been discarded by validation. The old error combined empty
`sourceIds` and empty `referenceAssetIds`, so the historical response does not
establish which field the model omitted.

## Changes

- Persist every candidate plan before checking page contracts.
- Share the same strict per-page validation between final validation and local
  issue collection; distinguish source-reference errors from asset-reference errors.
- Request one bounded, targeted correction for faulty pages. Valid pages remain
  byte-for-byte unchanged; corrected candidates are persisted before revalidation.
- A time-budget yield preserves the draft, so continuation repairs that draft
  rather than requesting the complete suite again.
- Explicitly require nonempty source and product-reference IDs in the planning
  instructions, including hero and CTA pages.
- State that a source ID traces the user's request, not proof of a claim. Do not
  insert arbitrary references or manufacture certification or efficacy evidence.
- Preserve product cache keys, existing image interfaces and strict final
  submission checks. No generated-image review calls are introduced.

## Verification

- Six new regressions cover targeted correction, untouched valid pages,
  persisted partial corrections, bounded persistent failure, budget continuation,
  unknown asset IDs, wrong replacement page numbers and recovery of an unindexable
  saved response (only that structural case recreates the full plan).
- All 62 visual-agent tests passed including the HTTP 402 diagnostic; subsequently
  the complete six-test reference-repair group passed with the additional
  unindexable-draft case. Three multipart tests pass.
- Frontend saved-plan synchronization, references/zero-review dispatch and error
  display regressions pass; JavaScript syntax validation passes.
- The actual German campaign passed all 24 planning contracts and produced nine
  validated prompts using its existing product cache. Product analysis was guarded
  against accidental reruns in the verification script.
- The next prompt batch received HTTP 402 from both `gpt-5.6-sol` and
  `gpt-5.6-terra` on the configured director endpoint. No explanatory body was
  returned. Verification stopped rather than repeatedly retrying or discarding
  completed work. Added a separate billing/credit diagnostic; no assertion that
  all images have generated or that the precise billing cause is known.
