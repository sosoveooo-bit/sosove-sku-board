# COD Hook AI Reference Analysis Plan

**Goal:** Make actual online product-image analysis mandatory before rendering uploaded-reference COD hook images, so product structure, real variants and correct use—not upload order or style references—control generation.

**Architecture:** Add a hook-only analyzer/cache/router module. Analyze every uploaded image individually with the configured vision director, validate complete indexed records, resolve explicit manual corrections and group same-variant views. Route only the selected product variant and its factual supporting images to the renderer; translate style references into presentation notes. Persist real analysis progress/results on the existing background image job and expose a product-analysis card in the existing hook UI.

## Boundaries

- Only `codHook` reference generation; text-only hooks, other suites, masked/current-image edits, frozen Atelier requests and all model/node settings retain their current behavior.
- Keep original user brief, selling-copy/no-text policy, exact source bytes and selected image model. No new provider fidelity parameter or invented product fact.
- Analyze 1–16 uploaded images without silently dropping images; oversized sets receive an explicit pre-generation validation error. Failed or incomplete online analysis stops before an image-generation submission.
- Cache only validated AI analysis, keyed by owner, complete prompt/context, manual roles, all original image hashes and model configuration. Do not treat a filename guess, OIP match or local template as a completed AI analysis.
- New/default hook references are auto-classified regardless of position; genuine manual corrections are retained. Same-variant front/back/detail images are grouped rather than treated as separate colors.

## Work

1. Implement `cod_hook_vision.analyze` and `prepare_generation`, strict schema/reference coverage validation, owner-scoped cache and variant-specific reference routing.
2. Add mandatory analysis after raw upload decoding and before every provider dispatch; bypass the OIP-gated visual-only hook enhancement when product analysis is active. Rebuild the hook prompt from its full current user source and append AI-confirmed product constraints and current copy policy.
3. Surface `productAnalysis` through job polling, final response and material metadata, with actual selected original-source indexes and variants. Show analyzing/ready/failed truthfully; ignore stale responses after the user changes references.
4. Add hook-only auto-role defaults/corrections and a readable product/structure/color/use analysis card. Keep the server's executed Prompt canonical.
5. Run isolated analyzer, cache, transport, frontend and scope regressions; use no live model/image calls. Activate locally only when existing image/director requests are idle. No VPS deployment or Git push in this task.

**Acceptance:** Product analysis is independent of OIP availability; every source image has a validated role; product variants and multiple views stay separate concepts; unrelated/style images do not donate product structure; original selling copy remains intact; failure never silently proceeds as if analysis succeeded.

## Completed — 2026-09-09

- Added the independent `cod_hook_vision` analyzer, strict complete-image schema validation, observed-fact minimum, integer source IDs, role alias normalization and owner-scoped 24-hour cache keyed by complete inputs and actual image bytes. Calls use the configured director, individual image inputs, a bounded analysis stage and no broken-stream replay.
- Every uploaded-reference hook now completes online product analysis before image dispatch. Text-only hooks and other modules retain their original paths. OIP matching is no longer a prerequisite for recognizing a hook product.
- Routing groups same-variant front/back views, preserves original bytes, excludes layout/style/scene bitmaps and unrelated products, and binds each output to its actual compact reference map. Both sync and async transports use the same output indexes; the older generic reference reorder is bypassed only for this server-generated hook mapping.
- Full user and selected-product selling copy remain in the final prompt. Image metadata records actual original reference indexes, variants and public analysis fields; internal cache/hash state is kept server-side. Failed recognition returns a failed analysis state before any image submission; an image-service failure after recognition preserves the completed analysis.
- Added Hook-only auto-role defaults including the first upload, optional manual corrections, input-count guard, stale-response protection and a real analysis card through initial/poll/final/error responses. Switching away from Hook removes its role scope.
- Validation: **644 Python tests and 47 Node controller tests passed**, plus Python/JavaScript syntax and diff checks. New coverage includes 25 analyzer tests, 7 complete-flow integration tests and 12 frontend cases. Mock desktop/mobile analysis cards were visually inspected; no user product images were sent to a live model and no paid image generation was performed.
- Local activation completed through the existing scheduled supervisor after verifying no image/Atelier work and no outgoing provider connections from the panel processes. Retired local panel launchers were consolidated to the canonical service, the new health endpoint returned OK and the served `20260909-cod-hook-vision-v1` script matches disk.
- Verified unchanged environment and director-setting hashes, default `gpt-image-2.5-sunburst` and seven image nodes. No Git commit/push or VPS deployment in this task. Actual output fidelity still requires a real original/result comparison.
