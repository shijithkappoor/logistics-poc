#!/usr/bin/env bash
# Helper: generate TypeScript types from backend OpenAPI
# Requires: npm install -D openapi-typescript

set -euo pipefail

OPENAPI_URL=${1:-http://localhost:8000/openapi.json}
OUT_FILE=${2:-src/services/generated-api-types.d.ts}

echo "Fetching OpenAPI from ${OPENAPI_URL}"
npx openapi-typescript "${OPENAPI_URL}" --output "${OUT_FILE}"
echo "Wrote types to ${OUT_FILE}"
