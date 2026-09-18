#!/usr/bin/env python3
"""
Re-applies the local customizations that `openapi-to-postmanv2` doesn't know
about: baseUrl/bearerToken defaults, the collection description, and
auto-auth test scripts on the login/register requests.

Run after regenerating DBC_Backend.postman_collection.json from openapi.yaml
(see docs/postman/README.md).
"""
import json
from pathlib import Path

COLLECTION_PATH = Path(__file__).parent / "DBC_Backend.postman_collection.json"

DESCRIPTION = (
    "Digital Business Card SaaS API — auto-generated from the live Django REST Framework "
    "backend's OpenAPI schema (drf-spectacular), so it always matches the actual code.\n\n"
    "## Quick start\n"
    "1. Set the `baseUrl` collection variable (defaults to `http://127.0.0.1:8000` for local dev).\n"
    "2. Run **api > v1 > auth > auth register create** or **auth login create** — a test script "
    "automatically captures the `access` token into the `bearerToken` collection variable.\n"
    "3. Every authenticated request uses `Bearer {{bearerToken}}` automatically — nothing else to configure.\n"
    "4. Tokens expire after 30 minutes (access) / 14 days (refresh) — just re-run login to refresh `bearerToken`.\n\n"
    "## Structure\n"
    "- `api/v1/...` — authenticated dashboard API, mirrors the app layout (auth, organizations, vcards, "
    "billing, appointments, analytics, orders, nfc, enquiries, notifications, directory, templates).\n"
    "- `api/public/cards/...` — unauthenticated public card JSON API.\n"
    "- `directory/` — public directory search.\n"
    "- `health/` — health checks.\n\n"
    "Note: the server-rendered public card page itself (`/@<slug>/`), `.vcf` download, and QR image "
    "endpoints return HTML/binary, not JSON, so they're not part of this OpenAPI-derived collection — "
    "hit them directly in a browser, e.g. `{{baseUrl}}/@<slug>/`."
)

LOGIN_SCRIPT = [
    "if (pm.response.code === 200 || pm.response.code === 201) {",
    "    const data = pm.response.json();",
    "    if (data.access) {",
    "        pm.collectionVariables.set('bearerToken', data.access);",
    "        console.log('bearerToken updated from', pm.info.requestName);",
    "    }",
    "}",
]


def walk(items):
    for item in items:
        if "item" in item:
            yield from walk(item["item"])
        else:
            yield item


def main():
    data = json.loads(COLLECTION_PATH.read_text())

    data["variable"] = [
        {"key": "baseUrl", "value": "http://127.0.0.1:8000", "type": "string"},
        {"key": "bearerToken", "value": "", "type": "string"},
    ]
    data["info"]["description"] = DESCRIPTION

    patched = 0
    for req in walk(data["item"]):
        path = "/".join(req.get("request", {}).get("url", {}).get("path", []))
        if req["request"]["method"] == "POST" and path in {"api/v1/auth/login/", "api/v1/auth/register/"}:
            req["event"] = [e for e in req.get("event", []) if e.get("listen") != "test"]
            req["event"].append({"listen": "test", "script": {"type": "text/javascript", "exec": LOGIN_SCRIPT}})
            patched += 1

    COLLECTION_PATH.write_text(json.dumps(data, indent=2))
    print(f"Patched {patched} auth request(s), set variables and description.")


if __name__ == "__main__":
    main()
