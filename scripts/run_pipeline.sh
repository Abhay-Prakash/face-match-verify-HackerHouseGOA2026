#!/usr/bin/env bash
# One-command demo runner for the face-match discovery pipeline.
#
# Prerequisites:
#   1. python -m venv .venv && source .venv/bin/activate
#   2. pip install -r requirements.txt
#   3. Copy .env.example -> .env and fill in keys (see README.md)
#   4. Deploy contract once: python -m src.blockchain.deploy
#
# Usage:
#   ./scripts/run_pipeline.sh
#   INPUT_IMAGE=path/to/photo.jpg IMAGE_URL=https://... ./scripts/run_pipeline.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

INPUT_IMAGE="${INPUT_IMAGE:-data/sample_input/person_a_1.jpg}"
IMAGE_URL="${IMAGE_URL:-}"

if [[ -z "$IMAGE_URL" ]]; then
  echo "ERROR: IMAGE_URL is required."
  echo "SearchApi.io needs a publicly reachable URL for the input photo."
  echo ""
  echo "Example:"
  echo "  IMAGE_URL=https://raw.githubusercontent.com/you/photo.jpg \\"
  echo "    ./scripts/run_pipeline.sh"
  exit 1
fi

if [[ ! -f "$INPUT_IMAGE" ]]; then
  echo "ERROR: Input image not found: $INPUT_IMAGE"
  exit 1
fi

if [[ -z "${CONTRACT_ADDRESS:-}" ]] && [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a && source .env && set +a
fi

if [[ -z "${CONTRACT_ADDRESS:-}" ]]; then
  echo "CONTRACT_ADDRESS not set — deploying HashRegistry first..."
  python -m src.blockchain.deploy
  # shellcheck disable=SC1091
  set -a && source .env 2>/dev/null || true && set +a
  if [[ -z "${CONTRACT_ADDRESS:-}" ]] && [[ -f data/output/deploy_info.json ]]; then
    CONTRACT_ADDRESS="$(python -c "import json; print(json.load(open('data/output/deploy_info.json'))['contract_address'])")"
    export CONTRACT_ADDRESS
    echo "Using contract from deploy_info.json: $CONTRACT_ADDRESS"
  fi
fi

echo "=== Face-Match Discovery Pipeline ==="
echo "Input:     $INPUT_IMAGE"
echo "Image URL: $IMAGE_URL"
echo ""

python main.py --input "$INPUT_IMAGE" --image-url "$IMAGE_URL"

echo ""
echo "=== Done ==="
echo "Outputs:"
echo "  data/output/match_result.json"
echo "  data/output/verification_log.json"
