# Contributing

Thanks for improving SOSOVE SKU Board. This project is a self-hosted operations
panel, so changes must keep the offline test suite green and must not require
paid model or image requests.

## Getting set up

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\activate
pip install -r sku_board/requirements.txt
cp .env.example .env
python -m sku_board.server --host 127.0.0.1 --port 8793
```

Node.js 18 or newer is required for the frontend contract tests.

## Before opening a pull request

Run the suites that cover your change:

```bash
python -m unittest discover -s sku_board/tests -p "test_*.py"
python -m unittest discover -s cod-chat-studio -p "test_*.py"
python -m unittest discover -s shopline_monitor/tests -p "test_*.py"
node --check sku_board/static/app.js
```

The `sku_board/tests/*.cjs` files are standalone Node harnesses. Run each one
directly, for example:

```bash
node sku_board/tests/test_visual_agent_frontend.cjs
```

## Ground rules

- **No real credentials or customer data.** Use fixture values such as
  `fixture-token` or `example.com`. `.env`, `data/`, `.run/`, logs, databases
  and key material are git-ignored; keep them that way.
- **No network calls in tests.** Patch the transport layer instead of contacting
  a provider. Tests must pass with no `.env` and no internet access.
- **Keep the generation pipeline free of post-render AI review.** The COD
  workload deliberately avoids a second model pass per image to control cost.
  Do not add a review step that runs per generated image.
- **Preserve product identity.** Prompt and plan changes must keep the uploaded
  product's real category, shape, materials, colours and visible text intact.
- **Document intentional behaviour changes.** Several tests intentionally skip
  expectations for removed routes. When you change a contract, update the test
  and explain why in the pull request.
- **Keep vendor code separate.** `open-image-prompts/` is a bundled third-party
  project with its own `LICENSE` and `DATA_LICENSE.md`. Do not relicense it.

## Commit and pull request style

Write short imperative commit subjects. In the pull request, describe the user
visible effect, list the suites you ran, and call out any migration needed for
existing saved plans or cached data.

## Reporting bugs

Open a GitHub issue with the panel version, deployment mode, reproduction steps
and the exact error text. Redact tokens, hostnames and customer data first.
Security problems go through `SECURITY.md` instead.
