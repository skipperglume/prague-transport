#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_FILE="$SCRIPT_DIR/secrets.txt"

if [[ ! -f "$SECRETS_FILE" ]]; then
	echo "Error: $SECRETS_FILE not found"
	return 1 2>/dev/null || exit 1
fi

GOLEMIO_API_KEY="$(head -n 1 "$SECRETS_FILE" | tr -d '\r' | xargs)"
if [[ -z "$GOLEMIO_API_KEY" ]]; then
	echo "Error: secrets.txt is empty"
	return 1 2>/dev/null || exit 1
fi

export GOLEMIO_API_KEY
source "$SCRIPT_DIR/golemio_venv/bin/activate"
