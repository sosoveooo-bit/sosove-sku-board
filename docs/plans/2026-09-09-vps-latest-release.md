# Latest Local Project VPS Deployment Plan

**Goal:** Deploy the current tested local source snapshot, including uncommitted modules and static assets, to the existing panel on `VPS_IP`.

**Architecture:** Reuse the verified native systemd service, Python 3.12 virtual environment and `/opt/sosove/sosove-sku-board` directory. Stage and hash-check a source snapshot before maintenance, back up the existing server application/configuration/data, publish only manifest-listed files, and verify health and external access. Roll back code and the small environment change if startup verification fails.

## Boundaries

- Preserve the server's accounts, session/credential keys, seven image nodes, director settings, image/job records, storage/retention settings, Nginx configuration and unrelated services.
- Do not copy the local `.env`, local user data/images, `.venv`, caches or Git history over the server.
- Include all current `cod_prompt_*` modules, UI assets, required public Open Image Prompts corpus/code and the local Linkfox prompt-skill files needed by Amazon A+.
- Synchronize only the image default to `gpt-image-2.5-sunburst`; set an asset-root path only if needed for a previously missing deployment dependency. Never replace node addresses or authentication values.
- Preserve existing backups; do not perform Git push or paid image generation.

## Steps

1. Verify SSH against the previously known host key; inspect current service, directory, resource headroom and persisted jobs.
2. Run local isolated regression tests and syntax checks. Create a stable source/dependency archive and SHA-256 manifest from actual files rather than HEAD alone.
3. Upload into a private staging directory, verify hashes and validate Linux imports/tests with temporary data and external networking disabled.
4. Wait for active panel tasks/requests to finish, stop only this panel for a brief maintenance window, back up its current tree and service definition, install manifest-listed files and preserve server data.
5. Start the existing service, verify public port 8793 and expected API/static routes, compare runtime versions/node counts/configuration fingerprints and retain rollback artifacts.

## Initial findings

- Server: Ubuntu 24.04, Python 3.12.3, native `sosove-sku-board.service` active; panel port 8793. Port 80 belongs to the separate Shopline dashboard and will remain unchanged.
- Runtime data is `sku_board/data`, not root `data`. Existing image jobs were idle at the initial inspection.
- Previous runtime reported JP25 `director-v30-fine-fashion-photo`, seven image services, local image storage and a seven-day TTL. Open Image Prompts data was incomplete.
- Local full regression: 587 Python tests plus 26 Node tests passed before staging.
