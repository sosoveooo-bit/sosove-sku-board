# Security Policy

## Supported versions

Only the `main` branch receives security fixes. Deployments should track the
latest commit rather than a pinned archive.

## Reporting a vulnerability

Report suspected vulnerabilities privately through GitHub's
[private vulnerability reporting](https://docs.github.com/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
on this repository. Do not open a public issue for an unpatched problem.

Please include the affected commit, the deployment mode (local, Docker, Nginx),
reproduction steps, and the impact you believe the issue has.

Expect an initial acknowledgement within a few business days. There is no bug
bounty program.

## Deployment hardening

The panel stores account records, provider credentials and generated material.
It is designed to run behind your own network boundary. Before exposing it:

- Set `SKU_BOARD_ADMIN_PASSWORD` and `SKU_BOARD_CREDENTIAL_ENCRYPTION_KEY` to
  unique random values. Never reuse the example placeholders.
- Keep `.env` on the host only. The repository ignores `.env`, `data/`, `.run/`,
  logs, databases and key material by default.
- Terminate TLS at Nginx (see `deploy/nginx/`), then set
  `SKU_BOARD_SECURE_COOKIE=1` and a real `SKU_BOARD_PUBLIC_URL`.
- Restrict the panel port with a firewall or a private network. The application
  does not ship its own authentication hardening against internet-wide scans.
- Give each integration its own credential. Rotate a key immediately if it was
  ever committed, pasted into an issue, or written to a log.

## Out of scope

- Vulnerabilities in third-party image, director or platform APIs you connect.
- Claims about the accuracy of AI-generated commercial or medical copy.
- Denial of service from your own generation workload or provider quotas.

## Secrets in this repository

The repository contains no credentials, tokens, customer data, or generated
material. `.env.example` lists configuration keys with placeholder values only.
If you find a real secret in the history, report it privately so it can be
rotated and purged.
