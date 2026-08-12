#!/usr/bin/env bash
set -euo pipefail

kit_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
return_dir="${1:?usage: verify-return.sh RETURN_DIRECTORY}"

python3 "$kit_dir/container/verify_return.py" \
  --return-dir "$return_dir" \
  --schema "$kit_dir/../receipt-schema-v1.1-candidate/decision-provenance-receipt-1.1.schema.json" \
  --corpus "$kit_dir/../decision-scope-census/corpus.json"
(
  cd "$return_dir"
  sha256sum -c RETURN-SHA256SUMS
)
