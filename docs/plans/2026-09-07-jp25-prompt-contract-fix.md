# JP25 Prompt Contract Fix Implementation Plan

**Goal:** Fix only the two approved JP25 defects: online seven-layer prompts lost during source binding, and source/localized-copy/evidence mismatches.

**Architecture:** Retain the existing online product analysis and page-brief pipeline. Bind source content and model enrichment by a stable one-based source index, preserve remotely authored visual layers during repeated source validation, and invalidate only JP25's stale plan/cache fingerprint. Other suites, provider nodes, retries, and model settings stay unchanged.

**Tech Stack:** Python backend, existing JavaScript client, unittest with isolated temporary data and mocked network.

## 1. Reproduce the approved defects

- Create `sku_board/tests/test_jp25_prompt_contract_regressions.py`.
- Test full remote 25-page layers through the final source lock for generic product and fashion authority pages.
- Test five explicit source points with localized copy/evidence, explicit indices, legacy ordered records, and repeated source binding.
- Run these tests against the existing code first and retain failing assertions as regression coverage.

## 2. Preserve online work

- Modify only JP25's source lock in `sku_board/backend.py` to merge content constraints without rebuilding a remote visual enhancement.
- Keep repeated binding idempotent; never manufacture missing remote prompt layers.
- Validate readiness after the final processing chain.

## 3. Bind source content and localized evidence

- Preserve source indices and model-localized enrichment during JP25 analysis normalization.
- Prefer explicit index bindings; accept legacy ordered output only when its source correspondence is unambiguous. Do not shift later points across missing records.
- Use the current page's source binding instead of the old fixed layout slot for title, labels, and evidence.
- Include explicit source indices in JP25's model response contract.
- Update only the JP25 plan/creative versions and front-end asset version, preserving all other suites.

## 4. Verify and activate locally

- Run new regressions and existing image/COD tests with a temporary data directory and real networking blocked.
- Syntax-check backend and frontend; review the scoped diff.
- Inspect active local jobs before any service restart; do not interrupt active generation.
- Verify local health and served asset version after activation. Do not generate paid sample images or deploy remotely.

No commits, pushes, or configuration migrations are part of this repair.

## Verification result

- Old-code failures reproduced before the fix; 11 focused regression tests now pass.
- Full isolated regression run: 286 tests passed (273 existing image-suite tests, 2 COD prompt-generator tests, 11 new JP25 tests). External requests were disabled and all test data used temporary directories.
- Backend AST parsing, frontend syntax check, and changed-file whitespace checks passed.
- Confirmed zero queued/running local image jobs before restarting only the existing panel process under its persistent supervisor. Logs and configuration were retained.
- Local health is healthy; the server serves `20260907-jp25-source-contract-v5` and JP25 plan version `director-v32-source-bound-online-prompts`.
- No paid generation, GitHub push, VPS deployment, or provider/model configuration change was performed.
