# COD source-driven online-only generation

Scope: COD country and COD detail suites; existing pages/UI and provider settings
remain intact. The 8795 client uses the shared engine automatically.

Diagnosis: the generation guard was conditional on companyEffectMode, permitting
incomplete online plans to render through local generic templates. Parallel
brief batches inherited local scene/pose/layout fields and lacked a whole-suite
source-driven evidence allocation. Generic Japanese fallback titles could be
frozen into the final copy.

Changes:
- Both suites always select company-effect planning and enforce existing complete,
  non-duplicate seven-layer checks at image submission regardless of stale flags.
- Increment COD plan versions to invalidate old client plans and analysis caches.
- Share a compact whole-suite evidence suggestion map by assigned source facts;
  these suggestions never establish product facts or override explicit requests.
- Remove local previsualization/scene/pose/layout fields before AI page writing;
  module IDs/content remain, but inherited positions are omitted.
- Support AI localizedHeadline for generic fallback copy; explicit copy retained.
- Put online page layers first; preserve the full brief once instead of repeated
  generic fidelity instructions. Deduplicate identical blocks. No silent final
  truncation: above provider limit returns an input error before generation.

Existing lexical route-duplicate audit remains; semantic suggestions are not
proof of visually different outputs. No post-generation AI review or auto-redraw.
Transport/model availability and upstream image obedience still affect results.
Tests use mocks/fixtures only, not paid generation. Real image quality needs a
small product trial after the current in-flight batch finishes.
