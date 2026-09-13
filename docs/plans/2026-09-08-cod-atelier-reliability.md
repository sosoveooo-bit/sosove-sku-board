# COD Prompt Atelier Reliability Implementation Plan

**Goal:** Make every product an isolated, recoverable AI prompt project, with identical exported and rendered prompts.

**Architecture:** Add an opt-in Atelier API and disk-backed per-user project/version store. A short AI outline pass determines all page assignments, then five-page AI batches fill the prompts. Existing SKU Board suite planners remain unchanged. A thin shared execution compiler preserves the AI master and page prompt verbatim, adding only canvas, reference and factual constraints.

**Tech Stack:** Python standard-library HTTP server and JSON persistence, existing AI Director/image clients, vanilla HTML/CSS/JavaScript, Python unittest and isolated Node VM tests.

## Agreed API contract

Prefix `/api/sku-board/cod-atelier` (existing login required).

- `GET /projects` → `{ok, projects:[{id,name,revision,status,updatedAt,...}]}`.
- `POST /projects/upload` multipart: `form` (JSON of existing frontend form), optional `projectId`, `revision`, `referencesMode` (`keep` or `replace`), `referenceBindings` JSON and `reference0..11` files → `{ok,project}`.
- `GET /projects/{id}?revision=N` → `{ok,project}`. Omitted revision returns current.
- `GET /projects/{id}/references/{index}?revision=N` → authenticated original image.
- `POST /projects/{id}/generate` JSON `{revision,mode:"fresh"|"resume"|"page",pageNumber?,instruction?}` → `{ok,project}`; processing continues in a background worker. Fresh/page create a new version; resume only fills incomplete pages of the same version.
- `POST /projects/{id}/cancel` JSON `{revision}` → `{ok,project}`; already completed pages remain.
- `POST /projects/{id}/edit-page` JSON `{revision,pageNumber,modelPrompt}` → `{ok,project}` with a new version containing only this edited page.
- `POST /projects/{id}/render` JSON `{revision,pageNumber,model,quality,generationProfile}` → existing image-job payload plus `projectId,revision,pageNumber`; exact saved execution prompt and server-owned references only.

Project snapshot: `{id,name,revision,form,references,versions,status,progress:{stage,completed,total},masterPrompt,outline,suitePages,hooks,director,error,fingerprint,materials}`. References: `{index,name,size,mime,sha256,role,previewUrl}`. Version summary: `{revision,status,createdAt}`. Page: `{page,section,localIndex,title,focus,headline,archetype,modelPrompt,executionPrompt,...}`. Hooks: `[{source,variants:[{type:"pain"|"effect"|"scene",text}]}]`. Status: `draft|planning|generating|complete|partial|error|cancelled`. `executionPrompt` is the shared exact render/export representation. The reference SHA256 and roles are part of the input fingerprint.

## Tasks and acceptance checks

1. Implement pure input normalization, stable input/reference fingerprint and exact prompt compiler in `sku_board/cod_prompt_contract.py`. Test exact preservation of custom colors, source page assignment, supplied promotions and count (including 5+5), and reject invalid input.
2. Implement project persistence, ownership checks, immutable versions, resumable outline/batches, actual model metadata, localized hooks and page rewrite in `sku_board/cod_prompt_atelier.py`. Add deterministic mocked transport tests for partial saves, cancellation, restart, ownership, same-name image changes and successful/failed model responses. Never treat these as live model quality evaluation.
3. Add authenticated server routes and exact image-render adapter. Prevent legacy fixed-page compilation or Open Image Prompts enhancement from changing Atelier execution prompts; leave other suite routes unchanged. Verify actual provider-bound prompt is identical to the preview apart from provider-required reference transport metadata.
4. Rebuild frontend state around project/revision/request identity; no automatic local-rule fallback. Isolate in-flight requests, preserve archives/results, allow resume/cancel, editable single-page prompts and one-click complete export. Test delayed responses after product/reference change, failure handling and exact counts.
5. Improve existing HTML/CSS with project/version controls, clear AI progress and error states, reference role selection, page editor and native-language hook variants. Retain the current ivory/coral/navy visual identity; improve labels, keyboard focus and hidden/disabled states. No new animation.
6. Run Python/Node checks and existing regression tests; test HTTP routes and visible local browser flows without generating paid images. Restart only the verified local 8793 server if safe. Report any live-model/auth limitation accurately.

## Scope boundaries

- Preserve existing user data and all other SKU Board suite behavior.
- No automatic filesystem deletion, deployment, paid image batch or credential changes.
- Existing source-provided claims remain product data, not evidence of certification or medical efficacy. Do not fabricate endorsements, medical outcomes, performance numbers or unsupported promotion terms.

## Verification completed (2026-09-08)

- 310 Python regression tests passed, including the existing image-suite/client contracts and new project, ownership, exact-render and HTTP tests.
- 26 isolated Node controller tests passed: late responses after product/reference switch, error handling without template fallback, exact5+5, rendering preferences, immutable edits, editor/draft preservation, page6 rewrite selection, historical version selection, model metadata and cancellation.
- JavaScript syntax and Python compilation passed; `git diff --check` found no whitespace errors.
- Browser testing used `sku_board/tests/atelier_preview_server.py`: a whitelisted loopback-only mock service with a temporary store and image rendering disabled. Verified archive restoration,5/10→10/10 resume, AI page-only rewrite, manual edit creating a new version, reload restoring latest version, deliberate AI failure, explicit resume, native hook types and enabling complete export only when complete.
- The production8793 service was restarted after confirming no queued/running image jobs. The current browser page retains the user's previous text draft and loads v10; browser console had no errors.
- No live AI/model-quality or paid-image batch was run. The production browser currently requires login to SKU Board before accessing saved projects/model configuration. Cancellation stops new submissions and late writes; already submitted provider image work may still finish and be charged.
