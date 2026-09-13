# COD Suite Visible Copy Implementation Plan

**Goal:** Make COD country and detail suites consistently render source-backed local-language selling copy by default, preserving explicit user copy restrictions and the different main/detail budgets.

**Architecture:** Resolve these two suites' text policy from the current brief before planner/cache fields, persist a versioned copy-policy stamp through page normalization for director/review calls without the brief, and use one suite-specific final text contract. Keep the complete selected-SKU selling-point JSON block through source extraction. Scope changes strictly to the two COD suite keys and their matching frontend templates.

**Tech Stack:** Existing Python planner/compiler, JavaScript panel, JSON skill definitions, temporary-data unittest and Node VM transport tests.

## Tasks

1. Audit policy precedence, stale plans, generic single-image instructions, selected-SKU source truncation and review rules.
2. Add failing tests for current-brief precedence over stale/AI no-text fields, title-only/no-text preservation, source-list coverage and non-COD isolation.
3. Apply a `cod-copy-v1` policy stamp and suite-specific visible-copy instruction throughout source locking, compilation, module construction and review. Ignore planner-only no-text defaults while preserving current user exclusions and all source data.
4. Add the complete `[COD suite selling-point sources]` JSON array to the two frontend templates; eliminate their generic single-image budget and correct the COD detail localization branch. Feed those sources into backend source allocation rather than reducing them to six suggestions.
5. Upgrade only country/detail plan revisions (`cod-country-v25-visible-source-copy`, `cod-detail-v17-visible-source-copy`) and the browser asset (`20260909-cod-suite-copy-v1`). Replan old-version COD retries rather than reusing stale no-text pages.
6. Run isolated regressions and syntax/scope checks. Activate locally when image/director tasks are idle, preserve logs and all model/node settings. No live paid generation, push or VPS deployment.

## Copy budgets

- Country main: one dominant core headline, 3–5 distinct approved supporting benefits if available and 1–2 matching proof areas.
- Country detail / detail suite: one source point per page, one clear localized heading and concise explanation or source-required structural fields.
- User no-text/title-only/price-only restrictions take precedence. No invented benefits, numbers, offers, certifications or reviews to fill missing content.
- JP25, Rakuten, Amazon A+, standalone hooks, image model selection and existing atelier work retain their previous behavior.

## Completed and verified — 2026-09-09

- Added the COD-only versioned copy-policy resolver. The current brief, including a cleared brief, outranks stale model/cache text fields. Brief-less analysis/review calls consume the resolved stamp preserved by page normalization.
- Both director stages, including the actual batched analysis branch, receive the same policy and copy contract. Final prompts and review use it consistently: correct required wording rather than silently omitting copy. Stale generated no-text prose is reconciled without changing original source records or photography intent.
- Added full selected-SKU source JSON extraction and removed the two templates' six-candidate cap and generic single-image budget. COD detail now uses its own generic-product and target-country route. Main rich support, detail one-point copy and structural fields remain distinct; restricted title/price modes suppress extra support modules.
- Fixed the edge case where an unprinted-product description such as a text-free bottle, packaging or T-shirt design was interpreted as an all-image no-text instruction. Explicit image-level no-text requests still take priority, including `本次所有图片无字`.
- Old-version retries in either COD suite replan; single-page redo first rebuilds the prompt from current raw intent, selected product and references so old truncated source lists do not persist. No historical image metadata is rewritten.
- Final verification: **511 Python tests passed**, with temporary data and mocked external requests. **26 existing Node atelier tests passed**; JavaScript syntax and Git diff checks passed. Added 15 backend and 11 frontend suite-copy regression tests.
- Waited for the user's active image jobs to complete. After verifying zero queued/running image/director jobs and no established panel request, stopped only the verified panel process; the existing hidden supervisor restarted it. Health is OK and served `20260909-cod-suite-copy-v1` JavaScript matches the local source byte-for-byte.
- Verified country v25/detail v17 and unchanged JP25 v33. Environment and director-settings hashes remain identical; default `gpt-image-2.5-sunburst` and all seven nodes remain intact. No paid generation, Git commit/push or VPS deployment was performed. Fresh rendered-image quality remains untested.
