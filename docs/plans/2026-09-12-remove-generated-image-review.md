# Remove generated-image AI review

User requested removal, not a default-off preference. Delete automatic visual
review and score-driven regeneration from the suite generation path. All speed
profiles retain image quality/concurrency and transport retries but perform no
post-generation AI review. Remove review settings, monitor counters and results
display. Keep the authenticated legacy endpoint as a disabled response so older
clients cannot spend model quota. Preserve pre-generation planning, reference
locks, selling-point checks, image download/storage and missing-page recovery.

Validation includes a mocked endpoint asserting zero model calls and frontend
contracts asserting no auto-review invocation or review controls.
