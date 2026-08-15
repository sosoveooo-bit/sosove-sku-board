# Verbatim prompt contract design

## Goal

Keep user-written selling points, authority themes, numbers, units, target users and use methods aligned with the page that renders them. Visual planning may shorten display copy, but it must retain the complete source meaning used to direct the photograph.

## Data flow

1. Store the task brief with a 64,000-character ceiling.
2. Parse source points while retaining both normalized planning fields and a punctuation-preserving `sourcePointVerbatim` value.
3. Bind each source point to one page before remote director refinement.
4. Preserve `sourcePointVerbatim` through plan JSON normalization and cached/recovered jobs.
5. Add a highest-priority verbatim source contract to the page's final generation prompt.
6. Keep the one-page/one-selling-point content budget so a complete suite does not collapse into repeated benefit collages.
7. Submit prompts with a shared 64,000-character provider ceiling. COD hook generation uses the full supplied brief instead of a head/tail excerpt.

## Compatibility and recovery

Plan versions are bumped for JP25, COD country and COD detail suites so saved older conversations are automatically replanned. Existing node configuration, credentials, product-reference routing and Open Image Prompts behavior stay unchanged.

## Verification

Regression tests cover content beyond the former 3,000-character request boundary, a marker in the middle of a long COD hook brief, and a long source point surviving planning, normalization and final prompts for both COD and JP25 flows.
