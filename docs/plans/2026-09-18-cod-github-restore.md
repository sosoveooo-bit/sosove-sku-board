# COD GitHub workflow restoration

## Requested scope

Restore COD country landing/detail generation from the project's GitHub main,
not an entire-workspace reset. Preserve other features, completed images, saved
tasks, custom director models, upload/JSON fixes, and COD hook direct rendering.

## Source and backup

- Remote: https://github.com/sosoveooo-bit/sosove-sku-board.git
- Fetched revision: `064a6b5daf5923ab761dc4f4def4a594735c5d3b` (2026-09-13).
- Snapshot and local backup: `.run/cod-github-restore-20260918-193546/`.
- Initial backup includes 81 changed/untracked files, Git patches, status,
  hashes, and a separately extracted upstream archive. Additional changed test
  fixtures were backed up before editing.
- No reset, checkout, stash, source deletion, database migration, or image deletion.

## Changes

1. Restore 16 relevant backend COD planner/compiler functions from the fetched
   revision. Fifteen bodies match upstream AST exactly. The source extractor
   retains an unused optional `suite_key` keyword for historical Agent tooling.
2. Restore the legacy source coverage guard while retaining historical Agent
   saved-plan compatibility. Keep Agent normalization/compilation/submission
   support so original saved prompts and original images remain usable.
3. Restore `prepareAiImageSuitePlan` and COD frontend plan versions from GitHub.
   New requests, including stale clients supplying an Agent flag, enter the
   GitHub planner rather than the five-Agent route.
4. Existing Agent tasks get an explicit “另存 GitHub 版任务” action. It copies
   requirements/references to a new draft with preview-first planning; original
   materials, operation IDs, prompts, and retry records remain in the old task.
5. Keep user's no-post-render-AI requirement: suppress COD hero A/B selection in
   both frontend and backend, even when an old client sends `heroAB=true`.
   Other suites retain their previous behavior.
6. Bump the app.js URL cache key so refreshing loads the restored route.

The GitHub main-image contract supports a primary source-backed benefit and
3–5 supporting benefits when sufficient source material exists. It is not a
promise that any model will render identical quality to the company reference.

## Verification

- Python compilation, Node syntax check, Git whitespace check.
- AST comparison against upstream and pre-change snapshot; unrelated backend
  functions retain their original definitions.
- 148 targeted offline Python regression tests passed: COD source coverage,
  main density, provenance, copy, frontend routing, model transport, custom
  models, upload fixes, no image review, hook frontend/backend contracts,
  and historical Agent submission compatibility.
- Node migration test: copy-on-create, old images/retries preserved, current
  and old Agent revisions both offer migration, no network calls.
- Node custom-model UI regression passed.
- Updated two outdated provenance fixtures to isolate their source/hash checks
  from the already-existing seven-layer completeness gate. Confirmed their old
  failures reproduce in the unmodified GitHub archive. A new regression verifies
  incomplete GitHub prompts still stop before image dispatch.
- The separate historical `test_cod_hook_copy_contracts` suite contains old
  assertions requiring hook product analysis/variant routing. An exploratory
  run reported four subtest failures for those removed behaviors. They were
  not used to re-enable paid hook analysis; hook implementation is preserved.
- No paid model or image-generation request was used for verification.
- Local service reloaded after verifying no queued/running image jobs. Scheduled
  supervisor remains running; listener changed from PID 12784 to PID 56636.
  `/api/health`, home page, and the cache-busted app.js responded successfully;
  live JavaScript contains the restored GitHub plan version and migration action.

## Usage

Refresh the application. Start a new COD country/detail task, or use the explicit
GitHub migration action on an Agent task. Review the new plan, then generate.
Normal retries of an existing saved Agent prompt continue to use that prompt;
they do not automatically rewrite existing images into the GitHub design.
