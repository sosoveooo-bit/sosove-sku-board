# COD country: all main images

User requested changing the country suite to entirely main images. Country total
24/30/37 now means 24/30/37 main images, zero detail pages; all supported totals
follow the same rule, even when an old brief contains a main/detail split.

The normal planner emits `section=主图` throughout, continuous section indexes and
main-prefixed roles. Existing core + source-backed support enrichment therefore
applies to every page, not just the first eight/fifteen. Per-page visual diversity,
local language locks, no-text restrictions and source authenticity remain intact.

Frontend counts, hints, reference-budget fallback and country plan version agree
with the backend (`cod-country-v30-all-main`). Browser asset version is refreshed.
Separate COD detail suite is unchanged. Existing images and explicitly saved old
page sections remain untouched; replan an old task to adopt all-main structure.

Backup: `.run/cod-all-main-20260918-234852/`. No paid generation or AI review added.

Verification: 72 targeted offline tests passed, including main-only counts and
support budgets for all pages, old split text, frontend Node VM, isolated detail
suite, language/diversity and old saved-section preservation. Node syntax check
passed. No image-model calls were made.
