# Director JSON input compatibility

## Evidence

The cached German campaign reached 15/24 prompts, then its gateway returned HTTP
502 with: `Response input messages must contain the word 'json' ... 'text.format'
... 'json_object'`. This is an explicit format-validation response, not evidence
of exhausted credits or an image-render failure.

The local transport sends Chat Completions `response_format: json_object`. The
pipeline's JSON instruction was only in the system message; its user message
contained context data and optional images. The upstream error mentions Responses
`text.format`, consistent with a translating gateway that excludes system
instructions from the input-message check. The gateway's internals are not locally
observable.

## Fix

- With JSON mode enabled, copy the message list and add a concise lowercase `json`
  output instruction to the last user message. Handle both plain text and image /
  text arrays; preserve image content and do not mutate caller-owned inputs.
- Keep non-JSON requests unchanged. Repeated preparation is idempotent.
- Recognize this exact JSON-input validation failure under HTTP 400 or 502 before
  generic gateway fail-fast. Permit one compatibility retry without the optional
  response-format parameter, while retaining the textual JSON contract.
- Keep auth, billing and unrelated gateway errors out of that retry branch.
- Existing structured parsing, per-page validation, time budgets and cancellation
  checks remain active. No new product analysis or generated-image review.

## Verification

- Ten structured-output/transport tests pass, including the new input-placement,
  immutability, multimodal preservation and bounded-retry regressions.
- All 66 visual-agent regressions and three director-chain tests passed.
- Live continuation advanced the existing German campaign from 15 to 21 validated
  prompts, with no product reanalysis or repeated completed pages. The missing-json
  validation error did not recur in these requests.
- The final three pages then received a different generic HTTP 502:
  `The request could not be processed. Please check the request parameters.`
  The response does not identify the offending parameter; completion of all 24
  prompts or image generation has not been verified. Work remains checkpointed.
- Local service 8793 was reloaded after active work finished; health returned OK.
