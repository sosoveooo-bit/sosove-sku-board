# AI Creative Workshop Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the SOSOVE AI image workspace as focused and guided as the company workshop while improving multi-image product analysis and director-owned page execution.

**Architecture:** Keep the existing single-page application and image-generation APIs, but introduce a focused AI workspace state in the frontend. Expand suite planning so the director receives all product references, owns product-specific creative fields for Japanese landing pages, and preserves fixed platform/page-role constraints as guardrails. Keep local fact-locking, output sanitization, node pooling, and fallback behavior.

**Tech Stack:** Python backend, vanilla JavaScript SPA, HTML/CSS, `unittest` regression tests.

---

### Task 1: Add regression coverage

**Files:**
- Modify: `D:\Backup\Documents\New project\sosove-sku-board\sku_board\tests\test_ai_image_suite.py`

1. Add a test that `10` is a supported Japan landing-page count and produces exactly ten coherent pages.
2. Add a test that the upload planner sends every uploaded product reference to the director in stable order.
3. Add a test that Japanese landing-page director output may refine focus, scene, pose, composition, visual treatment, headline, and reference indexes without changing page count, page role, archetype, or canvas.
4. Add a frontend source test for the focused AI workspace and quick-entry cards.
5. Run the focused tests and confirm they fail before implementation.

### Task 2: Expand multi-image director input

**Files:**
- Modify: `D:\Backup\Documents\New project\sosove-sku-board\sku_board\backend.py`

1. Normalize a list of up to eight director reference images.
2. Hash all reference images in the product-analysis cache key.
3. Attach every reference to the director request with a stable image number and filename.
4. Update upload planning to read all references instead of only the first.
5. Preserve compatibility for existing callers that pass one reference tuple.

### Task 3: Let the director own product-specific execution

**Files:**
- Modify: `D:\Backup\Documents\New project\sosove-sku-board\sku_board\backend.py`

1. Expand the director JSON contract with scene, pose, composition, visual effect, headline, and reference indexes.
2. For Japanese landing pages, merge these product-specific fields into locked base pages.
3. Preserve page number, role, archetype, canvas, market rules, and fact sanitization.
4. Keep rule-based output as the fallback when the director is disabled or unhealthy.

### Task 4: Correct selectable counts

**Files:**
- Modify: `D:\Backup\Documents\New project\sosove-sku-board\sku_board\backend.py`
- Modify: `D:\Backup\Documents\New project\sosove-sku-board\sku_board\static\app.js`

1. Add ten images as a supported Japan landing-page count.
2. Add a ten-page subset to the fixed fallback recipe.
3. Ensure task labels, progress, completion, and recovery use the requested count rather than the 32-page template maximum.

### Task 5: Focus the AI workspace

**Files:**
- Modify: `D:\Backup\Documents\New project\sosove-sku-board\sku_board\static\index.html`
- Modify: `D:\Backup\Documents\New project\sosove-sku-board\sku_board\static\app.js`
- Modify: `D:\Backup\Documents\New project\sosove-sku-board\sku_board\static\styles.css`

1. Hide board-only summaries, filters, insights, search, import, Facebook sync, clear-product, and add-SKU actions while AI Creative is active.
2. Update the header identity to “AI 创意工坊” in the AI view and restore the board title elsewhere.
3. Add quick entries for landing-page generation, reference localization/refresh, and free creative generation.
4. Add a three-step visual guide: product and references, generation plan, results and revision.
5. Move service diagnostics into a collapsible advanced area so business users see the generation workflow first.

### Task 6: Verify

1. Run the focused AI image suite tests.
2. Run the full test suite.
3. Restart the local service if required.
4. Open `http://127.0.0.1:8793/`, switch to AI Creative, and verify the focused layout and quick entries.
5. Confirm a ten-page plan reports `10/10` and that the director request contains all uploaded product references.
