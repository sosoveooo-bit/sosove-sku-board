# COD director latency

Scope: local COD country and detail company-mode planning only. Preserve full
seven-layer prompts, selling-point binding, reference inputs, duplicate auditing,
provider configuration and concurrency.

- Reuse matching complete/partial cache on initial COD planning instead of
  forcing analysis every time. Existing cache signatures invalidate changed input.
- Carry the round absolute deadline through model failover and split retries.
- Skip duplicate same-model stream retries in COD refinement; keep model failover
  and existing missing-page/split recovery.
- Report refinement wall time separately from aggregate request time.
- COD waiting UI reports returned pages and elapsed time rather than advancing
  fictional stages on a timer. This is not live per-batch server progress.

Limitations: HTTP connect/read timeouts are not a hard wall-clock cancellation.
Active requests can finish after deadline; no new model attempt starts once the
shared budget has fewer than five seconds. Live streaming progress and per-batch
durable checkpointing are not introduced by this patch.

Validation: suite regression, COD frontend contracts, deadline unit tests and JS
syntax check. No production generation or paid upstream requests for tests.
