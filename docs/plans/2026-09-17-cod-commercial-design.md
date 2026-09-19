# COD commercial design refinement

Scope: existing country/detail Agent pipeline only. Keep product cache, image interfaces,
legacy plans, Japanese suite and direct COD hook generation unchanged. No post-render AI review.

Implementation:
- Local category knowledge supplies choices, not a fixed page template or live market research.
- Cached asset observations accompany role IDs so designers can choose relevant references.
- PageSpecs record subject, visual method, layout family, human role, visual hook and reference rationale.
- Local plan checks detect repeated structural combinations and near-identical scene/layout prose.
- One targeted repair per request; retain draft and upstream artifacts for continuation.
- Dynamic prompts start with page-specific decisions and receive only selected asset descriptions.
- Creative revision invalidates campaign cache without invalidating product cache or old stored submissions.

Verification: mocked transport tests, cache/compatibility tests and frontend contracts. No paid generation.
Limitations: structured checks are not image similarity analysis; prose/labels may still misrepresent the output.
Prompt length is a drafting target, not silent truncation. Real visual improvement requires subsequent user sample generation.
