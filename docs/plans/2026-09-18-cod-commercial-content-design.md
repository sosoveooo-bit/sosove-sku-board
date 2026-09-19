# COD product identity and commercial content isolation

User approved optimizing the existing five-stage system, without changing image
interfaces or introducing generated-image AI review. The German example exposed
image-only identity inference, cached provisional classification, and internal
evidence notes being rendered as advertisements.

## Implementation

1. Supply the original product/campaign brief to first product analysis as
   user-supplied context, alongside explicit product facts and images. Keep
   image observations, seller declarations and uncertainty distinct. Add a
   structured identity assessment; material identity conflicts require a seller
   clarification before strategy, not automatic product reclassification.
2. Version the product contract once. Preserve old records and completed outputs.
   Cache subsequent use across country/size/style changes. Explicitly corrected
   product facts change the cache key. Provide a persistent product-facts editor
   on the COD monitor so identity/specification corrections are intentional.
3. Keep missingInformation/assumptions on the operator panel. Strategist and
   director create buyer-facing value explanations, not audit posters. Unknown
   claims stay unknown and are not upgraded into evidence.
4. Add commercial intent, benefit visualization and information hierarchy to
   PageSpecs. Preserve varied scenes, shots and layouts under shared visual DNA.
5. Run deterministic pre-render internal-copy checks; use the existing bounded
   per-page repair loop. The image prompt explicitly separates renderable copy
   from internal metadata. No new review agent or post-render call.

## Verification and deployment

Regression tests cover description transmission, identity conflict checkpoints,
cache reuse/correction, copy leakage, valid consumer instructions, UI escaping,
persistence and changed-profile submission rejection. Existing legacy image,
reference, cancellation and zero-review paths must pass. Reload local 8793 only
  when idle. Do not overwrite old images or start a paid suite during this change.

## Verified implementation

- Product contract v2 receives userBrief plus explicit seller productFacts. Old
  cache records remain intact; the updated contract analyzes once on next use,
  then reuses the result across campaign changes. Correct product identity/specs
  through the new explicit profile field, not by relying on a style-only prompt
  to invalidate product understanding.
- Identity conflicts checkpoint the product stage and stop before strategy.
  Retry without new facts reuses the checkpoint instead of analyzing again.
- The profile editor is available on COD landing/detail screens, persists locally
  and is transmitted by planning, plan sync and rendering requests. Saving uses
  no model calls. Existing finished work stays in the original local panel task;
  a correction task opens with a separate run and review-before-render mode.
- Deterministic replay of the historical German campaign flags the actual
  leaked copy on pages 18 and 21 (`nicht dokumentiert`, `Durch die Bilder
  gestützt`, `Nicht belegt`). Historical prompts/images were not changed.
- 74 visual-agent Python tests pass, plus 6 multipart/director-chain tests.
  Five frontend regression scripts and JavaScript syntax checks pass.
- No claim of matching company image quality is made before sample rendering.
  No paid model/image runs were started during this optimization.
