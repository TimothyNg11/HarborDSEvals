#!/bin/bash
# Source this script to load API keys from .env into the current shell.
# Tolerates the dotenv-style 'KEY = value' format that bash 'source' rejects.
#
#     source scripts/load_env.sh

_ENV_FILE="$(dirname "${BASH_SOURCE[0]}")/../.env"
if [ ! -f "$_ENV_FILE" ]; then
    echo "load_env.sh: .env not found at $_ENV_FILE" >&2
    return 1 2>/dev/null || exit 1
fi

while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    [[ -z "${line// }" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    # Split on first '=' then strip surrounding whitespace from both sides
    key="${line%%=*}"
    val="${line#*=}"
    key="${key#"${key%%[![:space:]]*}"}"   # ltrim
    key="${key%"${key##*[![:space:]]}"}"   # rtrim
    val="${val#"${val%%[![:space:]]*}"}"
    val="${val%"${val##*[![:space:]]}"}"
    # Strip surrounding quotes
    [[ "$val" =~ ^\"(.*)\"$ ]] && val="${BASH_REMATCH[1]}"
    [[ "$val" =~ ^\'(.*)\'$ ]] && val="${BASH_REMATCH[1]}"
    [[ -n "$key" && -n "$val" ]] && export "$key=$val"
done < "$_ENV_FILE"

unset _ENV_FILE line key val
