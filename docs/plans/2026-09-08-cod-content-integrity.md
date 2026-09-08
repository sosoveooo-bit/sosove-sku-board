# COD Content Integrity Implementation Plan

**Goal:** Repair COD source coverage, supplied commercial content, main/detail classification, narrative totals, and conflicting hook text/layout rules without changing JP25, Amazon, Rakuten, models or provider nodes.

**Architecture:** Keep existing COD online analysis and creative passes. Introduce an opt-in full source ledger for COD while retaining legacy extraction defaults for other suites. Allocate explicit selling points before optional detail fillers, validate complete coverage before generation, and derive promotions/reviews solely from the current user brief. Use actual page section metadata and suite totals throughout compilation/reference routing. Hook text and comparison policies share the same frontend/backend contract.

**Tech Stack:** Python backend and pure standard-library commerce parser, existing JavaScript frontend, isolated unittest/Node checks.

## Steps

1. Write failing coverage/section/narrative tests and source-commerce parser tests with synthetic data and no network.
2. Preserve all COD source records; prioritize them in the detail plan and report capacity gaps honestly. Enforce coverage before calling image providers.
3. Make unspecified promotions and feedback regular product/use pages; preserve exact supplied percentages and actual review quotes. Align planner, compiler, modules and review rules.
4. Classify main/detail pages by section and selected main/detail counts, not the number eight; use actual full-suite totals in batch/split-retry narrative stages.
5. Unify hook textPolicy and allow two-panel layout only for the comparison type. Update COD-only versions and workflow copy.
6. Run full isolated regressions, inspect scoped diffs and active local jobs, then activate locally while preserving logs and configuration.

## Out of scope

Whole-suite COD AI photography planning, independent hook creative A/B experiments, provider reliability overhaul, actual paid image generation, GitHub push and VPS deployment remain separate work.

## Verification and activation

- Complete 17-source compilation, short-suite submission gating, structured-title deduplication, global-requirement separation, real section routing and full-suite narrative calculations are covered.
- Commercial-source tests cover arbitrary supported discount percentages, original qualifiers/conditions, real review counts, absence of fabricated filler, JSON roundtrips and stale-source re-planning.
- Hook frontend/backend tests cover shared textPolicy, explicit text-free priority, and the comparison-only two-panel exception.
- Full isolated regression run: **364 tests passed**, with external networking disabled and temporary test data. Frontend syntax and changed-file whitespace checks passed.
- Preserved the active local image jobs and waited until the service was idle before restarting only the existing panel process under its supervisor. No running image job was stopped.
- Local health passed. Served asset: `20260908-cod-content-integrity-v7`; COD country: `cod-country-v23-source-complete`; COD detail: `cod-detail-v16-source-backed`. JP25 remains `director-v33-online-photography-plan`.
- No actual image generation, model/node configuration write, Git push, or VPS deployment was performed in this repair.
