#!/usr/bin/env python3
"""Print a secret-free SKU Board deployment summary."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sku_board import backend


def main() -> None:
    skill = backend.ai_image_skill_config()
    landing = next(item for item in skill["templates"] if item["key"] == "landing")
    director = backend.public_ai_director_settings(backend.load_ai_director_settings())
    inspiration = backend.open_image_prompts_status()
    service_count = len(backend.public_chatgpt2api_service_nodes())
    service_count += int(bool(backend.public_acore_image_service_node()))
    print(
        json.dumps(
            {
                "skillVersion": skill["version"],
                "planVersion": landing["planVersion"],
                "suiteCount": landing["count"],
                "suiteSize": landing["size"],
                "imageServiceCount": service_count,
                "directorConfigured": bool(director.get("configured")),
                "directorEnabled": bool(director.get("enabled")),
                "openImagePromptsReady": bool(inspiration.get("ready")),
                "openImagePromptsTaxonomy": inspiration.get("taxonomyVersion"),
                "outputTtlSeconds": int(os.environ.get("AI_IMAGE_OUTPUT_TTL_SECONDS", "86400")),
            },
            ensure_ascii=False,
        )
    )
    if "--probe" not in sys.argv[1:]:
        return
    image_health = backend.check_ai_image_service({"username": "deploy-check", "role": "admin"})["health"]
    print(
        json.dumps(
            {
                "imageServices": {
                    "status": image_health["status"],
                    "configured": image_health["configuredNodeCount"],
                    "healthy": image_health["healthyNodeCount"],
                    "nodes": [
                        {
                            "id": item.get("id"),
                            "name": item.get("name"),
                            "status": item.get("status"),
                            "httpStatus": item.get("httpStatus"),
                            "latencyMs": item.get("latencyMs"),
                            "accountPoolReady": item.get("accountPoolReady"),
                        }
                        for item in image_health.get("nodes", [])
                    ],
                },
            },
            ensure_ascii=False,
        )
    )
    settings = backend.load_ai_director_settings()
    public_settings = backend.public_ai_director_settings(settings)
    try:
        response = requests.get(
            f"{str(settings.get('baseUrl', '')).rstrip('/')}/models",
            headers={"Authorization": f"Bearer {settings.get('apiKey', '')}"},
            timeout=15,
        )
        payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        available_models = [
            str(item.get("id"))
            for item in payload.get("data", [])
            if isinstance(item, dict) and item.get("id")
        ]
    except Exception:
        available_models = []
    try:
        director_health = backend.test_ai_director_service(
            {}, {"username": "deploy-check", "role": "admin"}
        )["director"]
        director_probe = {
            "status": director_health["status"],
            "activeModel": director_health["activeModel"],
            "fallbackUsed": director_health["fallbackUsed"],
            "latencyMs": director_health["latencyMs"],
        }
    except Exception as exc:
        director_probe = {
            "status": "error",
            "configuredModel": public_settings.get("model"),
            "availableModels": available_models,
            "message": str(exc),
        }
    print(json.dumps({"director": director_probe}, ensure_ascii=False))


if __name__ == "__main__":
    main()
