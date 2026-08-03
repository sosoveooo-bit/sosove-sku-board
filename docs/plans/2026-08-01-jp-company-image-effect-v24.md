# Japanese Landing Company-Image Effect V24 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the local “日本产品落地页 25图” produce company-like mature Japanese fashion images with photography-led composition, disciplined page-specific density, exact product/reference binding, and zero unplanned content.

**Architecture:** Keep the fixed 25-page story, model configuration, keys, and image-service nodes intact. Replace the universal 4–5 module construction with a deterministic 2–3 module page contract for ordinary pages and narrow structured contracts for comparison, pain-grid, craft, and size/color pages. Compile a shared suite visual bible plus a strict current-page content boundary into every Japanese-fashion prompt, and always attach the uploaded person reference to human pages when one exists.

**Tech Stack:** Python prompt planner (`sku_board/backend.py`), vanilla JavaScript reference transport (`sku_board/static/app.js`), JSON skill manifest, Python `unittest` regression suite.

---

### Task 1: Lock company-like density in tests

**Files:**
- Modify: `sku_board/tests/test_ai_image_suite.py`

**Steps:**
1. Assert hero and ordinary pages use only 2–3 planned modules.
2. Assert comparison, pain grid, craft, and size/color pages retain only their required structures.
3. Assert every final prompt contains the shared visual bible and strict no-extra-content boundary.
4. Assert ordinary prompts remove generic badge/icon/card expansion language.
5. Run the focused tests and confirm they fail before implementation.

### Task 2: Replace universal module expansion

**Files:**
- Modify: `sku_board/backend.py`

**Steps:**
1. Add deterministic JP page-density classification.
2. Build two-module hero pages, two/three-module focused pages, and narrow structured pages.
3. Rebuild local module contracts on every compile so cached legacy 4–5 module plans do not return.
4. Limit labels by page class and include only verified Japanese support copy.

### Task 3: Compile the visual bible and content boundary

**Files:**
- Modify: `sku_board/backend.py`

**Steps:**
1. Add one shared suite visual bible covering casting profile, product-derived palette, natural daylight, photographic grade, and Japanese type hierarchy.
2. Add a highest-priority boundary that permits only current-page modules, copy, product, action, and evidence.
3. Update local previsualization ratios to photography-led hero/focused layouts.
4. Update the second-pass director instruction so it may refine camera/light only and may not add modules.

### Task 4: Keep uploaded identity present on every human page

**Files:**
- Modify: `sku_board/static/app.js`
- Modify: `sku_board/tests/test_ai_image_suite.py`

**Steps:**
1. Reserve one reference slot for the first uploaded person reference on each JP human page.
2. Keep page 24 product-only.
3. Preserve product/detail/usage reference priority and the five-reference limit.

### Task 5: Version, verify, and restart

**Files:**
- Modify: `sku_board/backend.py`
- Modify: `sku_board/static/app.js`
- Modify: `sku_board/static/index.html`
- Modify: `sku_board/skills/gpt-image2.json`
- Modify: `sku_board/tests/test_ai_image_suite.py`

**Steps:**
1. Bump the JP plan to V24 and the image skill to 3.9.0.
2. Run all 214 tests with an isolated data directory.
3. Restart `http://127.0.0.1:8793/` and verify health plus the active skill/version in the browser.
