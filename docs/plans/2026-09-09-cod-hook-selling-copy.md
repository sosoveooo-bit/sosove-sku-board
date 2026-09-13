# COD Hook Selling Copy Implementation Plan

**Goal:** Restore visible, source-backed selling points in the main panel's `codHook` images without changing any suite, image-model selection, service node or atelier workflow.

**Architecture:** Frontend and backend use the same requested-by-default text policy for hooks. A hook-specific copy contract authorizes faithful localization of supplied selling points even when no literal target-language headline was entered. On standard canvases, use one core headline plus two or three distinct supporting labels when actual sources permit and direct visual evidence. Explicit no-text, headline-only, price-only and narrow-strip instructions take priority. Keep product/source facts and exact quantities intact, with no invented credentials, efficacy evidence or offers.

**Tech Stack:** Existing Python/JavaScript prompt pipeline, JSON skill direction, isolated unittest and Node VM mocks.

## Work

1. Inspect recent hook job metadata and actual submitted prompts; distinguish missing source transport from contradictory default-copy instructions.
2. Add frontend and backend tests covering no-reference/reference requests, visible source-backed copy, narrow price strips, comparison, explicit exclusions, OIP append ordering and non-hook isolation.
3. Update only `codHook` policy/direction/selection/content budget in `sku_board/static/app.js`, `sku_board/backend.py`, and the `codHook` template in `sku_board/skills/gpt-image2.json`.
4. Carry the hook copy contract through text-only compilation and reference-image generation, and reassert it after optional visual enhancement before variant binding and submission. Retain the original user source and honor explicitly submitted `textPolicy=none`.
5. Update hook-specific former opt-in tests and the main script cache revision, without weakening source or no-text checks. Run all isolated regressions, model-default tests, JavaScript syntax and scope checks.
6. After active local image/director jobs finish, reload only the local panel using the existing supervisor without clearing logs. Verify runtime health/configuration and unchanged node/default-model settings. No live paid generation, Git push or VPS deployment.

## Acceptance

- Plain supplied product benefits default to readable localized selling copy, not an automatically text-free scene.
- Default supporting text is grounded in the current prompt/reference product, does not duplicate the headline and does not invent facts to reach a quota.
- Explicit copy restrictions, two-panel comparison conditions and 750x100/150 compact-strip rules remain effective.
- Text-only and uploaded-reference prompts include the same source/copy contract at final dispatch; other templates retain their existing contracts.

## Completed and verified — 2026-09-09

- Confirmed the former default was opt-in visible text, and a recent completed sunburst hook task contained `textPolicy=none`. Default hooks now permit localized source-backed selling copy without requiring the user to write an explicit text command.
- Updated standard hook, promotion and effect copy to one core headline, two or three distinct supporting short benefits when actual sources permit, and one or two visual evidence details. Explicit no-text/title-only/price-only requests, narrow strips and matched-condition comparison retain their dedicated restrictions.
- Fixed text-only compilation dropping the selected product's `[COD hook selling-point sources]` block. It is now preserved in full, with transport tests for both text and reference-image paths. The full source and final copy contract are protected from silent 64,000-character clipping by hook-only length validation.
- Reasserted the contract after optional visual enhancement, kept it in each reference-bound variant prompt and retained old-hook forced recompilation on generate. Other template source selection and content budgets remain untouched.
- All **485 Python tests passed** with temporary data and mocked external requests. JavaScript syntax and Git diff checks passed. New hook tests cover explicit constraints, full source text, selected-product source transport, copy budgets, variant binding, OIP ordering, length limits and non-hook isolation.
- Confirmed zero active image/director jobs and no established request connections before restarting only the verified local panel process. The existing scheduled supervisor restarted it; health is OK and the served `20260909-cod-hook-copy-v1` JavaScript matches the current source file.
- Compared environment and director settings by SHA-256: unchanged. Default image model remains `gpt-image-2.5-sunburst`, all seven service nodes remain present, and all non-hook skill templates match their previous contents.
- No paid image generation, Git push or VPS deployment was performed. Existing images remain unchanged; refresh the main panel and regenerate to use this contract. Rendered image quality still needs a real generation check.
