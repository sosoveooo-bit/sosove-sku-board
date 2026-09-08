# JP25 Online Photography Implementation Plan

**Goal:** Improve only JP25 photography decisions, cross-page narrative coordination, and conflicting prompt instructions while preserving product identity and source-point/copy bindings.

**Architecture:** Retain local content slots (10 main + 15 detail) as a coverage checklist. After online product/reference analysis, obtain a compact online photography plan for all 25 pages; cache that plan with the analysis and share it with every refinement batch and split retry. Let that online plan and each page's seven-layer brief own photography/layout, while local compilation enforces source facts, approved copy, and product identity only.

**Tech Stack:** Python standard-library helper, existing director transport/cache, existing JavaScript panel, isolated unittest mocks.

## Tasks

1. Add pure `sku_board/jp25_creative.py` helpers and tests for plan-message construction, strict normalization, field-whitelisted application, and a full-suite manifest. No I/O or provider configuration in this helper.
2. Add JP25 integration regressions: narrative stage uses 25 even in single-page retries; all batches see the same manifest; JP25 photography is not frozen to local presets; source/copy constraints remain; other suites retain their current contracts.
3. Integrate the compact online plan after product analysis and before page briefs, with bounded director calls and cache reuse on continuation. Preserve partial page prompts and report plan status honestly.
4. Remove JP25-only generic 32-word and fixed-local-camera/layout contradictions. Set field-specific output budgets; user source text remains untouched. Prefer online geometry over deterministic local module positions at compilation.
5. Update only JP25 plan/cache/asset versions and workflow copy. Preserve current providers, model settings, other suites, A/B generation and review strategies.
6. Run full isolated tests with networking disabled; review scope and syntax. Inspect active jobs, activate locally without deleting logs, and verify served versions/health.

## Explicit exclusions

- No VPS/GitHub deployment, node/model configuration changes, or actual paid image generation.
- No change to the other previously listed reliability findings.
- Reference-based visual scoring and a manual three-image approval workflow are not added in this priority pass; existing A/B and review remain.
- No promise of equal visual results; real same-product samples remain necessary to evaluate the improvement.

## Verification and activation

- Added 13 pure-helper tests and 11 integration tests, including global-first planning, shared all-page context, partial continuation, strict field whitelists, optional human presence, source preservation, and final compilation roundtrips.
- Full isolated image-suite/COD/JP25 regression run: **310 tests passed**, with real network requests disabled and temporary test data.
- Verified online side-view / warm-scene lighting survives the final prompt without the old front-view / daylight defaults; reference-supported-surface and material physics requirements remain.
- Frontend syntax and changed-file whitespace checks passed. Only JP25 plan/cache and asset versions were updated.
- Confirmed no queued/running local image jobs before activating via the existing persistent supervisor. Logs, images, administrator settings and provider nodes were retained.
- Local health passed and the server serves `20260907-jp25-online-photography-v6`, plan version `director-v33-online-photography-plan`.
- No live image generation, external deployment or Git push was performed. Visual quality still requires new real-product outputs for evaluation.
