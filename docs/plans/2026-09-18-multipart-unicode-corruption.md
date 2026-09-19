# Root cause: Unicode corruption in multipart scalar fields

## Exact reproduction
The current saved 20-page plan was JSON-parsed/stringified in Node, appended to
native FormData and serialized via Request.arrayBuffer (the same web transport
semantics as the UI). Python CGI parsing changed agentPrompt on pages 5 and 9.
For example `ウォームグレー` became `ウォー��グレー`; `背景` became `���景`.
The database and browser-side JSON had not changed.

`cgi.FieldStorage.read_lines_to_outerboundary` reads at most 64 KiB per chunk.
For scalar fields its private writer independently decodes each chunk as UTF-8
with replacement errors. A 3-byte Japanese character spanning chunks is damaged.
Direct backend invocations and mocked uploads skipped that transport boundary.

## Fix
`ByteFieldStorage` preserves raw multipart body bytes for both scalar fields and
files, including normal temporary-file spillover. The existing request handler
decodes each complete scalar field once, with strict UTF-8. Header/filename parsing,
upload limits, request authentication, reference hashes and saved-plan checks remain
unchanged. No prompt comparison bypass, replacement-character stripping, cache
invalidation or model regeneration.

## Validation
- Old parser reproduces damage on synthetic Japanese/Thai/Chinese/emoji JSON >64 KiB.
- New parser roundtrips the same JSON exactly and preserves binary file bytes and
  Unicode filenames. Small/empty fields work; invalid UTF-8 raises an error.
- Actual saved plan through native FormData + request-handler parsing: 20/20 pages
  match the stored plan, including agentPrompt and its stored promptHash.
- Live verification uses that multipart path to render page 5 under the existing
  suite run, without re-planning or repeating product analysis. Local receipts and
  results: `.run/cod-wire-page5-*.json` (not committed fixtures).
