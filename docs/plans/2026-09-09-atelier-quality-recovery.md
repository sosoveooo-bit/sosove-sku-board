# Atelier Quality, Export and Recovery Implementation Plan

**Goal:** Add actionable prompt quality checks, compact/batch exports, per-page draft safety, permanent image assets and a durable idempotent render queue without changing other SKU Board suites.

**Architecture:** Extend the opt-in Atelier modules. Quality is an advisory report with deterministic checks and optional configured-AI review/targeted repair, never an unqualified claim of native-language or medical accuracy. Server-owned render runs snapshot revision, pages and settings; they reuse known active/completed jobs, pause safely on uncertain outcomes, and only explicitly requested redo creates new work. Long-term assets are saved under the owner/project directory outside the shared temporary image cleanup.

**Tech Stack:** Existing Python/JSON server, vanilla JS/CSS, Python unittest and Node controller tests, isolated browser mock service.

## Boundaries

- Preserve dirty unrelated changes, old product versions and all user files. No paid-image batch, live model review, credential changes or external deployment during tests.
- Keep existing `/generate` and `/render` contracts backwards-compatible. Exact single-page executionPrompt remains canonical for image providers.
- Default complete export becomes compact: one master, shared execution requirements once, numbered per-page modelPrompt. Add independent-page export retaining each executionPrompt.
- Draft cache keyed by project+revision+page and persisted separately from saved versions; page selection/project changes cannot discard edits. Explicit discard is reversible through stored source version.

## API extensions (same prefix /api/sku-board/cod-atelier/projects/{id})

- `POST /review` JSON `{revision,mode:"rules"|"ai"}` → `{ok,project}`. `project.qualityReport={status,source,summary,issues:[{page,code,severity,message,field?}],checkedAt,...}`. Rules source identifies heuristic limits. AI mode runs in existing background generation mechanism; action explicit.
- `POST /generate` mode `repair`, revision: create new version rewriting only pages flagged by report; hook issues regenerated without changing other pages. Existing fresh/resume/page unchanged.
- `POST /render-queue` JSON `{revision,mode:"resume"|"redo",pageNumbers:[...],model,quality,generationProfile}` → `{ok,queue}`. Default resume reuses same run/config and existing jobs/results. Explicit redo is separately named in UI. Same active tuple returns existing run even when retried.
- `GET /render-queues?revision=N` → `{ok,queues:[queue]}`. `POST /render-queues/{queueId}/resume` and `/cancel` → `{ok,queue}`. Queue snapshot `{id,projectId,revision,status,settings,pages:[{page,status,jobId,error}],completed,total,error,createdAt,updatedAt}`. States queued/running/paused/partial/complete/error/needs_attention. Waiting unknown submission never triggers blind resubmission.
- `GET /assets/{assetId}?revision=N` → authenticated PNG/JPEG/WebP. `GET /images.zip?revision=N` → local ZIP of archived images plus manifest (missing entries identified).
- `POST /archive-images` JSON `{revision}` → attempt to preserve still-available older local images; no arbitrary file paths or public uploads.

## Work packages

1. Quality module and Atelier integration: language-script warnings, identical hooks, repeated page/layout, source mismatch signals, exact evidence/reference coverage. Optional AI review validates JSON/evidence and highlights reasons; repairs only affected pages and hooks. Tests deliberately bad/localized copy, duplicates, different products, short and long suites, repair isolation.
2. Frontend: two export choices, per-page draft caching/recovery, quality report/repair actions, queue controls and origin-version gallery, ZIP download. Tests page/project/reload drafts, stale responses, compact one-master vs standalone exact output, queue resume vs redo.
3. Durable render module: run records and workers independent of browser, reuse stable job keys, stop new submissions on cancel, resume after restart, mark unknown jobs as needs_attention. Tests duplicate clicks, concurrent submit, crash boundary, old versions, changed settings, closed-browser execution, cancellation and multi-account ownership.
4. Root integration: long-term assets and ZIP, authenticated routes and recovery startup, image bytes archival and idempotent existing-job metadata. Protect legacy images referenced by existing Atelier records from shared cleanup until migration. Verify no writes/cleanup outside scoped asset locations.
5. Regression, HTTP and browser tests with mock models. Inspect live queue before safely restarting8793. Report no live model/image-quality guarantee; preserve existing configured model choice.

## Implemented behavior and verification (2026-09-09)

- Added advisory rules and optional AI review, scoped evidence validation, targeted page/hook repair, and exact review-version invalidation. Reports do not certify language naturalness, factual claims or generated-image quality.
- Export now has compact/shared-once and exact standalone modes. Page drafts are persisted by project/revision/page; missing/quota-limited browser storage produces a warning rather than a false saved claim.
- New generated image bytes are saved in authenticated permanent project assets; existing legacy project image IDs are protected from shared temporary cleanup until migration. ZIP includes origin revisions and a manifest listing missing/unavailable images.
- Render queues submit in the server, persist job IDs/intent receipts, reuse subsets and unchanged completed pages across revisions, and distinguish resume from explicit paid redo. A missing/uncertain submission receipt pauses rather than resubmits. Provider hedging and automatic transport replay are disabled for canonical Atelier pages only.
- Queue deployment boundary is one SKU Board server process. Exclusive request receipt creation also blocks duplicate same-token submission across processes; this is not a distributed multi-server scheduler.
- Interrupted running Atelier image jobs are not blindly rerun after restart; queued jobs require a currently active authorized account. Already submitted work may still complete and be billed even after cancellation.
- Executed 325 shared image/model regression tests and the COD regression group, plus 47 Node controller tests. Python compilation, JS syntax, HTML ID uniqueness (121 IDs) and whitespace checks passed.
- A localhost-only mock fixture exercised rules review, batched AI-review protocol, duplicate queue reuse, three synthetic PNG outputs, permanent asset reads and ZIP manifest. No live model or paid image generation was invoked.
- Browser automation could not connect because its app authorization was unavailable; visual/browser interaction acceptance remains unverified this turn. HTTP verified the live8793 HTML and JS return200 with v11, and unauthenticated project API correctly returns401.
- Production8793 was restarted with `--skip-startup-cleanup` after verifying no queued/running image jobs; existing unrelated expired temporary images and job records were not removed during this update. The isolated8795 fixture was stopped afterward.
