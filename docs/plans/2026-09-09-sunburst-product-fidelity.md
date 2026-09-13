# Sunburst Product Fidelity Implementation Plan

**Goal:** Improve the fidelity of product-reference generation with `gpt-image-2.5-sunburst` by ensuring the intended product and detail images actually reach the renderer, with a precise product-detail contract and high-quality automatic rendering.

**Architecture:** Preserve original upload bytes and reference budgets. Correct explicit primary-variant mapping using original upload identity, keeping normal rotation when no primary variant was assigned. Reserve a diagnostic detail slot in the existing JP25 backend reference budget. Apply a Sunburst-only product-detail instruction and auto-to-high quality resolution to ordinary uploaded-reference generation without overriding explicit edit intent, fixed atelier prompts, masked edits, manual quality settings or text/layout rules.

**Tech Stack:** Existing Python image transport, JavaScript reference selection, isolated unittest and Node VM tests. No paid generation or image manipulation.

## Implementation

1. Trace uploads and schemas: original files are passed to multipart unchanged; director analysis thumbnails are separate. The configured gateway advertises `quality`, but its inspected OpenAPI document does not declare `input_fidelity`, so add no speculative provider parameter.
2. Fix frontend original-index mapping after style filtering and COD explicit-variant precedence. Preserve established multi-color rotation, first-page full ranges and provider-specific style isolation.
3. Reserve one useful detail image in the JP25 four-reference backend budget rather than allowing duplicate usage references to crowd it out.
4. For Sunburst reference generation, keep original source identity, documented construction, true material texture, color/pattern, proportions and physical labels explicit. Unsupported features and hidden product faces must not be invented. Honor deliberate user changes and preserve allowed on-image selling copy.
5. Upgrade only automatic quality to high on this reference-generation path. Preserve explicit low/medium/high selections, fast suite profiles, other models, text-only generation and existing edit/atelier contracts.
6. Test final submitted prompts, model/quality, original upload bytes, primary variant selection and detail-slot retention. Run full regressions, preserve model/node settings and activate locally only after running image/director jobs finish. No Git push or VPS deployment.

## Verification limits

Generation remains probabilistic: code/transport tests establish that the correct references and instructions are sent, not pixel-identical product reproduction. No fresh product/result pair was supplied in this request and no paid sample image will be generated without a separate request.

## Implementation and regression results — 2026-09-09

- Corrected original-upload primary-variant mapping after role filtering, matching original File identity rather than filenames or shifted indexes. COD honors a valid explicitly assigned variant; ordinary automatic rotation and complete-range reference budgets remain unchanged.
- JP25 human-page reference selection now reserves one diagnostic product detail before extra usage/person views exhaust the existing four-image budget. Original image bytes remain unchanged in both synchronous and asynchronous multipart requests.
- Sunburst ordinary product-reference generation now appends the product-detail fidelity contract to the base, per-page dispatch and saved prompt metadata. Shape, construction, materials, patterns, colors, physical labels and documented parts are fixed; style/person references have separate roles. Explicit named product edits and permitted marketing copy remain binding.
- Automatic quality becomes high only on this Sunburst product-reference path. Explicit quality, fast profiles, other models, pure text generation, style/person-only references, masked edits, direct existing-image edits and frozen atelier prompts retain their previous treatment.
- The configured gateway's read-only OpenAPI document advertises quality support; no speculative `input_fidelity` field was added. No image-generation request or public upload was made by the agent.
- Final regression run: **537 Python tests passed**, including 19 new backend fidelity/transport cases and 7 original-reference frontend cases. Python/JavaScript syntax and Git diff checks passed. No Git commit/push or VPS deployment.
- Local activation is gated on zero image/director jobs and no established panel requests, preserving active user work and logs. User image jobs completed during the wait; in-flight page requests still required a further idle-window check. Record the final activation outcome below.

### Activation outcome

The bounded idle checks still observed in-flight work after image jobs finished. No stop/restart was performed: the existing panel process was deliberately preserved. Source changes and all tests are complete, but the backend Sunburst detail contract and automatic high-quality path remain pending a restart when requests finish or an explicit user-approved interruption. The browser source revision is `20260909-sunburst-detail-v1`. No background restart or future automation was scheduled.
