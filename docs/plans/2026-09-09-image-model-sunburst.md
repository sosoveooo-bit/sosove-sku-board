# Image Model Sunburst Default Implementation Plan

**Goal:** Add the user-supplied gateway IDs `gpt-image-2.5`, `gpt-image-2.5-flare`, and `gpt-image-2.5-sunburst` to the local image panel, retaining legacy/provider-specific choices and selecting sunburst by default.

**Architecture:** Centralize the ChatGPT2API model catalog and default in the Python backend, expose it through the existing configuration API, and keep the frontend bootstrap catalog/default consistent. Explicit selected model IDs must survive all submission paths. Migrate the browser's old implicit default once without changing in-flight jobs or historical image metadata. Change only the local default-model environment key; preserve node inventory, secrets, director configuration, prompt workflows and existing unrelated work.

**Tech Stack:** Existing Python HTTP server, JavaScript panel, unittest and Node VM mocks; no paid image generation.

## Implementation

1. Inspect current model selection, configuration precedence, browser persistence, asynchronous and synchronous submission, editing and recovery paths.
2. Add failing transport/configuration and frontend tests for the new IDs, sunburst default, explicit older/custom choices and one-time browser preference migration.
3. Update `sku_board/backend.py`, `sku_board/static/app.js`, `sku_board/static/index.html`, and `.env.example`. Keep the Acore catalog and product/director prompt rules separate and unchanged.
4. Adjust only `CHATGPT2API_IMAGE_MODEL` in the active local environment, verifying all other entries remain identical. Exclude local settings from Git.
5. Run isolated regression tests, Python/JavaScript syntax and diff checks. Verify models pass through mocked JSON, multipart and editing submissions unchanged.
6. When no local image jobs or active planning requests remain, restart the existing panel supervisor without clearing logs, then verify health and served model configuration/default. Do not deploy VPS or push GitHub in this task.

## Acceptance

- Model selector includes all four `gpt-image-2`/`2.5` IDs as supplied by the user.
- New default and migrated old implicit defaults select `gpt-image-2.5-sunburst`; deliberate future changes remain effective.
- Requests preserve selected IDs instead of rewriting them to `gpt-image-2`.
- Legacy and `acore/` provider choices remain available, node addresses/keys and historical results remain intact.
- Treat new IDs as gateway model identifiers, not as a claim of independently verified official OpenAI model availability.

## Completed — 2026-09-09

- Centralized the gateway catalog/default; configuration, request normalization, async JSON/multipart, sync image/edit and metadata defaults now resolve through the shared helper. Explicit request model IDs are preserved.
- Recovered remote images retain their own task model (including mixed-model batches); an unreported historical model is `unknown` rather than being mislabeled as today's default.
- Frontend main/ad-launch selectors and static bootstrap include the new IDs. New/default drafts follow the server default, explicit choices survive persistence and reload, and in-flight/completed runs retain their original model. Acore choices still follow the configured provider catalog.
- Changed only `CHATGPT2API_IMAGE_MODEL` in the shared local environment. Compared all other entries and saved director settings by hash; they remained identical. The resolved panel inventory remains seven nodes (six ChatGPT2API plus the company node).
- Read-only `/models` probes on all six ChatGPT2API nodes returned HTTP 200 and advertised all four requested GPT image IDs. No image-generation request was submitted.
- Validation: all **457 Python tests** passed using isolated data and mocked external requests; the existing **26 Node atelier tests** passed, JavaScript syntax and Git diff checks passed. The 12 new frontend and 14 model-transport tests cover selection, reload, provider isolation and outgoing model IDs.
- Restarted the existing hidden scheduled-task supervisor after confirming no active image/director work or established panel request connections. Reloading the supervisor also reloads the changed shared environment. Logs were retained; health is OK, and served JavaScript matches the current `20260909-image-models-v1` file.
- Main/local panel only: no VPS deployment, Git commit/push, prompt-rule change or unrelated atelier source edit. The browser smoke check reached the login screen; authenticated selectors are covered by isolated frontend tests rather than a real user sign-in. Actual generated-image quality was not tested.
