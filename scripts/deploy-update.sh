#!/usr/bin/env bash
set -euo pipefail

git pull --ff-only
docker compose up -d --build
docker compose ps
