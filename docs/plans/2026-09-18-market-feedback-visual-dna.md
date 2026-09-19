# ADR: explicit market evidence, bounded feedback, shared visual DNA

## Decision
Country/detail Agent suites accept optional `marketKnowledge` and `marketFeedback` arrays.
Both panels can also accept these in the existing brief as JSON blocks:
`【市场资料】[...]【/市场资料】` and `【投放反馈】[...]【/投放反馈】`.
Market inputs are excluded from the original selling-point ledger. They are dated,
country/platform/category-scoped user observations, not verified external research.

Market record fields: country, platform, category (one value from product categories),
observedAt (YYYY-MM-DD), source, finding. Max 12 records per input, 16,000 characters.
Feedback additionally uses testId, comparisonContext and 2–4 variants with direction,
impressions, clicks, conversions. Counts must be nonnegative integers in valid order.
Out-of-scope, stale (>180 days), future or malformed evidence is excluded and displayed.

Strategy + visual direction -> one joint feedback review when eligible feedback exists
-> shared visualDNA -> page planning -> dynamic prompt -> existing image generation.
Default/no eligible feedback uses no extra model call. Success is checkpointed; failure
retains earlier stages. Continuation may retry a failed call, not a successful review.
Feedback gives descriptive rates, not significance, causality, or automatic winner selection.

The DNA is compiled locally from final director output: palette, typography, casting
policy, photographic language and variation policy. It does not lock a scene, pose,
camera angle or bitmap anchor. Every resolved prompt contains the same DNA and ID.
Product color identity takes priority over campaign color. No post-render AI review.

## Trade-offs and limits
No automatic web search or link fetching; sources are recorded, not independently verified.
No new A/B/C manual selection UI in this change. Direction remains automatically authored.
Structured input is less convenient than an import wizard, but preserves both existing UIs
and avoids hidden network/token cost. Short, fixed constraints are not layout templates.
Rendered compliance is not proven by string validation; paid visual testing remains separate.

## Compatibility
Product cache keys unchanged. New campaign revision redoes creative planning; persisted old
plans remain usable. Market fields affect new campaign fingerprints; empty fields preserve
old hash behavior. No changes to COD hook, Japanese suite or image generation interfaces.
