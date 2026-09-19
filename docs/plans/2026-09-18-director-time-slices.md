# Director planning time slices

Observed failure: a 240-second request completed page planning and six prompts, then
launched another prompt batch with only twenty seconds left. The UI classified the
resulting DirectorBudgetExhausted as an image-provider timeout.

Fix: reserve a stage-specific window before submitting any director call. Estimate
using recent successful durations plus margin, with floors (75s prompt/strategy,
90s product/direction, 140s planning), bounded by the fresh request window. Yield
before launching insufficiently budgeted work. Product and creative caches unchanged.

A yield is a checkpoint/continuation response, not a model failure. Clients continue
within their existing five-round bound only when durable work advanced. Product,
strategy, direction and planning progress count even when ready prompt count is zero.
If no progress is made, stop automatic continuation; preserve upstream failures as
real errors. Cancellation remains independent. After the bound, display a manual
continue-planning action, never remote-image recovery for a planning timeout.

Tests use a simulated slow 24-page campaign across multiple windows, verify no stage
repetition or last-20-second submissions, and check no-progress termination and both
frontend diagnostic/continuation paths. No paid image calls used for this repair.
