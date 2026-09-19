# COD visual diversity

User approved improving similar-looking COD country/detail images while preserving
selling points, cached analysis, existing generation APIs and no post-render AI review.

## Design

Chosen: deterministic, source-aware whole-suite shot constraints before the existing
director, plus local repeated-design detection and a per-page rendering contract.
This is cheaper than a second creative model pass and stronger than merely adding
"make it different" to every prompt. It does not replace independent AI-authored
seven-layer prompts with prewritten full-page templates.

Allocate shot scale, viewpoint, information placement and human-use intent across
compatible evidence families, penalizing adjacent/shared combinations. Keep actual
product geometry, benefits, verified variants, copy language, user requirements and
source-backed proof unchanged. Do not manufacture comparisons/results for variety.
Pass full-suite assignments into each planning batch so concurrent batches share
one allocation. Apply the same assignments to saved plans on compilation; preserve
their content while allowing inherited generic scenery/camera/layout to change.

Local text fingerprint checks identify repeated execution descriptions (not image
similarity measurements). They add targeted repair constraints to the normal image
request; no extra model round, no automatic paid image rerender, no new pause/error.
Explicit user scenes/poses/layout and existing text-free policies take precedence.
Older five-Agent adapter and non-COD suites are out of scope.

## Verification

Offline tests: deterministic distinct allocations; evidence compatibility; repeated
prompt detection ignoring headline/color changes; batch consistency; final Prompt
contract for both COD suites; original source/benefit and language preservation;
no additional model calls; existing regressions. Reload only with no active jobs.
Image quality remains to be checked by the user on a small regenerated sample.

## Result

- 120 targeted offline tests passed, including both COD suite compilers, saved
  plans, cross-batch allocation, language/source preservation, Japanese workflow
  isolation, existing no-review and transport checks.
- Updated the COD assertion in the Japanese integration suite: automatic COD
  scene/pose defaults are intentionally no longer frozen; non-COD freeze remains.
- Repetition detection uses bounded character-trigram comparisons for predictable
  local overhead rather than additional model requests.
- Pre-edit files: `.run/cod-diversity-20260918-224735/`.
- No real image generation, bitmap editing or paid model calls during verification.
