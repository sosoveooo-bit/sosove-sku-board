# Giikin Acore Image Provider

## Goal

Expose the three company image models in the SKU Board image panel as normal,
explicitly selectable models:

- `gpt-image-2`
- `nano-banana-2`
- `nano-banana-pro`

They are not fallback nodes. Selecting a company model routes the request only
to Giikin Acore; existing ChatGPT2API models continue to use the existing node
pool.

## Design

The browser uses provider-qualified model IDs (`acore/<model>`) so the duplicate
`gpt-image-2` name remains unambiguous. Display labels hide this implementation
detail and show `Company - <model>` in the model selector.

The backend reads `ACORE_IMAGE_AUTH_KEY` and `ACORE_IMAGE_BASE_URL` from the
environment. It submits JSON requests to `/task/generate/image` with the raw
personal key in the `Authorization` header, then polls
`/task/image/{taskId}` until completion. Returned image URLs are downloaded by
the backend and stored through the panel's existing output pipeline. The key is
never returned to the browser.

Panel sizes are mapped to the closest Acore aspect ratio from `1:1`, `16:9`,
`9:16`, `4:3`, and `3:4`. Reference images are encoded as data URLs for the
documented `inputImages` field. Mask-based inpainting remains on the existing
provider because Acore does not expose a mask contract.

Health checks use the authorized task-detail endpoint with a nonexistent probe
ID, which validates connectivity and authentication without creating a paid
image task. The Acore provider appears as its own node card and is filtered into
suite capacity calculations only when an Acore model is selected.

## Verification

Unit tests cover configuration redaction, model routing, aspect-ratio mapping,
health probes, async polling, image downloads, and provider dispatch. Final
verification includes the existing AI image test suite, a live health check,
and a browser pass on `http://127.0.0.1:8793/`.
