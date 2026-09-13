# COD Hook Image Result List Repair

**Goal:** Fix successful multi-node COD hook images being discarded by the collector, preserve original output identity on partial success, and recover already generated matching results without submitting more images.

**Verified cause:** Per-node non-partial calls return image lists. The multi-node per-prompt collector handled only dictionaries, so five successful node results were merged into an empty output list. The recent hook analysis completed successfully; the failure was downstream result aggregation. A gateway502 also caused a retry in the later attempt.

## Changes

1. Normalize complete per-node image lists into indexed outputs using the original assigned page indexes before merging. Preserve the old single-node and single-page hedge behavior. Empty/short unindexed lists are errors, not invented page mappings or blind resubmissions.
2. Bind partial hook materials to their actual successful output indexes for Prompt, reference-source indexes and variant IDs. Return the hook partial-result summary rather than silently discarding it.
3. Add owner-scoped, exact-analysis/model/count/size lookup of already saved hook results and a GET-only recovery action in the existing failed-hook UI. No new generation calls from the recovery action.
4. Query the configured providers read-only, verify candidate tasks against the failed job's complete analyzed source-fact map and time window, preserve their original image bytes, and restore confirmed results with an audit backup. Retain duplicate-attempt images separately.
5. Run isolated full-collector and public-flow regressions, activate locally when idle, verify configuration preservation. Do not push GitHub or deploy VPS in this repair.

## Verification and recovery outcome

- Multi-node list results now become indexed outputs before collection. Single-node/single-page behavior is retained. Short lists stop with an explicit count mismatch instead of invented associations or another automatic submission.
- Partial hook successes retain their original Prompt, reference indexes and variant IDs; the returned partial summary is visible to the UI.
- Added owner-scoped read-only recovery plus a failed-hook action. It matches the complete analysis key, model, requested count and canvas; it submits no generation request and ignores stale UI responses.
- All **671 Python regression tests passed**, including 11 collector cases, a full hook partial-metadata case, 4 owner/query isolation cases and 11 frontend recovery cases. JavaScript syntax and diff checks passed.
- Read-only provider inspection found **15 successful artifacts** matching the two failed jobs' time windows, Sunburst model, canvas and exact analyzed reference-fact maps. Original bytes were downloaded and verified; there were zero new image submissions during investigation/recovery.
- Restored five selected images to each failed job. The latest task uses its last completed five-image attempt; earlier retry artifacts remain in a separate 15-image ZIP. The pre-recovery job JSON was backed up before updating only these two owned records.
- Local service was restarted after checking for active work, and health/static version checks passed. The authenticated recovery route is registered; anonymous requests return401. The lookup finds the latest five restored images, whose SHA-256 hashes match the downloaded originals. ZIP integrity and all15 entries were verified.
- Recovery artifacts: `D:/Backup/Documents/New project/.run/hook-image-recovery-20260909-220601/`. Browser script: `20260909-hook-result-return-v1`. No VPS deployment or Git push in this repair.
